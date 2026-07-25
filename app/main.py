# -*- coding: utf-8 -*-
"""
Slide Captcha OCR Service
=========================
基于 sml2h3/ddddocr 官方 SDK 的滑块验证码识别 HTTP 服务。

    POST /capcode
    Content-Type: application/json
    X-API-Key: <your-secret>
    {
      "slidingImage": "<滑块图 URL 或 base64 / dataURL>",
      "backImage":    "<背景图 URL 或 base64 / dataURL>"
    }

    成功 → {"result": 175.0}
    失败 → {"error": "出现错误: ..."}
    未授权 → HTTP 401 {"detail": "unauthorized"}

鉴权:
  - 环境变量 API_KEY（或 CAPCODE_API_KEY）非空时，/capcode 必须带密钥
  - 未设置 API_KEY 时默认拒绝（REQUIRE_API_KEY=1），防止公网裸奔
  - 本地调试可设 REQUIRE_API_KEY=0 关闭强制

SDK:
  - https://github.com/sml2h3/ddddocr
  - https://pypi.org/project/ddddocr/
"""

from __future__ import annotations

import base64
import logging
import os
import secrets
import time
from typing import Any, Optional

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "20"))
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", str(8 * 1024 * 1024)))
SIMPLE_TARGET = os.environ.get("SIMPLE_TARGET", "1").strip() not in (
    "0",
    "false",
    "False",
    "no",
)

_API_KEY_RAW = (
    os.environ.get("API_KEY") or os.environ.get("CAPCODE_API_KEY") or ""
).strip()
REQUIRE_API_KEY = os.environ.get("REQUIRE_API_KEY", "1").strip() not in (
    "0",
    "false",
    "False",
    "no",
)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("slide-ocr")

_ocr = None
_ddddocr_version = "unknown"


def get_ocr():
    """懒加载 ddddocr（每个 uvicorn worker 进程一份模型）。"""
    global _ocr, _ddddocr_version
    if _ocr is None:
        import ddddocr

        _ddddocr_version = getattr(ddddocr, "__version__", "unknown")
        try:
            _ocr = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
        except TypeError:
            _ocr = ddddocr.DdddOcr(det=False, ocr=False)
        log.info(
            "ddddocr ready · version=%s · simple_target=%s",
            _ddddocr_version,
            SIMPLE_TARGET,
        )
    return _ocr


def load_image_bytes(data: str) -> bytes:
    if not data or not str(data).strip():
        raise ValueError("empty image field")
    s = str(data).strip()

    if s.startswith("http://") or s.startswith("https://"):
        with httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
            r = client.get(s)
            r.raise_for_status()
            raw = r.content
        if len(raw) > MAX_IMAGE_BYTES:
            raise ValueError(f"image too large: {len(raw)} > {MAX_IMAGE_BYTES}")
        if len(raw) < 32:
            raise ValueError("image too small")
        return raw

    if "," in s and s.lower().startswith("data:"):
        s = s.split(",", 1)[1]

    try:
        raw = base64.b64decode(s, validate=False)
    except Exception as e:
        raise ValueError(f"invalid base64: {e}") from e
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError(f"image too large: {len(raw)} > {MAX_IMAGE_BYTES}")
    if len(raw) < 32:
        raise ValueError("decoded image too small")
    return raw


def parse_slide_x(res: Any) -> float:
    if isinstance(res, dict):
        if (
            "target" in res
            and isinstance(res["target"], (list, tuple))
            and res["target"]
        ):
            return float(res["target"][0])
        for k in ("target_x", "x", "left", "targetX", "result"):
            if res.get(k) is not None:
                return float(res[k])
    if isinstance(res, (list, tuple)) and res:
        return float(res[0])
    if isinstance(res, (int, float)):
        return float(res)
    raise ValueError(f"unrecognized slide_match result: {type(res)} {res!r}")


def _extract_key(
    x_api_key: Optional[str],
    authorization: Optional[str],
    api_key_query: Optional[str],
) -> str:
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization and authorization.strip():
        auth = authorization.strip()
        if auth.lower().startswith("bearer "):
            return auth[7:].strip()
        return auth
    if api_key_query and api_key_query.strip():
        return api_key_query.strip()
    return ""


def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None),
    api_key: Optional[str] = Query(None, description="可选：?api_key="),
) -> None:
    """
    /capcode 鉴权。

    接受（任选其一）:
      - Header: X-API-Key: <key>
      - Header: Authorization: Bearer <key>
      - Query:  ?api_key=<key>
    """
    provided = _extract_key(x_api_key, authorization, api_key)

    if _API_KEY_RAW:
        if not provided or not secrets.compare_digest(provided, _API_KEY_RAW):
            raise HTTPException(status_code=401, detail="unauthorized")
        return

    if REQUIRE_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="server misconfigured: set env API_KEY (auth required)",
        )
    return


app = FastAPI(
    title="Slide Captcha OCR",
    description="ddddocr-based slider captcha OCR with API key auth",
    version="1.1.0",
)


@app.on_event("startup")
def _startup_log():
    if _API_KEY_RAW:
        log.info("auth: API_KEY enabled (len=%d)", len(_API_KEY_RAW))
    elif REQUIRE_API_KEY:
        log.warning(
            "auth: API_KEY empty but REQUIRE_API_KEY=1 → /capcode will return 503 "
            "until you set API_KEY"
        )
    else:
        log.warning(
            "auth: OPEN mode (REQUIRE_API_KEY=0, no API_KEY) — anyone can call /capcode"
        )


class CapRequest(BaseModel):
    slidingImage: str = Field(..., description="滑块小图：URL / base64 / dataURL")
    backImage: str = Field(..., description="背景大图：URL / base64 / dataURL")


@app.get("/")
def root():
    return {
        "msg": "API运行成功！",
        "service": "slide-ocr",
        "version": "1.1.0",
        "ddddocr": _ddddocr_version if _ocr is not None else "lazy",
        "auth": bool(_API_KEY_RAW) or REQUIRE_API_KEY,
        "endpoints": ["GET /", "GET /health", "POST /capcode"],
        "sdk": "https://github.com/sml2h3/ddddocr",
    }


@app.get("/health")
def health():
    try:
        get_ocr()
        return {
            "status": "ok",
            "engine": "ddddocr",
            "ddddocr_version": _ddddocr_version,
            "simple_target": SIMPLE_TARGET,
            "auth_required": bool(_API_KEY_RAW) or REQUIRE_API_KEY,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/capcode")
def capcode(req: CapRequest, _: None = Depends(verify_api_key)) -> dict:
    """
    滑块识别（需鉴权）。

    成功: {"result": <float>, "confidence": <float>, "candidates": [...]}
    失败: {"error": "出现错误: ..."}
    未授权: HTTP 401
    """
    t0 = time.time()
    try:
        block = load_image_bytes(req.slidingImage)
        bg = load_image_bytes(req.backImage)
    except Exception as e:
        return {"error": f"出现错误: {e}"}

    try:
        ocr = get_ocr()
        last_err: Optional[Exception] = None
        candidates: list[dict] = []

        for st in (True, False):
            try:
                try:
                    res = ocr.slide_match(block, bg, simple_target=st)
                except TypeError:
                    res = ocr.slide_match(block, bg)
                x = parse_slide_x(res)
                conf = 0.0
                if isinstance(res, dict):
                    conf = float(res.get("confidence") or res.get("score") or 0.0)
                if x is not None and x > 0:
                    candidates.append(
                        {
                            "x": round(float(x), 1),
                            "confidence": conf,
                            "simple_target": st,
                        }
                    )
            except Exception as e:
                last_err = e
                continue

        if not candidates:
            raise RuntimeError(last_err or "no valid x")

        # 按 confidence 选最优；置信度都接近 0 时仍取最高
        candidates.sort(key=lambda c: c["confidence"], reverse=True)
        best = candidates[0]
        x_out = float(best["x"])

        log.info(
            "capcode ok x=%s conf=%.4f cands=%s block=%dB bg=%dB cost=%.3fs",
            x_out,
            best["confidence"],
            [(c["x"], round(c["confidence"], 3)) for c in candidates],
            len(block),
            len(bg),
            time.time() - t0,
        )
        return {
            "result": x_out,
            "confidence": best["confidence"],
            "candidates": candidates,
        }
    except Exception as e:
        log.warning("capcode fail: %s", e)
        return {"error": f"出现错误: {e}"}
