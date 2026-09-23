
from faster_whisper import WhisperModel
_model = None
def get_model():
    global _model
    if _model is None:
        _model = WhisperModel("large-v3", device="cpu", compute_type="int8", download_root="./models")
    return _model
def transcribe_file(path: str):
    model = get_model()
    segments, info = model.transcribe(path, language=None, vad_filter=True, beam_size=5)
    result = []
    for seg in segments:
        result.append({"start": float(seg.start), "end": float(seg.end), "text": seg.text.strip(), "lang": info.language})
    return result, info.language
