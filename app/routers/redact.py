from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from app.core.pipeline import redact_bytes

router = APIRouter(tags=["redact"])

@router.post("/redact/replace")
async def redact_replace(
    file: UploadFile = File(...),
    policy: str = Form("face"),
    style: str = Form("box"),              # "box" | "swap" | "pixelate"(offline向け)
    mode: str | None = Form(None),
    face_style: str | None = Form(None),   # "synthetic","anime","cartoon","emoji","pixel","old","3d","blur"
    face_spec: str | None = Form(None),    # JSON文字列（任意: {"age":"adult","gender":"neutral",...}）
):
    image_bytes = await file.read()

    fspec = None
    if face_spec:
        import json
        try:
            fspec = json.loads(face_spec)
        except Exception:
            fspec = None

    bio, boxes = redact_bytes(
        image_bytes, policy, style, mode,
        mime_type=file.content_type,
        face_style=face_style, face_spec=fspec
    )
    return StreamingResponse(
        bio,
        media_type="image/png",
        headers={
            "X-PII-Boxes": str(len(boxes)),
            "X-Mode": mode or "",
        },
    )
