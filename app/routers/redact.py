from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from app.core.pipeline import redact_bytes
router = APIRouter(tags=["redact"])
@router.post("/redact/replace")
async def redact_replace(file: UploadFile = File(...), policy: str = Form("face"), style: str = Form("box"), mode: str | None = Form(None)):
    bio, boxes = redact_bytes(await file.read(), policy, style)
    return StreamingResponse(bio, media_type="image/png", headers={"X-PII-Boxes": str(len(boxes))})


@router.post("/detect/summary")
async def detect_summary(file: UploadFile = File(...), policy: str = Form("face")):
    _, boxes = redact_bytes(await file.read(), policy, style="box")
    return {"count": len(boxes), "boxes": boxes}
