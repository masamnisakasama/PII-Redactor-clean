# app/core/pipeline.py
import os
from .pipeline_offline import redact_bytes_offline

def redact_bytes(image_bytes: bytes, policy_csv: str, style: str = "box", mode: str | None = None):
    m = (mode or os.getenv("MODE", "offline")).lower()
    if m == "online":
        try:
            # ここで初めて online 側を import（requests が未導入でも offline 起動可）
            from .pipeline_online import redact_bytes_online
            return redact_bytes_online(image_bytes, policy_csv, style)
        except Exception as e:
            if os.getenv("ONLINE_FALLBACK_OFFLINE", "1") == "1":
                return redact_bytes_offline(image_bytes, policy_csv, style)
            raise
    return redact_bytes_offline(image_bytes, policy_csv, style)
