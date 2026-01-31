from azure.search.documents import SearchClient
import os
from azure.core.credentials import AzureKeyCredential

if __name__ == "__main__":
    search_endpoint = os.getenv("ai_search_url")
    ai_search_key = os.getenv("ai_search_key")
    index_name = "cloze_rag"
    search_client = SearchClient(endpoint = search_endpoint, index_name=index_name, credential=AzureKeyCredential(ai_search_key))
    new_index = search_client.delete_documents([])
    print(new_index)
    for index in new_index:
        print(index)