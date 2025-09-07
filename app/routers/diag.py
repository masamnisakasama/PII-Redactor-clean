# app/routers/diag.py
import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/diag")
def diag():
    key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("NANO_API_KEY")
        or ""
    ).strip()

    return {
        "mode": os.getenv("MODE", "offline"),
        "model": os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview"),
        "api_base": os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta"),
        "key_len": len(key),
        "key_tail": key[-6:] if key else "",
    }
