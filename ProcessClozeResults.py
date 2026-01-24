from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
import json

def parse_cloze_response(response_text: str) -> list[dict]:
    pairs:list[dict] = []
    
    try: 
        pairs = json.loads(response_text)
    except json.JSONDecodeError:
        print("Error: Response text is not valid JSON.")



    return pairs