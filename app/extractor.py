import os, requests, json, re
from datetime import datetime

KAZLLM_KEY = os.getenv("KAZLLM_API_KEY")
KAZLLM_URL = os.getenv("KAZLLM_BASE_URL", "https://llm.alem.ai/v1/chat/completions")

SYSTEM = """
Ты секретарь протокола Самрук-Казына. Извлеки ВСЕ поручения.
Сегодня 2026-05-13.
Правила дат: "до пятницы"=2026-05-16, "на этой неделе"=2026-05-16, "на следующей неделе"=2026-05-20, "к среде"=2026-05-14, "до конца недели"=2026-05-16, "за 2 недели"=2026-05-27, "за неделю"=2026-05-20, "за месяц"=2026-06-13.

Верни ТОЛЬКО валидный JSON без markdown, без текста до и после:
{"tasks":[{"assignee":"Ерлан","task":"подготовить претензию","deadline":"2026-05-16","source_quote":"Ерлан до конца недели подготовит претензию"}],"summary":"3 предложения резюме"}
Если задач нет: {"tasks":[],"summary":"..."}
"""


def _parse_json_safely(content: str):
    # Убираем markdown
    cleaned = content.replace("```json", "").replace("```", "").strip()
    # Ищем JSON объект
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except:
            pass
    # fallback - попробуем весь текст
    try:
        return json.loads(cleaned)
    except Exception as e:
        print(f"[EXTRACTOR] JSON parse failed: {e}\nCONTENT: {content[:500]}")
        return None


def extract_kazllm(text: str):
    headers = {
        "Authorization": f"Bearer {KAZLLM_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "kazllm",
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": text[:6000]},
        ],
        "temperature": 0.1,
    }
    r = requests.post(KAZLLM_URL, headers=headers, json=data, timeout=60)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]
    parsed = _parse_json_safely(content)
    if parsed:
        return parsed
    # если не распарсилось - вернем как summary чтобы таблица не была пустой
    return {"tasks": [], "summary": content[:500], "_raw": content}


def extract_openai(text: str):
    try:
        from openai import OpenAI

        client = OpenAI()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "Вытащи все поручения. Верни JSON {tasks:[{assignee,task,deadline:YYYY-MM-DD,source_quote}], summary: 3 предложения}",
                },
                {"role": "user", "content": text[:6000]},
            ],
            temperature=0.1,
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"[OPENAI FALLBACK FAILED] {e}")
        return {"tasks": [], "summary": text[:300]}


def extract_with_openai_and_kazllm(text: str):
    # Сначала пробуем KazLLM - у тебя он уже работает на llm.alem.ai
    try:
        if KAZLLM_KEY:
            result = extract_kazllm(text)
            # если задач 0 - пробуем OpenAI как fallback
            if result and len(result.get("tasks", [])) > 0:
                print(f"[EXTRACTOR] KazLLM OK: {len(result['tasks'])} tasks")
                return result
            print("[EXTRACTOR] KazLLM вернул 0 задач, пробую OpenAI fallback")
    except Exception as e:
        print(f"[EXTRACTOR] KazLLM error {e}")

    # Fallback
    return extract_openai(text)


# алиасы для main.py
extract_with_openai = extract_openai
extract_tasks = extract_with_openai_and_kazllm
