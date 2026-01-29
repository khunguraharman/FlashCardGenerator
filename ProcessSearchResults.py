from openai import AzureOpenAI, completions
from azure.core.credentials import AzureKeyCredential
import json, os
from AnkiCard import PresentationAsset
from pathlib import Path

def createResultsFile(targetFile: str) ->  str:
    if not targetFile.endswith(".txt"):
        targetFile += ".txt"
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)  # creates dir if it doesn't exist
    return results_dir / targetFile

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

def create_basic_cards(assets: list[PresentationAsset]) -> None:
    file_path = createResultsFile("final_basic_card_strings.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        for card in assets:
            f.write(card.front + "\n")
            f.write(card.back + "\n\n")
    return

def process_canonical_pairs(pairs: list[dict]) -> list[tuple[str, str]]:
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

    completions_list: list[tuple[str,str]] = []
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
        card: tuple[str, str] = tuple([content, completion.choices[0].message.content])
        completions_list.append(card)
    
    return completions_list

def create_cloze_cards(pairs: list[tuple[str, str]]) -> None:
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
                    "text": "You take canonical pairs of tabular data and reference the provided sentence to create a Cloze Anki card that serves as a fill-in-the-blank exercise for aspiring surgeons. You only reference the tabular data and the sample sentence provided. The canonical pairs and sample sentence represent factual information relevant to topics of orthopedic surgery. The tabular values should be replaced with {{cX::Y}}, where X is an integer representing the blank number, and Y is the string representing the answer."
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

    completed_cloze_cards: list[str] = []
    for pair in pairs:
        prompt_text = f"pairs: " + pair[0] + " ; sentence: " + pair[1]
        chat_prompt[1]['content'][0]['text'] = prompt_text
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
        completed_cloze_cards.append(completion.choices[0].message.content)

    file_path = createResultsFile("final_cloze_card_strings.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        for card in completed_cloze_cards:
            f.write(card + "\n")

    return