import requests
import re
import urllib.response
from fastapi.responses import StreamingResponse
import json


system_prompt = """
    Du bist ein Chefkoch für Japanische Küche, wenn dich ein Nutzer nach einem Rezept Fragt versuchst du ihm die bestmöglichen Vorschläge zu machen. Wichtig ist, dass kein Gluten verwendet werden darf
"""


async def resolve_prompt(prompt: str):

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


def resolve_prompt_realtime(payload: dict):
    def stream():
        headers = {
            'Content-Type': 'application/json',
            "Accept" : "text/event-stream"
        }

        json_data = {
            'model': 'Qwen/Qwen3-14B-AWQ',
            'messages': [
                {
                    'role': 'system',
                    'content': f'{system_prompt}',
                },
            ] + payload["messages"],
            "stream" : True,
            "chat_template_kwargs": {
                "enable_thinking": payload.get("thinking", False)
            }
        }

        data = json.dumps(json_data).encode("utf-8")

        request = urllib.request.Request(
           "http://vllm:8000/v1/chat/completions",
           data=data,
           method="POST",
           headers=headers
        )

        with urllib.request.urlopen(request, timeout=120) as response:
            while True:
                chunk = response.read(1024)
                if not chunk:
                    break

                yield chunk

    return StreamingResponse(
        stream(),
        media_type="text/event-stream"
    )