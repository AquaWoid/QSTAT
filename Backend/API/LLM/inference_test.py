import requests
import re

system_prompt = """
    Du bist ein Chefkoch für Japanische Küche, wenn dich ein Nutzer nach einem Rezept Fragt versuchst du ihm die bestmöglichen Vorschläge zu machen. Wichtig ist, dass kein Gluten verwendet werden darf
"""


def resolve_prompt(prompt: str):

    headers = {
        'Content-Type': 'application/json',
    }

    json_data = {
        'model': 'Qwen/Qwen3-14B-AWQ',
        'messages': [
            {
                'role': 'system',
                'content': f'{system_prompt}',
            },
            {
                'role': 'user',
                'content': f'{prompt}',
            },
        ],
    }

    response = requests.post('http://vllm:8000/v1/chat/completions', headers=headers, json=json_data)

    print(response.text)

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    print(content)
    return content

    #data = json.loads(response)
