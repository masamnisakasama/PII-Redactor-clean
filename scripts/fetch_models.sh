#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

MODELS_DIR="models"
mkdir -p "$MODELS_DIR"

curl_dl() { local url="$1" out="$2"; echo "↓ ${out}"; curl -L --fail --retry 3 --retry-delay 2 -o "${out}.part" "$url"; mv "${out}.part" "$out"; }

echo "==> Download EAST (text detector, .pb)"
EAST_PB="${MODELS_DIR}/frozen_east_text_detection.pb"
[[ -s "$EAST_PB" ]] || curl_dl "https://raw.githubusercontent.com/oyyd/frozen_east_text_detection.pb/master/frozen_east_text_detection.pb" "$EAST_PB"

echo "==> Download YuNet (OpenCV Zoo, face detector, ONNX)"
YUNET_ONNX="${MODELS_DIR}/face_detection_yunet_2023mar.onnx"
[[ -s "$YUNET_ONNX" ]] || curl_dl "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx" "$YUNET_ONNX"

echo "==> Download YOLOv8 (Ultralytics, Detect & Seg) - optional"
YOLO_DET_PT="${MODELS_DIR}/yolov8n.pt"
YOLO_SEG_PT="${MODELS_DIR}/yolov8n-seg.pt"
[[ -s "$YOLO_DET_PT" ]] || curl_dl "https://huggingface.co/ultralytics/YOLOv8/resolve/main/yolov8n.pt" "$YOLO_DET_PT"
if [[ ! -s "$YOLO_SEG_PT" ]]; then
  echo "Trying YOLOv8n-seg primary..."
  if curl -L --fail --retry 3 --retry-delay 2 -o "${YOLO_SEG_PT}.part" "https://huggingface.co/ultralytics/YOLOv8/resolve/main/yolov8n-seg.pt"; then
    mv "${YOLO_SEG_PT}.part" "$YOLO_SEG_PT"
  else
    echo "Primary 404, trying fallback mirror..."
    curl -L --fail --retry 3 --retry-delay 2 -o "${YOLO_SEG_PT}.part" "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n-seg.pt" && mv "${YOLO_SEG_PT}.part" "$YOLO_SEG_PT" || true
  fi
fi

echo "==> Download DNN face (Caffe Res10 300x300)"
# まず fp32（10.1MB）を取得、ダメなら fp16 を試す
DNN_FP32="${MODELS_DIR}/res10_300x300_ssd_iter_140000.caffemodel"
DNN_FP16="${MODELS_DIR}/res10_300x300_ssd_iter_140000_fp16.caffemodel"
if [[ ! -s "$DNN_FP32" && ! -s "$DNN_FP16" ]]; then
  echo "primary (fp32, opencv_3rdparty)…"
  if curl -L --fail --retry 3 --retry-delay 2 -o "${DNN_FP32}.part" \
     "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"; then
    mv "${DNN_FP32}.part" "$DNN_FP32"
  else
    echo "fallback (fp16, may 404 nowadays)…"
    curl -L --fail --retry 3 --retry-delay 2 -o "${DNN_FP16}.part" \
      "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000_fp16.caffemodel" \
      && mv "${DNN_FP16}.part" "$DNN_FP16" || true
  fi
fi

echo "==> Done. Files in $MODELS_DIR"
ls -lh "$MODELS_DIR"
