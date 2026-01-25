from openai import AzureOpenAI, completions
from azure.core.credentials import AzureKeyCredential
import json, os
from AnkiCard import PresentationAsset

def parse_search_response(response_text: str) -> list[dict]:
    pairs:list[dict] = []
    
    try: 
        pairs = json.loads(response_text)
    except json.JSONDecodeError:
        print("Error: Response text is not valid JSON.")
    
    return pairs

def process_qna(pairs: list[dict]) -> list[PresentationAsset]:
    assets = []

    for pair in pairs:
        content = pair["content"]
        split_content = content.split("\n 1.")
        front = split_content[0]
        back = content.removeprefix(front + "\n")
        assets.append(PresentationAsset(front, back))

    return assets

def process_canonical_pairs(pairs: list[dict]) -> list[str]:
    aoai_version = "2025-01-01-preview"
    aoai_api_key = os.getenv("azure_openai_gpt_key")
    gpt_url:str = os.getenv("azure_openai_gpt_endpoint")

    client = AzureOpenAI(
    api_version=aoai_version,
    azure_endpoint=gpt_url,
    api_key=aoai_api_key
    )

    deployment_name = "gpt-4.1-mini"

    # Prepare the chat prompt
    chat_prompt = [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": "You take canonical pairs of tabular data and create a single coherent sentence. You only reference the tabular data provided as canonical pairs. The canonical pairs represent factual information relevant to topics of orthopedic surgery."
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": ""
                }
            ]
        }
    ]

    completions_list: list[str] = []
    for pair in pairs:
        content: str = pair['content']
        chat_prompt[1]['content'][0]['text'] = content
        completion = client.chat.completions.create(model=deployment_name, 
                                                    messages=chat_prompt, 
                                                    max_tokens=2000,
                                                    temperature=0,
                                                    top_p=0.95,
                                                    frequency_penalty=0,
                                                    presence_penalty=0,
                                                    stop=None,
                                                    stream=False
        )
        completions_list.append(completion.choices[0].message.content)
    
    return completions_list