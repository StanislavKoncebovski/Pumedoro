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
    #region Class Constants
    PREFIXES = ['JUNIOR', 'JUN.', 'JR.', 'JR', 'JR.', 'JR', 'JR.', 'JR', 'JÚNIOR',
                'SENIOR', 'SEN.', 'SR.', 'SR', 'SR.', 'SR', 'SR.', 'SR', 'III', 'III', 'IV', 'IV']

    '''
    A given name item of two characters is valid if: (1) it has a capital letter as the first character, 
    (2) the second letter is a non-capitals vowel, or
    (3) the item is 'Ng'
    '''
    GIVEN_2CHAR_NAME_PATTERN = re.compile("^[A-Z][aeiouy]{1}$|^Ng$")

    NOBILIARITY_PARTICLES = ['aan', 'af', 'auf', 'da', 'dai', 'dal', 'dalla', 'das', 'de la', 'de', 'de', 'degli',
                             'dei', 'del', 'della', 'dem', 'den', 'der', 'des', 'des', 'di', 'dos', 'du', 'het',
                             'van', 'vom', 'von', 'zu', 'zur']
    #endregion

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

    @property
    def dataframe(self):
        df = pd.DataFrame.from_dict(self._dictionary, orient='index', columns=['occ_given', 'occ_family', 'soundex', 'metaphone'])
        return df

    def clear_dictionary(self):
        '''
        Empties the name dictionary.
        @return:
        '''
        self._dictionary.clear()

    def update_dictionary(self, folder: str, recursive: bool = True):
        '''
        Updates the name dictionary from a folder containing XML files with raw extraction data.
        @param folder: The path to the folder.
        @param recursive: carry out recursively.
        @return: None.
        '''
        file_names = glob.glob(folder + '/**/*.xml', recursive=True)[:4]

        count = 1
        for file_name in file_names:
            print(f"Processing file {file_name} ({count} of {len(file_names)})")
            self._update_dictionary_from_file(file_name)
            count += 1

    def store_dictionary(self, file_name: str):
        '''
        Stores the dictionary as a CSV file
        @param file_name:
        @return:
        '''
        df = self.dataframe
        df.to_csv(file_name)

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
            # Extract and handle raw string for the given names
            given_name_raw = author.find("GivenName").text

            given_names = self._get_given_names(given_name_raw)

            for given_name in given_names:
                if given_name in self._dictionary:
                    self._dictionary[given_name][0] += 1
                else:
                    self._dictionary[given_name] = [1, 0, '', '']

            # Extract and handle raw string for the family name
            family_name_raw = author.find("FamilyName").text
            family_name = self._get_family_name(family_name_raw)

            if family_name in self._dictionary:
                self._dictionary[family_name][1] += 1
            else:
                self._dictionary[family_name] = [0, 1, '', '']

    def _get_given_names(self, name_string: str, apply_strict_rules: bool = False) -> list[str]:
        '''
        Extracts valid given names from a raw name string.
        @param name_string: The raw string to extract from.
        @param apply_strict_rules: If set to True, raw given name string is completely ignored
            if confusion of given and family names may be detected.
        @return: List of valid given names.
        '''
        # result = []

        # (1) split by space:
        items = name_string.split(' ')

        # (2) Remove all prefixes
        items = [x for x in items if x.upper() not in PumedoroDictionaryCreator.PREFIXES]

        # (3) Remove all one-letter items
        items = [x for x in items if len(x) >= 2]

        # (4) Handle two-character items
        for item in items:
            if len(item) == 2 and item not in PumedoroDictionaryCreator.NOBILIARITY_PARTICLES:
                if not PumedoroDictionaryCreator.GIVEN_2CHAR_NAME_PATTERN.match(item.strip()):
                    items.remove(item)

        # (5) Handle nobiliarity particles: if a n.p. is found, remove it and all following items
        for particle in PumedoroDictionaryCreator.NOBILIARITY_PARTICLES:
            items_lower = [i.lower() for i in items]
            if particle in items_lower:
                index = items_lower.index(particle)
                del items[index:]

        return items

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
        # (1) split by space:
        items = name_string.split(' ')

        # (2) Remove all prefixes
        items = [x for x in items if x.upper() not in PumedoroDictionaryCreator.PREFIXES]

        return ' '.join(items)
    #endregion

if __name__ == '__main__':
    creator = PumedoroDictionaryCreator()

    folder = r"P:\Projects\1017.Pumedoro\Data\TrainingData\Covid"
    creator.update_dictionary(folder)

    df = creator.dataframe

    print(df.head(50))

    creator.store_dictionary("test.csv")