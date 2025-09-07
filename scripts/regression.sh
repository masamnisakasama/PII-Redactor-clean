#!/usr/bin/env bash
set -euo pipefail
MODE="${1:-online}"          # online | offline
PORT="${2:-8000}"
IMG="${3:-$HOME/Downloads/faces.jpeg}"
OUT="${4:-/tmp/out_${MODE}.png}"
HDR="/tmp/h_${MODE}.txt"
BASE="http://127.0.0.1:${PORT}"

curl -sS -X POST "${BASE}/redact/replace" \
  -F "file=@${IMG}" -F "policy=face,email,phone,id" \
  -F "style=box" -F "mode=${MODE}" \
  -o "${OUT}" -D "${HDR}"

grep -q "HTTP/1.1 200" "${HDR}"
grep -qi "x-mode: ${MODE}" "${HDR}"
file "${OUT}" | grep -qi "PNG image" && echo "✅ ${MODE} passed -> ${OUT}"
