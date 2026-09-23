import os
from datetime import datetime

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><title>Протокол</title>
<style>
 body{{font-family:Inter,-apple-system,Segoe UI,Roboto,sans-serif;background:#f6f7f9;margin:0;padding:40px;color:#1a1f36}}
 .paper{{max-width:900px;margin:0 auto;background:white;border-radius:16px;box-shadow:0 10px 30px rgba(0,0,0,.08);padding:48px}}
 .badge{{display:inline-block;background:#eef2ff;color:#4f46e5;padding:6px 12px;border-radius:999px;font-size:12px;font-weight:600}}
 h1{{font-size:32px;margin:16px 0 8px}} .meta{{color:#64748b;font-size:14px;margin-bottom:28px}}
 .summary{{background:#f8fafc;border-left:4px solid #4f46e5;padding:18px 20px;border-radius:0 12px 12px 0;line-height:1.6}}
 h2{{margin-top:36px;font-size:20px;border-bottom:2px solid #f1f5f9;padding-bottom:8px}}
 table{{width:100%;border-collapse:collapse;margin-top:16px;font-size:14px}}
 th{{background:#1e293b;color:white;text-align:left;padding:12px 14px}}
 td{{padding:12px 14px;border-bottom:1px solid #e2e8f0;vertical-align:top;line-height:1.5}}
 tr:nth-child(even) td{{background:#f8fafc}}
 .deadline{{background:#fef3c7;color:#92400e;padding:4px 8px;border-radius:6px;font-weight:600;font-size:12px;white-space:nowrap}}
 .assignee{{font-weight:600}} .quote{{color:#64748b;font-style:italic;font-size:12px}}
 .transcript{{background:#fbfbfb;border:1px solid #e2e8f0;border-radius:12px;padding:20px;white-space:pre-wrap;line-height:1.7;font-size:13px;max-height:400px;overflow:auto}}
 .footer{{margin-top:40px;text-align:center;color:#94a3b8;font-size:12px}}
</style></head><body><div class="paper">
 <span class="badge">ALEM PROTOCOL • Трек 08</span>
 <h1>Протокол совещания</h1>
 <div class="meta">Дата: {date} • Язык: {lang} • Сегментов: {segments} • KazLLM + faster-whisper</div>
 <h2>Краткое резюме</h2><div class="summary">{summary}</div>
 <h2>Поручения — {tasks_count}</h2>
 <table><thead><tr><th style="width:18%">Ответственный</th><th style="width:40%">Задача</th><th style="width:15%">Срок</th><th style="width:27%">Источник</th></tr></thead>
 <tbody>{rows}</tbody></table>
 <h2>Полный транскрипт</h2><div class="transcript">{transcript}</div>
 <div class="footer">Сгенерировано Alem Protocol — STT локально • KazLLM (llm.alem.ai)</div>
</div></body></html>
"""


def _build_rows(tasks):
    if not tasks:
        return '<tr><td colspan="4" style="text-align:center;color:#ef4444;padding:24px;">Поручения не извлечены</td></tr>'
    rows = ""
    for t in tasks:
        rows += f"<tr><td class='assignee'>{t.get('assignee','-')}</td><td>{t.get('task','-')}<div class='quote'>«{t.get('source_quote','')[:180]}»</div></td><td><span class='deadline'>{t.get('deadline','-')}</span></td><td class='quote'>{t.get('source_quote','')[:220]}</td></tr>"
    return rows


def export_to_html(transcript: str, tasks: list, summary: str, lang="ru", segments=0):
    os.makedirs("uploads", exist_ok=True)
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    html = HTML_TEMPLATE.format(
        date=date_str,
        lang=lang,
        segments=segments,
        summary=summary or "Резюме не сформировано.",
        tasks_count=len(tasks),
        rows=_build_rows(tasks),
        transcript=transcript[:12000].replace("<", "&lt;").replace(">", "&gt;"),
    )
    path = f"uploads/protocol_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[EXPORT HTML] {path}")
    return path


def _find_font():
    for p in [
        "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]:
        if os.path.exists(p):
            return p
    return None


def export_to_pdf(transcript: str, tasks: list, summary: str):
    os.makedirs("uploads", exist_ok=True)
    from fpdf import FPDF

    font_path = _find_font()
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    use_custom = False
    if font_path and os.path.exists(font_path):
        try:
            pdf.add_font("DejaVu", "", font_path, uni=True)
            use_custom = True
            pdf.set_font("DejaVu", "", 10)
        except:
            use_custom = False
    if not use_custom:
        pdf.set_font("Helvetica", "", 10)

    def safe(t):
        if use_custom:
            return t
        return t.encode("latin-1", "ignore").decode("latin-1")

    pdf.cell(
        0,
        10,
        safe(f"Protocol - {datetime.now().strftime('%d.%m.%Y')} - {len(tasks)} tasks"),
        ln=True,
    )
    pdf.ln(2)
    pdf.multi_cell(0, 6, safe(summary or ""))
    pdf.ln(4)
    for t in tasks[:20]:
        pdf.set_font("DejaVu" if use_custom else "Helvetica", "B", 9)
        pdf.multi_cell(0, 5, safe(f"{t.get('assignee','-')} | {t.get('deadline','-')}"))
        pdf.set_font("DejaVu" if use_custom else "Helvetica", "", 9)
        pdf.multi_cell(0, 5, safe(t.get("task", "-")))
        pdf.ln(2)
    path = f"uploads/protocol_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(path)
    print(f"[EXPORT PDF] {path}")
    return path


def export_to_docx(transcript: str, tasks: list, summary: str):
    return export_to_html(transcript, tasks, summary)
