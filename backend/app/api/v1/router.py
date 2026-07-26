"""
API v1 Router Aggregator

Mounts all v1 sub-routers under /api/v1/.
Each module manages its own route prefix and tags.
"""

from __future__ import annotations

from fastapi import APIRouter

api_v1_router = APIRouter()

# ---------------------------------------------------------
# Import and mount all sub-routers
# ---------------------------------------------------------

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.organizations import router as org_router
from app.api.v1.endpoints.projects import router as project_router
from app.api.v1.endpoints.benchmarks import router as benchmark_router
from app.api.v1.endpoints.evaluations import router as evaluation_router
from app.api.v1.endpoints.reports import router as report_router
from app.api.v1.endpoints.metrics import router as metrics_router
from app.api.v1.endpoints.billing import router as billing_router
from app.api.v1.endpoints.api_keys import router as api_key_router
from app.api.v1.endpoints.audit import router as audit_router
from app.api.v1.endpoints.demo import router as demo_router
from app.api.v1.endpoints.websocket import router as ws_router

api_v1_router.include_router(auth_router)
api_v1_router.include_router(org_router)
api_v1_router.include_router(project_router)
api_v1_router.include_router(benchmark_router)
api_v1_router.include_router(evaluation_router)
api_v1_router.include_router(report_router)
api_v1_router.include_router(metrics_router)
api_v1_router.include_router(billing_router)
api_v1_router.include_router(api_key_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(demo_router)
api_v1_router.include_router(ws_router)

