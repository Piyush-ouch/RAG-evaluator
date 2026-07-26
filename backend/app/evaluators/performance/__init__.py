"""
Performance Evaluators Package

Imports all performance evaluator modules so they self-register via the
@register_evaluator decorator when this package is imported.
"""

from app.evaluators.performance.latency import LatencyEvaluator
from app.evaluators.performance.cost import CostEvaluator

__all__ = [
    "LatencyEvaluator",
    "CostEvaluator",
]
