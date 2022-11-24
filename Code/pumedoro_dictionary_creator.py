from typing import Optional

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

    ABBREVIATION_PATTERN = re.compile("^([A-Z]\.)+$|^([A-Z]\.)-([A-Z]\.)$")

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
        self._soundex = fuzzy.Soundex(4)
        self._dmeta = fuzzy.DMetaphone()

    @property
    def dictionary(self):
        '''
        Gets the internal dictionary.
        @return:
        '''
        return self._dictionary


    def get_dataframe(self, sortby: str=''):
        data = []
        for key in self._dictionary:
            data.append([key, self._dictionary[key][0], self._dictionary[key][1], self._dictionary[key][2], self._dictionary[key][3]])

        df = pd.DataFrame(data, columns=['name', 'occ_given', 'occ_family', 'soundex', 'metaphone'])

        if sortby == 'name':
            df = df.sort_values(by='name')
        elif sortby == 'occ_given' or sortby == 'given':
            df = df.sort_values(by='occ_given', ascending=False)
        elif sortby == 'occ_family' or sortby == 'family':
            df = df.sort_values(by='occ_family', ascending=False)

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
        file_names = glob.glob(folder + '/**/*.xml', recursive=True)

        count = 1
        for file_name in file_names:
            print(f"Processing file {file_name} ({count} of {len(file_names)})")
            self.update_dictionary_from_file(file_name)
            count += 1

    def sort_dictionary(self):
        pass

    def store_dictionary(self, file_name: str, sortby: str = ''):
        '''
        Stores the dictionary as a CSV file
        @param file_name:
        @return:
        '''
        df = self.get_dataframe(sortby)
        df.to_csv(file_name)

    def update_dictionary_from_file(self, file_name: str):
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
                if given_name is None:
                    continue

                given_name = given_name.title()

                if given_name in self._dictionary:
                    self._dictionary[given_name][0] += 1
                else:
                    self._dictionary[given_name] = [1, 0, self._get_soundex(given_name), self._get_metaphone(given_name)]

            # Extract and handle raw string for the family name
            family_name_raw = author.find("FamilyName").text
            family_name = self._get_family_name(family_name_raw)

            if family_name is None:
                continue

            family_name = family_name.title()

            if family_name in self._dictionary:
                self._dictionary[family_name][1] += 1
            else:
                self._dictionary[family_name] = [0, 1, self._get_soundex(family_name), self._get_metaphone(family_name)]

    # region Protected Auxiliary
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

        # (*) Ignore entries like "A.B.C." and "A.-B."
        items = [x for x in items if not (PumedoroDictionaryCreator.ABBREVIATION_PATTERN.match(x))]

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

    def _get_family_name(self, name_string: str) -> Optional[str]:
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
        try:
            items = name_string.split(' ')
        except:
            return None

        # (2) Remove all prefixes
        items = [x for x in items if x.upper() not in PumedoroDictionaryCreator.PREFIXES]

        return ' '.join(items)

    def _get_soundex(self, text: str):
        try:
            return self._soundex(text)
        except:
            return ''

    def _get_metaphone(self, text: str):
        try:
            return self._dmeta(text)[0].decode("utf-8")
        except:
            return ''

    #endregion

if __name__ == '__main__':
    creator = PumedoroDictionaryCreator()

    folder = r"P:\Projects\1017.Pumedoro\Data\TrainingData"
    creator.update_dictionary(folder)

    df = creator.get_dataframe(sortby='given')

    print(df.head(50))

    creator.store_dictionary("Training_Data.csv", 'given')