# app/core/pipeline_online.py
import io
from typing import Tuple, List
import cv2
import numpy as np

from .online_gemini import edit_image_with_gemini,build_prompt

def redact_bytes_online(image_bytes: bytes, policy_csv: str, style: str="box", mime_type: str|None=None):
    prompt = build_prompt(policy_csv, style)
    edited_png = edit_image_with_gemini(image_bytes, prompt=prompt, mime_type=mime_type)
    bio = io.BytesIO(edited_png); bio.seek(0)
    return bio, []