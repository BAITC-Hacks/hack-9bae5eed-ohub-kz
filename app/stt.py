import os
from faster_whisper import WhisperModel

_model = None
_diar_pipe = None


def get_model(model_name="small"):
    global _model
    if _model is None:
        print(f"[STT] Загружаю {model_name}...")
        _model = WhisperModel(
            model_name, device="cpu", compute_type="int8", download_root="./models"
        )
    return _model


def get_diarization(audio_path):
    global _diar_pipe
    try:
        from pyannote.audio import Pipeline
        import torch

        if _diar_pipe is None:
            print("[DIAR] Загружаю pyannote...")
            token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
            try:
                _diar_pipe = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1", token=token
                )
            except TypeError:
                _diar_pipe = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1", use_auth_token=token
                )
            _diar_pipe.to(torch.device("cpu"))
        diar = _diar_pipe(audio_path)
        return [
            {"start": turn.start, "end": turn.end, "speaker": speaker}
            for turn, _, speaker in diar.itertracks(yield_label=True)
        ]
    except Exception as e:
        print(f"[DIAR] Отключена, включаю эвристику: {e}")
        return []


def transcribe_file(path: str, model_name="small"):
    model = get_model(model_name)
    print(f"[STT] Транскрибирую {path}...")
    segments, info = model.transcribe(path, language=None, vad_filter=True, beam_size=5)
    result = []
    for seg in segments:
        result.append(
            {
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "speaker": "SPEAKER_00",
            }
        )

    diar = get_diarization(path)
    if diar:
        for r in result:
            spk = next(
                (d["speaker"] for d in diar if d["start"] <= r["start"] <= d["end"]),
                "SPEAKER_00",
            )
            r["speaker"] = spk
    else:
        # Эвристика для демо на Windows: меняем спикера каждые 3 реплики + по паузе >1.5с
        print("[DIAR] Эвристика: 3 условных спикера для демо")
        speakers = ["SPEAKER_00", "SPEAKER_01", "SPEAKER_02"]
        last_end = 0
        idx = 0
        for i, r in enumerate(result):
            if r["start"] - last_end > 1.5 or i % 4 == 0:
                idx = (idx + 1) % len(speakers)
            r["speaker"] = speakers[idx]
            last_end = r["end"]

    print(
        f"[STT] Язык: {info.language}, сегментов: {len(result)}, спикеров: {len(set(x['speaker'] for x in result))}"
    )
    return result, info.language
