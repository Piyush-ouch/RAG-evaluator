"""
Evaluator Registry

Plugin system for evaluators. All evaluators self-register here.
The pipeline queries the registry to find which evaluators to run.
"""

from __future__ import annotations

from typing import Type

from app.evaluators.base import BaseEvaluator

# Global registry
_EVALUATOR_REGISTRY: dict[str, Type[BaseEvaluator]] = {}


def register_evaluator(evaluator_class: Type[BaseEvaluator]) -> Type[BaseEvaluator]:
    """
    Decorator to register an evaluator class.

    Usage:
        @register_evaluator
        class HallucinationDetector(BaseEvaluator):
            name = "hallucination"
            ...
    """
    _EVALUATOR_REGISTRY[evaluator_class.name] = evaluator_class
    return evaluator_class


def get_evaluator(name: str) -> BaseEvaluator:
    """Get an evaluator instance by name."""
    if name not in _EVALUATOR_REGISTRY:
        raise ValueError(f"Unknown evaluator: '{name}'. Available: {list(_EVALUATOR_REGISTRY.keys())}")
    return _EVALUATOR_REGISTRY[name]()


def get_all_evaluators() -> dict[str, Type[BaseEvaluator]]:
    """Get all registered evaluators."""
    return _EVALUATOR_REGISTRY.copy()


def list_evaluator_names() -> list[str]:
    """List all registered evaluator names."""
    return list(_EVALUATOR_REGISTRY.keys())
