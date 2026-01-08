from dataclasses import dataclass, field
from http import client
from pyclbr import Class
from typing import ClassVar, Union
import re, hashlib, os
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchIndexingBufferedSender


def normalize_question(q: str) -> str:
    q = q.strip().lower()
    q = re.sub(r"\s+", " ", q)          # collapse whitespace    
    return q

def make_id_from_question(question: str) -> str:
    norm = normalize_question(question)
    digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()
    return f"q_{digest[:32]}"           # short, still extremely collision-resistant

def normalize_headers(headers: list[str]) -> str:
    normalized_headers: str
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
class RawClozeAnkiCard:
    tableHeaders: list[str]
    clozeFragments: list[str]

@dataclass
class ClozeAnkiCard(AnkiCard):
    headers: list[str]
    clozeDeletions: list[str]
    def __post_init__(self) -> None:
        normalized_headers = normalize_headers(self.headers)
        normalized_deletions = normalized_headers(self.clozeDeletions)
        combined = normalized_headers.join(normalized_deletions)
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
        headers: list[str] = lines[i].split('\t')
        fragments = lines[i+1].split('\t')
        anki_cards.append(ClozeAnkiCard(headers, clozeDeletions = fragments))
    return anki_cards

if __name__ == "__main__":
    doc_path = "basic_anki_cards.txt"
    basic_anki_cards = create_basic_cards(doc_path)
    #cloze_anki_cards = create_cloze_cards("cloze_anki_cards.txt")
    embedding_url:str = os.getenv("azure_openai_endpoint")
    aoai_model_name = "text-embedding-3-large"
    aoai_deployment = aoai_model_name
    aoai_version = "2024-12-01-preview"
    aoai_api_key = os.getenv("azure_openai_api_key")

    client = AzureOpenAI(
        api_version=aoai_version,
        azure_endpoint=embedding_url,
        api_key=aoai_api_key
    )

    search_endpoint = os.getenv("ai_search_url")
    ai_search_key = os.getenv("ai_search_key")

    batch_client = SearchIndexingBufferedSender(endpoint = search_endpoint, index_name="test_rag", credential=AzureKeyCredential(ai_search_key))
    documents = []
    docs_to_remove = []
    for card in basic_anki_cards:
        print(card)
        answer_text: str =  "\n".join(line.strip() for line in card.back if line.strip())
        embedding_text = "\n".join([
            f"Q: {card.front.strip()}",
            "A:", answer_text])
        response = client.embeddings.create(input = [embedding_text], model=aoai_deployment)
        embedding:list[float] = response.data[0].embedding
        documents.append( {"id": card.id ,"question": card.front, "answer": answer_text, "vector_text_ada_large": embedding})
        docs_to_remove.append( {"id": card.id} )
    batch_client.delete_documents(documents = docs_to_remove)
    flushed = batch_client.flush()
    batch_client.upload_documents(documents = documents)
    flushed_2 = batch_client.flush()
    batch_client.close()