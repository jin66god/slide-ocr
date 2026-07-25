# slide-ocr

基于 **[sml2h3/ddddocr](https://github.com/sml2h3/ddddocr)** 官方 SDK 的滑块验证码识别 HTTP 服务（FastAPI + Docker）。

兼容青龙/脚本圈常见 **CAPCODE** 协议，可直接给「草原云」等脚本使用：

```bash
export CAPCODE_URL='http://你的服务器IP:8118/capcode'
```

| 项目 | 说明 |
|------|------|
| OCR SDK | [sml2h3/ddddocr](https://github.com/sml2h3/ddddocr) · PyPI [`ddddocr`](https://pypi.org/project/ddddocr/) |
| 本仓库锁定 | `ddddocr>=1.6.1,<2.0`（PyPI 当前最新稳定 **1.6.1**，Python ≥3.10） |
| Web 框架 | FastAPI + uvicorn |
| 部署 | Docker / docker compose |
| 协议 | `POST /capcode` → `{"result": x}` |

> **是的：用的就是 sml2h3/ddddocr 官方包**，不是魔改 fork。版本以 PyPI 为准；升级时改 `app/requirements.txt` 后重新 build 即可。

---

## 目录结构

```text
slide-ocr/
├── app/
│   ├── main.py              # FastAPI 服务
│   └── requirements.txt     # 依赖（含最新 ddddocr）
├── docs/
│   └── API.md               # 接口说明
├── scripts/
│   └── test-capcode.sh      # 自测脚本
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── LICENSE                  # MIT
└── README.md
```

---

## 快速开始（Docker，推荐）

### 1. 克隆

```bash
git clone https://github.com/jin66god/slide-ocr.git
cd slide-ocr
```

### 2. 启动

```bash
# 默认端口 8118，2 个 worker
docker compose up -d --build

# 4C24G 可加大 worker
WORKERS=4 docker compose up -d --build
```

### 3. 验证

```bash
curl http://127.0.0.1:8118/health
# {"status":"ok","engine":"ddddocr","ddddocr_version":"1.6.1",...}

bash scripts/test-capcode.sh http://127.0.0.1:8118
```

### 4. 给业务脚本用

```bash
export CAPCODE_URL='http://你的服务器公网或内网IP:8118/capcode'
```

---

## API 摘要

### `POST /capcode`

```http
Content-Type: application/json

{
  "slidingImage": "https://.../xxx_block.png",
  "backImage": "https://.../xxx.png"
}
```

成功：

```json
{"result": 175.0}
```

失败：

```json
{"error": "出现错误: ..."}
```

`slidingImage` / `backImage` 支持：

- `http://` / `https://` 图片链接  
- 纯 base64  
- `data:image/png;base64,...`

完整说明见 [docs/API.md](./docs/API.md)。

### 其它端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 存活 |
| GET | `/health` | 引擎健康（会加载模型） |
| POST | `/capcode` | 滑块识别 |

---

## 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `PORT` | `8118` | 宿主机映射端口 |
| `WORKERS` | `2` | uvicorn workers（4C 建议 2~4） |
| `SIMPLE_TARGET` | `1` | `slide_match(simple_target=True)` |
| `HTTP_TIMEOUT` | `20` | 拉取远程图片超时（秒） |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `MEM_LIMIT` | `8g` | 容器内存上限（compose） |
| `CPUS` | `3.5` | 容器 CPU 上限（compose） |

示例：

```bash
cp .env.example .env
# 编辑 .env 后
docker compose up -d --build
```

---

## 资源建议

| 配置 | 是否合适 |
|------|----------|
| 1C1G | 可跑，建议 1 worker + swap，低并发 |
| 2C4G | 日常自用够用 |
| **4C24G** | **很宽裕**，`WORKERS=2~4` |

ddddocr 滑块模型常驻大约 **每 worker 0.5~1GB** 量级；内存大头在模型，不在 FastAPI。

---

## 常用运维

```bash
# 日志
docker logs -f slide-ocr

# 重启
docker compose restart

# 停掉
docker compose down

# 升级 ddddocr：改 app/requirements.txt 后
docker compose up -d --build
```

---

## 无 Docker 本地跑（开发）

需要 Python **≥3.10**（ddddocr 1.6.x 要求）。

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8118 --workers 1
```

---

## 与「公网 dcfocr」的关系

部分脚本默认：

```text
http://dcfocr.20232024.xyz/capcode
```

那是**第三方私有打码站**，协议与本服务相同（`slidingImage` + `backImage` → `result`），但**不是开源项目**，可用性不保证。

本仓库是你自己可控的开源替代，算法侧使用官方 **ddddocr**。

---

## 安全建议

- 生产环境不要把服务无鉴权裸奔公网；优先 **内网 / VPN / 反代 + Token**。
- 仅用于你有权处理的验证码场景，遵守目标站点与当地法律。
- 本项目 **MIT**；ddddocr 本身许可证与依赖以 [上游仓库](https://github.com/sml2h3/ddddocr) 为准。

---

## 致谢

- [sml2h3/ddddocr](https://github.com/sml2h3/ddddocr) — 验证码识别 SDK  
- [FastAPI](https://github.com/tiangolo/fastapi) · [uvicorn](https://github.com/encode/uvicorn)

---

## License

[MIT](./LICENSE)
