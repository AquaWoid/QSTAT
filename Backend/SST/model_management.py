from pathlib import Path

HF_CACHE = Path.home() / ".cache" / "huggingface" / "hub"

MODEL_REPOS = {
    "faster-whisper": ["mobiuslabsgmbh/faster-whisper-large-v3-turbo"],
    "qwen-asr": ["Qwen/Qwen3-ASR-1.7B", "Qwen/Qwen3-ForcedAligner-0.6B"],
}


def _is_repo_cached(repo_id: str) -> bool:
    folder = "models--" + repo_id.replace("/", "--")
    snapshots = HF_CACHE / folder / "snapshots"
    return snapshots.is_dir() and any(snapshots.iterdir())


def get_model_status() -> dict:
    return {
        model_id: {"installed": all(_is_repo_cached(r) for r in repos)}
        for model_id, repos in MODEL_REPOS.items()
    }


def download_model(model_id: str, progress_callback):
    """Download all HF repos for a model. Calls progress_callback(0-100) as files complete."""
    from huggingface_hub import list_repo_files, hf_hub_download, snapshot_download

    repos = MODEL_REPOS[model_id]
    progress_callback(0)

    # Collect every file across all repos so we can track progress
    all_files: list[tuple[str, str]] = []
    for repo_id in repos:
        try:
            all_files.extend((repo_id, f) for f in list_repo_files(repo_id))
        except Exception:
            all_files = []
            break

    if not all_files:
        # Fallback: snapshot_download without granular progress
        for repo_id in repos:
            snapshot_download(repo_id)
        progress_callback(100)
        return

    total = len(all_files)
    done = 0

    for repo_id, filename in all_files:
        try:
            hf_hub_download(repo_id=repo_id, filename=filename)
        except Exception:
            pass
        done += 1
        progress_callback(int(done / total * 95))

    progress_callback(100)
