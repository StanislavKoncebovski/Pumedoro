import sqlite3

import pandas


class PumedoroDatabase:
    #region Class constants
    SQL_CREATION_NAME = "CREATE TABLE IF NOT EXISTS `name` (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(64), " \
                        "occ_given INTEGER, occ_family INTEGER, soundex VARCHAR(8), metaphone VARCHAR(8))"

    SQL_CREATION_VERSION = "CREATE TABLE IF NOT EXISTS `version` (number INTEGER PRIMARY KEY AUTOINCREMENT, " \
                           "date_time TIME, comment VARCHAR(128))"
    #endregion

    def __init__(self, database_path: str):
        self._connection = sqlite3.connect(database_path)
        self._cursor = self._connection.cursor()

        self._cursor.execute(PumedoroDatabase.SQL_CREATION_NAME)
        self._cursor.execute(PumedoroDatabase.SQL_CREATION_VERSION)

    def load_data_frame(self, file_name: str):
        '''
        Loads a pandas DataFrame from a CSV file
        @param file_name: The name of the file.
        @return: The data frame loaded.
        '''
        return pandas.read_csv(file_name, header=0)

    def clear_names(self):
        '''
        Clears the `names` table
        @return:
        '''
        self._cursor.execute("DELETE FROM `name`")

    def populate_names(self, data_frame: pandas.DataFrame):
        '''
        Populates the `name` table of the database with data from a dafa frame.
        @param data_frame: The data frame to populate with.
        @return:
        '''
        error_file = open("errors.txt", "a")

        data_frame = data_frame.reset_index()

        length = data_frame.shape[0]

        # for record in data_frame:
        for index, record in data_frame.iterrows():
            try:
                name = record[2].replace("'", "''")
                command = f"INSERT INTO `name` VALUES(null, '{name}', {record[3]}, {record[4]}, '{record[5]}', '{record[6]}')"
                self._cursor.execute(command)
                print(f"Processed {index} records of {length}")
            except:
                error_file.write(f"{record[1]}: {record[2]}")
                continue

        self._connection.commit()
        error_file.close()

if __name__ == '__main__':
    database_path = "test_pumedoro.db3"

    db = PumedoroDatabase(database_path)

    data_file = "Training_Data.csv"

    df = db.load_data_frame(data_file)

    db.populate_names(df)