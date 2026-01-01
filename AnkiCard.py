from dataclasses import dataclass
from pyclbr import Class
from typing import ClassVar, Union
import re

@dataclass
class TextBlock:
    content: list[str]

@dataclass
class TableBlock:
    content: list[list[str]]

BackBlock = Union[TextBlock, TableBlock]

@dataclass
class AnkiCard:
        tableStart: ClassVar[str] = "--Start Table--"
        tableEnd: ClassVar[str] = "--End Table--"
        front:str
        back:list[BackBlock]

def is_front_of_card(first_char: str) -> bool:
    # Implement logic to determine if a string is the front of an Anki card    
    if first_char.isupper() and 'A' <= first_char <= 'Z' and not:
        return True
    else:
        return False

def entering_table_block(line: str) -> bool:
    if line.startswith(AnkiCard.tableStart):
        return True
    else:
        return False

def exiting_table_block(line: str) -> bool:
    if line.startswith(AnkiCard.tableEnd):
        return True
    else:
        return False

def get_table_dimensions(line: str) -> tuple[int, int]:
    match = re.search(r'(\d+)x(\d+)$', line)
    if match:
        dims = tuple(map(int, match.groups()))
        return dims
    else:
        return tuple(0, 0)

def handle_back_block(line: str) -> BackBlock:
    if not entering_table_block(line):
        return TextBlock([line])
    else:
        dims = get_table_dimensions(line)
        cells = line.split('\t')
        table:list[list[str]]
        for row in range(0, dims[0]): #iterate 0,1,2
            table.append([])
            for col in range(0, dims[1]): #iterate 0,1,2
                index = 2*row + col + row
                print(cells[index])
                table[row].append(cells[index])
        return table

def create_anki_cards(doc_path: str) -> list[AnkiCard]:
    anki_cards = []
    with open(doc_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    front = lines[0].strip()
    back = []
    dims = (0, 0)
    enteredTable = False
    for line in lines[1:]:
        clean = line.strip()        
        first_char = clean[0]
        
        # append to back
        if not is_front_of_card(first_char) and not enteredTable:
            back.append(handle_back_block(line))
        #create a new card and reinitialize front and back
        elif is_front_of_card(first_char) and not enteredTable:
            anki_cards.append(AnkiCard(front, back))
            front = clean
            back = []
    return anki_cards

if __name__ == "__main__":
    doc_path = "raw_anki_cards.txt"
    anki_cards = create_anki_cards(doc_path)
    for card in anki_cards:
        print(card)