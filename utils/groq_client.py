import re
import json
from groq import Groq

MODEL = "llama-3.3-70b-versatile"


def call_groq(system: str, user: str, temperature: float, api_key: str) -> str:
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def parse_json_response(raw: str) -> dict:
    cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(cleaned)
