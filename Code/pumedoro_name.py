class PumedoroName:
    '''
    Abstraction of a PubMed author's name element (given name or family name).
    Stores the name string (which can be a given name, a family name, or both, like "Martin"),
    number of occurrences as a given name, number of occurrences as a family name, soundex and metaphone.
    '''
    __slots__ = ['id', 'value', 'occ_given', 'occ_family', 'soundex', 'metaphone']
    id: int; value: str; occurrences: int; soundex: str; metaphone: str

    def __init__(self):
        self.id = 0
        self.value = ''
        self.occ_given = 0
        self.occ_family = 0
        self.soundex = ''
        self.metaphone = ''

    def __str__(self):
        '''
        String representation of the instance.
        :return:
        '''
        return f"[{self.id}]: {self.value} ({self.occ_given}, {self.occ_family})"