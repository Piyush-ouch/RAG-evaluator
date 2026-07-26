"""
Evaluators Package

Auto-imports all evaluator subpackages so evaluators self-register.
"""

# Import all evaluator subpackages to trigger registration
import app.evaluators.quality  # noqa: F401
import app.evaluators.security  # noqa: F401
import app.evaluators.performance  # noqa: F401
