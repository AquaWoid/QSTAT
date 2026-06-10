import re, sys, os, json

cloud_model_path = os.path.join(sys.path[0], "external_models.json")

def list_local_models():
    model_list = os.listdir(r"../.cache/huggingface/hub")
    model_list_cleaned = []

    for m in model_list:
        m = re.sub("models--", "", m)
        m = re.sub("--", "/", m)
        model_list_cleaned.append(m)

    return model_list_cleaned


def list_cloud_models():

    with open(cloud_model_path, "r", encoding="utf-8") as f:
        models = json.loads(f.read())
        for m in models:
            print(m.get("identifier"))


list_cloud_models()
print(list_local_models())