#Retrieval
import json, re
from pathlib import Path
import requests
import chromadb

#chroma_client_http = chromadb.HttpClient(host="chroma", port=8000)   #Docker Version - Will use that again once docker compose is re-implemented
#chroma_client_http = chromadb.HttpClient(host="localhost", port=8080)
chroma_client_http = chromadb.PersistentClient(Path("UserData/default/vectors"))

def retrieve_chunks(user_id: str, query: str, n: int = 8) -> list:
    """
    Returns list of dicts: {file, fileId, page, score, preview, chunkType, turnId, ts}
    Used by the QualScope chat endpoint for RAG context + cite events.
    """
    try:
        collection = chroma_client_http.get_or_create_collection(name=user_id)
        results = collection.query(query_texts=[query], n_results=n)
        chunks = []
        for vid, doc, meta, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            score = round(max(0.0, 1.0 - dist), 3)
            source = meta.get("source", "unknown")
            chunk_type = meta.get("type", "document")
            # For transcript chunks, vector ID is "{fid}_{turnId}" e.g. "abc123_t01"
            turn_id = vid.split("_", 1)[1] if chunk_type == "transcript" and "_" in vid else None
            chunks.append({
                "file": source,
                "fileId": source,
                "page": meta.get("chunk_index", 0) + 1,
                "score": score,
                "preview": doc[:300],
                "chunkType": chunk_type,
                "turnId": turn_id,
                "ts": meta.get("ts"),
            })
        return chunks
    except Exception:
        return []


# Legacy Function - Kept for backwards compatability
def retrieve_context(user_id : str, subject : str, query : str):

    collection = chroma_client_http.get_or_create_collection(name=user_id)

    results = collection.query(
        query_texts=[query],
        n_results=4
    )

    #context_blocks = [] #WIP
    #citation_map = {}

    system_prompt = f"""
    You are a helpful assistant. You answer questions about the following research question: {subject}. 
    Only answer based on knowledge I'm providing you. Don't use your internal knowledge and don't make things up.
    If you don't know the answer, just say: I don't know.
    Make sure that you always cite the exact document and section you retrieved the information from.
    --------------------
    The data:
    """+str(results['documents'])+"""
    """+str(results['metadatas'])+"""
    """

    #return system_prompt


    return [
        {
            "role": "system",
            "content": f"{system_prompt}"
        },
        {
            "role": "user",
            "content": f"{query}"
        }
        ]
    

    response = requests.post(
    url="http://localhost:8000/v1/chat/completions",
            headers = {
                'Content-Type': 'application/json'
            },
    data=json.dumps({
        "model": "Qwen/Qwen3-14B-AWQ",
        "messages": [
        {
            "role": "system",
            "content": f"{system_prompt}"
        },
        {
            "role": "user",
            "content": f"{query}"
        }
        ]
    })
    )

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
    #print(content)
    return content


def remove_document(user_id: str, document_id : str):
    collection = chroma_client_http.get_or_create_collection(name=user_id)  
    

def debug_retrieve():
    collection = chroma_client_http.get_or_create_collection(name="default")
    ids = collection.get(include=[])["ids"]

    unique_roots = sorted({id_.split("_")[0] for id_ in ids})

    print(unique_roots)
#debug_retrieve()
# print(retrieve_context("testuser", "software", "what is Atrain?"))