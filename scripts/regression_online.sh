#!/usr/bin/env bash
set -euo pipefail
IMG="${1:-$HOME/Downloads/faces.jpeg}"
OUT="${2:-/tmp/out_on.png}"
HDR="/tmp/h_on.txt"

curl -sS -X POST http://127.0.0.1:8000/redact/replace \
  -F "file=@${IMG}" -F "policy=face,email,phone,id" \
  -F "style=box" -F "mode=online" \
  -o "$OUT" -D "$HDR"

grep -q "HTTP/1.1 200" "$HDR"
grep -q "x-mode: online" "$HDR"
file "$OUT" | grep -qi "PNG image" && echo "✅ online passed -> $OUT"