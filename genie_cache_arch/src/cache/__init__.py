"""Cache module with Static, Semantic, and unified Cache Manager."""

from .models import (
    CacheEntry,
    CacheSource,
    QueryMetrics,
    GenieQueryResult,
    NormalizerState,
    SemanticSearchResult
)
from .static_cache import StaticCache
from .semantic_cache import SemanticCache
from .cache_manager import CacheManager, get_cache_manager

__all__ = [
    # Models
    "CacheEntry",
    "CacheSource",
    "QueryMetrics",
    "GenieQueryResult",
    "NormalizerState",
    "SemanticSearchResult",
    # Cache layers
    "StaticCache",
    "SemanticCache",
    # Manager
    "CacheManager",
    "get_cache_manager"
]
