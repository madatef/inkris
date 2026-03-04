# syntax=docker/dockerfile:1.7
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# OS deps (adjust if you need libpq, gcc, etc. for your wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast, deterministic installs with uv.lock)
RUN pip install --no-cache-dir uv

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock ./

# Install deps (no dev deps; frozen lock)
RUN uv sync --frozen --no-dev

# Copy the app code and built SPA assets
COPY . .

# Render sets PORT; locally default is 8000
EXPOSE 8000

# Production default: run your existing entrypoint
CMD ["python", "server.py"]