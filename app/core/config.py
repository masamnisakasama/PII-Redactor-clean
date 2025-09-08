from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "models"

def _env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    return v if v not in (None, "") else default

# Backends
FACE_BACKEND = (_env("FACE_BACKEND", "haar") or "haar").lower()
TEXT_BACKEND = (_env("TEXT_BACKEND", None) or _env("OCR_BACKEND", "tesseract")).lower()

# Model paths
EAST_MODEL_PATH = Path(_env("EAST_MODEL_PATH", (MODELS / "frozen_east_text_detection.pb").as_posix()))
YUNET_MODEL_PATH = Path(_env("YUNET_MODEL_PATH", (MODELS / "face_detection_yunet_2023mar.onnx").as_posix()))
HAAR_MODEL_PATH = Path(_env("HAAR_MODEL_PATH", (MODELS / "haarcascade_frontalface_default.xml").as_posix()))
YOLO_DET_PATH = Path(_env("YOLO_DET_PATH", (MODELS / "yolov8n.pt").as_posix()))
YOLO_SEG_PATH = Path(_env("YOLO_SEG_PATH", (MODELS / "yolov8n-seg.pt").as_posix()))

# --- DNN (Caffe) paths and threshold ---
DNN_CAFFE_PROTO = Path(os.getenv("DNN_CAFFE_PROTO", (MODELS / "deploy.prototxt").as_posix()))
DNN_CAFFE_MODEL = Path(os.getenv("DNN_CAFFE_MODEL", (MODELS / "res10_300x300_ssd_iter_140000_fp16.caffemodel").as_posix()))
try:
    FACE_DNN_CONF = float(os.getenv("FACE_DNN_CONF", "0.60"))
except Exception:
    FACE_DNN_CONF = 0.60
