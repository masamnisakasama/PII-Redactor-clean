#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

ok=1
check() {
  local f="$1" min_kb="$2"
  if [[ -s "$f" ]]; then
    sz=$(du -k "$f" | awk '{print $1}')
    if (( sz < min_kb )); then
      echo "?? too small: $f (${sz}KB < ${min_kb}KB)"; ok=0
    else
      echo "OK: $f (${sz}KB)"
    fi
  else
    echo "!! missing: $f"; ok=0
  fi
}

# ===== 基本モデル =====
check models/frozen_east_text_detection.pb 90000
check models/face_detection_yunet_2023mar.onnx 150
check models/yolov8n.pt 3000
[[ -s models/yolov8n-seg.pt ]] && check models/yolov8n-seg.pt 5000 || echo "warn: missing optional models/yolov8n-seg.pt"

# DNN (どちらかあればOK)
if [[ -s models/res10_300x300_ssd_iter_140000_fp16.caffemodel ]]; then
  check models/res10_300x300_ssd_iter_140000_fp16.caffemodel 5000
elif [[ -s models/res10_300x300_ssd_iter_140000.caffemodel ]]; then
  check models/res10_300x300_ssd_iter_140000.caffemodel 9000
else
  echo "!! missing: DNN Caffe res10 model"
  ok=0
fi

# AnimeGAN / ComixGAN
ANIME_MIN_KB="${ANIMEGAN_MIN_KB:-1000}"
COMIX_MIN_KB="${COMIXGAN_MIN_KB:-1000}"

if compgen -G "models/animegan/*.onnx" > /dev/null; then
  echo "--- animegan ---"
  for f in models/animegan/*.onnx; do
    check "$f" "$ANIME_MIN_KB"
  done
else
  echo "warn: missing optional models/animegan/*.onnx"
fi

if compgen -G "models/comixgan/*.onnx" > /dev/null; then
  echo "--- comixgan ---"
  for f in models/comixgan/*.onnx; do
    check "$f" "$COMIX_MIN_KB"
  done
else
  echo "warn: missing optional models/comixgan/*.onnx"
fi

# ===== サマリ =====
if (( ok == 1 )); then
  echo "==> verify: OK"
else
  echo "==> verify: NG"
fi
exit $ok
