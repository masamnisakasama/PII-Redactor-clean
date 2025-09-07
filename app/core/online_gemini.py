# app/core/online_gemini.py

# response_mime_type入れると400(INVALID_ARGUMENT)なので入れない
# このモデルは画像MIME指定を受け付けない
# オンラインは座標情報（boxes）を返さない設計なので常にx-pii-boxes: 0であることに注意
# [Gemini] key loaded (tail=...)" と "[redact online failed] -> fallback offline: ...でエラーログ取得可能

import os, base64
from io import BytesIO
from typing import Optional
from PIL import Image

DEFAULT_PROMPT = (
    "Blur or pixelate ALL human faces, and black-box any visible PII text "
    "(phone numbers, emails, IDs, addresses). Return the edited image only. No text."
)

def _infer_mime(image_bytes: bytes, fallback: str = "image/jpeg") -> str:
    try:
        im = Image.open(BytesIO(image_bytes))
        fmt = (im.format or "").upper()
        return {
            "JPEG": "image/jpeg", "JPG": "image/jpeg",
            "PNG": "image/png", "WEBP": "image/webp",
            "GIF": "image/gif", "BMP": "image/bmp",
            "TIFF": "image/tiff",
        }.get(fmt, fallback)
    except Exception:
        return fallback

def _extract_inline_image(js: dict) -> Optional[bytes]:
    parts = js.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for p in parts:
        if not isinstance(p, dict): continue
        d = None
        if isinstance(p.get("inline_data"), dict):
            d = p["inline_data"].get("data")
        elif isinstance(p.get("inlineData"), dict):
            d = p["inlineData"].get("data")
        if d:
            try: return base64.b64decode(d)
            except Exception: pass
    return None

# nanobananaに画像が渡されるが、ないならオフラインにFBする
def _post_gemini(parts, *, model: str, base_url: str, api_key: str) -> bytes:
    import requests, json
    url = f"{base_url}/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = { "contents": [ { "role": "user", "parts": parts } ] }
    # デバッグ（必要ならコメントアウト）
    # print("[Gemini] payload keys:", list(payload.keys()))
    r = requests.post(url, headers=headers, json=payload, timeout=(15, 60))
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        raise RuntimeError(f"Gemini HTTPError {r.status_code}: {r.text}") from e
    js = r.json()
    img = _extract_inline_image(js)
    if not img:
        raise RuntimeError("Gemini did not return an image")
    return img

# imageが渡される
def edit_image_with_gemini(image_bytes: bytes, prompt: Optional[str] = None, mime_type: Optional[str] = None) -> bytes:
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("NANO_API_KEY")
        or ""
    ).strip()
    if not api_key:
        raise RuntimeError("No API key found. Set GEMINI_API_KEY or NANO_API_KEY.")
    print(f"[Gemini] key loaded (tail=****{api_key[-6:]}, len={len(api_key)})")

    model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview")
    base  = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta")
    mt    = mime_type or _infer_mime(image_bytes)
    b64   = base64.b64encode(image_bytes).decode("ascii")
    text  = prompt or DEFAULT_PROMPT

    parts1 = [{"inline_data": {"mime_type": mt, "data": b64}}, {"text": text}]
    parts2 = [{"text": text}, {"inline_data": {"mime_type": mt, "data": b64}}]

    try:
        return _post_gemini(parts1, model=model, base_url=base, api_key=api_key)
    except Exception:
        return _post_gemini(parts2, model=model, base_url=base, api_key=api_key)

def build_prompt(policy_csv: str, style: str) -> str:
    items = [p.strip().lower() for p in (policy_csv or "").split(",") if p.strip()]
    targets = []
    if "face" in items:    targets.append("ALL human faces (every person)")
    if "email" in items:   targets.append("emails")
    if "phone" in items:   targets.append("phone numbers")
    if "id" in items:      targets.append("IDs and ID numbers")
    if "address" in items: targets.append("addresses")
    style_txt = "heavily pixelate" if style == "pixelate" else "black-box"
    targets_txt = ", ".join(targets) or "any visible PII"
    return (f"{style_txt} {targets_txt}. "
            f"Return only the edited image. No captions, no text.")