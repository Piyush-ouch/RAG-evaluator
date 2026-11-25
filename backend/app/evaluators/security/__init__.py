"""
Security Evaluators Package

Imports all security evaluator modules so they self-register via the
@register_evaluator decorator when this package is imported.
"""

from app.evaluators.security.prompt_injection import PromptInjectionChecker
from app.evaluators.security.jailbreak import JailbreakChecker
from app.evaluators.security.pii_leakage import PIILeakageDetector
from app.evaluators.security.toxicity import ToxicityDetector
from app.evaluators.security.prompt_leakage import PromptLeakageDetector
from app.evaluators.security.secret_detection import SecretDetectionEvaluator
from app.evaluators.security.tool_misuse import ToolMisuseEvaluator
from app.evaluators.security.policy_compliance import PolicyComplianceEvaluator
from app.evaluators.security.role_escalation import RoleEscalationEvaluator
from app.evaluators.security.input_validation import InputValidationEvaluator
from app.evaluators.security.output_validation import OutputValidationEvaluator

__all__ = [
    "PromptInjectionChecker",
    "JailbreakChecker",
    "PIILeakageDetector",
    "ToxicityDetector",
    "PromptLeakageDetector",
    "SecretDetectionEvaluator",
    "ToolMisuseEvaluator",
    "PolicyComplianceEvaluator",
    "RoleEscalationEvaluator",
    "InputValidationEvaluator",
    "OutputValidationEvaluator",
]
