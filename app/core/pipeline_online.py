# app/core/pipeline_online.py
import io
from PIL import Image
from .online_gemini import redact_with_gemini

def redact_bytes_online(image_bytes: bytes, policy_csv: str, style: str = "box"):
    # オンラインはモデルに一括委任（座標は返さない方針）
    from .online_gemini import redact_with_gemini
    edited_png = redact_with_gemini(image_bytes)
    bio = io.BytesIO(edited_png)
    bio.seek(0)
    return bio, []  # boxesは空で返す設計
