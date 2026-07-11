import json
from pathlib import Path
import API.storage as storage
from datetime import datetime

CB_PATH = Path(__file__).parent.parent / "UserData" / "default" / "codebooks"

def merge_codebooks(ids: list):
    merged = []
    dt = datetime.now().isoformat(timespec='minutes')
    for file in ids:
        with open(f"{CB_PATH}/{file}.json", "r", encoding="utf-8") as f:
            codebook = json.load(f)

        merged.extend(codebook)

    storage.create_codebook(merged, f"merged_{dt}")
    
    return merged

#merge_codebooks(["37fd0e73", "058c72f3","ad2dceef"])