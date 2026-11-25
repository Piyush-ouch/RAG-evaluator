# =========================================================
# Root Dockerfile (Fast Cloud Build for Railway / Render)
# Builds in ~25 seconds with lightweight core runtime dependencies
# =========================================================

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN pip install \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "python-multipart>=0.0.9" \
    "sqlalchemy[asyncio]>=2.0.30" \
    "asyncpg>=0.29.0" \
    "aiosqlite>=0.20.0" \
    "alembic>=1.13.0" \
    "greenlet>=3.0.0" \
    "pydantic>=2.7.0" \
    "pydantic-settings>=2.3.0" \
    "email-validator>=2.1.0" \
    "python-jose[cryptography]>=3.3.0" \
    "passlib[bcrypt]>=1.7.4" \
    "httpx>=0.27.0" \
    "cryptography>=42.0.0" \
    "celery[redis]>=5.4.0" \
    "redis>=5.0.0" \
    "boto3>=1.34.0" \
    "jinja2>=3.1.0" \
    "structlog>=24.1.0" \
    "prometheus-client>=0.20.0" \
    "sentry-sdk[fastapi]>=2.0.0" \
    "tenacity>=8.3.0" \
    "orjson>=3.10.0" \
    "python-slugify>=8.0.0"

COPY backend/app/ app/
COPY backend/alembic/ alembic/
COPY backend/alembic.ini .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
