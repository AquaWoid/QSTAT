import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


def store_vectors(documents : list, metadatas : list, ids : list, user: str, embedding_model : str = "all-MiniLM-L6-v2"):
    
    #chroma_client = chromadb.HttpClient(host="chroma", port=8000) Docker Version
    chroma_client = chromadb.HttpClient(host="localhost", port=8080)
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