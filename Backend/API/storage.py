"""
JSON based persistence.

Layout under Backend/UserData/default/:
  files.json         – file metadata list
  codebook.json      – legacy single-codebook state (migrated on first run)
  codebooks/         – multi-codebook storage
    index.json        – [{id, name, createdAt}, ...]
    {codebookId}.json – codebook state, same shape as legacy codebook.json
  uploads/           – raw uploaded blobs ({fileId}.{ext})
  transcripts/       – transcript turns ({fileId}.json)
"""
import json, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from RAG.vectorstore import remove_stale_document_vectors

BASE_DIR = Path(__file__).parent.parent / "UserData" / "default"
UPLOADS_DIR = BASE_DIR / "uploads"
MARKDOWN_DIR = UPLOADS_DIR / "markdown"
TRANSCRIPTS_DIR = BASE_DIR / "transcripts"
FILES_JSON = BASE_DIR / "files.json"
CODEBOOK_JSON = BASE_DIR / "codebook.json"  # legacy, read once for migration
CODEBOOKS_DIR = BASE_DIR / "codebooks"
CODEBOOKS_INDEX = CODEBOOKS_DIR / "index.json"
CONFIGS_JSON = BASE_DIR / "configs.json"

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
    remove_stale_document_vectors(user_id="default") #Todo: Vector DB removal with Placeholder Userid need to swap later
    return True


def save_upload(file_id: str, suffix: str, data: bytes) -> Path:
    _ensure(UPLOADS_DIR)
    path = UPLOADS_DIR / f"{file_id}{suffix}"
    path.write_bytes(data)
    return path

def save_markdown(file_id: str, suffix: str, data: str) -> Path:
    _ensure(MARKDOWN_DIR)
    path = MARKDOWN_DIR / f"{file_id}{suffix}"
    path.write_text(data)
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


# ── Codebooks ────────────────────────────────────────────────────────────────

DEFAULT_CODEBOOK: list = []


def _codebook_path(codebook_id: str) -> Path:
    return CODEBOOKS_DIR / f"{codebook_id}.json"


def _ensure_codebooks_initialized():
    """One-time migration: wrap the legacy single codebook.json into codebooks/."""
    if CODEBOOKS_INDEX.exists():
        return
    _ensure(CODEBOOKS_DIR)
    legacy = _rj(CODEBOOK_JSON, DEFAULT_CODEBOOK)
    cb_id = str(uuid.uuid4())[:8]
    meta = {"id": cb_id, "name": "Codebook 1", "createdAt": datetime.now(timezone.utc).isoformat()}
    _wj(CODEBOOKS_INDEX, [meta])
    _wj(_codebook_path(cb_id), legacy)
    set_active_codebook_id(cb_id)


def list_codebooks() -> list:
    _ensure_codebooks_initialized()
    return _rj(CODEBOOKS_INDEX, [])


def get_active_codebook_id() -> str:
    _ensure_codebooks_initialized()
    cfg = load_config()
    active = cfg.get("activeCodebookId")
    index = _rj(CODEBOOKS_INDEX, [])
    if active and any(m["id"] == active for m in index):
        return active
    if index:
        set_active_codebook_id(index[0]["id"])
        return index[0]["id"]
    return create_codebook([])["id"]


def set_active_codebook_id(codebook_id: str):
    cfg = load_config()
    cfg["activeCodebookId"] = codebook_id
    save_config(cfg)


def load_codebook(codebook_id: Optional[str] = None) -> list:
    codebook_id = codebook_id or get_active_codebook_id()
    return _rj(_codebook_path(codebook_id), DEFAULT_CODEBOOK)


def save_codebook(codebook: list, codebook_id: Optional[str] = None):
    codebook_id = codebook_id or get_active_codebook_id()
    _wj(_codebook_path(codebook_id), codebook)



def add_filename_to_ids(items: list[dict], filename: str) -> list[dict]:
    file_prefix = Path(filename).stem

    def update_item(item: dict) -> None:
        if "id" in item:
            item["id"] = f"{file_prefix}_{item['id']}"
        for child in item.get("children", []):
            update_item(child)

    for item in items:
        update_item(item)

    return items


def create_codebook(codes: list, name: Optional[str] = None) -> dict:
    """Create a new codebook, make it active, and return its {id, name, createdAt}."""
    _ensure_codebooks_initialized()
    index = _rj(CODEBOOKS_INDEX, [])
    cb_id = str(uuid.uuid4())[:8]
    meta = {"id": cb_id, "name": name or f"Codebook {len(index) + 1}", "createdAt": datetime.now(timezone.utc).isoformat()}
    index.append(meta)
    _wj(CODEBOOKS_INDEX, index)
    codes = add_filename_to_ids(codes, cb_id)
    _wj(_codebook_path(cb_id), codes)
    set_active_codebook_id(cb_id)
    return meta


def rename_codebook(codebook_id: str, name: str) -> Optional[dict]:
    index = _rj(CODEBOOKS_INDEX, [])
    for m in index:
        if m["id"] == codebook_id:
            m["name"] = name
            _wj(CODEBOOKS_INDEX, index)
            return m
    return None




def delete_codebook(codebook_id: str) -> bool:
    index = _rj(CODEBOOKS_INDEX, [])
    new_index = [m for m in index if m["id"] != codebook_id]
    if len(new_index) == len(index):
        return False
    _wj(CODEBOOKS_INDEX, new_index)
    _codebook_path(codebook_id).unlink(missing_ok=True)
    cfg = load_config()
    if cfg.get("activeCodebookId") == codebook_id:
        if new_index:
            cfg["activeCodebookId"] = new_index[0]["id"]
            save_config(cfg)
        else:
            create_codebook([])  # keeps at least one codebook around, sets it active
    return True


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


# ── Config ───────────────────────────────────────────────────────────────────

DEFAULT_CONFIG: dict = {}


def load_config() -> dict:
    cfg = _rj(CONFIGS_JSON, None)
    if cfg is None:
        _wj(CONFIGS_JSON, DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    return cfg


def save_config(config: dict):
    _wj(CONFIGS_JSON, config)


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
