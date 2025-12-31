class AnkiCard:
    def __init__(self, front: str, back: list[str]):
        self.front = front
        self.back = back
    def __repr__(self):
        return f"AnkiCard(front={self.front!r}, back={self.back!r})"