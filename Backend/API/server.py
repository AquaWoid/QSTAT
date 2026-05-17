from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware


import tempfile, shutil, os

import API.SST.speech_recognition as speech_recognition
import API.LLM.inference as LLM
import RAG.controller as RAG_Controller

app = FastAPI()

origins = [
    "http://app.localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]    
)

@app.post("/chat")
def chat(payload: dict):
    return LLM.resolve_prompt_realtime(payload)


@app.post("/chatContext")
def chat(payload: dict):
    return LLM.resolve_prompt_with_context("testuser", "software", "what is Atrain?")


@app.post("/store_vector")
def store():
    return RAG_Controller.test_store()
    


@app.get("/")
def read_root():
    return {"API": "Functional"}


@app.get("/askForRecipe")
async def receive_prompt(prompt: str):
    try:
        result = await LLM.resolve_prompt(prompt)
        return {"result" : result }
    except Exception as e:
        return {"Error: " : f"Couldn't Resolve Prompt. Error Code: {e}"}


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...)):

    suffix = os.path.splitext(file.filename or "")[1] or ".mp3"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    try: 
        sst_result = speech_recognition.transcribe(temp_path)
        return {"transcription": sst_result}      
    finally:
        os.remove(temp_path)
"""
    contents = await file.read()
    sst_result = speech_recognition.transcribe(contents)
    return {"transcription": sst_result}
"""
