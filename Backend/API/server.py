from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

print("DEBUG:: STAGE 2 :: FASTAPI IMPORTED ")
from API.DataModels.model_configs import topic_model_settings
import tempfile, shutil, os

print("DEBUG:: STAGE 3 :: FASTAPI IMPORTED ")
import API.SST.speech_recognition as speech_recognition
import API.SST.speech_recognition

import API.LLM.inference_test as LLM

print("DEBUG:: STAGE 4 :: FASTAPI IMPORTED ")
app = FastAPI()

origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]    
)


@app.get("/")
def read_root():
    return {"API": "Functional"}


@app.get("/askForRecipe")
async def receive_prompt(prompt: str):
    return {"result" : LLM.resolve_prompt(prompt)}

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
