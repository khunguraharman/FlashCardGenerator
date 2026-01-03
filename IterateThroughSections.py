from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
import os, json
from AnkiCard import BasicAnkiCard, RawClozeAnkiCard
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

def write_basic_cards(content: list[str]) -> None:
    file_path = "basic_anki_cards.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        for line in content:
            f.write(line + "\n")
    return

def write_cloze_cards(content: list[RawClozeAnkiCard]) -> None:
    file_path = "cloze_anki_cards.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        for card in content:
            for header in card.tableHeaders:
                f.write(header + "\t")
            # create a new line
            f.write("\n")
            # repeat headers for each row
            for fragment in card.clozeFragments:
                # write out fragments                
                f.write(fragment + "\t")
            f.write("\n")
    return

def parse_ref(ref: str) -> tuple[str, int]:
    # "/paragraphs/0" -> ("paragraphs", 0)
    _, kind, idx = ref.split("/")
    return kind, int(idx)

def process_table(table) -> list[RawClozeAnkiCard]:
    all_fragments: list[RawClozeAnkiCard] = []
    cloze_fragments: list[str] = []
    headers: list[str] = []
    current_row: int = 1
    for cell in table.cells:
        if cell.kind == "columnHeader" and cell.row_index == 0:
            headers.append(cell.content)
            continue
        row = cell.row_index
        if row == current_row:
            cloze_fragments.append(cell.content)
        else:
            all_fragments.append(RawClozeAnkiCard(headers, cloze_fragments))
            cloze_fragments = [cell.content]
            current_row = row
    return all_fragments

def analyze_document() -> None:
    endpoint = os.getenv("doc_intel_endpoint")
    credential = AzureKeyCredential(os.getenv("doc_intel_key"))
    model_id = "prebuilt-layout"
    doc_path = "ortho_review.pdf"
    document_intelligence_client = DocumentIntelligenceClient(endpoint, credential)
    with open(doc_path, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            model_id=model_id,body=AnalyzeDocumentRequest(bytes_source=f.read()), pages="170-173"
        )
    result = poller.result()

    sections = result.sections

    if sections is None:
        return

    if sections[0].elements is None:
        return

    # start the stack at the first section's first element
    stack: list[tuple[int,int]] = [(0,0)]

    visited_sections:set[int] = set()

    paragraphs_to_print: list[str] = []
    tables_to_print: list[list[str]] = []

    while stack:
        section_idx, element_idx = stack.pop()
        # add the section to visited when you first enter it
        if element_idx == 0:
            if section_idx in visited_sections:
                continue
            visited_sections.add(section_idx)

        section = sections[section_idx]
        elements = section.elements or  []
        current_ref = elements[element_idx]

        #ensure the next element is processed as well
        if element_idx + 1 < len(elements):
            stack.append((section_idx, element_idx + 1))

        kind, idx = parse_ref(current_ref)

        if kind == "sections":
            if idx not in visited_sections:
                stack.append((idx, 0))
        elif kind == "paragraphs":
            if element_idx == 0 or result.paragraphs[idx].content.startswith(BasicAnkiCard.EXLCUDE_NOTES):
                continue
            else:
                paragraphs_to_print.append(result.paragraphs[idx].content.strip())
        elif kind == "tables":
            tables_to_print.extend(process_table(result.tables[idx]))

    write_basic_cards(paragraphs_to_print)
    write_cloze_cards(tables_to_print)
    return

if __name__ == "__main__":
    analyze_document()