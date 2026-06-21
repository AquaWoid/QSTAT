import re, sys, os, json
from pathlib import Path



#cloud_model_path = os.path.join(sys.path[0], "models.json")
cloud_model_path = Path("API/LLM/models.json")


def get_available_models():
    with open(cloud_model_path, "r", encoding="utf-8") as f:
        models = json.loads(f.read())
        return models



#legacy function

def list_local_models():
    model_list = os.listdir(r"../.cache/huggingface/hub")
    model_list_cleaned = []

    for m in model_list:
        m = re.sub("models--", "", m)
        m = re.sub("--", "/", m)
        model_list_cleaned.append(m)

    return model_list_cleaned


    