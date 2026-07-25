# API 文档

Base URL 示例：`http://127.0.0.1:8118`

## 鉴权（重要）

`/capcode` **默认需要 API Key**，防止公网地址泄露后被刷。

在 `.env` 中设置：

```bash
API_KEY=你的长随机密钥
REQUIRE_API_KEY=1
```

生成示例：

```bash
openssl rand -hex 24
```

### 传密钥方式（任选其一）

| 方式 | 示例 |
|------|------|
| Header `X-API-Key`（推荐） | `X-API-Key: your-secret` |
| Header `Authorization` | `Authorization: Bearer your-secret` |
| Query | `POST /capcode?api_key=your-secret` |

未带密钥或密钥错误 → **HTTP 401** `{"detail":"unauthorized"}`  
服务端未配置 `API_KEY` 且 `REQUIRE_API_KEY=1` → **HTTP 503**（拒绝裸奔）

`GET /` 与 `GET /health` **不鉴权**（便于探活；不消耗识别算力也可考虑再收紧）。

---

## `GET /`

存活探测（无需密钥）。

```json
{
  "msg": "API运行成功！",
  "service": "slide-ocr",
  "version": "1.1.0",
  "auth": true,
  "endpoints": ["GET /", "GET /health", "POST /capcode"]
}
```

## `GET /health`

引擎就绪（无需密钥）。

```json
{
  "status": "ok",
  "engine": "ddddocr",
  "ddddocr_version": "1.6.1",
  "simple_target": true,
  "auth_required": true
}
```

## `POST /capcode`

滑块识别（**需鉴权**）。

### Request

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `slidingImage` | string | 是 | 滑块图：URL / base64 / dataURL |
| `backImage` | string | 是 | 背景图：同上 |

```bash
curl -X POST http://127.0.0.1:8118/capcode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret" \
  -d '{"slidingImage":"https://..._block.png","backImage":"https://....png"}'
```

成功：

```json
{"result": 175.0}
```

失败：

```json
{"error": "出现错误: ..."}
```

### 青龙 / 草原云

```bash
export CAPCODE_URL='http://你的服务器IP:8118/capcode'
export CAPCODE_API_KEY='your-secret'
# 或
export CAPCODE_URL='http://IP:8118/capcode'
export CAPCODE_KEY='your-secret'
```

脚本请求时应带 Header：`X-API-Key: $CAPCODE_API_KEY`

---

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `PORT` | `8118` | 监听端口 |
| `WORKERS` | `2` | uvicorn workers |
| `API_KEY` | （空） | 访问密钥，**生产必填** |
| `REQUIRE_API_KEY` | `1` | 强制鉴权；`0` 允许匿名（仅本地） |
| `SIMPLE_TARGET` | `1` | ddddocr simple_target |
| `HTTP_TIMEOUT` | `20` | 下载远程图超时 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
