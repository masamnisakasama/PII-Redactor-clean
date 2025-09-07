from __future__ import annotations
from typing import Optional, Dict, Iterable

FACE_STYLES = {
    # 匿名性重視の別人化（既定）
    "synthetic": (
        "Replace EVERY visible human face with a photorealistic, "
        "non-identifiable synthetic face."
    ),
    # 遊び心スタイル
    "anime":   "Transform every face into a clean, high-quality anime-style face.",
    "cartoon": "Transform every face into a flat cartoon-style face.",
    "emoji":   "Replace every face with a large emoji-like face matching the expression.",
    "pixel":   "Replace every face with an 8x8 pixel-art styled face.",
    "old":     "Age every face to look like an elderly person (realistic).",
    "3d":      "Transform every face into a neutral 3D-rendered stylized face.",
    # フォールバック（強匿名）
    "blur":    "Heavily blur or pixelate every human face.",
}

def _want_any(policy_csv: str, keys: Iterable[str]) -> bool:
    wants = {p.strip().lower() for p in (policy_csv or "").split(",") if p.strip()}
    return any(k in wants for k in keys)

def build_image_prompt(
    policy_csv: str,
    style: str,
    *,
    face_style: Optional[str] = None,
    face_spec: Optional[Dict] = None,
) -> str:
    """
    policy_csv: "face,email,phone,id" 等
    style:      "box" | "swap"（swap時は顔差し替え指示に切替）
    face_style: "synthetic"|"anime"|"cartoon"|"emoji"|"pixel"|"old"|"3d"|"blur"
    face_spec:  {"age":"adult","gender":"neutral","hair":"short",...} のようなヒント
    """
    wants_face = _want_any(policy_csv, ("face",))
    wants_text = _want_any(policy_csv, ("email","phone","id","address","text"))

    parts: list[str] = []

    # 顔の処理
    if style.lower() == "swap" and wants_face:
        key = (face_style or "synthetic").lower()
        directive = FACE_STYLES.get(key, FACE_STYLES["synthetic"])
        parts.append(directive)
        if face_spec:
            hints = []
            if face_spec.get("age"):    hints.append(f"approximate age group: {face_spec['age']}")
            if face_spec.get("gender"): hints.append(f"gender presentation: {face_spec['gender']}")
            if face_spec.get("hair"):   hints.append(f"hair style: {face_spec['hair']}")
            if hints:
                parts.append("Keep attributes: " + ", ".join(hints) + ". Avoid resembling any real person.")
        parts.append("Preserve pose, lighting and background.")
    else:
        if wants_face:
            parts.append("Blur or pixelate ALL human faces.")

    # テキストPII
    if wants_text:
        parts.append("Black-box any visible PII text such as phone numbers, emails, IDs and addresses.")

    # 出力方針
    parts.append("Return the edited image only. No text or watermark.")
    return " ".join(parts)
