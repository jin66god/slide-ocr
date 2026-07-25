#!/usr/bin/env bash
# 用法:
#   export CAPCODE_API_KEY='your-secret'
#   bash scripts/test-capcode.sh [BASE_URL]
set -euo pipefail
BASE="${1:-http://127.0.0.1:8118}"
BASE="${BASE%/}"
KEY="${CAPCODE_API_KEY:-${API_KEY:-}}"

echo "== GET / =="
curl -fsS "${BASE}/" ; echo

echo "== GET /health =="
curl -fsS "${BASE}/health" ; echo

echo "== POST /capcode without key (expect 401/503) =="
code=$(curl -sS -o /tmp/cap_noauth.json -w "%{http_code}" -X POST "${BASE}/capcode" \
  -H "Content-Type: application/json" \
  -d '{"slidingImage":"x","backImage":"y"}' || true)
echo "HTTP $code  body=$(head -c 200 /tmp/cap_noauth.json 2>/dev/null)"
echo

if [[ -z "$KEY" ]]; then
  echo "跳过带密钥测试：请 export CAPCODE_API_KEY=你的密钥"
  exit 0
fi

BLOCK="${TEST_BLOCK:-https://ys-oss.iyunxh.com/captcha/block/05b656cde974bb1a7ce072a05bab6fd5_block.png}"
BG="${TEST_BG:-https://ys-oss.iyunxh.com/captcha/block/05b656cde974bb1a7ce072a05bab6fd5.png}"

echo "== POST /capcode with X-API-Key =="
curl -fsS -X POST "${BASE}/capcode" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${KEY}" \
  -d "{\"slidingImage\":\"${BLOCK}\",\"backImage\":\"${BG}\"}"
echo
echo "CAPCODE_URL=${BASE}/capcode"
echo "CAPCODE_API_KEY=***"
