
def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:06.3f}"


# GPU only for now. Todo: Indicate in Frontend or work on Hardware aware Device Map
def transcribe_qwen(file):
    from qwen_asr import Qwen3ASRModel
    import torch

    model = Qwen3ASRModel.from_pretrained(
        "Qwen/Qwen3-ASR-1.7B",
        dtype=torch.bfloat16,
        device_map="cuda:0",
        max_inference_batch_size=32, # Batch size limit for inference. -1 means unlimited. Smaller values can help avoid OOM.
        max_new_tokens=16384, #128^2
        forced_aligner="Qwen/Qwen3-ForcedAligner-0.6B",
        forced_aligner_kwargs=dict(
            dtype=torch.bfloat16,
            device_map="cuda:0",
            # attn_implementation="flash_attention_2",
        )
    )

    results = model.transcribe(
        audio=str(file),
        language=None, # none = auto
        return_time_stamps=True,
    )

    result = results[0]
    items = list(result.time_stamps) if result.time_stamps else []

    PAUSE_THRESHOLD = 0.5  # seconds between words to start a new segment

    segments = []
    if items:
        current = [items[0]]
        for item in items[1:]:
            if item.start_time - current[-1].end_time > PAUSE_THRESHOLD:
                segments.append({
                    "start_raw": current[0].start_time,
                    "end_raw": current[-1].end_time,
                    "start_formatted": format_time(current[0].start_time),
                    "end_formatted": format_time(current[-1].end_time),
                    "text": " ".join(w.text for w in current).strip(),
                })
                current = [item]
            else:
                current.append(item)
        segments.append({
            "start_raw": current[0].start_time,
            "end_raw": current[-1].end_time,
            "start_formatted": format_time(current[0].start_time),
            "end_formatted": format_time(current[-1].end_time),
            "text": " ".join(w.text for w in current).strip(),
        })

    return {
        "text": result.text,
        "segments": segments,
    }


def transcribe_faster(file):
    from faster_whisper import WhisperModel
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


#Legacy Whisper Function
def transcribe(file):
    import whisper
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