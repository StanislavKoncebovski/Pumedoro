from dataclasses import dataclass

@dataclass()
class PubMedAuthorName:
    given_name: str = ''
    family_name: str = ''

@dataclass()
class PubMedAuthorNameStatItem:
    id: int = 0
    value: str = ''
    occ_given: int = 0
    occ_family: int = 0
    soundex: str = ''
    metaphone: str = ''