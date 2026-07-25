#!/usr/bin/env bash
# 用法: bash scripts/test-capcode.sh [BASE_URL]
set -euo pipefail
BASE="${1:-http://127.0.0.1:8118}"
BASE="${BASE%/}"

echo "== GET / =="
curl -fsS "${BASE}/" ; echo

echo "== GET /health =="
curl -fsS "${BASE}/health" ; echo

BLOCK="${TEST_BLOCK:-https://ys-oss.iyunxh.com/captcha/block/05b656cde974bb1a7ce072a05bab6fd5_block.png}"
BG="${TEST_BG:-https://ys-oss.iyunxh.com/captcha/block/05b656cde974bb1a7ce072a05bab6fd5.png}"

echo "== POST /capcode (sample URLs, needs outbound network) =="
curl -fsS -X POST "${BASE}/capcode" \
  -H "Content-Type: application/json" \
  -d "{\"slidingImage\":\"${BLOCK}\",\"backImage\":\"${BG}\"}"
echo
echo "OK if body contains {\"result\": <number>}"
echo "CAPCODE_URL=${BASE}/capcode"
