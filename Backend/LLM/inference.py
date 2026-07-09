import requests
import re
import urllib.request
import json
from fastapi.responses import StreamingResponse
import API.Configs.system_prompts as system_prompts
import RAG.retrieval as RAG
import os
from dotenv import load_dotenv
from pathlib import Path
import LLM.tokenizer as tokenizer
import API.storage as storage
#current_dir = Path(__file__).resolve().parent
#env_path = current_dir.parent / ".env"

#load_dotenv(env_path)

or_key = os.getenv("OPENROUTER_KEY")
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8001/v1")

LLM_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_MODEL = "deepseek/deepseek-v4-flash"


def _get_active_model() -> tuple:
    """Read the user-selected model from configs.json. Returns (model_id, url, headers)."""

    cfg = storage.load_config()
    active = cfg.get("activeModel", {})
    model_id = active.get("identifier") or LLM_MODEL
    kind = active.get("kind", "cloud")
    url = f"{VLLM_BASE_URL}/chat/completions" if kind == "local" else LLM_URL
    headers = {"Authorization": f"Bearer {or_key}"} if kind != "local" else {}
    return model_id, url, headers

def get_active_codebook():

    config = storage.load_config()
    active_codebook_id = config.get("activeCodebookId")
    active_codebook_path = active_codebook_id + ".json"

    CB_PATH = Path(__file__).parent.parent / "UserData" / "default" / "codebooks"
    codebook_text = ""

    with open(CB_PATH / active_codebook_path, "r", encoding="utf-8") as f:
        codebook_text = f.read()
        return codebook_text



def resolve_response_message(response):
    content = response.json()["choices"][0]["message"]["content"]
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    message = re.search(r"[\{\[].*[\}\]]", content, re.DOTALL)
    return message



# QualScope SSE streaming 

def stream_chat_qualscope(payload: dict):

    messages = payload.get("messages", [])
    print("MESSAGES:: ", messages)

    if "/analyze-codebook" in messages[-1]["content"]:
        print("- - - - - ANALYZE CODEBOOK - Command Found - - - - - - -")

    rag_cfg = payload.get("rag", {"on": False, "scope": "all"})

    _cfg_model, _cfg_url, _cfg_auth = _get_active_model()
    model_identifier = payload.get("model") or _cfg_model
    if "modelKind" in payload:
        kind = payload["modelKind"]
        url = f"{VLLM_BASE_URL}/chat/completions" if kind == "local" else LLM_URL
        auth = {} if kind == "local" else {"Authorization": f"Bearer {or_key}"}
    else:
        url, auth = _cfg_url, _cfg_auth
    req_headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        **auth,
    }

    # System Prompt building
    sys_content = (
        "You are QSTAT, an AI assistant for qualitative researchers. "
        "Always answer in the input language"
        "Help analyse interview transcripts and research documents with precision. "
        "Format responses in markdown. "
    )

    if "/analyze-codebook" in messages[-1]["content"]:
        print("- - - - - ANALYZE CODEBOOK - Command Found")
        sys_content += f"Analyze the following codebook and give meaninfull insights about it. Codebook: {get_active_codebook()}"
    else:

        cite_id = max(100, int(payload.get("nextCiteId", 100)))
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
                            "chunkType": chunk.get("chunkType", "document"),
                            "turnId": chunk.get("turnId"),
                            "ts": chunk.get("ts"),
                        },
                    }
                    yield f"data: {json.dumps(event)}\n\n"
                    retrieved_chunks.append({"id": cite_id, **chunk})
                    cite_id += 1
            except Exception:
                pass


        if retrieved_chunks:
            source_block = "\n\n".join(
                f"[^{chunk['id']}] **{chunk['file']}** (p.{chunk['page']}, relevance {chunk['score']:.2f}):\n{chunk['preview']}"
                for chunk in retrieved_chunks
            )
            sys_content += (
                "\n\nWhen referencing the sources below, use [^N] inline notation "
                "(e.g. [^100]). Available sources:\n\n" + source_block
            )

    full_messages = [{"role": "system", "content": sys_content}] + messages

    print(full_messages)

    req_data = json.dumps({
        "model": model_identifier,
        "messages": full_messages,
        "stream": True,
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode("utf-8")

    try:
        request = urllib.request.Request(
            url,
            data=req_data,
            method="POST",
            headers=req_headers,
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




def deductive_agent(research_question: str):
    
    MD_DIR = Path(__file__).parent.parent / "UserData" / "default" / "uploads" / "markdown"    
    context_window = 16384
    codebook_combined = []

    cfg = storage.load_config()
    active = cfg.get("activeModel", {})
    model_kind = active.get("kind", "cloud")

    for i, file in enumerate(os.listdir(MD_DIR)):

        print("File #", i+1, " : ", file)
        with open(MD_DIR / file, "r") as f:
            document_text = f.read()
            if(tokenizer.get_document_tokens(document_text) < context_window or model_kind == "cloud"):
            #print(document_text)
                status = f"processing  {i+1} of {len(os.listdir(MD_DIR))}"
                #yield {"type" : "status", "message" : status}
                print(status)
                codebook = generate_deductive(research_question, document_text, Path(file).stem)
                codebook_combined.extend(codebook)
                codebooks_validated = json.dumps(codebook_combined, indent=2, ensure_ascii=False)
            else:
                print("- - - - - - DOCUMENT TOO LARGE FOR CONTEXT WINDOW - - - - - -")


    print(
            "------- Codebooks List ---------",
            codebook_combined,
            "------- Codebooks Validated ---------",
            codebooks_validated
    )


    return codebook_combined
  

"""
    model_id, url, auth = _get_active_model()    
    
    print(
        "\n----------------DEDUCTIVE CODEBOOK - AGENTIC FLOW----------------------\n\n",
        "Modelid" , model_id, "url", url, "auth: ", auth, "\n Research Question: ", research_question, "\n\n",
        "----------------DEDUCTIVE CODEBOOK - AGENTIC FLOW----------------------\n"
    )  
"""
            
    



def generate_deductive(research_question: str, document: str, document_id: str):
    model_id, url, auth = _get_active_model()
    prompt = "Research Question: " + research_question + "\n" + "Document: \n" + document
    print(
        "\n----------------DEDUCTIVE CODEBOOK----------------------\n\n",
        "Modelid" , model_id, "url", url, "auth: ", auth, "\n RQ: ", research_question, "\n\n",
        "----------------DEDUCTIVE CODEBOOK----------------------\n"
    )

    try:
        response = requests.post(
            url,
            headers=auth,
            json={
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompts.get_deductive_codebook_prompt(5,15, docname=document_id)},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False},
            },
            timeout=60,
        )
        message = resolve_response_message(response)
        if message:
            print("Codebook Output: ", message.group(0))
            return json.loads(message.group(0))
    except Exception:
        pass
    return []


def evaluate_deductive_codebook():
    return True




def auto_annotate(transcript: str):

    codebook_text = get_active_codebook()


    model_id, url, auth = _get_active_model()
    print(
        "\n---------------- AUTO ANNOTATION ----------------------\n\n",
        "Modelid" , model_id, "url", url, "auth: ", auth, "\n\n",
        "---------------- AUTO ANNOTATION ----------------------\n"
    )

    prompt = f"""
    #### Transcript 
    {transcript}
    #### Codebook
    {codebook_text}
            """
    
    system_prompt = system_prompts.get_auto_annoint_prompt_compact()
    #system_prompt = system_prompts.get_auto_annoint_prompt()

    try:
        response = requests.post(
            url,
            headers=auth,
            json={
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False},
            },
            timeout=1200,
        )
        message = resolve_response_message(response)
        #print("response output:", response)
        #print("message output: ", message)
        if message:
            print("message group output ", message.group(0))
            return json.loads(message.group(0))
    except Exception as e:
        print("ERROR: ", e)
        pass
    return []


def auto_annotation_agent(transcript: str):


    annotations = auto_annotate(transcript)

    transcript_json = json.loads(transcript)

    for item in transcript_json:
        item["codes"] = annotations.get(item["id"], [])


    return transcript_json

def debug_auto_anno():
    
    # "b6127f59.json"

    T_PATH = Path(__file__).parent.parent / "UserData" / "default" / "transcripts" / "autoannotest.json"
    with open(T_PATH, "r", encoding="utf-8") as f:
        transcript = f.read()

    #print(transcript)
    print(auto_annotation_agent(transcript))

#debug_auto_anno()
#auto_annotate("test")



#deductive_agent("How can we leverage machine learning for qualitative research?")
#Legacy Function - Will be removed soon
def generate_deductive_codebook(research_question: str):
    model_id, url, auth = _get_active_model()
    prompt = "Research Question: " + research_question
    print(
        "\n----------------DEDUCTIVE CODEBOOK----------------------\n\n",
        "Modelid" , model_id, "url", url, "auth: ", auth, "\n Prompt: ", prompt, "\n\n",
        "----------------DEDUCTIVE CODEBOOK----------------------\n"
    )

    try:
        response = requests.post(
            url,
            headers=auth,
            json={
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompts.get_deductive_codebook_prompt(5,15)},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False},
            },
            timeout=60,
        )
        message = resolve_response_message(response)
        if message:
            print("Codebook Output: ", message.group(0))
            return json.loads(message.group(0))
    except Exception:
        pass
    return []




def generate_codebook(transcript_text: str):
    model_id, url, auth = _get_active_model()
    prompt = "Input Text: " + transcript_text


    print(
        "\n----------------GENERATE CODEBOOK----------------------\n\n",
        "Modelid" , model_id, "url", url, "auth: ", auth, "\n Prompt: ", prompt, "\n\n",
        "----------------GENERATE CODEBOOK----------------------\n"
    )

    try:
        response = requests.post(
            url,
            headers=auth,
            json={
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompts.get_codebook_prompt(10,15)},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False},
            },
            timeout=60,
        )
        content = response.json()["choices"][0]["message"]["content"]
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        m = re.search(r"\[.*\]", content, re.DOTALL)
        if m:
            print("Codebook Output: ", m.group(0))
            return json.loads(m.group(0))
    except Exception:
        pass
    return []




    print(
        "\n----------------GENERATE CODEBOOK----------------------\n\n",
        "Modelid" , model_id, "url", url, "auth: ", auth, "\n Prompt: ", prompt, "\n\n",
        "----------------GENERATE CODEBOOK----------------------\n"
    )

    try:
        response = requests.post(
            url,
            headers=auth,
            json={
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompts.get_codebook_prompt(5,15)},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False},
            },
            timeout=60,
        )
        content = response.json()["choices"][0]["message"]["content"]
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        m = re.search(r"\[.*\]", content, re.DOTALL)
        if m:
            print("Codebook Output: ", m.group(0))
            return json.loads(m.group(0))
    except Exception:
        pass
    return []

# Code suggestion - Legacy Function, kept for backwards compatibility
def suggest_codes(transcript_text: str, existing_names: list) -> list:
    model_id, url, auth = _get_active_model()
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

    print(
        "\n----------------CODE SUGGEST----------------------\n\n",
        "Modelid" , model_id, "url", url, "auth: ", auth, "\n Prompt: ", prompt, "\n\n",
        "----------------CODE SUGGEST----------------------\n"
    )

    try:
        response = requests.post(
            url,
            headers=auth,
            json={
                "model": model_id,
                "messages": [
                    {"role": "system", "content": "You are a qualitative research assistant. Output only valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "chat_template_kwargs": {"enable_thinking": False},
            },
            timeout=60,
        )
        content = response.json()["choices"][0]["message"]["content"]
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        m = re.search(r"\[.*\]", content, re.DOTALL)
        if m:
            return json.loads(m.group(0))
    except Exception:
        pass
    return []



# Legacy helpers (kept for backwards compat) 

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
        LLM_URL,
        headers={"Content-Type": "application/json"},
        json={
            "model": LLM_MODEL,
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
            "model": LLM_MODEL,
            "messages": RAG.retrieve_context(user_id, subject, query),
            "stream": True,
            "chat_template_kwargs": {"enable_thinking": enable_thinking},
        }).encode("utf-8")
        request = urllib.request.Request(
            LLM_URL, data=req_data, method="POST",
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
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": f"{resolve_system_prompt(payload.get('mode', ''))}"},
            ] + payload["messages"],
            "stream": True,
            "chat_template_kwargs": {"enable_thinking": payload.get("thinking", False)},
        }).encode("utf-8")
        request = urllib.request.Request(
            LLM_URL, data=req_data, method="POST",
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        )
        with urllib.request.urlopen(request, timeout=120) as resp:
            while True:
                chunk = resp.read(1024)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(stream(), media_type="text/event-stream")
