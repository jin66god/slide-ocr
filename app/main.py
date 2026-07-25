# -*- coding: utf-8 -*-
"""
Slide Captcha OCR Service
=========================
基于 sml2h3/ddddocr 官方 SDK 的滑块验证码识别 HTTP 服务。

协议兼容常见青龙/脚本圈 CAPCODE 接口（如草原云原脚本 ocr 方法）:

    POST /capcode
    Content-Type: application/json
    {
      "slidingImage": "<滑块图 URL 或 base64 / dataURL>",
      "backImage":    "<背景图 URL 或 base64 / dataURL>"
    }

    成功 → {"result": 175.0}
    失败 → {"error": "出现错误: ..."}

SDK 来源:
  - GitHub: https://github.com/sml2h3/ddddocr
  - PyPI:   https://pypi.org/project/ddddocr/  (本仓库 requirements 固定最新稳定版)
"""

from __future__ import annotations

import base64
import logging
import os
import time
from typing import Any, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "20"))
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", str(8 * 1024 * 1024)))
# ddddocr.slide_match(simple_target=...)：缺口滑块一般 True 更稳
SIMPLE_TARGET = os.environ.get("SIMPLE_TARGET", "1").strip() not in (
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
        # 只要滑块匹配：det=False, ocr=False，减小内存与启动时间
        # show_ad=False：关闭广告输出（新版本参数）
        try:
            _ocr = ddddocr.DdddOcr(det=False, ocr=False, show_ad=False)
        except TypeError:
            # 极老版本无 show_ad
            _ocr = ddddocr.DdddOcr(det=False, ocr=False)
        log.info(
            "ddddocr ready · version=%s · simple_target=%s",
            _ddddocr_version,
            SIMPLE_TARGET,
        )
    return _ocr


def load_image_bytes(data: str) -> bytes:
    """支持 http(s) URL / dataURL / 纯 base64。"""
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
    """解析 ddddocr.slide_match 返回值 → 缺口 x。"""
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


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Slide Captcha OCR",
    description="ddddocr-based slider captcha solver (CAPCODE compatible)",
    version="1.0.0",
)


class CapRequest(BaseModel):
    slidingImage: str = Field(..., description="滑块小图：URL / base64 / dataURL")
    backImage: str = Field(..., description="背景大图：URL / base64 / dataURL")


@app.get("/")
def root():
    return {
        "msg": "API运行成功！",
        "service": "slide-ocr",
        "ddddocr": _ddddocr_version if _ocr is not None else "lazy",
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
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/capcode")
def capcode(req: CapRequest) -> dict:
    """
    CAPCODE 兼容接口。

    成功: {"result": <float>}
    失败: {"error": "出现错误: ..."}
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
        x: Optional[float] = None
        modes = [True, False] if SIMPLE_TARGET else [False, True]
        for st in modes:
            try:
                try:
                    res = ocr.slide_match(block, bg, simple_target=st)
                except TypeError:
                    # 旧签名无 simple_target
                    res = ocr.slide_match(block, bg)
                x = parse_slide_x(res)
                if x is not None and x > 0:
                    break
            except Exception as e:
                last_err = e
                continue

        if x is None or x <= 0:
            raise RuntimeError(last_err or "no valid x")

        x_out = round(float(x), 1)
        log.info(
            "capcode ok x=%s block=%dB bg=%dB cost=%.3fs",
            x_out,
            len(block),
            len(bg),
            time.time() - t0,
        )
        return {"result": x_out}
    except Exception as e:
        log.warning("capcode fail: %s", e)
        return {"error": f"出现错误: {e}"}
