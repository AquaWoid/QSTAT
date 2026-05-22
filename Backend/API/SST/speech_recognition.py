import whisper
import sys
from faster_whisper import WhisperModel


def initialize_qwen_asr():
    model = ""
    return model

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:06.3f}"

def transcribe_faster(file):
    print("starting transcription")
    model_size = "turbo"
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        device = "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    print(f"Model {model_size} Loaded with compute type: {compute_type}")
    segments_raw, info = model.transcribe(file, beam_size=5)

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))


    segments = [
        {
            "start_raw": segment.start,
            "end_raw": segment.end,
            "start_formatted": format_time(segment.start),
            "end_formatted": format_time(segment.end),
            "text": segment.text.strip()
        }
        for segment in segments_raw
    ]    

    return {
        "text": "",
        "segments": segments
    }

    print(segments_formatted)
  #  for segment in segments:
   #     print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))



def transcribe(file):
    model = whisper.load_model("turbo")
    result = model.transcribe(file)
    segments = [
        {
            "start_raw": segment["start"],
            "end_raw": segment["end"],
            "start_formatted": format_time(segment["start"]),
            "end_formatted": format_time(segment["end"]),
            "text": segment["text"].strip()
        }
        for segment in result["segments"]
    ]

    return {
        "text": result["text"],
        "segments": segments
    }