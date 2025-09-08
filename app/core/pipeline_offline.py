# app/core/pipeline_offline.py
import io
from PIL import Image
from .offline_detectors import bgr_from_bytes, detect_faces, tokens, match_pii
from .paint import apply

# テキスト系ポリシー（モジュールレベルで定義：インデントの罠を避ける）
TEXT_POLICIES = {
    "email","phone","address","id","name","amount","date",
    "plate","nationalid","zipcode","creditcard","ssn"
}

def redact_bytes_offline(image_bytes: bytes, policy_csv: str, style: str = "box"):
    img = bgr_from_bytes(image_bytes)
    policy = {p.strip() for p in (policy_csv or "").split(",") if p.strip()}

    boxes = []
    if "face" in policy:
        try:
            boxes += detect_faces(img)
        except Exception:
            # 顔検出失敗はスルーして他へ
            pass

    # テキスト系ポリシーがあるときだけ OCR 実行
    if policy & TEXT_POLICIES:
        try:
            toks = tokens(img)
            boxes += match_pii(toks, policy)
        except Exception:
            # OCR 側の例外は握りつぶして画像処理を継続
            pass

    out = apply(img.copy(), boxes, (style or "box"))
    bio = io.BytesIO()
    Image.fromarray(out[:, :, ::-1].copy()).save(bio, format="PNG")  # BGR→RGB
    bio.seek(0)
    return bio, boxes
