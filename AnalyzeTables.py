from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
import os, json
from AnkiCard import AnkiCard, is_front_of_card, create_anki_cards
from dataclasses import dataclass

@dataclass
class TableDimensions:
    page: int
    row_count: int
    column_count: int
    span_start: int
    span_end: int

def check_table(paragraph, next_table: TableDimensions) -> bool:
    par_page = paragraph.bounding_regions[0].page_number
    if par_page != next_table.page:
        return False
    if paragraph.spans[0].offset >= next_table.span_start and paragraph.spans[0].offset + paragraph.spans[0].length <= next_table.span_end:
        return True
    return False

def append_raw_cards(paragraph, raw_anki_cards: list[str]) -> None:
    if not paragraph.role:
        raw_anki_cards.append(paragraph.content)
    return

def concatenate_table_cells(paragraph, raw_anki_cards: list[str]) -> None:
    if not paragraph.role:
        raw_anki_cards[-1] += "\t" + paragraph.content
    return    

def write_raw_anki_cards(content: list[str]) -> None:
    file_path = "raw_anki_cards_w_tables.txt"
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
            model_id=model_id,body=AnalyzeDocumentRequest(bytes_source=f.read()), pages="122"
        )
    result = poller.result()

    tables = result.tables
    table_index = 0
    raw_table = tables[table_index]
    next_table = TableDimensions(raw_table.bounding_regions[0].page_number, raw_table.row_count, raw_table.column_count, raw_table.spans[0].offset, raw_table.spans[0].offset + raw_table.spans[0].length)

    raw_anki_cards = []
    inTable: bool = False
    for paragraph in result.paragraphs:
        if table_index >= len(tables):
            append_raw_cards(paragraph, raw_anki_cards)
            continue
        if not check_table(paragraph=paragraph, next_table=next_table):
            if inTable:
                inTable = False
                raw_anki_cards.append(f"{AnkiCard.tableEnd}{next_table.row_count}x{next_table.column_count}")
                table_index += 1
            append_raw_cards(paragraph, raw_anki_cards)

        elif check_table:
            if not inTable:
                inTable = True
                raw_anki_cards.append(f"{AnkiCard.tableStart}{next_table.row_count}x{next_table.column_count}")
                append_raw_cards(paragraph, raw_anki_cards)
            else:
                concatenate_table_cells(paragraph, raw_anki_cards)
    write_raw_anki_cards(raw_anki_cards)
    return

if __name__ == "__main__":
    analyze_document()

