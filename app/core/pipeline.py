# app/core/pipeline.py

from typing import Tuple, List, Optional, Dict, Any
import io, os
from .pipeline_offline import redact_bytes_offline
from .pipeline_online  import redact_bytes_online

def redact_bytes(
    image_bytes: bytes,
    policy_csv: str,
    style: str,
    mode: Optional[str] = None,
    mime_type: Optional[str] = None,
    *,
    face_style: Optional[str] = None,
    face_spec: Optional[Dict[str, Any]] = None,
) -> Tuple[io.BytesIO, List[tuple]]:
    m = (mode or os.getenv("MODE", "offline")).lower()
    if m == "online":
        try:
            return redact_bytes_online(
                image_bytes, policy_csv, style,
                mime_type=mime_type, face_style=face_style, face_spec=face_spec
            )
        except Exception as e:
            if os.getenv("ONLINE_FALLBACK_OFFLINE", "1") == "1":
                print("[online error -> fallback offline]", repr(e))
                return redact_bytes_offline(image_bytes, policy_csv, style)
            raise
    # default: offline
    return redact_bytes_offline(image_bytes, policy_csv, style)
