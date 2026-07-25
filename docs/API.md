# API 文档

Base URL 示例：`http://127.0.0.1:8000`

## `GET /`

存活探测。

**响应示例**

```json
{
  "msg": "API运行成功！",
  "service": "slide-ocr",
  "ddddocr": "lazy",
  "endpoints": ["GET /", "GET /health", "POST /capcode"],
  "sdk": "https://github.com/sml2h3/ddddocr"
}
```

## `GET /health`

引擎就绪检查（会触发 ddddocr 加载）。

**成功**

```json
{
  "status": "ok",
  "engine": "ddddocr",
  "ddddocr_version": "1.6.1",
  "simple_target": true
}
```

## `POST /capcode`

滑块识别。兼容青龙脚本常见 CAPCODE 协议（如草原云 `ocr()`）。

### Request

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `slidingImage` | string | 是 | 滑块小图：`http(s)` URL / 纯 base64 / `data:image/...;base64,...` |
| `backImage` | string | 是 | 背景大图：同上 |

```http
POST /capcode HTTP/1.1
Content-Type: application/json

{
  "slidingImage": "https://example.com/block.png",
  "backImage": "https://example.com/bg.jpg"
}
```

### Response

成功：

```json
{"result": 175.0}
```

失败：

```json
{"error": "出现错误: empty image field"}
```

> `result` 为缺口在背景图上的 **x 像素坐标**（与背景图原始分辨率同一坐标系）。

### curl

```bash
curl -X POST http://127.0.0.1:8000/capcode \
  -H "Content-Type: application/json" \
  -d '{"slidingImage":"https://..._block.png","backImage":"https://....png"}'
```

### 青龙 / 草原云

```bash
export CAPCODE_URL='http://你的服务器IP:8000/capcode'
```

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `PORT` | `8000` | 监听端口 |
| `HOST` | `0.0.0.0` | 绑定地址 |
| `WORKERS` | `2` | uvicorn worker 数 |
| `SIMPLE_TARGET` | `1` | ddddocr `simple_target`，`0` 关闭 |
| `HTTP_TIMEOUT` | `20` | 下载远程图片超时（秒） |
| `MAX_IMAGE_BYTES` | `8388608` | 单图最大字节 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
