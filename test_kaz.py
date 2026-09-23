import os, requests, json

KAZLLM_KEY = os.getenv("KAZLLM_API_KEY") or "sk-3qfA3hXRvhe3QbGJJgm9gw"
KAZLLM_URL = "https://llm.alem.ai/v1/chat/completions"  # правильный!

transcript = """
Спикер 1: Коллеги, по бюджету нужно закрыть до пятницы.
Спикер 2: Ерлан, бюджетті жұмаға дейін тексеру керек, отчет дайындау.
Спикер 1: Да, и Асхат, тебе поручаю подготовить протокол до ертең.
"""

prompt = """
Сен хаттама хатшысысың. Мәтіннен тапсырмаларды тап.
Тек JSON: {"tasks":[{"assignee":"аты","task":"не істеу","deadline":"YYYY-MM-DD","source_quote":"цитата"}],"summary":"3 сөйлем"}
Бүгін 2026-05-13. ертең=2026-05-14, жұмаға дейін=2026-05-16.
"""

headers = {"Authorization": f"Bearer {KAZLLM_KEY}", "Content-Type": "application/json"}
data = {
    "model": "kazllm",
    "messages": [
        {"role": "system", "content": prompt},
        {"role": "user", "content": transcript},
    ],
    "temperature": 0.1,
}

r = requests.post(KAZLLM_URL, headers=headers, json=data, timeout=30)
print("STATUS:", r.status_code)
print("RAW:", r.text[:2000])  # посмотрим что вернуло

j = r.json()
if "choices" in j:
    print("\n--- KAZLLM OK ---")
    print(j["choices"][0]["message"]["content"])
else:
    print("\n--- ОШИБКА API ---")
    print(j)
