
import os, json
from datetime import datetime, timedelta

PROMPT = "Ты секретарь. Выдели поручения из транскрипта. Учитывай ru/kk/shala. Верни JSON: tasks:[{assignee, task, deadline YYYY-MM-DD, priority, source_quote}], summary."

def extract_with_openai(transcript_text: str):
    try:
        from openai import OpenAI
        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type":"json_object"},
            messages=[{"role":"system","content":PROMPT},{"role":"user","content": transcript_text[:12000]}],
            temperature=0.2
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"OpenAI failed: {e}")
        return fallback_extract(transcript_text)

def fallback_extract(text: str):
    tasks = []
    for line in text.split("."):
        low = line.lower()
        if any(k in low for k in ["нужно","поручаю","сделать","подготовить","тексеру","дайындау"]):
            tasks.append({"assignee":"Не назначен","task":line.strip()[:150],"deadline":(datetime.now()+timedelta(days=3)).strftime("%Y-%m-%d"),"priority":"medium","source_quote":line.strip()[:100]})
    return {"tasks": tasks[:10], "summary":"Fallback summary: "+text[:300]}
