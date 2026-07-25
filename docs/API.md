# API 文档

Base URL 示例：`http://127.0.0.1:8118`

## 鉴权

`/capcode` **默认需要 API Key**。

```bash
# .env
API_KEY=你的长随机密钥
REQUIRE_API_KEY=1
```

```bash
openssl rand -hex 24
```

### 传密钥（任选其一）

| 方式 | 示例 |
|------|------|
| Header `X-API-Key`（推荐） | `X-API-Key: your-secret` |
| Header `Authorization` | `Authorization: Bearer your-secret` |
| Query | `POST /capcode?api_key=your-secret` |

| 状态 | 含义 |
|------|------|
| **401** | 未带密钥或密钥错误 |
| **503** | 服务端未配置 `API_KEY` 且强制鉴权 |

`GET /`、`GET /health` 默认不鉴权（探活）。

---

## `GET /`

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

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `slidingImage` | string | 是 | 滑块图：`http(s)` URL / 纯 base64 / dataURL |
| `backImage` | string | 是 | 背景图：同上 |

```bash
curl -X POST http://127.0.0.1:8118/capcode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret" \
  -d '{
    "slidingImage": "https://example.com/block.png",
    "backImage": "https://example.com/bg.jpg"
  }'
```

### 响应

成功：

```json
{"result": 175.0}
```

失败：

```json
{"error": "出现错误: ..."}
```

`result` 为缺口在背景图坐标系下的 **x 像素**（与背景原图分辨率一致）。

### 客户端示例

```bash
export SLIDE_OCR_URL='http://127.0.0.1:8118/capcode'
export SLIDE_OCR_API_KEY='your-secret'

curl -X POST "$SLIDE_OCR_URL" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $SLIDE_OCR_API_KEY" \
  -d '{"slidingImage":"...","backImage":"..."}'
```

---

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `PORT` | `8118` | 监听端口 |
| `WORKERS` | `2` | uvicorn workers |
| `API_KEY` | （空） | 访问密钥，生产必填 |
| `REQUIRE_API_KEY` | `1` | 强制鉴权 |
| `SIMPLE_TARGET` | `1` | ddddocr `simple_target` |
| `HTTP_TIMEOUT` | `20` | 下载远程图超时（秒） |
| `MAX_IMAGE_BYTES` | `8388608` | 单图大小上限 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
