import json, re
from pathlib import Path
import requests
import chromadb

_VECTORS_DIR = Path(__file__).resolve().parent.parent / "UserData" / "default" / "vectors"

def retrieve_chunks(user_id: str, query: str, n: int = 8) -> list:
    try:
        chroma_client = chromadb.PersistentClient(_VECTORS_DIR)
        collection = chroma_client.get_or_create_collection(name=user_id)
        count = collection.count()
        if count == 0:
            return []
        results = collection.query(query_texts=[query], n_results=min(n, count))
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
    except Exception as e:
        print(f"[retrieval] retrieve_chunks failed: {e}")
        return []

