import sqlite3

class PumedoroClientDatabase:
    def __init__(self, database_path: str):
        self._connection = sqlite3.connect(database_path)
        self._cursor = self._connection.cursor()

    def get_name_frequencies(self, name: str) ->(float, float):
        command = f"SELECT * FROM `name` WHERE `name` = '{name}'"
        result = self._cursor.execute(command)
        result = self._cursor.fetchone()

        if result is not None:
            occ_given = result[2]
            occ_family = result[3]

            return (occ_given / (occ_given + occ_family), occ_family/ (occ_given + occ_family))
        else:
            return (0, 0)

if __name__ == '__main__':
    database_path = r"P:\Projects\Pumedoro\Data\pumedoro.db3"

    db = PumedoroClientDatabase(database_path)

    frequencies = db.get_name_frequencies('Johnson')

    print(frequencies)