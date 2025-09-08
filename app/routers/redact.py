# app/routers/redact.py
import os
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from app.core.pipeline import redact_bytes

router = APIRouter()

@router.post("/redact/replace")
async def redact_replace(
    file: UploadFile = File(...),
    policy: str = Form(...),
    style: str = Form("box"),
    mode: str | None = Form(None),
):
    image_bytes = await file.read()
    mime_type = file.content_type  
    bio, boxes = redact_bytes(image_bytes, policy, style, mode=mode, mime_type=mime_type)
    return StreamingResponse(
        bio,
        media_type="image/png",
        headers={
            "X-PII-Boxes": str(len(boxes)),
            "X-Mode": (mode or os.getenv("MODE", "offline")),
        },
    )
