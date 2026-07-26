"""
Quality Evaluators Package

Imports all quality evaluator modules so they self-register via the
@register_evaluator decorator when this package is imported.
"""

from app.evaluators.quality.correctness import CorrectnessEvaluator
from app.evaluators.quality.faithfulness import FaithfulnessEvaluator
from app.evaluators.quality.hallucination import HallucinationDetector
from app.evaluators.quality.context_precision import ContextPrecisionEvaluator
from app.evaluators.quality.context_recall import ContextRecallEvaluator
from app.evaluators.quality.groundedness import GroundednessEvaluator
from app.evaluators.quality.citation_quality import CitationQualityEvaluator
from app.evaluators.quality.bias import BiasEvaluator

__all__ = [
    "CorrectnessEvaluator",
    "FaithfulnessEvaluator",
    "HallucinationDetector",
    "ContextPrecisionEvaluator",
    "ContextRecallEvaluator",
    "GroundednessEvaluator",
    "CitationQualityEvaluator",
    "BiasEvaluator",
]
