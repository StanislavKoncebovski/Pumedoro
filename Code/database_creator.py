import sqlite3

class PumedoroDatabaseCreator:
    def export_name_dictionary(self):
        pass

    def create_name_dictionary(self, given_names_file_name: str, family_names_file_name: str):
        '''
        Creates a combined name dictionary from two separate dictionaries for given and family names.
        :param given_names_file_name: The name of the CSV file with given names
        :param family_names_file_name: The name of the CSV file with family names
        :return: The combined dictionary. Key: the name (case-sensitive); value: tuple of two integers,
        of which the first one is the number of occurrences as a given name,
        the second one the number of occurrences as a family name.
        '''
        result = {}

        with open(given_names_file_name, "r", encoding="utf-8") as given_names_file:
            lines = given_names_file.read().split('\n')

        for line in lines:
            cells = line.split(',')

            if (len(cells) == 2):
                name = cells[0].strip()

                try:
                    occurrences = int(cells[1])
                except:
                    continue

                if occurrences > 0:
                    result[name] = [occurrences, 0]

        with open(family_names_file_name, "r", encoding="utf-8") as family_names_file:
            lines = family_names_file.read().split('\n')

        for line in lines:
            cells = line.split(',')
            if (len(cells) == 2):
                name = cells[0].strip()

                try:
                    occurrences = int(cells[1])
                except:
                    continue

                if name in result:
                    result[name][1] = occurrences
                else:
                    result[name] = [0, occurrences]

        return result

    def store_to_database(self, name_dictionary, database_path: str):
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()

        create_table_name = "CREATE TABLE IF NOT EXISTS `name` (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(64), occurrences_given INTEGER, occurrences_family INTEGER)"
        cursor.execute(create_table_name)

        length = len(name_dictionary)
        count = 1

        for name in name_dictionary:
            name1 = name.replace("'", "''")
            command = f"INSERT INTO `name` VALUES(null, '{name1}', {name_dictionary[name][0]}, {name_dictionary[name][1]})"
            try:
                cursor.execute(command)
                print(f"Processed {count} records of {length}")
                count += 1
            except:
                print(f"********************* '{name}', {name_dictionary[name][0]}, {name_dictionary[name][1]}")
                print(f"********************* {command}")

        connection.commit()


if __name__ == '__main__':
    # given_names_file_name = "given_names.csv"
    # family_names_file_name = "family_names.csv"

    given_names_file_name = r'P:\Projects\1017.Pumedoro\Data\Training_Data_Results\TrainingData_by_given_names.csv'
    family_names_file_name = r'P:\Projects\1017.Pumedoro\Data\Training_Data_Results\TrainingData_by_family_names.csv'

    pumedoro = PumedoroDatabaseCreator()

    name_dictionary = pumedoro.create_name_dictionary(given_names_file_name, family_names_file_name)

    print(name_dictionary)

    pumedoro.store_to_database(name_dictionary, "pumedoro_test.db3")

