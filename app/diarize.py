from pyannote.audio import Pipeline
import torch

pipe = None


def get_diarization(audio_path):
    global pipe
    if pipe is None:
        pipe = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", use_auth_token=True
        )
        pipe.to(torch.device("cpu"))
    diar = pipe(audio_path)
    # вернет список {start, end, speaker}
    return [
        {"start": turn.start, "end": turn.end, "speaker": speaker}
        for turn, _, speaker in diar.itertracks(yield_label=True)
    ]
