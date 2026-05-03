import random
import urllib.parse
import requests


def _fetch_pollinations(query: str) -> bytes | None:
    """AI-generated image from Pollinations.ai — no key required."""
    prompt = urllib.parse.quote(f"{query} educational professional cinematic wide")
    url = (
        f"https://image.pollinations.ai/prompt/{prompt}"
        f"?width=1920&height=1080&nologo=true&seed={random.randint(1, 99999)}"
    )
    try:
        resp = requests.get(url, timeout=8)
        return resp.content if resp.status_code == 200 else None
    except Exception:
        return None


def _fetch_unsplash(query: str, api_key: str) -> bytes | None:
    """Real photograph from Unsplash — requires a free API key."""
    try:
        meta = requests.get(
            "https://api.unsplash.com/photos/random",
            params={"query": query, "orientation": "landscape", "client_id": api_key},
            timeout=8,
        )
        if meta.status_code != 200:
            return None
        url = meta.json()["urls"]["regular"]
        img = requests.get(url, timeout=12)
        return img.content if img.status_code == 200 else None
    except Exception:
        return None


def fetch_cover_image(query: str, unsplash_key: str = "") -> bytes | None:
    """Return image bytes for the cover slide.

    Only fetches if an Unsplash key is supplied — avoids slow external
    calls when no key is set. Returns None (solid colour cover) otherwise.
    """
    if unsplash_key and unsplash_key.strip():
        return _fetch_unsplash(query, unsplash_key.strip())
    return None
