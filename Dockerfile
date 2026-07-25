# syntax=docker/dockerfile:1
# Slide Captcha OCR · ddddocr (sml2h3) + FastAPI
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8118 \
    HOST=0.0.0.0 \
    WORKERS=2 \
    SIMPLE_TARGET=1 \
    LOG_LEVEL=INFO

WORKDIR /app

# Pillow / onnxruntime 常见系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY app/main.py /app/main.py

EXPOSE 8118

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8118/health || exit 1

# WORKERS 可通过环境变量覆盖；4C 机器建议 2~4
CMD ["sh", "-c", "uvicorn main:app --host ${HOST} --port ${PORT} --workers ${WORKERS}"]
