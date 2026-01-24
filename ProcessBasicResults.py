import json

def parse_basic_response(response_text: str) -> list[dict]:
    items = []

    try:
        items = json.loads(response_text)
    except:
        print("not a true JSON")

    return items