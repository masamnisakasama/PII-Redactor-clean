from __future__ import annotations
import os
from pathlib import Path
from typing import List, Tuple
import cv2
import numpy as np

from .config import (
    FACE_BACKEND,
    YUNET_MODEL_PATH, HAAR_MODEL_PATH,
    YOLO_DET_PATH,
    DNN_CAFFE_PROTO, DNN_CAFFE_MODEL, FACE_DNN_CONF
)

Rect = Tuple[int, int, int, int]  # x, y, w, h

def _ensure_file(p: Path, what: str):
    if not p.exists():
        raise RuntimeError(f"{what} not found: {p}. Run scripts/fetch_models.sh or set path in .env")

# ---------- Haar ----------
def _faceboxes_haar(img_bgr: np.ndarray) -> List[Rect]:
    _ensure_file(HAAR_MODEL_PATH, "HAAR cascade")
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(HAAR_MODEL_PATH.as_posix())
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(24, 24))
    return [tuple(map(int, (x, y, w, h))) for (x, y, w, h) in faces]  # type: ignore

# ---------- YuNet (OpenCV Zoo / ONNX) ----------
def _faceboxes_yunet(img_bgr: np.ndarray) -> List[Rect]:
    if not hasattr(cv2, "FaceDetectorYN_create"):
        return _faceboxes_haar(img_bgr)
    _ensure_file(YUNET_MODEL_PATH, "YuNet ONNX")
    h, w = img_bgr.shape[:2]
    det = cv2.FaceDetectorYN_create(
        model=YUNET_MODEL_PATH.as_posix(), config="",
        input_size=(w, h), score_threshold=0.6, nms_threshold=0.3, top_k=5000
    )
    det.setInputSize((w, h))
    _, faces = det.detect(img_bgr)
    rects: List[Rect] = []
    if faces is not None:
        for f in faces:
            x, y, w, h = f[:4].astype(int).tolist()
            rects.append((x, y, w, h))
    return rects

# ---------- YOLOv8 (Ultralytics) ----------
def _faceboxes_yolo(img_bgr: np.ndarray) -> List[Rect]:
    try:
        from ultralytics import YOLO
    except Exception:
        return _faceboxes_haar(img_bgr)
    model = YOLO(YOLO_DET_PATH.as_posix() if YOLO_DET_PATH.exists() else "yolov8n.pt")
    res = model.predict(img_bgr, verbose=False)
    rects: List[Rect] = []
    for r in res:
        if r.boxes is None:
            continue
        for b in r.boxes:
            x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
            rects.append((x1, y1, max(1, x2-x1), max(1, y2-y1)))
    return rects

# ---------- DNN (Caffe SSD Res10 300x300) ----------
def _faceboxes_dnn(img_bgr: np.ndarray) -> List[Rect]:
    # 必要ファイル確認
    proto = DNN_CAFFE_PROTO
    model = DNN_CAFFE_MODEL
    if not proto.exists():
        # deploy.prototxt が無ければ Haar にフォールバック
        return _faceboxes_haar(img_bgr)
    if not model.exists():
        # caffemodel が無ければ Haar にフォールバック
        return _faceboxes_haar(img_bgr)

    net = cv2.dnn.readNetFromCaffe(proto.as_posix(), model.as_posix())
    (h, w) = img_bgr.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(img_bgr, (300, 300)), 1.0,
                                 (300, 300), (104.0, 117.0, 123.0),
                                 swapRB=False, crop=False)
    net.setInput(blob)
    detections = net.forward()
    conf_th = float(os.getenv("FACE_DNN_CONF", FACE_DNN_CONF))
    rects: List[Rect] = []
    for i in range(0, detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence < conf_th:
            continue
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (x1, y1, x2, y2) = box.astype("int")
        x1 = max(0, min(x1, w - 1))
        y1 = max(0, min(y1, h - 1))
        x2 = max(0, min(x2, w - 1))
        y2 = max(0, min(y2, h - 1))
        rects.append((x1, y1, max(1, x2 - x1), max(1, y2 - y1)))
    return rects

# ---------- Public API ----------
def faceboxes(img_bgr: np.ndarray) -> List[Rect]:
    """
    既存呼び出し名を維持。ENV(FACE_BACKEND)で切替。
    """
    backend = os.getenv("FACE_BACKEND", FACE_BACKEND).lower()
    if backend == "yunet":
        return _faceboxes_yunet(img_bgr)
    if backend == "yolo":
        return _faceboxes_yolo(img_bgr)
    if backend == "dnn":
        return _faceboxes_dnn(img_bgr)
    return _faceboxes_haar(img_bgr)
