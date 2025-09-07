# app/core/pipeline.py
import os


from typing import Tuple, List
import io

from .pipeline_offline import redact_bytes_offline
from .pipeline_online  import redact_bytes_online

def redact_bytes(image_bytes: bytes, policy_csv: str, style: str, mode: str | None = None, mime_type: str | None = None) -> Tuple[io.BytesIO, List[tuple]]:
    import os
    m = (mode or os.getenv("MODE", "offline")).lower()
    if m == "online":
        try:
            return redact_bytes_online(image_bytes, policy_csv, style, mime_type=mime_type)
        except Exception as e:
            if os.getenv("ONLINE_FALLBACK_OFFLINE", "1") == "1":
                # ログにだけ吐いて静かにフォールバック
                print("[online error -> fallback offline]", repr(e))
                return redact_bytes_offline(image_bytes, policy_csv, style)
            raise
    # default: offline
    return redact_bytes_offline(image_bytes, policy_csv, style)