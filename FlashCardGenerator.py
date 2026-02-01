
import os
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchIndexingBufferedSender
from AnkiCard import BasicAnkiCard, ClozeAnkiCard, create_basic_cards, create_cloze_cards

def push_basic_anki_card():
    doc_path = "basic_anki_cards.txt"
    basic_anki_cards = create_basic_cards(doc_path)
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
    for card in basic_anki_cards:
        answer_text: str =  "\n".join(line.strip() for line in card.back if line.strip())
        embedding_text = "\n".join([
            f"Q: {card.front.strip()}",
            "A:", answer_text])
        response = client.embeddings.create(input = [embedding_text], model=aoai_deployment)
        embedding:list[float] = response.data[0].embedding
        documents.append( {"id": card.id ,"question": card.front, "answer": answer_text, "vector_text_ada_large": embedding}) 
    batch_client.upload_documents(documents = documents)
    batch_client.flush()
    batch_client.close()
    return

def create_string_from_cloze_card(card: ClozeAnkiCard) -> str:
    canonical_pairs:str = ""
    for i in range(len(card.headers)):
        pair:str = f"{card.headers[i]}: {card.clozeDeletions[i]} \n"
        canonical_pairs += pair
    return canonical_pairs

def push_cloze_anki_card():
    doc_path = "cloze_anki_cards.txt"
    cloze_anki_cards = create_cloze_cards(doc_path)
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

    batch_client = SearchIndexingBufferedSender(endpoint = search_endpoint, index_name="cloze_rag", credential=AzureKeyCredential(ai_search_key))
    documents = []
    for card in cloze_anki_cards:
        embedding_text = create_string_from_cloze_card(card)
        response = client.embeddings.create(input = [embedding_text], model=aoai_deployment)
        embedding:list[float] = response.data[0].embedding
        documents.append( {"id": card.id ,"pairs": embedding_text, "vector_text_ada_large": embedding}) 
    batch_client.upload_documents(documents = documents)
    batch_client.flush()
    batch_client.close()
    return

if __name__ == "__main__":
    #push_basic_anki_card()
    push_cloze_anki_card()