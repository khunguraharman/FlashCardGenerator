from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, AnalyzeResult, ParagraphRole
import os, json, re
from AnkiCard import BasicAnkiCard, ClozeAnkiCard, RawClozeAnkiCard, TableLocation
from ProcessResults import handle_pediatric_approach_table, write_basic_cards, check_multi_page_table, write_cloze_cards, parse_ref, process_table, process_multi_page_table, section_exception, process_exception_table_one, process_footer_headers, create_set_title_pages

# this functions helps viaualize the document structure
def analyze_document() -> None:
    endpoint = os.getenv("doc_intel_endpoint")
    credential = AzureKeyCredential(os.getenv("doc_intel_key"))
    model_id = "prebuilt-layout"
    doc_path = "ortho_review.pdf"
    document_intelligence_client = DocumentIntelligenceClient(endpoint, credential)
    with open(doc_path, "rb") as f:
        poller = document_intelligence_client.begin_analyze_document(
            model_id=model_id,body=AnalyzeDocumentRequest(bytes_source=f.read()), pages="40-123"
        )
    result = poller.result()
    titlePages = create_set_title_pages(result.pages)

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

    current_section = ""

    while stack:
        section_idx, element_idx = stack.pop()
        
        if element_idx == 0:
            # skip section if re-entering an already visited section
            if section_idx in visited_sections:
                continue
            # add the section to visited when you first enter it
            visited_sections.add(section_idx)

        # get all elements of the section, tables, paragraphs, etc...
        section = sections[section_idx]
        elements = section.elements or  []

        # check what element to process in the current iteration
        current_ref = elements[element_idx]

        # is another iteration is required for the next element?
        if element_idx + 1 < len(elements):
            stack.append((section_idx, element_idx + 1))

        kind, idx = parse_ref(current_ref)        

        if kind == "sections":
            if idx not in visited_sections:
                stack.append((idx, 0))
        elif kind == "paragraphs":

            if result.paragraphs[idx].bounding_regions[0].page_number in titlePages:
                current_section = result.paragraphs[idx].content
                continue

            if (element_idx == 0 and not section_exception(result.paragraphs[idx].content)) or result.paragraphs[idx].content.startswith(BasicAnkiCard.EXLCUDE_NOTES):
                continue

            if result.paragraphs[idx].bounding_regions[0].page_number == 268:
                if result.paragraphs[idx].content in RawClozeAnkiCard.EXCLUDE_STRINGS:
                    continue
            
            paragraphs_to_print.append(result.paragraphs[idx].content.strip() + f"\t pg:{result.paragraphs[idx].bounding_regions[0].page_number} \t SECTION:{current_section}")

            if result.paragraphs[idx].bounding_regions[0].page_number == 594 and result.paragraphs[idx+1].role == ParagraphRole.PAGE_FOOTER:
                # get the next table and it's index
                for i in range(element_idx, len(elements)):
                    element_kind, table_idx = parse_ref(elements[i])
                    if element_kind == "tables":
                        break
                spinal_table = process_footer_headers(result.paragraphs[idx+1], result.paragraphs[idx+2], result.tables[table_idx], table_idx)
                paragraphs_to_print.extend(spinal_table)
                continue

        elif kind == "tables":
            if RawClozeAnkiCard.TABLE_TO_SKIP.page == result.tables[idx].bounding_regions[0].page_number and idx == RawClozeAnkiCard.TABLE_TO_SKIP.table_index:
                continue

            # two multipage tables should be included as BasicAnkiCards, check if those exceptions are hit
            if result.tables[idx].bounding_regions[0].page_number == 589:
                paragraphs_to_print.extend(process_exception_table_one(result.tables[idx], result.tables[idx+1], idx))
                continue

            if result.tables[idx].bounding_regions[0].page_number == 269:
                tables_to_print.extend(handle_pediatric_approach_table(result.tables[idx]))
                continue

            multi_page_table: bool = check_multi_page_table(result.tables, idx)
            #if multi page table, must prepare to skip next table
            if multi_page_table:
                tables_to_print.extend(process_multi_page_table(result.tables[idx], result.tables[idx + 1]))
            else:
                tables_to_print.extend(process_table(result.tables[idx], current_section, result.tables[idx].bounding_regions[0].page_number))

    write_basic_cards(paragraphs_to_print)
    write_cloze_cards(tables_to_print)
    return

if __name__ == "__main__":
    analyze_document()