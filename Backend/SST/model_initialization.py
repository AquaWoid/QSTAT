import whisper 
from transformers import VoxtralRealtimeForConditionalGeneration, AutoProcessor

models = ["whisper", "voxtral", "qwen-ars"]

submodels_whisper = {
    "tiny":"tiny", # ~1GB Vram
    "base":"base", # ~1GB Vram
    "small":"small", # ~2GB Vram
    "medium":"medium", # ~5GB Vram
    "large":"large", # ~10GB Vram
    "turbo":"turbo" # ~6GB Vram 
    }

submodels_voxtral = {
    "mini" : "mistralai/Voxtral-Mini-3B-2507",
    "mini_realtime" : "mistralai/Voxtral-Mini-4B-Realtime-2602",
    "small" : "mistralai/Voxtral-Small-24B-2507" #Not sure if i can fit 24b on my GPU for testing atm
}

submodels_qwen = {
    "0.6" : "Qwen/Qwen3-ASR-0.6B",
    "1.7" : "Qwen/Qwen3-ASR-1.7B",
    "0.6_forced" : "Qwen/Qwen3-ForcedAligner-0.6B"
}

def load_model(model_archetype : str, model_name : str):
    if(model_archetype == "whisper"):
        model = whisper.load_model(model_name)
        return model
    elif(model_archetype == "voxtral"):
        repo_id = model_name
        processor = AutoProcessor.from_pretrained(repo_id)
        model = VoxtralRealtimeForConditionalGeneration.from_pretrained(repo_id, device_map="auto")
        return processor, model
    elif(model_archetype == "qwen"):
        return "model"


