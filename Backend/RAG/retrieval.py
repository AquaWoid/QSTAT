#Retrieval
import json, re
import requests
import chromadb

chroma_client_http = chromadb.HttpClient(host="chroma", port=8000)

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


print(retrieve_context("testuser", "software", "what is Atrain?"))