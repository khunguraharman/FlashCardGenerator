from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult
import os, json, re
from AnkiCard import BasicAnkiCard, ClozeAnkiCard, RawClozeAnkiCard, TableLocation
from ProcessResults import write_basic_cards, check_multi_page_table, write_cloze_cards, parse_ref, process_table, process_multi_page_table, section_exception, process_exception_table

# this functions helps viaualize the document structure
def analyze_document() -> None:
    endpoint = os.getenv("doc_intel_endpoint")
    credential = AzureKeyCredential(os.getenv("doc_intel_key"))
    model_id = "prebuilt-layout"
    doc_path = "ortho_review.pdf"
    document_intelligence_client = DocumentIntelligenceClient(endpoint, credential)
    with open(doc_path, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            model_id=model_id,body=AnalyzeDocumentRequest(bytes_source=f.read()), pages="589-590"
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

        # get section paragraph 0 

        if kind == "sections":
            if idx not in visited_sections:
                stack.append((idx, 0))
        elif kind == "paragraphs":
            if (element_idx == 0 and not section_exception(result.paragraphs[idx].content)) or result.paragraphs[idx].content.startswith(BasicAnkiCard.EXLCUDE_NOTES):
                continue
            else:
                paragraphs_to_print.append(result.paragraphs[idx].content.strip())
        elif kind == "tables":
            if RawClozeAnkiCard.TABLE_TO_SKIP.page == result.tables[idx].bounding_regions[0].page_number and idx == RawClozeAnkiCard.TABLE_TO_SKIP.table_index:
                continue

            # two multipage tables should be included as BasicAnkiCards, check if those exceptions are hit
            if result.tables[idx].bounding_regions[0].page_number == 589:
                paragraphs_to_print.extend(process_exception_table(result.tables[idx], result.tables[idx+1], idx))
                continue

            multi_page_table: bool = check_multi_page_table(result.tables, idx)
            #if multi page table, must prepare to skip next table
            if multi_page_table:
                tables_to_print.extend(process_multi_page_table(result.tables[idx], result.tables[idx + 1]))
            else:
                tables_to_print.extend(process_table(result.tables[idx]))

    write_basic_cards(paragraphs_to_print)
    write_cloze_cards(tables_to_print)
    return

if __name__ == "__main__":
    analyze_document()