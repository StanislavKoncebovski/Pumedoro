from typing import Optional
import requests
import xml.etree.ElementTree as ET
import numpy as np


class NCBIExtractor:
    """
    Class to extract article properties from the NCBI database.
    At present, supports the following article properties:
    - authors' affiliations
    - abstract
    """
    # region Class Constants
    NCBI_SEARCH_REQUEST_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed"  # default URL base to query for publication IDs.
    NCBI_FETCH_REQUEST_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed"  # default URL base to fetch the publication infos.
    DEFAULT_SIZE_OF_EXTRACTION_PORTION = 200  # Default number of entries in an extraction portion.
    NUMBER_OF_IDS_IN_PARTIAL_REQUEST = 1000  # Number of IDs in a partial request for IDs.
    # endregion

    # region Static Properties
    """
    Dictionary of downloaded texts. Key: the NCBI ID; value: the downloaded page text.
    """
    _texts: dict[int, str] = {}

    # endregion

    # region Static access methods
    @classmethod
    def text_ids(cls) -> list[int]:
        """
        Gets the text pubmed_ids (keys).
        :return: The list of text pubmed_ids.
        """
        return list(NCBIExtractor._texts.keys())

    def __class_getitem__(cls, key: int) -> Optional[str]:
        """
        Gets an article by its NCBI ID.
        :param key: The NCBI ID of the article.
        :return: The text of the article, if found, otherwise None.
        """
        if key in NCBIExtractor._texts.keys():
            return NCBIExtractor._texts[key]
        else:
            return None

    @classmethod
    def merge_text(cls, delimiter: str = " ") -> str:
        """
        Gets the merged text combining all accumulated text of the dictionary.
        :param: delimiter: Text to place after each item text.
        :return: The concatenated text of the dictionary entries, if the latter is not empty, otherwise, an empty string.
        """
        result = ""
        for key in NCBIExtractor._texts.keys():
            result += NCBIExtractor._texts[key]
            result += delimiter

        return result
    # endregion

    # region General Features
    @classmethod
    def get_article_ids_for_topics(cls, topics: list[str]) -> list[int]:
        """
        Retrieves NCBI IDs for a search topic.
        :param topics: A list of topics to find IDs for.
        :return: List of NCBI IDs.
        """
        result = []

        total_number_of_ids = NCBIExtractor._get_count_of_findings(topics)

        if total_number_of_ids <= 0:
            return result

        count_ids_downloaded = 0
        start_index = 0

        while count_ids_downloaded < total_number_of_ids:
            ids_portion = NCBIExtractor._download_portion_of_request_ids \
                    (
                    topics,
                    start_index,
                    NCBIExtractor.NUMBER_OF_IDS_IN_PARTIAL_REQUEST,
                    True
                )

            result += ids_portion
            count_ids_downloaded += len(ids_portion)
            start_index = len(result)

            print(f"count_ids_downloaded={count_ids_downloaded}, new start index = {start_index}")

        return result
    # endregion

    # region Abstract extraction
    @classmethod
    def get_abstract(cls, article_id: int) -> Optional[str]:
        """
        Tries to extract article abstract from an NCBI database item.
        :param article_id: The NCBI ID of the article.
        :return: The summary abstract created as the concatenated text of all abstract chunks of the article, if successful;
        empty string if the ID was valid, but no abstracts found;
        None if no article with this ID could be found.
        """

        fetch_url = f"{NCBIExtractor.NCBI_FETCH_REQUEST_BASE}&retmode=xml&id={article_id}"
        request = requests.request("get", fetch_url)
        response = request.text

        tree = ET.fromstring(response)

        x_pubmed_article = tree.find('PubmedArticle')
        return NCBIExtractor._extract_abstract_from_article(x_pubmed_article)

    @classmethod
    def add_abstract(cls, article_id: int):
        """
        Tries to extract article abstract from an NCBI database item and to add it to the text dictionary.
        The text item will only be added if the article retrieved was not None or empty.
        :param article_id: The NCBI ID of the article.
        :return: 
        """
        abstract = NCBIExtractor.get_abstract(article_id)
        if abstract is not None and len(abstract) > 0 and article_id not in NCBIExtractor._texts:
            NCBIExtractor._texts[article_id] = abstract

    @classmethod
    def add_abstracts(cls, article_ids: list[int]):
        """
        Tries to extract article abstracts from a number of NCBI database items and to add it to the text dictionary.
        The text item will only be added if the article retrieved was not None or empty.
        :param article_ids: List of the NCBI IDs of the articles.
        :return: 
        """
        NCBIExtractor._texts.clear()

        number_of_chunks = int(len(article_ids) / NCBIExtractor.DEFAULT_SIZE_OF_EXTRACTION_PORTION) + 1

        for id_subset in np.array_split(article_ids, number_of_chunks):
            abstract = NCBIExtractor._add_articles_by_ids(id_subset)
    # endregion

    # region Affiliation extraction
    @classmethod
    def extract_ncbi_affiliations(cls, search_terms: list[str]) -> list[str]:
        """
        Extracts a list of PubMed raw affiliation strings from the NCBI ESearch server.
        :param search_terms: list of search terms (will be concatenated with '+')
        :return: List of raw affiliation strings found.
        """
        result = []

        ids = NCBIExtractor.get_article_ids_for_topics(search_terms)
        for start_index in range(0, len(ids), NCBIExtractor.DEFAULT_SIZE_OF_EXTRACTION_PORTION):
            ids_to_process = ids[start_index: start_index + NCBIExtractor.DEFAULT_SIZE_OF_EXTRACTION_PORTION]
            portion = NCBIExtractor._extract_affiliations(ids_to_process)
            result += portion

            print(f"Extracted {len(portion)} affiliations starting from index {start_index} (total: {len(ids)})")

        return result

    @classmethod
    def extract_ncbi_authors(cls, search_terms: list[str]) -> list[str]:
        result = []
        ids = NCBIExtractor.get_article_ids_for_topics(search_terms)
        for start_index in range(0, len(ids), NCBIExtractor.DEFAULT_SIZE_OF_EXTRACTION_PORTION):
            ids_to_process = ids[start_index: start_index + NCBIExtractor.DEFAULT_SIZE_OF_EXTRACTION_PORTION]
            portion = NCBIExtractor._extract_authors(ids_to_process)
            result += portion

            print(f"Extracted {len(portion)} affiliations starting from index {start_index} (total: {len(ids)})")

        return result
    # endregion

    # region Protected Auxiliary
    @classmethod
    def _extract_abstract_from_article(cls, x_pubmed_article: ET.Element) -> (int, str):
        """
        Extracts abstracts from a PubMed article.
        :param x_pubmed_article: The ElementTree element containing the affiliation info to extract.
        :return: List of raw affiliation contained in the article.
        """
        abstract = ""
        x_medline_citation = x_pubmed_article.find('MedlineCitation')
        x_pmid = x_medline_citation.find("PMID")
        pmid = int(x_pmid.text)
        x_article = x_medline_citation.find('Article')
        x_abstract = x_article.find('Abstract')

        if x_abstract is None:
            return None

        for x_abstract_text in x_abstract.findall('AbstractText'):
            abstract += f"\n{x_abstract_text.text}"

        return pmid, abstract

    @classmethod
    def _add_articles_by_ids(cls, pubmed_ids: list[int]):
        """
        Downloads PubMed entries to articles with given PubMed IDs and adds them to the dictionary.
        :param pubmed_ids: List of id's to download and add.
        :return:
        """
        NCBIExtractor._texts.clear()

        fetch_url = f"{NCBIExtractor.NCBI_FETCH_REQUEST_BASE}&retmode=xml&id={','.join(pubmed_ids)}"

        request = requests.request("get", fetch_url)

        if request.status_code == 414:
            raise ValueError("STATUS_URI_TOO_LONG")

        response = request.text

        tree = ET.fromstring(response)

        for x_pubmed_article in tree.findall('PubmedArticle'):
            tuple = NCBIExtractor._extract_abstract_from_article(x_pubmed_article)

            if tuple is None:
                continue

            pmid = tuple[0]
            abstract = tuple[1]
            NCBIExtractor._texts[pmid] = abstract

    @classmethod
    def _get_count_of_findings(cls, search_terms: list[str]) -> int:
        """
        Gets the count of findings for a search pattern.
        :param search_terms: The search pattern.
        :return: The number of IDs corresponding to the pattern.
        """
        request_url = f"{NCBIExtractor.NCBI_SEARCH_REQUEST_BASE}&rettype=count&term={'+'.join(search_terms)}"
        try:
            request = requests.request("get", request_url)
            response = request.text
            tree = ET.fromstring(response)
            x_count = tree.find('Count')
            return int(x_count.text)
        except:
            return 0

    @classmethod
    def _download_portion_of_request_ids(cls, search_terms: list[str], start_index: int, number_of_entries: int, notify: bool = True) -> list[str]:
        """
        Downloads a portion of size number_of_entries from a PubMed IDs from an ID list, starting from the index start_index.
        The REST API does not allow to download all IDs at once, but is rather limited to a maximum number od IDs per step (100000).
        :param search_terms: The search pattern.
        :param start_index: Th index to start from.
        :param number_of_entries: The number of indices to download.
        :param notify: If set to True, the function will notify the user fulfilling the step.
        :return: The list of Pubmed IDs for the portion.
        """
        result = []
        search_url = f"{NCBIExtractor.NCBI_SEARCH_REQUEST_BASE}&retmax={number_of_entries}&retstart={start_index}&term={'+'.join(search_terms)}"
        request = requests.request("get", search_url)
        response = request.text
        tree = ET.fromstring(response)
        x_id_list = tree.find('IdList')
        for xId in x_id_list.findall('Id'):
            result.append(xId.text)

        if notify:
            print(f"Downloaded IDs from index {start_index}")

        return result

    @classmethod
    def _extract_affiliations_from_article(cls, x_pubmed_article: ET.Element) -> list[str]:
        """
        Extracts the full affiliation info from a PubMed article.
        :param x_pubmed_article: The ElementTree element containing the affiliation info to extract.
        :return: List of raw affiliation contained in the article.
        """
        result = []
        x_medline_citation = x_pubmed_article.find('MedlineCitation')
        x_article = x_medline_citation.find('Article')
        x_author_list = x_article.find('AuthorList')

        for x_author in x_author_list.findall('Author'):
            for x_affiliation_info in x_author.findall('AffiliationInfo'):
                x_affiliation = x_affiliation_info.find('Affiliation')
                result.append(x_affiliation.text)

        return result

    @classmethod
    def _extract_authors_from_article(cls, x_pubmed_article: ET.Element) -> list[str]:
        """
        Extracts the full affiliation info from a PubMed article.
        :param x_pubmed_article: The ElementTree element containing the affiliation info to extract.
        :return: List of raw affiliation contained in the article.
        """
        result = []
        x_medline_citation = x_pubmed_article.find('MedlineCitation')
        x_article = x_medline_citation.find('Article')
        x_author_list = x_article.find('AuthorList')

        for x_author in x_author_list.findall('Author'):
            last_name = x_author.find("LastName").text
            first_name = x_author.find("ForeName").text
            initials = x_author.find("Initials").text

            result.append(f"{last_name}, {first_name} {initials}")

        return result

    @classmethod
    def _extract_affiliations(cls, ids: list[str]) -> list[str]:
        """
        Extracts raw affiliations form a list of PubMed IDs.
        :param ids: The list of IDs.
        :return: List of raw affiliation contained in the defined PubMed articles.
        """
        result = []

        fetch_url = f"{NCBIExtractor.NCBI_FETCH_REQUEST_BASE}&retmode=xml&id={','.join(ids)}"

        request = requests.request("get", fetch_url)

        if request.status_code == 414:
            raise ValueError("STATUS_URI_TOO_LONG")

        response = request.text

        try:
            tree = ET.fromstring(response)

            for x_pubmed_article in tree.findall('PubmedArticle'):
                affiliations = NCBIExtractor._extract_affiliations_from_article(x_pubmed_article)

                for affiliation in affiliations:
                    if affiliation not in result:
                        result.append(affiliation)

            return result
        except:
            return []

    @classmethod
    def _extract_authors(cls, ids: list[str]) -> list[str]:
        """
        Extracts raw authors form a list of PubMed IDs.
        :param ids: The list of IDs.
        :return: List of raw authors contained in the defined PubMed articles.
        """
        result = []

        fetch_url = f"{NCBIExtractor.NCBI_FETCH_REQUEST_BASE}&retmode=xml&id={','.join(ids)}"

        request = requests.request("get", fetch_url)

        if request.status_code == 414:
            raise ValueError("STATUS_URI_TOO_LONG")

        response = request.text

        try:
            tree = ET.fromstring(response)

            for x_pubmed_article in tree.findall('PubmedArticle'):
                affiliations = NCBIExtractor._extract_authors_from_article(x_pubmed_article)

                for affiliation in affiliations:
                    if affiliation not in result:
                        result.append(affiliation)

            return result
        except:
            return []
    # endregion


if __name__ == '__main__':
    terms = ["dicom", "system"]

    extractor = NCBIExtractor()

    result = extractor.extract_ncbi_authors()
    # result = extractor.extract_ncbi_authors(terms)
    #
    # print(result)