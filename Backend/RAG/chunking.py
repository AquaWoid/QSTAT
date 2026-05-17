from langchain_text_splitters import MarkdownHeaderTextSplitter

def chunk_markdown_doc(doc, doc_title : str, debug : bool = False):

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("##", "section"),
            ("###", "subsection")
        ]
    )

    chunks = markdown_splitter.split_text(doc)
    documents = []
    metadata = []
    ids = []
    source = doc_title

    for i, chunk in enumerate(chunks):
        documents.append(chunk.page_content)
        ids.append(f"{source}_chunk_{i}")
        metadata.append({
            **chunk.metadata,
            "source": source,
            "chunk_index": i        
            })

    if debug:
        print(
            "Chunking Complete: ",
            f"Documents {documents} \n",
            f"Metadatas: {metadata} \n",
            f"IDS {ids} \n"
        )
        print("CHUNKS:  ", len(chunks))

    return documents, metadata, ids
