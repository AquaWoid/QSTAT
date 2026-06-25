import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from pathlib import Path

_VECTORS_DIR = Path(__file__).resolve().parent.parent / "UserData" / "default" / "vectors"

def store_vectors(documents : list, metadatas : list, ids : list, user: str, embedding_model : str = "all-MiniLM-L6-v2"):

    #chroma_client = chromadb.HttpClient(host="chroma", port=8000) Docker Version
    _VECTORS_DIR.mkdir(parents=True, exist_ok=True)
    chroma_client = chromadb.PersistentClient(_VECTORS_DIR)
    #chroma_client = chromadb.HttpClient(host="localhost", port=8080)
    sentence_transformer_ef = SentenceTransformerEmbeddingFunction(
    model_name=embedding_model,
    device="cpu",
    normalize_embeddings=False
    )


    #collection = chroma_client.get_or_create_collection(name=user, embedding_function=sentence_transformer_ef) #Have to test first
    collection = chroma_client.get_or_create_collection(name=user)

    collection.upsert(
    documents=documents,
    metadatas=metadatas,
    ids=ids
    )
    return {"status" : f"sucessfully stored vectors for collection: {user}"}


def locatepath(user_id : str):

    import os

    print("cwd:", os.getcwd())
    print("resolved path:", Path(f"Backend/UserData/{user_id}/uploads").resolve())

def remove_stale_document_vectors(user_id: str): 



    _VECTORS_DIR.mkdir(parents=True, exist_ok=True)
    chroma_client = chromadb.PersistentClient(_VECTORS_DIR)
    #chroma_client = chromadb.HttpClient(host="localhost", port=8080)
    collection = chroma_client.get_or_create_collection(name=user_id)  

    local_roots = {p.stem for p in Path(f"UserData/{user_id}/uploads").iterdir() if p.is_file()}
    print("Local Persistent Roots:", local_roots)


    ids = collection.get(include=[])["ids"]
    unique_roots = sorted({id_.split("_")[0] for id_ in ids})
    print("Unique Roots in DB: ", unique_roots)


    ids_to_delete = [
        id_ for id_ in ids
        if id_.split("_")[0] not in local_roots
    ]

    print(f"Deleting {len(ids_to_delete)} chunks")
    print("Chunks to delete: ", ids_to_delete)    

    try:
        collection.delete(ids=ids_to_delete)
    except:
        print("--- \n No stale chunks to delete \n Vector DB and Local Documents in Sync \n ---")
        

    remaining_ids = collection.get(include=[])["ids"]

    remaining_stale = [
        id_ for id_ in remaining_ids
        if id_.split("_")[0] not in local_roots
    ]

    print("Remaining stale chunks:", remaining_stale)


#remove_stale_document_vectors(user_id="default")
#locatepath("default")
