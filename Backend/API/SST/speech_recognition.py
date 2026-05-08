import whisper
import sys

"""

audioFile = sys.path[0] + "/test.mp3"
model = whisper.load_model("turbo")
result = model.transcribe(audioFile)

for segment in result["segments"]:
    print(
        f"{format_time(segment['start'])} --> "
        f"{format_time(segment['end'])} | "
        f"{segment['text'].strip()}"
    )
"""

def initialize_qwen_asr():
    model = ""
    return model

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:06.3f}"

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