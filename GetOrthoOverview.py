from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
import os, json

def write_raw_anki_cards(content: list[str]) -> None:
    file_path = "raw_anki_cards.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        for line in content:
            f.write(line + "\n")
    return

def analyze_document() -> None:
    endpoint = os.getenv("doc_intel_endpoint")
    credential = AzureKeyCredential(os.getenv("doc_intel_key"))
    model_id = "prebuilt-layout"
    doc_path = "ortho_review.pdf"
    document_intelligence_client = DocumentIntelligenceClient(endpoint, credential)
    with open(doc_path, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            model_id=model_id,body=AnalyzeDocumentRequest(bytes_source=f.read()), pages="18-699"
        )
    result = poller.result()
    
    raw_anki_cards = []
    for paragraph in result.paragraphs:
        if not paragraph.role:
            raw_anki_cards.append(paragraph.content)

    write_raw_anki_cards(raw_anki_cards)
    return

if __name__ == "__main__":
    analyze_document()

