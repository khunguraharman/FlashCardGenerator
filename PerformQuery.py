from azure.search.documents.knowledgebases.models import KnowledgeBaseMessage, KnowledgeBaseMessageTextContent, KnowledgeBaseRetrievalRequest, KnowledgeRetrievalMinimalReasoningEffort, SearchIndexKnowledgeSourceParams
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.core.credentials import AzureKeyCredential
import os

def getQuery() -> str:
    try:
        query = input("Enter your query: ")
    except EOFError:
        query = "I want to learn about screws."
    return query

def structureMessages(instruction: str, user_input: str) -> list[dict]:
    messages = [
    {
        "role": "system",
        "content": instruction
    }
    ]

    messages.append({
        "role": "user",
        "content": user_input
    })
    return messages

def structureRequest(messages: list[dict], knowledge_src_name: str) -> KnowledgeBaseRetrievalRequest:
    req = KnowledgeBaseRetrievalRequest(
        messages=[
            KnowledgeBaseMessage(
            role=i["role"], 
            content=[KnowledgeBaseMessageTextContent(text=i["content"])]
            ) for i in messages if i["role"] != "system"
        ],
        knowledge_source_params=[
            SearchIndexKnowledgeSourceParams(
                knowledge_source_name=knowledge_src_name,
                include_references=True,
                include_reference_source_data=True,
                always_query_source=True
            )
        ],
        include_activity = True,
        retrieval_reasoning_effort = KnowledgeRetrievalMinimalReasoningEffort
    )
    return req

def performQuery() -> None:
    user_input = getQuery()

    search_endpoint = os.getenv("ai_search_url")
    ai_search_key = os.getenv("ai_search_key")

    agent_client_basic = KnowledgeBaseRetrievalClient(endpoint=search_endpoint, knowledge_base_name="knowledgebase-1767925291166", credential=AzureKeyCredential(ai_search_key))
    agent_client_cloze = KnowledgeBaseRetrievalClient(endpoint=search_endpoint, knowledge_base_name="knowledgebase-1768870241919", credential=AzureKeyCredential(ai_search_key))
    
    basic_message = structureMessages(instruction="You retrieve question and answers on topics relevant to orthopedic surgery, for the purpose of aspriting surgeons to study",
                                      user_input = user_input)
    cloze_message = structureMessages(instruction="You retrieve canonical pairs on topics relevant to orthopedic surgery, for the purpose of aspiring surgeons to study",
                                      user_input = user_input)

    basic_req = structureRequest(messages=basic_message, knowledge_src_name="knowledgesource-1767925273396")
    cloze_req = structureRequest(messages=cloze_message, knowledge_src_name="knowledgesource-1768175052028")
    
    basic_result = agent_client_basic.retrieve(retrieval_request=basic_req)
    print(f"Retrieved content from '{"knowledgebase-1767925291166"}' successfully.")

    cloze_result = agent_client_cloze.retrieve(retrieval_request=cloze_req)
    print(f"Retrieved content from '{"knowledgebase-1768870241919"}' successfully.")
    return

if __name__ == "__main__":
    performQuery()