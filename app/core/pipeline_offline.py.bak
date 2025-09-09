# app/core/pipeline_offline.py
import io, numpy as np
from PIL import Image
from .offline_detectors import bgr_from_bytes, detect_faces, tokens, match_pii
from .paint import apply

def redact_bytes_offline(image_bytes: bytes, policy_csv: str, style: str = "box"):
    img = bgr_from_bytes(image_bytes)
    policy = {p.strip() for p in (policy_csv or "").split(",") if p.strip()}
    boxes = []
    if "face" in policy:
        try:
            boxes += detect_faces(img)
        except Exception:
            pass
    toks = tokens(img)
    boxes += match_pii(toks, policy)

    out = apply(img.copy(), boxes, style or "box")
    bio = io.BytesIO()
    Image.fromarray(out[:, :, ::-1].copy()).save(bio, format="PNG")
    bio.seek(0)
    return bio, boxes
