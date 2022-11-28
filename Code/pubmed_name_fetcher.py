from xml.dom import minidom

import requests
import xml.etree.ElementTree as ET
from pubmed_author_name import PubMedAuthorName
from xml.etree.ElementTree import Element as XElement


class PubMedNameFetcher:
    '''
    Implements methods to fetch author names from PubMed article server.
    '''

    #region Class Constants
    # default URL base to query for publication IDs.
    NCBI_SEARCH_REQUEST_BASE            = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed"

    # Number of IDs in a partial request for IDs.
    NUMBER_OF_IDS_IN_PARTIAL_REQUEST    = 1000

    # Default URL base to fetch the publication infos.
    NCBI_FETCH_REQUEST_BASE             = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed"

    # Default number of entries in an extraction portion.
    DEFAULT_SIZE_OF_EXTRACTION_PORTION  = 200
    #endregion

    #region Initialization
    def __init__(self):
        self._authors = []
    #endregion

    #region Properties
    @property
    def authors(self) -> list[PubMedAuthorName]:
        return self._authors
    #endregion

    #region Public Features
    def fetch_author_names(self, token: str):
        '''
        Fetches author names from PubMed server by a token
        @param token: the token to fetch by.
        @return: None, the result is in self._authors.
        '''
        ids = self._get_article_ids_for_token(token)

        self._authors = []

        start = 0
        extract = True
        while extract:
            print(f"Extracting authors with IDs from {start} to {min(len(ids), start + PubMedNameFetcher.DEFAULT_SIZE_OF_EXTRACTION_PORTION)}")
            self._authors += self._extract_authors(ids[start:start + PubMedNameFetcher.DEFAULT_SIZE_OF_EXTRACTION_PORTION])
            start += PubMedNameFetcher.DEFAULT_SIZE_OF_EXTRACTION_PORTION
            extract = start <= len(ids)

    def write_xml(self, xml_file_name):
        x = XElement("Authors")
        for author in self._authors:
            x_author = ET.SubElement(x, "Author")

            x_family_name = ET.SubElement(x_author, "FamilyName")
            x_family_name.text = author.family_name

            x_given_name = ET.SubElement(x_author, "GivenName")
            x_given_name.text = author.given_name

        with open(xml_file_name, "w", encoding="utf-8") as file:
            raw_string = ET.tostring(x, 'utf-8').decode("utf-8")
            reparsed = minidom.parseString(raw_string)
            reparsed = reparsed.toprettyxml(indent="  ")

            file.write(reparsed)


    def write_json(self, json_file_name):
        pass

    def write_csv(self, csv_file_name, separator = ','):
        pass
    #endregion

    #region Private Auxiliary
    def _get_number_of_finds(self, token: str) -> int:
        '''
        Gets the number of finds corresponding to a token.
        @param token: The token.
        @return: Tne number of finds found.
        '''
        request_url     = f"{PubMedNameFetcher.NCBI_SEARCH_REQUEST_BASE}&rettype=count&term={token}"

        try:
            request     = requests.request("get", request_url)
            response    = request.text
            tree        = ET.fromstring(response)
            x_count     = tree.find('Count')
            return int(x_count.text)
        except:
            return 0

    def _get_article_ids_for_token(self, token: str) -> list[str]:
        '''
        Gets the list of article IDs for a token.
        @param token: The token to find IDs for.
        @return: List of IDs.
        '''
        number_of_finds = self._get_number_of_finds(token)

        if number_of_finds <= 0:
            return []

        result = []

        count_ids_downloaded = 0
        start = 0

        while count_ids_downloaded < number_of_finds:
            ids_portion = self._get_portion_of_ids_for_token(token, start, PubMedNameFetcher.NUMBER_OF_IDS_IN_PARTIAL_REQUEST)
            result += ids_portion
            count_ids_downloaded += len(ids_portion)
            start = len(result)

        print(f"count_ids_downloaded={count_ids_downloaded}, new start index = {start}")

        return result

    def _get_portion_of_ids_for_token(self, token: str, start: int, number_of_entries: int) -> list[str]:
        '''
        Fetches a portion of IDs for a token starting from a defined index.
        @param token: The token to find IDs for.
        @param start: Starting index.
        @param number_of_entries: Number of IDs to fetch.
        @return: A list of IDs in the portion
        '''
        result = []
        search_url = f"{PubMedNameFetcher.NCBI_SEARCH_REQUEST_BASE}&retmax={number_of_entries}&retstart={start}&term={token}"
        request = requests.request("get", search_url)
        response = request.text

        try:
            tree = ET.fromstring(response)
            x_id_list = tree.find('IdList')

            for xId in x_id_list.findall('Id'):
                result.append(xId.text)

            print(f"Downloaded IDs from index {start}")

            return result
        except:
            return []

    def _extract_authors(self, ids: list[str]) -> list[PubMedAuthorName]:
        '''
        Extracts author names from a number of articles given by their PubMed IDs.
        @param ids: The list of IDs to extract authors from.
        @return: List of authors extracted.
        '''
        result = []

        fetch_url = f"{PubMedNameFetcher.NCBI_FETCH_REQUEST_BASE}&retmode=xml&id={','.join(ids)}"

        try:
            request = requests.request("get", fetch_url)
        except:
            # at any net error, skip this portion
            return []

        response = request.text

        try:
            tree = ET.fromstring(response)

            for x_pubmed_article in tree.findall('PubmedArticle'):
                try:
                    authors = self._extract_authors_from_article(x_pubmed_article)
                    result += authors
                except:
                    pass

            return result
        except:
            return []

    def _extract_authors_from_article(self, x: ET.Element) -> list[PubMedAuthorName]:
        '''
        Extracts PubMed authors for an article represented by its XML Tree element.
        @param x: The XML tree element to extract authors from.
        @return: List of authors of the article.
        '''
        result = []

        x_medline_citation = x.find('MedlineCitation')
        x_article = x_medline_citation.find('Article')
        x_author_list = x_article.find('AuthorList')

        for x_author in x_author_list.findall('Author'):
            last_name = x_author.find("LastName").text
            first_name = x_author.find("ForeName").text

            pubmedAuthor = PubMedAuthorName()
            pubmedAuthor.family_name = last_name
            pubmedAuthor.given_name = first_name

            result.append(pubmedAuthor)

        return result


#endregion

if __name__ == '__main__':
    fetcher = PubMedNameFetcher()
    token = "education+Malta"

    fetcher.fetch_author_names(token)
    fetcher.write_xml("test_malta.xml")


