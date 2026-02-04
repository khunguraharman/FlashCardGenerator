from dataclasses import dataclass, field
from email import header
from http import client
from pyclbr import Class
from typing import ClassVar
import re, hashlib

def normalize_question(q: str) -> str:
    q = q.strip().lower()
    q = re.sub(r"\s+", " ", q)          # collapse whitespace    
    return q

def make_id_from_question(question: str) -> str:
    norm = normalize_question(question)
    digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()
    return f"q_{digest[:32]}"           # short, still extremely collision-resistant

def normalize_headers(headers: list[str]) -> str:
    normalized_headers: str = []
    for header in headers:
        header = header.strip().lower()
        header = re.sub(r"\s+", " ", header)  # collapse whitespace
        normalized_headers.append(header)
    return normalized_headers

@dataclass
class AnkiCard:
    id: str = field(init=False)

@dataclass
class BasicAnkiCard(AnkiCard):
    front: str
    back: list[str]

    EXLCUDE_NOTES: ClassVar[str] = "NOTE:"    
    def __post_init__(self) -> None:
        self.id = make_id_from_question(self.front)

@dataclass
class TableLocation:
    page: int
    table_index: int

@dataclass
class RawClozeAnkiCard:
    tableHeaders: list[str]
    section: str
    page: int
    clozeFragments: list[str]

    TABLE_TO_SKIP: ClassVar[TableLocation] = TableLocation(page=-1, table_index=-1)
    MULTI_PAGE_TABLES: ClassVar[dict[int,int]] = {172: 173, 186: 187, 225: 226, 551: 552}
    EXCLUDE_STRINGS: ClassVar[set[str]] = {"What are the advantages and disadvantages of arthroscopic vs. open and screw vs. suture fixation? [JAAOS 2018;26:360-367]", "Advantages", "Disadvantages"}

@dataclass
class ClozeAnkiCard(AnkiCard):
    headers: list[str] = field(default_factory=list)
    section: str = field(default_factory=str)
    page: int = field(default_factory=int)
    clozeDeletions: list[str] = field(default_factory=list)
    def __post_init__(self) -> None:
        normalized_headers = normalize_headers(self.headers)
        normalized_deletions = normalize_headers(self.clozeDeletions)
        combined = "".join(normalized_headers)
        combined += "".join(normalized_deletions)
        self.id = make_id_from_question(combined)

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
        reference: list[str] = lines[i].split('\t')
        section = reference[-2]
        page = int(reference[-1])
        headers = reference[:-2]
        fragments = lines[i+1].split('\t')
        fragments = fragments[:-1]
        anki_cards.append(ClozeAnkiCard(headers, section, page, clozeDeletions = fragments))
    return anki_cards

@dataclass
class PresentationAsset:
    front: str
    back: str