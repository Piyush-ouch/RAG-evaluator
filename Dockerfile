# =========================================================
# Root Dockerfile (For Railway / Render Root-Directory Deploys)
# Builds and runs the FastAPI Backend (with automatic SQLite & in-process worker fallback)
# =========================================================

FROM python:3.12-slim

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

COPY backend/pyproject.toml ./
COPY backend/app/ app/
COPY backend/alembic/ alembic/
COPY backend/alembic.ini .

RUN pip install . aiosqlite

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
