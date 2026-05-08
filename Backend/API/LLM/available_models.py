import re, os

def list_models():
    model_list = os.listdir(r"../.cache/huggingface/hub")
    model_list_cleaned = []

    for m in model_list:
        m = re.sub("models--", "", m)
        m = re.sub("--", "/", m)
        model_list_cleaned.append(m)

    return model_list_cleaned