from pumedoro_name import PumedoroName
import xml.etree.ElementTree as ET
import re
import pandas as pd
import fuzzy
import glob
import os

class PumedoroDictionaryCreator:
    '''
    Creates a name dictionary out of an XML file with raw given and family names extracted from PubMedArticles.
    '''
    def __init__(self):
        '''
        Initializes the internal dictionary.
        The dictionary has a name (case-sensitive string) as the key and an instance of PumedoroName as the value.
        '''
        self._dictionary = {}

    @property
    def dictionary(self):
        '''
        Gets the internal dictionary.
        @return:
        '''
        return self._dictionary

    def clear_dictionary(self):
        '''
        Empties the name dictionary.
        @return:
        '''
        self._dictionary.clear()

    def update_dictionary(self, folder: str):
        '''
        Updates the name dictionary from a folder containing XML files with raw extraction data.
        @param folder: The path to the folder.
        @return: None.
        '''
        pass

    #region Protected Auxiliary
    def _update_dictionary_from_file(self, file_name: str):
        '''
        Updates the name dictionary from an XML file.
        @param file_name: The name of the file.
        @return: None.
        '''
        root = ET.parse(file_name).getroot()
        authors = root.findall("Author")

        for author in authors:
            # Extract raw strings for the given and family names
            given_name_raw = author.find("GivenName").text
            family_name_raw = author.find("FamilyName").text

    def _get_given_names(self, name_string: str) -> list[str]:
        '''
        Extracts valid given names from a raw name string.
        @param name_string: The raw string to extract from.
        @return: List of valid given names.
        @cases:
        "John Meinhard Xavier P" -> ["John", "Meinhard", "Xavier"]
        "John Meinhard Xavier Pt" -> ["John", "Meinhard", "Xavier"]
        "John Meinhard Xavier Pta" -> ["John", "Meinhard", "Xavier"]
        "Xu" -> ["Xu"]
        "Li Xi" -> ["Li Xi"]
        "Karl-Heinz"-> ["Karl-Heinz"]
        "Bryanne Brissian de Souza" -> ["Bryanne"]: take only the first component, since given and family names probably confused (Brazil)
        "M G M O" -> ignore completely
        "Fernando César Júnior" -> ["Fernando", "César"]: ignore "Júnior", "Junior", etc. in raw given names.
        "O Junior" -> ignore, since 'Junior' shall be removed first.
        "Maria Del" -> ["Maria"]: ignore "del" etc. if more than two items (see case "Bryanne")
        "Maxi von" -> ["Maxi"]
        "Dagmar Meyer Zu", "Dagmar Meyer zu" -> ["Dagmar Meyer"] (?)
        "Erik Schulze Zur" -> ["Erik Schulze"]  (?)
        "Annabelle von der" -> ["Annabelle"]
        "Anne-Els van de" -> ["Anne-Els"] (van den, het, aan)
        "Del Grande" -> ("del" first) ignore completely, since given and family names probably confused
        Sweden: 'af'
        France: 'de', 'du', "des', 'de la'
        Germany: 'von', 'zu', 'auf'
        Italy: Del, Della, Dei, Dal, Dalla, Dai, degli
        Portugal: 'dos', 'das'
        '''
        # TODO: implement me!
        pass

    def _get_family_name(self, name_string: str) -> str:
        '''
        Extracts valid family name from a raw name string.
        @param name_string: The raw string to extract from.
        @return: The valid family name.
        @cases:
        "Leite-Júnior" -> "Leite": ignore "Júnior", "Junior", etc. in raw family names.
        "Langhi Júnior" -> "Langhi": see above.
        "Del Grande" -> "Del Grande"
        "von Hardenberg" -> "von Hardenberg"
        "Pogge von Strandmann" -> "Pogge von Strandmann"
        "von dem Knesebeck" -> "von dem Knesebeck"
        '''
        # TODO: implement me!
        pass
    #endregion