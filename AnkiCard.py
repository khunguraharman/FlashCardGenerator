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
    if first_char.isupper() and 'A' <= first_char <= 'Z':
        return True
    else:
        return False

def check_in_table_block(line: str, inTable: bool, dims: tuple[int, int]) -> tuple[bool, tuple[int, int]]:
    if line.startswith(AnkiCard.tableStart):
        rowcol = get_table_dimensions(line)
        #print(f"Assigned dims: {rowcol}")
        #print(f"DETECTED A TABLE: {line}")
        return (True, rowcol)
    elif line.startswith(AnkiCard.tableEnd):
        rowcol = (0, 0)
        #print(f"Assigned dims: {rowcol}")
        #print(f"NOT A TABLE: {line}")
        return (False, rowcol)
    else:
        #print(f"No Change to dims: {dims}")
        #print(f"NO CHANGE: {line}")
        return (inTable, dims)

def get_table_dimensions(line: str) -> tuple[int, int]:
    match = re.search(r'(\d+)x(\d+)$', line)
    if match:
        dims = tuple(map(int, match.groups()))
        return dims
    else:
        return tuple(0, 0)

def handle_table_block(line: str, dims: tuple[int, int]) -> TableBlock:
    #print(line)
    #print(dims)
    cells = line.split('\t')
    table:list[list[str]] = []
    for row in range(0, dims[0]): #iterate 0,1,2
        cols = []
        for col in range(0, dims[1]): #iterate 0,1,2
            index = 2*row + col + row
            cols.append(cells[index])
            print(cells[index])
        table.append(cols)
    return table

def create_anki_cards(doc_path: str) -> list[AnkiCard]:
    anki_cards = []
    with open(doc_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    front = lines[0].strip()
    back = []
    dims = (0,0)
    inTable = False
    for line in lines[1:]:
        clean = line.strip()
        first_char = clean[0]
        (inTable, dims) = check_in_table_block(clean, inTable, dims)
        # if inTable = True, must append to back
        if inTable:
            if clean.startswith(AnkiCard.tableStart):
                continue            
            back.append(handle_table_block(line, dims))
        #create a new card and reinitialize front and back
        elif not inTable and not is_front_of_card(first_char):
            if clean.startswith(AnkiCard.tableEnd):
                continue
            back.append(TextBlock([clean]))
        else:
            anki_cards.append(AnkiCard(front, back))
            front = clean
            back = []
    return anki_cards

if __name__ == "__main__":
    doc_path = "raw_anki_cards_w_tables.txt"
    anki_cards = create_anki_cards(doc_path)
    for card in anki_cards:
        print(card)