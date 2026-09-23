
from pyannote.audio import Pipeline
import torch, os
_pipe = None
def get_pipeline():
    global _pipe
    if _pipe is None:
        hf_token = os.getenv("HF_TOKEN")
        _pipe = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=hf_token)
        if torch.cuda.is_available():
            _pipe.to(torch.device("cuda"))
    return _pipe
def diarize_file(path: str):
    pipe = get_pipeline()
    diarization = pipe(path)
    turns = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        turns.append({"start": float(turn.start), "end": float(turn.end), "speaker": speaker})
    return turns
def merge_transcript_with_diarization(transcript, diarization):
    merged = []
    for seg in transcript:
        mid = (seg["start"] + seg["end"]) / 2
        speaker = "SPEAKER_00"
        for turn in diarization:
            if turn["start"] <= mid <= turn["end"]:
                speaker = turn["speaker"]
                break
        merged.append({**seg, "speaker": speaker})
    return merged
