# slide-ocr

基于 **[sml2h3/ddddocr](https://github.com/sml2h3/ddddocr)** 官方 SDK 的滑块验证码识别 HTTP 服务（FastAPI + Docker）。

兼容青龙/脚本圈常见 **CAPCODE** 协议，并带 **API Key 鉴权**，避免公网地址被滥用。

```bash
export CAPCODE_URL='http://你的服务器IP:8118/capcode'
export CAPCODE_API_KEY='你的密钥'
```

| 项目 | 说明 |
|------|------|
| OCR SDK | [sml2h3/ddddocr](https://github.com/sml2h3/ddddocr) · PyPI `ddddocr>=1.6.1` |
| Web | FastAPI + uvicorn |
| 端口默认 | **8118** |
| 鉴权 | `API_KEY` + Header `X-API-Key` / `Authorization: Bearer` |
| 协议 | `POST /capcode` → `{"result": x}` |

---

## 安全说明（为什么要鉴权）

如果只暴露：

```text
http://IP:8118/capcode
```

任何人都能刷识别接口，白白吃你的 CPU/带宽。  
因此本服务 **默认强制 API Key**：

- 未带密钥 / 密钥错误 → **401**
- 服务端没配 `API_KEY` → **503**（拒绝无密钥上线）

本地调试才允许：

```bash
REQUIRE_API_KEY=0   # 不推荐公网
```

---

## 快速开始（Docker）

### 1. 克隆

```bash
git clone https://github.com/jin66god/slide-ocr.git
cd slide-ocr
```

### 2. 配置密钥

```bash
cp .env.example .env
# 编辑 .env，至少改 API_KEY
# 生成示例:
#   openssl rand -hex 24
```

`.env` 关键项：

```bash
PORT=8118
WORKERS=2
API_KEY=换成你自己的长随机串
REQUIRE_API_KEY=1
```

### 3. 启动

```bash
docker compose up -d --build
```

### 4. 验证

```bash
# 健康检查（无需密钥）
curl http://127.0.0.1:8118/health

# 无密钥应 401
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8118/capcode \
  -H "Content-Type: application/json" \
  -d '{"slidingImage":"x","backImage":"y"}'

# 带密钥
curl -X POST http://127.0.0.1:8118/capcode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 你的密钥" \
  -d '{"slidingImage":"https://..._block.png","backImage":"https://....png"}'
```

### 5. 业务脚本

```bash
export CAPCODE_URL='http://你的IP:8118/capcode'
export CAPCODE_API_KEY='你的密钥'
```

请求头：

```http
X-API-Key: 你的密钥
```

---

## 目录结构

```text
slide-ocr/
├── app/
│   ├── main.py
│   └── requirements.txt
├── docs/API.md
├── scripts/test-capcode.sh
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── LICENSE
└── README.md
```

---

## API 摘要

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/` | 否 | 存活 |
| GET | `/health` | 否 | 引擎健康 |
| POST | `/capcode` | **是** | 滑块识别 |

成功响应：

```json
{"result": 175.0}
```

完整字段与错误码见 [docs/API.md](./docs/API.md)。

### 传 Key 的三种方式

```bash
# 1) 推荐
-H "X-API-Key: SECRET"

# 2)
-H "Authorization: Bearer SECRET"

# 3) 不推荐写在 URL 日志里
POST /capcode?api_key=SECRET
```

---

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `PORT` | `8118` | 宿主机端口 |
| `WORKERS` | `2` | worker 数（4C 建议 2~4） |
| `API_KEY` | — | **生产必填** |
| `REQUIRE_API_KEY` | `1` | 强制鉴权 |
| `SIMPLE_TARGET` | `1` | ddddocr simple_target |
| `HTTP_TIMEOUT` | `20` | 拉图超时 |
| `LOG_LEVEL` | `INFO` | 日志 |
| `MEM_LIMIT` | `8g` | 容器内存上限 |
| `CPUS` | `3.5` | 容器 CPU 上限 |

---

## 资源建议

| 配置 | 说明 |
|------|------|
| 1C1G | 可跑，1 worker + swap |
| 2C4G | 日常够用 |
| 4C24G | `WORKERS=2~4` 很宽裕 |

---

## 运维

```bash
docker logs -f slide-ocr
docker compose restart
docker compose down

# 改密钥后
# 编辑 .env 中 API_KEY，再:
docker compose up -d
```

---

## 无 Docker 本地开发

Python ≥ 3.10：

```bash
cd app
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export API_KEY=dev-secret
export REQUIRE_API_KEY=1
uvicorn main:app --host 0.0.0.0 --port 8118 --workers 1
```

---

## 安全建议

1. **务必设置强 `API_KEY`**，不要用 `change-me` 上线  
2. 优先内网 / 安全组只放行你的青龙机器 IP  
3. 生产可再加 Nginx 限流、HTTPS  
4. 不要把 Key 提交进 Git  
5. 仅用于你有权处理的验证码场景  

---

## 致谢

- [sml2h3/ddddocr](https://github.com/sml2h3/ddddocr)  
- FastAPI / uvicorn  

## License

[MIT](./LICENSE) — ddddocr 许可证以[上游](https://github.com/sml2h3/ddddocr)为准。
