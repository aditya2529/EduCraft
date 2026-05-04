import re
import json
import time
from groq import Groq, RateLimitError

MODEL = "llama-3.1-8b-instant"   # 20,000 TPM free tier (vs 6,000 for 70b)
MAX_RETRIES = 3
RETRY_WAIT  = 62   # seconds — Groq's free tier resets every 60s


def call_groq(system: str, user: str, temperature: float, api_key: str,
              on_retry=None) -> str:
    """
    Call the Groq API with automatic retry on rate limit errors.

    on_retry: optional callable(attempt, wait_seconds) — called before each
              retry so the UI can show a countdown.
    """
    client = Groq(api_key=api_key)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
                max_tokens=4096,
            )
            return response.choices[0].message.content.strip()

        except RateLimitError:
            if attempt == MAX_RETRIES:
                raise                          # give up after final attempt
            if on_retry:
                on_retry(attempt, RETRY_WAIT)
            time.sleep(RETRY_WAIT)


def parse_json_response(raw: str) -> dict:
    # Strip markdown fences
    cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Model added text before/after the JSON — extract the outermost { ... }
        start = cleaned.find("{")
        end   = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise
