"""
JSON-file-based persistence for QualScope.

Layout under Backend/UserData/default/:
  files.json         – file metadata list
  codebook.json      – codebook state
  uploads/           – raw uploaded blobs ({fileId}.{ext})
  transcripts/       – transcript turns ({fileId}.json)
"""
import json, uuid
from pathlib import Path
from typing import Optional

from RAG.vectorstore import remove_stale_document_vectors

BASE_DIR = Path(__file__).parent.parent / "UserData" / "default"
UPLOADS_DIR = BASE_DIR / "uploads"
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"
FILES_JSON = BASE_DIR / "files.json"
CODEBOOK_JSON = BASE_DIR / "codebook.json"

# In-memory async-job tracker: {jobId: {status, progress, fileId, error?}}
_jobs: dict = {}


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _rj(path: Path, default):
    try:
        return json.loads(path.read_text("utf-8")) if path.exists() else default
    except Exception:
        return default


def _wj(path: Path, data):
    _ensure(path.parent)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")


# ── Files ────────────────────────────────────────────────────────────────────

def list_files() -> list:
    return _rj(FILES_JSON, [])


def get_file(file_id: str) -> Optional[dict]:
    return next((f for f in list_files() if f["id"] == file_id), None)


def add_file(meta: dict) -> dict:
    files = list_files()
    files.append(meta)
    _wj(FILES_JSON, files)
    return meta


def update_file(file_id: str, patch: dict) -> Optional[dict]:
    files = list_files()
    for i, f in enumerate(files):
        if f["id"] == file_id:
            files[i] = {**f, **patch}
            _wj(FILES_JSON, files)
            return files[i]
    return None


def delete_file_meta(file_id: str) -> bool:
    files = list_files()
    new_files = [f for f in files if f["id"] != file_id]
    if len(new_files) == len(files):
        return False
    _wj(FILES_JSON, new_files)
    for p in _ensure(UPLOADS_DIR).iterdir():
        if p.stem == file_id:
            p.unlink(missing_ok=True)
    t = TRANSCRIPTS_DIR / f"{file_id}.json"
    t.unlink(missing_ok=True)
    remove_stale_document_vectors(user_id="default") #Vector DB removal with Placeholder Userid need to swap later
    return True


def save_upload(file_id: str, suffix: str, data: bytes) -> Path:
    _ensure(UPLOADS_DIR)
    path = UPLOADS_DIR / f"{file_id}{suffix}"
    path.write_bytes(data)
    return path


def get_upload_path(file_id: str) -> Optional[Path]:
    for p in _ensure(UPLOADS_DIR).iterdir():
        if p.stem == file_id:
            return p
    return None


# ── Transcripts ──────────────────────────────────────────────────────────────

def save_transcript(file_id: str, turns: list):
    _ensure(TRANSCRIPTS_DIR)
    _wj(TRANSCRIPTS_DIR / f"{file_id}.json", turns)


def load_transcript(file_id: str) -> Optional[list]:
    return _rj(TRANSCRIPTS_DIR / f"{file_id}.json", None)


# ── Codebook ─────────────────────────────────────────────────────────────────

DEFAULT_CODEBOOK: list = []


def load_codebook() -> list:
    return _rj(CODEBOOK_JSON, DEFAULT_CODEBOOK)


def save_codebook(codebook: list):
    _wj(CODEBOOK_JSON, codebook)


def patch_code(code_id: str, patch: dict) -> Optional[dict]:
    book = load_codebook()
    safe = {k: v for k, v in patch.items() if k not in ("id", "children")}
    for g in book:
        if g["id"] == code_id:
            g.update(safe)
            save_codebook(book)
            return g
        for c in g.get("children", []):
            if c["id"] == code_id:
                c.update({k: v for k, v in safe.items() if k != "children"})
                save_codebook(book)
                return c
    return None


def delete_code(code_id: str) -> bool:
    book = load_codebook()
    new_book = [g for g in book if g["id"] != code_id]
    if len(new_book) < len(book):
        save_codebook(new_book)
        return True
    for g in book:
        old = len(g.get("children", []))
        g["children"] = [c for c in g.get("children", []) if c["id"] != code_id]
        if len(g["children"]) < old:
            save_codebook(book)
            return True
    return False


# ── Jobs ─────────────────────────────────────────────────────────────────────

def create_job(file_id: str) -> str:
    jid = str(uuid.uuid4())
    _jobs[jid] = {"status": "running", "progress": 0, "fileId": file_id}
    return jid


def get_job(job_id: str) -> Optional[dict]:
    return _jobs.get(job_id)


def update_job(job_id: str, patch: dict):
    if job_id in _jobs:
        _jobs[job_id].update(patch)
