"""Unified Cache Manager orchestrating Static and Semantic cache layers."""

import logging
from typing import Optional, Tuple

from databricks.sdk import WorkspaceClient

from config import get_settings
from .models import CacheEntry, CacheSource
from .static_cache import StaticCache
from .semantic_cache import SemanticCache

logger = logging.getLogger(__name__)


class CacheManager:
    """Unified cache manager orchestrating static and semantic cache layers."""

    def __init__(self, workspace_client: Optional[WorkspaceClient] = None):
        """
        Initialize cache manager.

        Args:
            workspace_client: Databricks workspace client
        """
        self.settings = get_settings()
        self.w = workspace_client or WorkspaceClient()

        # Initialize cache layers
        self.static_cache = StaticCache(workspace_client=self.w)
        self.semantic_cache = SemanticCache(workspace_client=self.w)

    def get(
        self,
        normalized_question: str,
        original_question: str,
        use_semantic: bool = True,
        similarity_threshold: Optional[float] = None
    ) -> Tuple[Optional[CacheEntry], CacheSource]:
        """
        Get cache entry from static or semantic cache.

        Lookup order:
        1. Static cache (exact match)
        2. Semantic cache (similarity match) if use_semantic=True
        3. None (cache miss)

        Args:
            normalized_question: Normalized question for cache key
            original_question: Original user question
            use_semantic: Whether to check semantic cache on static miss
            similarity_threshold: Minimum similarity for semantic cache

        Returns:
            Tuple of (CacheEntry or None, CacheSource)
        """
        # Generate cache key
        cache_key = StaticCache.generate_cache_key(normalized_question)

        # 1. Try static cache (exact match)
        logger.info(f"Checking static cache for key: {cache_key[:16]}...")
        static_entry = self.static_cache.get(cache_key)

        if static_entry:
            logger.info(f"Static cache HIT (confidence: 1.0)")
            return static_entry, CacheSource.STATIC

        logger.info("Static cache MISS")

        # 2. Try semantic cache (similarity match)
        if use_semantic:
            logger.info(f"Checking semantic cache with threshold: {similarity_threshold or self.settings.semantic_similarity_threshold}")
            semantic_result = self.semantic_cache.get_best_match(
                normalized_question=normalized_question,
                similarity_threshold=similarity_threshold
            )

            if semantic_result:
                # Convert to CacheEntry
                entry = self.semantic_cache.convert_to_cache_entry(
                    semantic_result,
                    original_question
                )
                logger.info(
                    f"Semantic cache HIT (confidence: {entry.confidence_score:.3f})"
                )
                return entry, CacheSource.SEMANTIC

            logger.info("Semantic cache MISS")

        # 3. Cache miss
        logger.info("Cache MISS (both layers)")
        return None, CacheSource.NONE

    def set(self, entry: CacheEntry, update_both: bool = True) -> bool:
        """
        Store cache entry in both layers.

        Args:
            entry: Cache entry to store
            update_both: Whether to update both static and semantic cache

        Returns:
            True if at least one cache layer succeeded
        """
        success = False

        # Update static cache (always)
        logger.info(f"Storing to static cache: {entry.cache_key[:16]}...")
        static_success = self.static_cache.set(entry)
        if static_success:
            logger.info("Static cache updated successfully")
            success = True
        else:
            logger.error("Failed to update static cache")

        # Update semantic cache (if requested)
        if update_both:
            logger.info(f"Adding to semantic cache: {entry.cache_key[:16]}...")
            semantic_success = self.semantic_cache.add_entry(entry)
            if semantic_success:
                logger.info("Semantic cache updated successfully")
                success = True
            else:
                logger.error("Failed to update semantic cache")

        return success

    def invalidate(self, cache_key: str) -> bool:
        """
        Invalidate cache entry from static cache.

        Note: Semantic cache (Delta table) is eventually consistent.
        Manual invalidation requires deleting from Delta table and syncing index.

        Args:
            cache_key: Cache key to invalidate

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Invalidating cache key: {cache_key[:16]}...")
        return self.static_cache.invalidate(cache_key)

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from static cache.

        Returns:
            Number of entries deleted
        """
        logger.info("Cleaning up expired cache entries...")
        deleted_count = self.static_cache.cleanup_expired()
        logger.info(f"Cleaned up {deleted_count} expired entries")
        return deleted_count

    def get_stats(self) -> dict:
        """
        Get cache statistics from both layers.

        Returns:
            Dictionary with cache statistics
        """
        logger.info("Gathering cache statistics...")

        # Get static cache stats
        static_stats = self.static_cache.get_stats()

        # Get semantic cache (index) status
        semantic_status = self.semantic_cache.get_index_status()

        return {
            "static_cache": static_stats,
            "semantic_cache": {
                "index_name": semantic_status.get("name"),
                "index_state": semantic_status.get("state"),
                "pipeline_type": semantic_status.get("pipeline_type"),
                "source_table": semantic_status.get("source_table")
            }
        }

    def sync_semantic_index(self) -> bool:
        """
        Trigger Vector Search index sync for semantic cache.

        Only needed for TRIGGERED pipeline type.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Triggering semantic cache index sync...")
        return self.semantic_cache.sync_index()


# Global cache manager instance (singleton pattern)
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get or create cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
