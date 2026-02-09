"""Cached FAERS product comparison data loader."""
import json
from pathlib import Path

_CACHE_PATH = Path(__file__).parent.parent.parent / "analysis" / "results" / "faers_product_comparison.json"
_cache = None


def get_faers_comparison() -> dict:
    """Load cached FAERS product comparison data."""
    global _cache
    if _cache is None:
        with open(_CACHE_PATH) as f:
            _cache = json.load(f)
    return _cache
