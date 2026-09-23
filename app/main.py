from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import os, shutil, uuid

from .stt import transcribe_file
from .extractor import extract_with_openai_and_kazllm
from .export import export_to_html, export_to_pdf

app = FastAPI(title="Alem Protocol - 08 Innovations")


@app.get("/")
def health():
    return {"status": "ok", "kazllm": "https://llm.alem.ai/v1/chat/completions"}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    tmp_path = f"uploads/{uuid.uuid4()}_{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    transcript, lang = transcribe_file(tmp_path, model_name="small")
    full_text = (
        "\n".join([s.get("text", "") if isinstance(s, dict) else s for s in transcript])
        if transcript and isinstance(transcript[0], dict)
        else "\n".join([s["text"] for s in transcript])
    )
    # совместимость с обоими форматами transcript
    if isinstance(transcript[0], dict):
        full_text = "\n".join(
            [f"[{s.get('speaker','')}] {s.get('text','')}" for s in transcript]
        )
    else:
        full_text = "\n".join([s["text"] for s in transcript])
    result = extract_with_openai_and_kazllm(full_text)
    return JSONResponse(
        {
            "language_detected": lang,
            "segments": len(transcript),
            "tasks": result.get("tasks", []),
            "summary": result.get("summary", ""),
            "transcript_preview": full_text[:2000],
        }
    )


@app.post("/export")
async def export_protocol(file: UploadFile = File(...), format: str = "html"):
    tmp_path = f"uploads/{uuid.uuid4()}_{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    transcript, lang = transcribe_file(tmp_path, model_name="small")
    if isinstance(transcript[0], dict):
        full_text = "\n".join(
            [f"[{s.get('speaker','')}] {s.get('text','')}" for s in transcript]
        )
    else:
        full_text = "\n".join([s["text"] for s in transcript])

    result = extract_with_openai_and_kazllm(full_text)
    tasks = result.get("tasks", [])
    summary = result.get("summary", "")

    if format == "pdf":
        try:
            pdf_path = export_to_pdf(full_text, tasks, summary)
            return FileResponse(
                pdf_path, filename="protocol.pdf", media_type="application/pdf"
            )
        except Exception as e:
            # если PDF упал из-за шрифтов - отдай HTML чтобы не было 500
            print(f"[EXPORT] PDF failed, fallback HTML: {e}")
            html_path = export_to_html(
                full_text, tasks, summary, lang=lang, segments=len(transcript)
            )
            return FileResponse(
                html_path, filename="protocol.html", media_type="text/html"
            )
    elif format == "both":
        html_path = export_to_html(
            full_text, tasks, summary, lang=lang, segments=len(transcript)
        )
        try:
            pdf_path = export_to_pdf(full_text, tasks, summary)
            print(f"[EXPORT] both: html={html_path} pdf={pdf_path}")
        except Exception as e:
            print(f"[EXPORT] PDF in both failed: {e}")
        return FileResponse(html_path, filename="protocol.html", media_type="text/html")
    else:
        html_path = export_to_html(
            full_text, tasks, summary, lang=lang, segments=len(transcript)
        )
        return FileResponse(html_path, filename="protocol.html", media_type="text/html")
