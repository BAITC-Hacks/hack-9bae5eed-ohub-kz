
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil, pathlib
from .stt import transcribe_file
from .diarization import diarize_file, merge_transcript_with_diarization
from .extractor import extract_with_openai
from .export import export_docx, export_pdf

app = FastAPI(title="Alem Protocol AI")
UPLOAD_DIR = pathlib.Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
def root():
    return {"status":"ok"}

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    path = UPLOAD_DIR / file.filename
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    transcript, lang = transcribe_file(str(path))
    try:
        diar = diarize_file(str(path))
        merged = merge_transcript_with_diarization(transcript, diar)
    except Exception as e:
        print(f"diarization failed {e}")
        merged = [{"speaker":"SPEAKER_00", **s} for s in transcript]
    full_text = "\n".join([f"{m['speaker']}: {m['text']}" for m in merged])
    extracted = extract_with_openai(full_text)
    docx_path = UPLOAD_DIR / "protocol.docx"
    pdf_path = UPLOAD_DIR / "protocol.pdf"
    export_docx(merged, extracted["tasks"], extracted["summary"], str(docx_path))
    export_pdf(merged, extracted["tasks"], extracted["summary"], str(pdf_path))
    return {"language_detected": lang, "transcript": merged, "tasks": extracted["tasks"], "summary": extracted["summary"]}

@app.get("/download/docx")
def dl_docx():
    return FileResponse(UPLOAD_DIR / "protocol.docx", filename="protocol.docx")

@app.get("/download/pdf")
def dl_pdf():
    return FileResponse(UPLOAD_DIR / "protocol.pdf", filename="protocol.pdf")
