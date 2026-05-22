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
    retrieved_chunks = []

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
                retrieved_chunks.append({"id": cite_id, **chunk})
                cite_id += 1
        except Exception:
            pass

    # Build system prompt — include numbered sources so LLM can cite them inline
    sys_content = (
        "You are QualScope, an AI assistant for qualitative researchers. "
        "Help analyse interview transcripts and research documents with precision. "
        "Format responses in markdown. "
    )
    if retrieved_chunks:
        source_block = "\n\n".join(
            f"[^{c['id']}] **{c['file']}** (p.{c['page']}, relevance {c['score']:.2f}):\n{c['preview']}"
            for c in retrieved_chunks
        )
        sys_content += (
            "\n\nWhen referencing the sources below, use [^N] inline notation "
            "(e.g. [^100]). Available sources:\n\n" + source_block
        )

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
        f"Existing top-level code categories: {existing_str}\n\n"
        "Suggest 3-5 NEW top-level qualitative code categories (themes/dimensions) "
        "not already in the list. These are parent categories, not sub-codes. "
        "Return ONLY a valid JSON array, no other text:\n"
        '[{"name":"Category Name","desc":"Brief analytical definition","color":"1"}]\n'
        "Colors are strings 1-6; pick distinct colors not used by existing categories. "
        "No trailing commas, no explanation."
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
