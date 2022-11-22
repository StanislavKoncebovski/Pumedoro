import xml.etree.ElementTree as ET
from xml.dom import minidom
from xml.etree.ElementTree import Element as XElement
import requests
from pubmed_author import PubMedAuthor

class Pumex:
    '''
    PUMEX = PubMed Author Extractor.
    '''
    #region Class Constants

    # default URL base to query for publication IDs.
    NCBI_SEARCH_REQUEST_BASE    = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed"

    # Number of IDs in a partial request for IDs.
    NUMBER_OF_IDS_IN_PARTIAL_REQUEST = 1000

    # Default URL base to fetch the publication infos.
    NCBI_FETCH_REQUEST_BASE     = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed"

    # Default number of entries in an extraction portion.
    DEFAULT_SIZE_OF_EXTRACTION_PORTION = 200
    #endregion

    def retrieve_authors(self, topics: list[str]) -> list[PubMedAuthor]:
        '''
        Retrieves a list of author names for all publications concerning given topics.
        :param topics: The list of topics to retrive upon.
        :return: List of PubMedAuthor instances.
        '''
        result = []

        ids = self._get_article_ids_for_topics(topics)

        for start_index in range(0, len(ids), Pumex.DEFAULT_SIZE_OF_EXTRACTION_PORTION):
            ids_to_process = ids[start_index: start_index + Pumex.DEFAULT_SIZE_OF_EXTRACTION_PORTION]
            portion = self._extract_authors(ids_to_process)

            result += portion

            print(f"Extracted {len(portion)} authors starting from index {start_index} (total: {len(ids)})")

        return result


    #region Private Auxiliary
    def _get_number_of_finds(self, topics: list[str]) -> int:
        '''
        Gets the number of finds for the list of search topics.
        :param topics: List of search topics.
        :return: The total number of PubMed IDs found.
        '''
        request_url = f"{Pumex.NCBI_SEARCH_REQUEST_BASE}&rettype=count&term={'+'.join(topics)}"

        try:
            request = requests.request("get", request_url)
            response = request.text
            tree = ET.fromstring(response)
            x_count = tree.find('Count')
            return int(x_count.text)
        except:
            return 0

    def _get_article_ids_for_topics(self, topics: list[str]) -> list[str]:
        '''
        Gets PubMed Ids for the list of search topics.
        :param topics: List of search topics.
        :return: List of PubMed IDs.
        '''
        result = []

        total_number_of_ids = self._get_number_of_finds(topics)

        print(f"Found {total_number_of_ids} IDs for the topic(s)")

        if total_number_of_ids <= 0:
            return result

        count_ids_downloaded = 0
        start_index = 0

        while count_ids_downloaded < total_number_of_ids:
            ids_portion = self._download_portion_of_request_ids \
                    (
                    topics,
                    start_index,
                    Pumex.NUMBER_OF_IDS_IN_PARTIAL_REQUEST
                    )

            result += ids_portion
            count_ids_downloaded += len(ids_portion)
            start_index = len(result)
            print(f"count_ids_downloaded={count_ids_downloaded}, new start index = {start_index}")

        return result

    def _download_portion_of_request_ids(self, topics: list[str], start_index: int, number_of_entries: int) -> list[str]:
        result = []
        search_url = f"{Pumex.NCBI_SEARCH_REQUEST_BASE}&retmax={number_of_entries}&retstart={start_index}&term={'+'.join(topics)}"
        request = requests.request("get", search_url)
        response = request.text
        tree = ET.fromstring(response)
        x_id_list = tree.find('IdList')

        for xId in x_id_list.findall('Id'):
            result.append(xId.text)

        print(f"Downloaded IDs from index {start_index}")

        return result

    def _extract_authors(self, ids: list[str]) -> list[PubMedAuthor]:
        '''
        Extracts authors for a list of PubMed IDs.
        :param ids: List of PubMed IDs.
        :return: List of authors.
        '''
        result = []

        fetch_url = f"{Pumex.NCBI_FETCH_REQUEST_BASE}&retmode=xml&id={','.join(ids)}"

        try:
            request = requests.request("get", fetch_url)
        except:
            return []

        if request.status_code == 414:
            raise ValueError("STATUS_URI_TOO_LONG")

        response = request.text

        try:
            tree = ET.fromstring(response)

            for x_pubmed_article in tree.findall('PubmedArticle'):
                try:
                    authors = self._extract_authors_from_article(x_pubmed_article)

                    for author in authors:
                        if author not in result:
                            result.append(author)
                except:
                    pass

            return result
        except:
            return []

    def _extract_authors_from_article(self, x: ET.Element) -> list[PubMedAuthor]:
        '''
        Extracts a PubMedAuthor from its XML representation in PubMed XML response format.
        :param x: The XML representation as an instance of ET.Element.
        :return: An instance of PubMedAuthor.
        '''
        result = []

        x_medline_citation = x.find('MedlineCitation')
        x_article = x_medline_citation.find('Article')
        x_author_list = x_article.find('AuthorList')

        for x_author in x_author_list.findall('Author'):
            last_name = x_author.find("LastName").text
            first_name = x_author.find("ForeName").text
            initials = x_author.find("Initials").text

            pubmedAuthor = PubMedAuthor()
            pubmedAuthor.family_name    = last_name
            pubmedAuthor.given_name     = first_name
            pubmedAuthor.initials       = initials

            result.append(pubmedAuthor)

        return result
    #endregion

def create_corpus(topics: list[str], comma_separated:bool, sort_by_length: bool):
    pumex = Pumex()
    authors = pumex.retrieve_authors(topics)

    if comma_separated:
        author_strings = [author.to_comma_separated_string() for author in authors]
    else:
        author_strings = [author.to_comalles_string() for author in authors]

    if sort_by_length:
        author_strings.sort(key=len, reverse=True)

    file_name = f"{'_'.join(topics)}"

    if comma_separated:
        file_name += "_comma_"
    else:
        file_name += "_no_comma_"

    file_name += ".txt"

    with open(file_name, "w", encoding="utf-8") as file:
        file.write('\n'.join(author_strings))

def create_training_data(topics: list[str], min_length: int = -1, max_length: int = -1):
    pumex = Pumex()
    authors = pumex.retrieve_authors(topics)

    file_name = f"{'_'.join(topics)}"

    file_name = "TrainingData/" + file_name
    file_name += ".xml"

    x = XElement("Authors")
    for author in authors:
        try:
            author_string = author.to_comma_separated_string()

            if min_length >= 0 and max_length > 0 and (len(author_string) < min_length or len(author_string) > max_length):
                continue

            x_author = ET.SubElement(x, "Author")

            x_family_name = ET.SubElement(x_author, "FamilyName")
            x_family_name.text  = author.family_name

            x_given_name = ET.SubElement(x_author, "GivenName")
            x_given_name.text = author.given_name

            x_initials = ET.SubElement(x_author, "Initials")
            x_initials.text = author.initials
        except:
            continue

    rough_string = ET.tostring(x, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    reparsed = reparsed.toprettyxml(indent="  ")

    with open(file_name, "w", encoding="utf-8") as file:
        file.write(reparsed)


if __name__ == '__main__':

    country_file_name = "countries2.txt"

    with open(country_file_name, "r", encoding="utf-8") as country_file:
        countries = country_file.read().split('\n')

    # countries = ["China"]

    for country in countries:
        print(f"Processing country: {country}")
        print("===========================================\n")

        topics = ["behavior", country]
        create_training_data(topics)

