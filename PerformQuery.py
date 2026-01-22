from azure.search.documents.knowledgebases.models import KnowledgeBaseRetrievalRequest
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.core.credentials import AzureKeyCredential
import os

def getQuery() -> str:
    try:
        query = input("Enter your query: ")
    except EOFError:
        query = "I want to learn about screws."
    return query

def performQuery() -> None:
    user_input = getQuery()

    search_endpoint = os.getenv("ai_search_url")
    ai_search_key = os.getenv("ai_search_key")

    agent_client = KnowledgeBaseRetrievalClient(endpoint=search_endpoint, knowledge_base_name="knowledgebase-1767925291166", credential=AzureKeyCredential(ai_search_key))

    messages = [
    {
        "role": "system",
        "content": "You return questions and answers on topics relevant to orthopedic surgery for the sole purpose of helping aspiring surgeons study."
    }
    ]

    messages.append({
        "role": "user",
        "content": user_input
    })


    return

if __name__ == "__main__":
    performQuery()