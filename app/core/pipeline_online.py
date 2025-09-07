import io
from typing import Tuple, List, Optional
from .online_gemini import edit_image_with_gemini
from .online_prompt import build_image_prompt

def redact_bytes_online(
    image_bytes: bytes,
    policy_csv: str,
    style: str = "box",
    *,
    mime_type: Optional[str] = None,
    face_style: Optional[str] = None,
    face_spec: Optional[dict] = None,
) -> Tuple[io.BytesIO, List[tuple]]:
    """
    オンラインは Gemini に「編集済み画像」を生成させる。
    - style=="swap" のときは顔差し替え（face_style/face_spec でバリエーション）
    - 座標情報は取得しないので boxes は空
    """
    prompt = build_image_prompt(policy_csv, style, face_style=face_style, face_spec=face_spec)
    edited_png = edit_image_with_gemini(image_bytes, prompt=prompt, mime_type=mime_type)
    bio = io.BytesIO(edited_png); bio.seek(0)
    return bio, []
