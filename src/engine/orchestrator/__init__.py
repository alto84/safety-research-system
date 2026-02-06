"""
Multi-model orchestration layer.

Routes queries to optimal foundation models, normalizes heterogeneous
outputs, and ensembles predictions with calibrated uncertainty.
"""

from src.engine.orchestrator.router import PromptRouter
from src.engine.orchestrator.normalizer import ResponseNormalizer
from src.engine.orchestrator.ensemble import EnsembleAggregator
from src.engine.orchestrator.gateway import SecureAPIGateway

__all__ = [
    "PromptRouter",
    "ResponseNormalizer",
    "EnsembleAggregator",
    "SecureAPIGateway",
]
