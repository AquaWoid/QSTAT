from functools import lru_cache
from transformers import AutoTokenizer



@lru_cache(maxsize=1)
def get_tokenizer():
    return AutoTokenizer.from_pretrained(
        "Qwen/Qwen3-4B-AWQ",
        use_fast=True
    )

def get_document_tokens(mardkown: str) -> int:
    tokenizer = get_tokenizer()

    return len(tokenizer.encode(mardkown, add_special_tokens=False))

