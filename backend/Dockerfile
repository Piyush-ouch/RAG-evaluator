# =========================================================
# Backend Dockerfile — Multi-stage Build
# =========================================================

# --- Base Stage ---
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

# --- Development Stage ---
FROM base AS development

COPY . .
RUN pip install -e ".[dev]" aiosqlite 2>/dev/null || pip install ".[dev]" aiosqlite

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port ${PORT:-8000}"]

# --- Production Stage ---
FROM base AS production

COPY pyproject.toml ./
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

RUN pip install ".[prod]" aiosqlite 2>/dev/null || pip install . aiosqlite

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
