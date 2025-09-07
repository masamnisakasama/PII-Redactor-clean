# app/core/online_gemini.py
import os, base64

DEFAULT_PROMPT = (
  "Redact personal data in this photo: "
  "1) Blur or pixelate ALL human faces. "
  "2) Black-box any visible PII text (phone numbers, emails, IDs, addresses). "
  "Do not change layout or colors except redactions. Output only the edited image."
)

def redact_with_gemini(image_bytes: bytes, prompt: str | None = None) -> bytes:
    import requests  # ← ここで読み込む
    model   = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview")
    api_key = os.environ["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    b64 = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/png", "data": b64}},
                {"text": prompt or DEFAULT_PROMPT}
            ]
        }]
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    js = r.json()
    parts = js["candidates"][0]["content"]["parts"]
    for p in parts:
        if "inline_data" in p and "data" in p["inline_data"]:
            import base64 as _b64
            return _b64.b64decode(p["inline_data"]["data"])
    raise RuntimeError("Gemini did not return an image")
