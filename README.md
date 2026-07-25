# slide-ocr

基于 **[sml2h3/ddddocr](https://github.com/sml2h3/ddddocr)** 官方 SDK 的**滑块验证码识别 HTTP 服务**（FastAPI + Docker）。

纯通用服务：上传/传入滑块图与背景图，返回缺口 **x** 坐标。带 **API Key 鉴权**，避免公网被刷。

| 项目 | 说明 |
|------|------|
| OCR SDK | [sml2h3/ddddocr](https://github.com/sml2h3/ddddocr) · `ddddocr>=1.6.1` |
| Web | FastAPI + uvicorn |
| 默认端口 | **8118** |
| 鉴权 | `API_KEY` + `X-API-Key` / `Authorization: Bearer` |
| 接口 | `POST /capcode` → `{"result": x}` |

---

## 功能

- `slide_match` 滑块缺口定位（官方 ddddocr）
- 支持图片 **URL / base64 / dataURL**
- API Key 鉴权（默认强制）
- Docker / docker compose 一键部署
- 健康检查：`GET /health`

---

## 快速开始

### 1. 克隆

```bash
git clone https://github.com/jin66god/slide-ocr.git
cd slide-ocr
```

### 2. 配置

```bash
cp .env.example .env
# 生成密钥
openssl rand -hex 24
# 写入 .env 的 API_KEY=...
```

```bash
PORT=8118
WORKERS=2
API_KEY=你的长随机串
REQUIRE_API_KEY=1
```

### 3. 启动

```bash
docker compose up -d --build
```

### 4. 调用

```bash
# 探活（无需密钥）
curl http://127.0.0.1:8118/health

# 识别（需要密钥）
curl -X POST http://127.0.0.1:8118/capcode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 你的密钥" \
  -d '{
    "slidingImage": "https://example.com/block.png",
    "backImage": "https://example.com/bg.jpg"
  }'
```

成功示例：

```json
{"result": 175.0}
```

无密钥 / 密钥错误 → **HTTP 401**。

---

## 目录

```text
slide-ocr/
├── app/main.py
├── app/requirements.txt
├── docs/API.md
├── scripts/test-capcode.sh
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── LICENSE
└── README.md
```

---

## API

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/` | 否 | 存活 |
| GET | `/health` | 否 | 引擎健康 |
| POST | `/capcode` | **是** | 滑块识别 |

### 传 Key（任选）

```http
X-API-Key: SECRET
Authorization: Bearer SECRET
POST /capcode?api_key=SECRET
```

完整说明：[docs/API.md](./docs/API.md)

---

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `PORT` | `8118` | 宿主机端口 |
| `WORKERS` | `2` | uvicorn workers |
| `API_KEY` | — | **生产必填** |
| `REQUIRE_API_KEY` | `1` | 强制鉴权；`0` 仅本地调试 |
| `SIMPLE_TARGET` | `1` | ddddocr `simple_target` |
| `HTTP_TIMEOUT` | `20` | 远程拉图超时（秒） |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `MEM_LIMIT` | `8g` | 容器内存上限 |
| `CPUS` | `3.5` | 容器 CPU 上限 |

---

## 资源建议

| 配置 | 说明 |
|------|------|
| 1C1G | 可跑，建议 1 worker + swap |
| 2C4G | 日常够用 |
| 4C24G | `WORKERS=2~4` 宽裕 |

模型常驻大约每 worker **0.5~1GB** 量级。

---

## 运维

```bash
docker logs -f slide-ocr
docker compose restart
docker compose down
# 改 API_KEY 后
docker compose up -d
```

---

## 本地开发（无 Docker）

Python ≥ 3.10：

```bash
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export API_KEY=dev-secret
uvicorn main:app --host 0.0.0.0 --port 8118 --workers 1
```

---

## 安全建议

1. 生产必须设置强 `API_KEY`  
2. 安全组尽量只放行调用方 IP  
3. 可再加 Nginx / HTTPS / 限流  
4. 不要把密钥提交进 Git  
5. 仅用于合法、授权场景  

---

## 致谢

- [sml2h3/ddddocr](https://github.com/sml2h3/ddddocr)  
- [FastAPI](https://github.com/tiangolo/fastapi) · [uvicorn](https://github.com/encode/uvicorn)

## License

[MIT](./LICENSE) — ddddocr 许可证以上游仓库为准。
