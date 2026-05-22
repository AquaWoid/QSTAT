import requests
import re
import urllib.request
import json
from fastapi.responses import StreamingResponse
import API.Configs.system_prompts as system_prompts
import RAG.retrieval as RAG

hostname = "localhost"
VLLM_MODEL = "Qwen/Qwen3-14B-AWQ"
VLLM_URL = f"http://{hostname}:8000/v1/chat/completions"


# ── QualScope SSE streaming ───────────────────────────────────────────────────

def stream_chat_qualscope(payload: dict):
    """
    Generator that yields QualScope SSE events:
      data: {"type":"token","value":"..."}\n\n
      data: {"type":"cite","value":{...}}\n\n
      data: {"type":"done"}\n\n
    """
    messages = payload.get("messages", [])
    rag_cfg = payload.get("rag", {"on": False, "scope": "all"})

    cite_id = 100  # start well above seed CITES (1-9) to avoid collisions
    context_parts = []

    # RAG retrieval
    if rag_cfg.get("on") and messages:
        query = messages[-1]["content"] if messages else ""
        try:
            chunks = RAG.retrieve_chunks("default", query, n=8)
            for chunk in chunks:
                event = {
                    "type": "cite",
                    "value": {
                        "id": cite_id,
                        "kind": "d",
                        "file": chunk["file"],
                        "fileId": chunk["fileId"],
                        "page": chunk.get("page", 1),
                        "score": chunk["score"],
                        "preview": chunk["preview"],
                    },
                }
                yield f"data: {json.dumps(event)}\n\n"
                context_parts.append(chunk["preview"])
                cite_id += 1
        except Exception:
            pass

    # Build system prompt
    sys_content = (
        "You are QualScope, an AI assistant for qualitative researchers. "
        "Help analyse interview transcripts and research documents with precision. "
        "When you reference specific passages use [^N] notation matching the citation IDs provided."
    )
    if context_parts:
        sys_content += "\n\nRelevant context retrieved from the corpus:\n\n" + "\n\n---\n\n".join(context_parts)

    full_messages = [{"role": "system", "content": sys_content}] + messages

    req_data = json.dumps({
        "model": VLLM_MODEL,
        "messages": full_messages,
        "stream": True,
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode("utf-8")

    try:
        request = urllib.request.Request(
            VLLM_URL,
            data=req_data,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        )
        buf = ""
        with urllib.request.urlopen(request, timeout=120) as resp:
            while True:
                chunk = resp.read(512)
                if not chunk:
                    break
                buf += chunk.decode("utf-8", errors="replace")
                while "\n\n" in buf:
                    line, buf = buf.split("\n\n", 1)
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    try:
                        data = json.loads(raw)
                        token = data["choices"][0]["delta"].get("content", "")
                        if token:
                            token = re.sub(r"<think>.*?</think>", "", token, flags=re.DOTALL)
                            if token:
                                yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"
                    except Exception:
                        pass
    except Exception as e:
        yield f"data: {json.dumps({'type': 'token', 'value': f'[Error connecting to LLM: {e}]'})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


# ── Code suggestion ───────────────────────────────────────────────────────────

def suggest_codes(transcript_text: str, existing_names: list) -> list:
    existing_str = ", ".join(existing_names[:40]) if existing_names else "none"
    prompt = (
        f"Transcript excerpt:\n{transcript_text}\n\n"
        f"Existing codebook entries: {existing_str}\n\n"
        "Suggest 3-5 new qualitative codes not already in the list. "
        "Return ONLY a JSON array, no other text:\n"
        '[{"name":"Code Name","desc":"Brief definition","color":"1"}]\n'
        "Colors must be strings from 1 to 6. Spread them across colors."
    )

    try:
        resp = requests.post(
            VLLM_URL,
            json={
                "model": VLLM_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a qualitative research assistant. Output only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False},
            },
            timeout=60,
        )
        content = resp.json()["choices"][0]["message"]["content"]
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        m = re.search(r"\[.*\]", content, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception:
        pass
    return []


# ── Legacy helpers (kept for backwards compat) ────────────────────────────────

def resolve_system_prompt(mode: str):
    if mode == "recipes":
        return system_prompts.debug_japanese_recipes_german
    elif mode == "codebook":
        return system_prompts.codebook_creation
    elif mode == "RAG":
        return RAG.retrieve_context("testuser", "", "")
    return ""


async def resolve_prompt(prompt: str):
    resp = requests.post(
        VLLM_URL,
        headers={"Content-Type": "application/json"},
        json={
            "model": VLLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompts.codebook_creation},
                {"role": "user", "content": prompt},
            ],
        },
    )
    content = resp.json()["choices"][0]["message"]["content"]
    return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()


def resolve_prompt_with_context(user_id: str, subject: str, query: str, enable_thinking: bool = False):
    def stream():
        req_data = json.dumps({
            "model": VLLM_MODEL,
            "messages": RAG.retrieve_context(user_id, subject, query),
            "stream": True,
            "chat_template_kwargs": {"enable_thinking": enable_thinking},
        }).encode("utf-8")
        request = urllib.request.Request(
            VLLM_URL, data=req_data, method="POST",
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        )
        with urllib.request.urlopen(request, timeout=120) as resp:
            while True:
                chunk = resp.read(1024)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(stream(), media_type="text/event-stream")


def resolve_prompt_realtime(payload: dict):
    def stream():
        req_data = json.dumps({
            "model": VLLM_MODEL,
            "messages": [
                {"role": "system", "content": f"{resolve_system_prompt(payload.get('mode', ''))}"},
            ] + payload["messages"],
            "stream": True,
            "chat_template_kwargs": {"enable_thinking": payload.get("thinking", False)},
        }).encode("utf-8")
        request = urllib.request.Request(
            VLLM_URL, data=req_data, method="POST",
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        )
        with urllib.request.urlopen(request, timeout=120) as resp:
            while True:
                chunk = resp.read(1024)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(stream(), media_type="text/event-stream")
