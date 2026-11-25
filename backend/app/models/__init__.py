"""
ORM Models Package

All SQLAlchemy models are imported here for Alembic migration auto-detection.
"""

from app.models.organization import Organization
from app.models.user import User
from app.models.membership import Membership, RoleEnum
from app.models.project import Project
from app.models.connection import Connection
from app.models.provider_config import ProviderConfig
from app.models.vector_config import VectorConfig
from app.models.llm_provider import LLMProviderConfig
from app.models.vector_db import VectorDBConfig
from app.models.benchmark import BenchmarkSuite, Question
from app.models.evaluation import Evaluation, EvaluationResult
from app.models.retrieved_chunk import RetrievedChunk
from app.models.metric import Metric
from app.models.cost import CostRecord
from app.models.latency import LatencyRecord
from app.models.security_finding import SecurityFinding
from app.models.report import Report
from app.models.audit_log import AuditLog
from app.models.api_key import ApiKey
from app.models.billing import BillingAccount, BillingUsage
from app.models.prompt_template import PromptTemplate
from app.models.regression import RegressionHistory
from app.models.notification import Notification
from app.models.subscription import Subscription

__all__ = [
    "Organization",
    "User",
    "Membership",
    "RoleEnum",
    "Project",
    "Connection",
    "ProviderConfig",
    "VectorConfig",
    "LLMProviderConfig",
    "VectorDBConfig",
    "BenchmarkSuite",
    "Question",
    "Evaluation",
    "EvaluationResult",
    "RetrievedChunk",
    "Metric",
    "CostRecord",
    "LatencyRecord",
    "SecurityFinding",
    "Report",
    "AuditLog",
    "ApiKey",
    "BillingAccount",
    "BillingUsage",
    "PromptTemplate",
    "RegressionHistory",
    "Notification",
    "Subscription",
]
