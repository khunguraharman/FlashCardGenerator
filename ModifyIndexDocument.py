from azure.search.documents import SearchClient
import os
from azure.core.credentials import AzureKeyCredential

if __name__ == "__main__":
    search_endpoint = os.getenv("ai_search_url")
    ai_search_key = os.getenv("ai_search_key")
    index_name = "cloze_rag_v2"
    search_client = SearchClient(endpoint = search_endpoint, index_name=index_name, credential=AzureKeyCredential(ai_search_key))
    # docs: list[dict] = [{"id": "q_37a2de2ccd307a902811af1da31d8911"},
    #                     {"id": "q_37a84d70b93ec6faa85a669f1c71e702"},
    #                     {"id": "q_ca222cd99382f4ab1fd5116b7497229d"},
    #                     {"id": "q_2cfd59a38cd25c7c7c7f1ba9fe8b4efd"},
    #                     {"id": "q_0610da945d4afd9bd6a4eb2ccd64d273"}]
    new_index = search_client.delete_documents([])
    print(new_index)
    for index in new_index:
        print(index)