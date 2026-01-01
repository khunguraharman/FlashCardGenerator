class AnkiCard:
    def __init__(self, front: str, back: list[str], table: list[list[str]]):
        self.front = front
        self.back = back
        self.table = table
    def __repr__(self):
        return f"AnkiCard(front={self.front!r}, back={self.back!r}, table={self.table!r})"

def is_front_of_card(first_char: str) -> bool:
    # Implement logic to determine if a string is the front of an Anki card    
    if first_char.isupper() and 'A' <= first_char <= 'Z':
        return True
    else:
        return False

def create_anki_cards(doc_path: str) -> list[AnkiCard]:
    anki_cards = []
    with open(doc_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    front = lines[0].strip()
    back = []
    for line in lines[1:]:
        clean = line.strip()
        first_char = clean[0]
        # append to back
        if not is_front_of_card(first_char):
            back.append(clean)
        #create a new card and reinitialize front and back
        else:
            anki_cards.append(AnkiCard(front, back))
            front = clean
            back = []            
    return anki_cards

if __name__ == "__main__":
    doc_path = "raw_anki_cards.txt"
    anki_cards = create_anki_cards(doc_path)
    for card in anki_cards:
        print(card)