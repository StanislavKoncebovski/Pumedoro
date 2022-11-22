import xml.etree.ElementTree as ET
import re
import pandas as pd
import fuzzy
import glob
import os

class PMName:
    '''
    Abstraction of a PubMed author's name element (given name or family name),
    the whole name or its part (like in 'Jean-Pierre' 'Jean' and 'Pierre' are both elements).
    '''
    __slots__ = ['id', 'value', 'occurrences', 'soundex', 'metaphone']
    id: int; value: str; occurrences: int; soundex: str; metaphone: str

    def __init__(self):
        self.id = 0
        self.value = ''
        self.occurrences = 0
        self.soundex = ''
        self.metaphone = ''

    def __str__(self):
        '''
        String representation of the instance.
        :return:
        '''
        return f"[{self.id}]: {self.value} ({self.occurrences})"

class PMCache:
    '''
    A valid given name should have a capital as the first character, and a number of non-capitals following,
    but if the length of the name is 2, the second letter must be a vowel. Exception: "Ng" (which is valid).
    '''
    GIVEN_NAME_PATTERN = re.compile("^[A-Z][aeiouy]{1}$|^[A-Z][a-z]{2,}$|^Ng$")
    SUFFIXES = ['jr', 'jr.', 'junior', 'júnior', 'jun',  'jun.', 'sr', 'sr.', 'senior', 'sen', 'sen.', 'iii']

    def __init__(self):
        '''
        Clears the bnames' dictionaries
        '''
        self._given_names = {}
        self._family_names = {}

    def process_file(self, file_name: str):
        '''
        Processes an XML file with names
        :param file_name:
        :return:
        '''
        root = ET.parse(file_name).getroot()
        authors = root.findall("Author")

        for author in authors:
            try:
                given_name_raw = author.find("GivenName").text
                given_names = self._get_given_names(given_name_raw)

                for given_name in given_names:
                    if given_name in self._given_names:
                        self._given_names[given_name].occurrences += 1
                    else:
                        pm_given = PMName()
                        pm_given.value = given_name.title()
                        pm_given.occurrences = 1
                        self._given_names[given_name] = pm_given

                family_name_raw = author.find("FamilyName").text
                family_name_raw = self._clean_family_name(family_name_raw)

                if family_name_raw in self._family_names:
                    self._family_names[family_name_raw].occurrences += 1
                else:
                    pm_family = PMName()
                    pm_family.value = family_name_raw.title()
                    pm_family.occurrences += 1
                    self._family_names[family_name_raw] = pm_family
            except:
                continue

    def process_folder(self, folder_name, clear_collections: bool = True):
        '''
        Processes a folder creating a cache from all XML files in it.
        :param folder_name:
        :return:
        '''
        files = glob.glob(f"{folder_name}\\*.xml")

        if clear_collections:
            self._given_names.clear()
            self._family_names.clear()

        for file in files:
            print(f"Processing file {file}")
            self.process_file(file)

    def process_folders(self, folders: list[str]):
        '''
        Processes a number of folders
        :param folders:
        :return:
        '''
        self._given_names.clear()
        self._family_names.clear()

        for folder in folders:
            folder_name = os.path.basename(folder)
            print(f"\n\nProcessing folder {folder_name} \n\n")

            self.process_folder(folder, False)

    def create_data_frame(self, sortby: str = 'none'):
        '''
        Creates a dataframe with the following columns:
        name, occurrences_given, occurrences_family, soundex, metaphone
        :return:
        '''

        soundex = fuzzy.Soundex(4)
        dmeta = fuzzy.DMetaphone()
        table = {}

        for name in self._given_names:
            gn = self._given_names[name]
            occurrences_given = gn.occurrences
            occurrences_family = 0
            try:
                v_soundex = soundex(name)
            except:
                pass

            try:
                methaphone = dmeta(name)[0].decode("utf-8")
            except:
                pass

            table[name] = [name, occurrences_given, occurrences_family, v_soundex, methaphone]

        for name in self._family_names:
            fn = self._family_names[name]
            occurrences_given = 0
            occurrences_family = fn.occurrences
            try:
                v_soundex = soundex(name)
            except:
                pass

            try:
                methaphone = dmeta(name)[0].decode("utf-8")
            except:
                pass

            if name in table:
                table[name][2] = fn.occurrences
            else:
                table[name] = [name, occurrences_given, occurrences_family, v_soundex, methaphone]

        df = pd.DataFrame(table.values(), columns=['name', 'occurrences_given', 'occurrences_family', 'soundex', 'metaphone'])

        if sortby == 'name':
            df = df.sort_values(by='name')
        elif sortby == 'occurrences_given' or sortby == 'given':
            df = df.sort_values(by='occurrences_given', ascending=False)
        elif sortby == 'occurrences_family' or sortby == 'family':
            df = df.sort_values(by='occurrences_family', ascending=False)
        else:
            pass

        return df

    #region Private Auxiliary
    def _get_given_names(self, text: str) -> list[str]:
        # split by space
        items = text.split(' ')
        result = []

        for item in items:
            if PMCache.GIVEN_NAME_PATTERN.match(item):
                result.append(item)

        return result

    def _clean_family_name(self, text: str) -> str:
        '''
        Cleans the family name from suffixes like 'jr', 'sr' etc.
        :param text:
        :return:
        '''
        cells = text.split(' ')
        result = []

        for cell in cells:
            if cell.upper() in PMCache.SUFFIXES:
                continue
            else:
                result.append(cell)

        return ' '.join(result)
    #endregion

########################### global functions ##########################
def create_folder_name_statistics(folder: str):
    '''
    Creates a name statistics for a folder:
    :return:
    '''
    cache = PMCache()

    # folder = r"P:\Projects\1010.Alcor\Code\Python\TrainingData\Covid"
    folder_name = os.path.basename(folder)

    cache.process_folder(f"{folder}\\*.xml")

    print("Sorted by frequency of given names:\n\n")
    df = cache.create_data_frame('given')
    print(f"\n\nData frame contains {df.shape[0]} rows\n\n")

    print(df.head(50))

    non_zero_given_names = len(df[df['occurrences_given'] > 0])

    df[['name', 'occurrences_given']].to_json(f"{folder_name}_by_given_names.json", orient='records', lines=True)
    df[['name', 'occurrences_given']].to_csv(f"{folder_name}_by_given_names.csv", index=False)

    print(f"Non-zero given names: {non_zero_given_names}")

    with open(f"non_zero_given_names_{folder_name}.txt", "w", encoding="utf-8") as file:
        file.write(f"Non-zero given names in folder {folder_name}: {non_zero_given_names}")

    print("Sorted by frequency of family names:\n\n")
    df = cache.create_data_frame('family')

    print(df.head(50))

    non_zero_family_names = len(df[df['occurrences_family'] > 0])

    with open(f"non_zero_family_names_{folder_name}.txt", "w", encoding="utf-8") as file:
        file.write(f"Non-zero family names in folder {folder_name}: {non_zero_family_names}")

    df[['name', 'occurrences_family']].to_json(f"{folder_name}_by_family_names.json", orient='records', lines=True)
    df[['name', 'occurrences_family']].to_csv(f"{folder_name}_by_family_names.csv", index=False)

    print(f"Non-zero family names: {non_zero_family_names}")

if __name__ == '__main__':
    folders = [r"P:\Projects\1010.Alcor\Data\TrainingData\Covid",
               r"P:\Projects\1010.Alcor\Data\TrainingData\Measurement",
               r"P:\Projects\1010.Alcor\Data\TrainingData\Education",
               r"P:\Projects\1010.Alcor\Data\TrainingData\Behavior"]

    cache = PMCache()
    cache.process_folders(folders)

    folder_name = "TrainingData"

    print("Sorted by frequency of given names:\n\n")
    df = cache.create_data_frame('given')
    print(f"\n\nData frame contains {df.shape[0]} rows\n\n")

    print(df.head(50))

    df[['name', 'occurrences_given']].to_json(f"{folder_name}_by_given_names.json", orient='records', lines=True)
    df[['name', 'occurrences_given']].to_csv(f"{folder_name}_by_given_names.csv", index=False)

    non_zero_given_names = len(df[df['occurrences_given'] > 0])

    with open(f"non_zero_given_names_{folder_name}.txt", "w", encoding="utf-8") as file:
        file.write(f"Non-zero given names in folder {folder_name}: {non_zero_given_names}")

    print("Sorted by frequency of family names:\n\n")
    df = cache.create_data_frame('family')

    print(df.head(50))

    non_zero_family_names = len(df[df['occurrences_family'] > 0])

    with open(f"non_zero_family_names_{folder_name}.txt", "w", encoding="utf-8") as file:
        file.write(f"Non-zero family names in folder {folder_name}: {non_zero_family_names}")

    df[['name', 'occurrences_family']].to_json(f"{folder_name}_by_family_names.json", orient='records', lines=True)
    df[['name', 'occurrences_family']].to_csv(f"{folder_name}_by_family_names.csv", index=False)

    print(f"Non-zero family names: {non_zero_family_names}")