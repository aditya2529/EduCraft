import re
import json
import time
from groq import Groq, RateLimitError, APIStatusError

MODEL      = "llama-3.1-8b-instant"  # 20,000 TPM free tier (vs 6,000 for 70b)
MAX_RETRIES = 3
RETRY_WAIT  = 62   # seconds — Groq free tier resets every 60 s


def call_groq(system: str, user: str, temperature: float, api_key: str,
              on_retry=None, max_tokens: int = 4096) -> str:
    """
    Call the Groq API with automatic retry on rate-limit and transient server errors.

    on_retry: optional callable(attempt, remaining_seconds) — called every
              second of the back-off wait so the UI can show a live countdown.
    max_tokens: cap on output tokens; callers should pass the minimum needed to
                avoid hitting Groq's per-request token ceiling on the free tier.
    """
    client = Groq(api_key=api_key.strip(), timeout=90.0)

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
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()

        except RateLimitError:
            if attempt == MAX_RETRIES:
                raise
            for remaining in range(RETRY_WAIT, 0, -1):
                if on_retry:
                    on_retry(attempt, remaining)
                time.sleep(1)

        except APIStatusError as e:
            if e.status_code in (500, 502, 503, 504) and attempt < MAX_RETRIES:
                for remaining in range(RETRY_WAIT, 0, -1):
                    if on_retry:
                        on_retry(attempt, remaining)
                    time.sleep(1)
            else:
                raise


def parse_json_response(raw: str) -> dict:
    """Parse the model output, tolerating markdown fences and surrounding text."""
    # Strip markdown fences
    cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
    # Try direct parse first
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Model added text before/after the JSON — extract outermost { … }
        start = cleaned.find("{")
        end   = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            data = json.loads(cleaned[start : end + 1])
        else:
            raise

    # Guard: if the model wrapped its error in JSON, expose it
    if isinstance(data, dict) and "error" in data and len(data) == 1:
        raise ValueError(f"Model returned an error: {data['error']}")

    return data
