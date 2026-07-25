"""
Application Constants & Enumerations

Centralized enums used across the entire application.
Using StrEnum for JSON-serializable enum values.
"""

from __future__ import annotations

import enum


# ---------------------------------------------------------
# User & Organization
# ---------------------------------------------------------

class UserRole(str, enum.Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    OWNER = "owner"
    DEVELOPER = "developer"
    VIEWER = "viewer"

    @property
    def level(self) -> int:
        """Numeric permission level — higher = more access."""
        return {
            UserRole.VIEWER: 10,
            UserRole.DEVELOPER: 20,
            UserRole.OWNER: 30,
            UserRole.ADMIN: 40,
        }[self]

    def has_at_least(self, required: "UserRole") -> bool:
        """Check if this role meets the minimum required role."""
        return self.level >= required.level


class AuthProvider(str, enum.Enum):
    """Authentication providers."""
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"


class BillingPlan(str, enum.Enum):
    """Subscription plans."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    TRIAL = "trial"
    TEAM = "team"


class BillingInterval(str, enum.Enum):
    """Billing interval."""
    MONTHLY = "monthly"
    ANNUAL = "annual"


# ---------------------------------------------------------
# AI Providers
# ---------------------------------------------------------

class LLMProviderType(str, enum.Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"
    AZURE_OPENAI = "azure_openai"
    OLLAMA = "ollama"


class VectorDBType(str, enum.Enum):
    """Supported vector database providers."""
    PINECONE = "pinecone"
    QDRANT = "qdrant"
    WEAVIATE = "weaviate"
    MILVUS = "milvus"
    CHROMA = "chroma"
    FAISS = "faiss"


# ---------------------------------------------------------
# Evaluation
# ---------------------------------------------------------

class EvaluationStatus(str, enum.Enum):
    """Evaluation lifecycle states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class EvaluatorType(str, enum.Enum):
    """Types of evaluators in the evaluation engine."""
    # Quality
    HALLUCINATION = "hallucination"
    CORRECTNESS = "correctness"
    FAITHFULNESS = "faithfulness"
    CONTEXT_PRECISION = "context_precision"
    CONTEXT_RECALL = "context_recall"
    RETRIEVAL_PRECISION = "retrieval_precision"
    RETRIEVAL_RECALL = "retrieval_recall"
    CHUNK_RELEVANCE = "chunk_relevance"
    CITATION_VERIFICATION = "citation_verification"

    # Performance
    LATENCY = "latency"
    COST = "cost"

    # Security
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    TOXICITY = "toxicity"
    BIAS = "bias"
    PII_LEAKAGE = "pii_leakage"
    COMPLIANCE = "compliance"

    # Regression
    REGRESSION = "regression"


class SecurityTestType(str, enum.Enum):
    """Categories of security tests."""
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    ROLE_ESCALATION = "role_escalation"
    PII_REQUEST = "pii_request"
    SECRET_LEAKAGE = "secret_leakage"
    SQL_INJECTION = "sql_injection"
    CODE_EXECUTION = "code_execution"
    DATA_EXFILTRATION = "data_exfiltration"
    SYSTEM_PROMPT_EXTRACTION = "system_prompt_extraction"
    HIDDEN_PROMPT_LEAKAGE = "hidden_prompt_leakage"


class SecuritySeverity(str, enum.Enum):
    """Severity levels for security findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class BenchmarkDomain(str, enum.Enum):
    """Built-in benchmark domains."""
    GENERAL = "general"
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    INSURANCE = "insurance"
    EDUCATION = "education"
    LEGAL = "legal"
    GOVERNMENT = "government"
    CUSTOM = "custom"


class QuestionDifficulty(str, enum.Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ---------------------------------------------------------
# Reports
# ---------------------------------------------------------

class ReportType(str, enum.Enum):
    """Types of generated reports."""
    EXECUTIVE_SUMMARY = "executive_summary"
    HALLUCINATION = "hallucination"
    RETRIEVAL = "retrieval"
    LATENCY = "latency"
    SECURITY = "security"
    COST = "cost"
    AI_SAFETY = "ai_safety"
    FULL = "full"


class ReportFormat(str, enum.Enum):
    """Report export formats."""
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"


# ---------------------------------------------------------
# API Keys
# ---------------------------------------------------------

class ApiKeyPermission(str, enum.Enum):
    """API key permission scopes."""
    READ = "read"
    EVALUATE = "evaluate"
    ADMIN = "admin"


# ---------------------------------------------------------
# Audit
# ---------------------------------------------------------

class AuditAction(str, enum.Enum):
    """Auditable actions."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    EVALUATE = "evaluate"
    INVITE = "invite"
    REVOKE = "revoke"
    CONFIGURE = "configure"


# ---------------------------------------------------------
# Email
# ---------------------------------------------------------

class EmailProviderType(str, enum.Enum):
    """Email provider types."""
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    SES = "ses"
    RESEND = "resend"
