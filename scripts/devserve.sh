#!/usr/bin/env bash（オフライン起動用）
# ターミナルで「scripts/devserve.sh モデル名」
set -euo pipefail
BACKEND="${1:-haar}"    # haar|yunet|dnn|yolo
PYTHONPATH="$(pwd)" FACE_BACKEND="$BACKEND" \
uvicorn app.main:app --host 127.0.0.1 --port 8000 --env-file .env --reload
