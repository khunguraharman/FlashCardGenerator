from dataclasses import dataclass
from pyclbr import Class
from typing import ClassVar, Union
import re

@dataclass
class AnkiCard:
    pass

@dataclass
class BasicAnkiCard(AnkiCard):
    front: str
    back: list[str]

    EXLCUDE_NOTES: ClassVar[str] = "NOTE:"

@dataclass
class RawClozeAnkiCard:
    tableHeaders: list[str]
    clozeFragments: list[str]

@dataclass
class ClozeAnkiCard(AnkiCard):
    headers: list[str]
    clozeDeletions: list[str]

def is_front_of_card(first_char: str) -> bool:
    # Implement logic to determine if a string is the front of an Anki card    
    if first_char.isupper() and 'A' <= first_char <= 'Z':
        return True
    else:
        return False

def create_basic_cards(doc_path: str) -> list[BasicAnkiCard]:
    anki_cards = []
    with open(doc_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    front = lines[0]
    back = []
    for line in lines[1:]:        
        first_char = line[0]
        if not is_front_of_card(first_char):
            back.append(line)
        else:
            anki_cards.append(BasicAnkiCard(front, back))
            front = line
            back = []
    return anki_cards

def create_cloze_cards(doc_path: str) -> list[ClozeAnkiCard]:
    anki_cards:list[ClozeAnkiCard] = []
    with open(doc_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    for i in range(0, len(lines), 2):
        headers: list[str] = lines[i].split('\t')
        fragments = lines[i+1].split('\t')
        anki_cards.append(ClozeAnkiCard(headers, clozeDeletions = fragments) )       
    return anki_cards

if __name__ == "__main__":
    doc_path = "basic_anki_cards.txt"
    basic_anki_cards = create_basic_cards(doc_path)
    for card in basic_anki_cards:
        print(card)