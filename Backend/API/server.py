from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os, uuid

import API.SST.speech_recognition as speech_recognition
import API.LLM.inference as LLM
import API.storage as storage

app = FastAPI(title="QualScope API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_EXTS = {
    ".mp3": "mp3", ".mp4": "mp3",
    ".pdf": "pdf",
    ".docx": "doc", ".doc": "doc",
    ".xlsx": "xls", ".xls": "xls",
}

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/")
def health():
    return {"status": "ok"}


# ── Files ─────────────────────────────────────────────────────────────────────

@app.get("/files")
def list_files():
    return storage.list_files()


@app.post("/files")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    name = file.filename or "unnamed"
    suffix = os.path.splitext(name)[-1].lower()
    file_type = VALID_EXTS.get(suffix)
    if not file_type:
        raise HTTPException(400, f"Unsupported file type: {suffix}")

    fid = str(uuid.uuid4())[:8]
    data = await file.read()
    path = storage.save_upload(fid, suffix, data)

    meta = {
        "id": fid, "name": name, "type": file_type,
        "status": "proc", "meta": "processing…", "progress": 0,
    }
    storage.add_file(meta)
    background_tasks.add_task(_process_file, fid, file_type, str(path))
    return meta


@app.delete("/files/{file_id}")
def delete_file(file_id: str):
    if not storage.delete_file_meta(file_id):
        raise HTTPException(404, "File not found")
    return {"ok": True}


@app.get("/files/{file_id}/transcript")
def get_file_transcript(file_id: str):
    turns = storage.load_transcript(file_id)
    if turns is None:
        raise HTTPException(404, "Transcript not available")
    return turns


@app.patch("/files/{file_id}/transcript")
def update_file_transcript(file_id: str, body: dict):
    turns = body.get("turns")
    if turns is None:
        raise HTTPException(400, "body must contain 'turns'")
    storage.save_transcript(file_id, turns)
    return {"ok": True}


@app.get("/files/{file_id}/audio")
def get_audio(file_id: str):
    path = storage.get_upload_path(file_id)
    if not path:
        raise HTTPException(404, "Audio file not found")
    suffix = path.suffix.lower()
    media_type = "audio/mpeg" if suffix in (".mp3", ".mp4") else "audio/wav"
    return FileResponse(str(path), media_type=media_type)


# ── Transcribe ────────────────────────────────────────────────────────────────

@app.post("/transcribe")
async def start_transcribe(body: dict, background_tasks: BackgroundTasks):
    fid = body.get("fileId")
    f = storage.get_file(fid) if fid else None
    if not f:
        raise HTTPException(404, "File not found")
    if f["type"] != "mp3":
        raise HTTPException(400, "Only audio files can be transcribed")
    path = storage.get_upload_path(fid)
    if not path:
        raise HTTPException(404, "Upload not on disk")

    jid = storage.create_job(fid)
    storage.update_file(fid, {"status": "proc", "meta": "transcribing… 0%", "progress": 0})
    background_tasks.add_task(_transcribe_job, jid, fid, str(path))
    return {"jobId": jid}


@app.get("/transcribe/status/{job_id}")
def transcribe_status(job_id: str):
    job = storage.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.post("/chat")
def chat(payload: dict):
    return StreamingResponse(
        LLM.stream_chat_qualscope(payload),
        media_type="text/event-stream",
        headers={"x-accel-buffering": "no", "cache-control": "no-cache, no-transform"},
    )


# ── Codebook ──────────────────────────────────────────────────────────────────

@app.get("/codebook")
def get_codebook():
    return storage.load_codebook()


@app.post("/codebook/suggest")
def suggest_codes(body: dict):
    transcript_id = body.get("transcriptId")
    existing = body.get("existing", storage.load_codebook())

    transcript = storage.load_transcript(transcript_id) if transcript_id else []
    excerpt = ""
    if transcript:
        excerpt = "\n".join(
            f"{t.get('speaker', 'Speaker')}: " + " ".join(s["t"] for s in t.get("segments", []))
            for t in transcript[:20]
        )

    existing_names = [
        c["name"]
        for g in existing
        for c in [{"name": g["name"]}] + g.get("children", [])
    ]

    return LLM.suggest_codes(excerpt, existing_names)


@app.patch("/codebook/{code_id}")
def patch_code(code_id: str, patch: dict):
    result = storage.patch_code(code_id, patch)
    if result is None:
        raise HTTPException(404, "Code not found")
    return result


@app.delete("/codebook/{code_id}")
def delete_code(code_id: str):
    if not storage.delete_code(code_id):
        raise HTTPException(404, "Code not found")
    return {"ok": True}


# ── Background workers ────────────────────────────────────────────────────────

def _process_file(fid: str, ftype: str, path: str):
    try:
        if ftype == "mp3":
            _process_audio(fid, path)
        else:
            _process_document(fid, path)
    except Exception as e:
        storage.update_file(fid, {"status": "error", "meta": f"error: {e}", "progress": None})


def _transcribe_job(jid: str, fid: str, path: str):
    try:
        _process_audio(fid, path)
        storage.update_job(jid, {"status": "done", "progress": 100})
    except Exception as e:
        storage.update_job(jid, {"status": "error", "error": str(e)})
        storage.update_file(fid, {"status": "error", "meta": f"failed: {e}", "progress": None})


def _process_audio(fid: str, path: str):
    import RAG.vectorstore as vs

    result = speech_recognition.transcribe_faster(path)
    segs = result["segments"]
    if not segs:
        storage.update_file(fid, {"status": "ok", "meta": "0:00 · transcribed", "progress": None})
        return

    turns = []
    for i, seg in enumerate(segs):
        ts = int(seg["start_raw"])
        h, m, s = ts // 3600, (ts % 3600) // 60, ts % 60
        turns.append({
            "id": f"t{i + 1:02d}",
            "speaker": "Speaker",
            "spk": "b",
            "ts": f"{h:02d}:{m:02d}:{s:02d}",
            "segments": [{"t": seg["text"]}],
        })
        storage.update_file(fid, {
            "meta": f"transcribing… {int((i + 1) / len(segs) * 80)}%",
            "progress": int((i + 1) / len(segs) * 80),
        })

    storage.save_transcript(fid, turns)

    docs = [" ".join(s["t"] for s in t["segments"]) for t in turns]
    metas = [{"source": fid, "type": "transcript", "ts": t["ts"], "chunk_index": i} for i, t in enumerate(turns)]
    ids = [f"{fid}_{t['id']}" for t in turns]
    try:
        vs.store_vectors(docs, metas, ids, "default")
    except Exception:
        pass

    total = int(segs[-1]["end_raw"])
    h, m, s = total // 3600, (total % 3600) // 60, total % 60
    dur = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    storage.update_file(fid, {"status": "ok", "meta": f"{dur} · transcribed", "progress": None})


def _process_document(fid: str, path: str):
    import RAG.chunking as chk
    import RAG.vectorstore as vs
    from pathlib import Path as P

    storage.update_file(fid, {"meta": "indexing…", "progress": 20})
    suffix = P(path).suffix.lower()
    pages = 1

    try:
        if suffix == ".pdf":
            from docling.document_converter import DocumentConverter
            doc = DocumentConverter().convert(path).document
            text = doc.export_to_markdown()
            try:
                pages = len(list(doc.pages))
            except Exception:
                pages = max(1, len(text) // 3000)
        else:
            with open(path, "r", errors="replace") as f:
                text = f.read()
            pages = max(1, len(text) // 3000)

        docs, mets, ids = chk.chunk_markdown_doc(text, fid)
        storage.update_file(fid, {"meta": "embedding…", "progress": 70})
        try:
            vs.store_vectors(docs, mets, ids, "default")
        except Exception:
            pass
        storage.update_file(fid, {"status": "ok", "meta": f"{pages} pp · {len(docs)} chunks", "progress": None})
    except Exception:
        storage.update_file(fid, {"status": "ok", "meta": "indexed", "progress": None})
