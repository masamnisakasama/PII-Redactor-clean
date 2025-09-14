# app/routers/compose.py 
from __future__ import annotations

import io, os, base64
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response

# 既存パイプラインそのまま利用
from app.core.pipeline import redact_bytes
# 自然文→CSV（オフライン辞書）
from app.rag.offline.policy import nl_to_policy as offline_nl2csv

router = APIRouter(prefix="/compose", tags=["compose"])

def _safe_header(v: Optional[str]) -> str:
    """HTTPヘッダ用にASCII化。非ASCIIは b64utf8:xxxx に変換して落ちないようにする"""
    if not v:
        return ""
    try:
        v.encode("latin-1")
        return v
    except UnicodeEncodeError:
        return "b64utf8:" + base64.b64encode(v.encode("utf-8")).decode("ascii")

@router.post("/resolve_then_redact")
async def resolve_then_redact(
    file: UploadFile = File(...),
    policy: Optional[str] = Form(None),       # 既存CSVが来たらそれを最優先
    policy_nl: Optional[str] = Form(None),    # 自然文（例: 顔とメールを隠して）
    style: str = Form("box"),
    mode: Optional[str] = Form(None),         # 既存の offline/online 切替（未指定は既定）
):
    # 1) CSV決定（明示CSV > 自然文）
    resolved = (policy or "").strip()
    if not resolved and policy_nl:
        resolved = offline_nl2csv(policy_nl)

    # 2) 画像を既存パイプラインへ
    try:
        image_bytes = await file.read()
        bio, boxes = redact_bytes(
            image_bytes=image_bytes,
            policy_csv=resolved,
            style=style,
            mode=mode,  # 既存の MODE ロジックに従う
        )
    except Exception as e:
        # ここで握りつぶさずAPIエラーとして返す
        raise HTTPException(status_code=500, detail=f"redact_bytes failed: {e!r}")

    # 3) PNGを返す（ヘッダはASCII化）
    headers = {
        "X-Policy-Input": _safe_header(policy_nl or ""),
        "X-Policy-Resolved": _safe_header(resolved or ""),
        "X-PII-Boxes": str(len(boxes)),
        "X-Mode": _safe_header(mode or os.getenv("MODE", "offline")),
        "X-Style": _safe_header(style),
    }
    return Response(content=bio.getvalue(), media_type="image/png", headers=headers)
