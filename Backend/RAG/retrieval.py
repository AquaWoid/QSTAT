import json, re
from pathlib import Path
import requests
import chromadb

#chroma_client_http = chromadb.HttpClient(host="chroma", port=8000)   #Legacy variant will most like be removed soon

def retrieve_chunks(user_id: str, query: str, n: int = 8) -> list:
    try:
        chroma_client = chromadb.PersistentClient(Path("UserData/default/vectors"))
        collection = chroma_client.get_or_create_collection(name=user_id)
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

