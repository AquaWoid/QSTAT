from RAG import ingest, chunking, vectorstore, retrieval

def test_store():

    with open("UserData/User/testuser/Documents/atrain/atrain.md", "r", encoding="UTF-8") as file:
        doc = file.read()

    documents, metadatas, ids  = chunking.chunk_markdown_doc(doc, "atrain.md", False)

    storage_result = vectorstore.store_vectors(documents, metadatas, ids, "testuser")

    return storage_result
    
    