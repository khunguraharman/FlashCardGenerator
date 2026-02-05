from AnkiCard import RawClozeAnkiCard, TableLocation
import re

def write_basic_cards(content: list[str]) -> None:
    file_path = "basic_anki_cards.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        for line in content:
            f.write(line + "\n")
    return

def check_multi_page_table(result_tables, index: int) -> bool:
    # if last table, cannot be multi-page
    if index >= len(result_tables) - 1:
        return False

    first_page = result_tables[index].bounding_regions[0].page_number
    
    next_table_page = result_tables[index+1].bounding_regions[0].page_number

    is_multi_page = RawClozeAnkiCard.MULTI_PAGE_TABLES.get(first_page) == next_table_page

    if is_multi_page:
        RawClozeAnkiCard.TABLE_TO_SKIP = TableLocation(next_table_page, index + 1)

    return is_multi_page

def write_cloze_cards(content: list[RawClozeAnkiCard]) -> None:
    file_path = "cloze_anki_cards.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        for card in content:
            for header in card.tableHeaders:
                f.write(header + "\t")
            f.write(card.section + "\t")
            f.write(str(card.page))
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

def process_table(table, section: str, page: int) -> list[RawClozeAnkiCard]:
    all_fragments: list[RawClozeAnkiCard] = []
    cloze_fragments: list[str] = []
    headers: list[str] = []
    current_row: int = 1
    for cell in table.cells:
        if cell.row_index == 0:
            headers.append(cell.content)
            continue
        row = cell.row_index
        if row == current_row:
            cloze_fragments.append(cell.content)
        else:
            all_fragments.append(RawClozeAnkiCard(headers, section, page, cloze_fragments))
            cloze_fragments = [cell.content]
            current_row = row
    all_fragments.append(RawClozeAnkiCard(headers, section, page, cloze_fragments))
    return all_fragments

def merge_page_split_rows(table, next_table, section: str, page: int) -> list[RawClozeAnkiCard]:
    first_page = table.bounding_regions[0].page_number
    second_page = next_table.bounding_regions[0].page_number
    tmp_list = process_table(table, section, page)
    columns = table.column_count            
    assert columns == next_table.column_count, f"table.column_count {table.column_count} != next_table.column_count {next_table.column_count} for pages {first_page}-{second_page}"
    rows = next_table.row_count
    for i in range(rows):
        tmp_cloze_fragments: list[str] = []
        for j in range(columns):
            tmp_cloze_fragments.append(next_table.cells[i * columns + j].content)
        tmp_list.append(RawClozeAnkiCard(tmp_list[0].tableHeaders, section, page, tmp_cloze_fragments))
    return tmp_list

def process_multi_page_table(table, next_table, section: str, page: int) -> list[RawClozeAnkiCard]:
    first_page = table.bounding_regions[0].page_number
    second_page = next_table.bounding_regions[0].page_number
    match first_page:
        case 172 if RawClozeAnkiCard.MULTI_PAGE_TABLES.get(172) == second_page:
            tmp_list = process_table(table, section, page)
            tmp_list[-1].clozeFragments[-3] += next_table.cells[0].content + " " + next_table.cells[3].content + " " + next_table.cells[6].content + " " + next_table.cells[7].content
            tmp_list[-1].clozeFragments[-2] += next_table.cells[1].content
            tmp_list[-1].clozeFragments[-1] += next_table.cells[2].content + " " + next_table.cells[5].content + " " + next_table.cells[8].content
            return tmp_list
        case 186 if RawClozeAnkiCard.MULTI_PAGE_TABLES.get(186) == second_page:
            return merge_page_split_rows(table, next_table, section, page)
        case 225 if RawClozeAnkiCard.MULTI_PAGE_TABLES.get(225) == second_page:
            return merge_page_split_rows(table, next_table, section, page)
        case 551 if RawClozeAnkiCard.MULTI_PAGE_TABLES.get(551) == second_page:
            tmp_list = merge_page_split_rows(table, next_table, section, page)
            tmp_list[1].clozeFragments[-1] += " " + tmp_list[2].clozeFragments[-1]
            del tmp_list[2]
            return tmp_list

    return []

def section_exception(section: str) -> bool:
    if bool(re.match(r'^\d+\.', section)):
        return True
    elif bool(re.match(r'^[a-z]\.', section)):
        return True
    else:
        return False

def process_exception_table_one(first_table, next_table, idx) -> list[str]:
    RawClozeAnkiCard.TABLE_TO_SKIP = TableLocation(next_table.bounding_regions[0].page_number, idx + 1)
    headers: list[str] = []
    #appeding headers
    for column in range(first_table.column_count):
        headers.append(f"{first_table.cells[column].content.strip()} \t")            

    values = []
    for table in [first_table, next_table]:
        current_section = ""
        starting_cell = 0
        if table == first_table:
            starting_cell = first_table.column_count # if two columns, start at cell index 2, else start at 0        
        for cell in range(starting_cell, len(table.cells)):
            if table.cells[cell].content.strip().isupper():
                current_section = table.cells[cell].content.strip()
                continue
            if table.cells[cell].content.strip() == "":
                continue
            string = f"table: {headers[table.cells[cell].column_index]}: {current_section}: {table.cells[cell].content.strip()} \t"
            values.append(string)

    return values

def process_footer_headers(paragraph_one, paragraph_two, next_table, table_idx) -> list[str]:
    split_headers = paragraph_two.content.strip().split(" ")
    values: list[str] = []
    headers: list[str] = [paragraph_one.content.strip()]
    headers.extend(split_headers)
    # get the index of the next table
    RawClozeAnkiCard.TABLE_TO_SKIP = TableLocation(next_table.bounding_regions[0].page_number, table_idx)
    current_section = ""
    for cell in range(0, len(next_table.cells)):
        if next_table.cells[cell].content.strip().isupper():
            current_section = next_table.cells[cell].content.strip()
            continue
        if next_table.cells[cell].content.strip() == "":
            continue
        string = f"table: {headers[next_table.cells[cell].column_index]}: {current_section}: {next_table.cells[cell].content.strip()} \t"
        values.append(string)
    return values

def process_technique_table(table, section: str, page: int) -> list[RawClozeAnkiCard]:
    headers: list[str] = ["Technique", "Advantages", "Disadvantages"]
    all_fragments: list[RawClozeAnkiCard] = []
    for row in range(0, table.row_count):        
        cloze_fragments: list[str] = []
        for col in range(0, table.column_count):
            cloze_fragments.append(table.cells[row * table.column_count + col].content.strip())
        all_fragments.append(RawClozeAnkiCard(headers, section, page, cloze_fragments))
    return all_fragments

def process_fixation_table(table, section: str, page: int) -> list[RawClozeAnkiCard]:
    headers: list[str] = ["Fixation", "Advantages", "Disadvantages"]
    all_fragments: list[RawClozeAnkiCard] = []    
    for row in range(1, table.row_count):
        cloze_fragments: list[str] = []
        for col in range(0, table.column_count):
            cloze_fragments.append(table.cells[row * table.column_count + col].content.strip())
        all_fragments.append(RawClozeAnkiCard(headers, section, page, cloze_fragments))
    return all_fragments

def handle_pediatric_approach_table(table, section: str, page: int) -> list[RawClozeAnkiCard]:
    assert table.bounding_regions[0].page_number == 269
    if table.row_count == 2:
        return process_technique_table(table, section, page)
    else:
        return process_fixation_table(table, section, page)

def create_set_title_pages(pages) -> dict[int, str]:
    titlePages : dict[int, str] = {}
    for page in pages:
        if page.page_number == 179 or page.page_number == 547:
            titlePages[page.page_number] = page.lines[0].content
        elif len(page.lines) == 1 and page.lines[0].content.isupper():
            titlePages[page.page_number] = page.lines[0].content
    return titlePages