from azure.search.documents.knowledgebases.models import KnowledgeBaseMessage, KnowledgeBaseMessageTextContent, KnowledgeBaseRetrievalRequest, KnowledgeBaseRetrievalResponse, KnowledgeRetrievalLowReasoningEffort, SearchIndexKnowledgeSourceParams
from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
from azure.core.credentials import AzureKeyCredential
import os
from ProcessSearchResults import create_basic_cards, create_cloze_cards, parse_search_response, process_canonical_pairs, process_qna

def getQuery(question: str) -> str:
    try:
        query = input(question)
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
        retrieval_reasoning_effort = KnowledgeRetrievalLowReasoningEffort
    )
    return req

def performQuery() -> tuple[KnowledgeBaseRetrievalResponse, KnowledgeBaseRetrievalResponse]:
    search_endpoint = os.getenv("ai_search_url")
    ai_search_key = os.getenv("ai_search_key")

    agent_client_basic = KnowledgeBaseRetrievalClient(endpoint=search_endpoint, knowledge_base_name="knowledgebase-1767925291166", credential=AzureKeyCredential(ai_search_key))
    agent_client_cloze = KnowledgeBaseRetrievalClient(endpoint=search_endpoint, knowledge_base_name="knowledgebase-1768870241919", credential=AzureKeyCredential(ai_search_key))
    
    basic_query = getQuery("Enter your query for basic Q&A retrieval: ")
    basic_message = structureMessages(instruction="You retrieve question and answers on topics relevant to orthopedic surgery, for the purpose of aspriting surgeons to study",
                                      user_input = basic_query)
    cloze_query = getQuery("Enter your query for canonical pair retrieval: ")
    cloze_message = structureMessages(instruction="You retrieve canonical pairs on topics relevant to orthopedic surgery, for the purpose of aspiring surgeons to study",
                                      user_input = cloze_query)

    basic_req = structureRequest(messages=basic_message, knowledge_src_name="knowledgesource-1767925273396")
    cloze_req = structureRequest(messages=cloze_message, knowledge_src_name="knowledgesource-1768175052028")
    
    basic_result = agent_client_basic.retrieve(retrieval_request=basic_req)
    print(f"Retrieved content from '{"knowledgebase-1767925291166"}' successfully.")

    cloze_result = agent_client_cloze.retrieve(retrieval_request=cloze_req)
    print(f"Retrieved content from '{"knowledgebase-1768870241919"}' successfully.")
    return tuple([basic_result, cloze_result])

if __name__ == "__main__":
    searchResults = performQuery()
    create_basic_cards(process_qna(parse_search_response(searchResults[0].response[0].content[0].text)))
    create_cloze_cards(process_canonical_pairs(parse_search_response(searchResults[1].response[0].content[0].text)))
