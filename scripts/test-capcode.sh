#!/usr/bin/env bash
# 用法:
#   export API_KEY='your-secret'   # 或 CAPCODE_API_KEY
#   bash scripts/test-capcode.sh [BASE_URL]
#   TEST_BLOCK=... TEST_BG=... bash scripts/test-capcode.sh
set -euo pipefail
BASE="${1:-http://127.0.0.1:8118}"
BASE="${BASE%/}"
KEY="${API_KEY:-${CAPCODE_API_KEY:-}}"

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
  echo "跳过带密钥识别测试：请 export API_KEY=你的密钥"
  echo "完整识别还需提供可访问的图片 URL："
  echo "  TEST_BLOCK=... TEST_BG=... bash scripts/test-capcode.sh"
  exit 0
fi

if [[ -z "${TEST_BLOCK:-}" || -z "${TEST_BG:-}" ]]; then
  echo "已设置 API_KEY，但未设置 TEST_BLOCK / TEST_BG，跳过真实识图。"
  echo "示例:"
  echo "  TEST_BLOCK='https://example.com/block.png' \\"
  echo "  TEST_BG='https://example.com/bg.jpg' \\"
  echo "  API_KEY=*** bash scripts/test-capcode.sh"
  exit 0
fi

echo "== POST /capcode with X-API-Key =="
curl -fsS -X POST "${BASE}/capcode" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${KEY}" \
  -d "{\"slidingImage\":\"${TEST_BLOCK}\",\"backImage\":\"${TEST_BG}\"}"
echo
echo "OK · endpoint=${BASE}/capcode"
