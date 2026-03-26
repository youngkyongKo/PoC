"""End-to-end query pipeline orchestrating normalization, caching, and Genie API."""

import logging
import time
from datetime import datetime
from typing import Optional, Tuple

from databricks.sdk import WorkspaceClient

from config import get_settings
from src.normalizer import (
    normalize_question,
    NormalizerState,
    simple_normalize_phase1,
    simple_normalize_phase2
)
from src.cache import get_cache_manager, CacheManager, CacheEntry, CacheSource
from src.cache.models import QueryMetrics, GenieQueryResult
from src.genie import get_genie_client, GenieClient

logger = logging.getLogger(__name__)


class QueryPipeline:
    """End-to-end query pipeline for Genie with caching."""

    def __init__(
        self,
        workspace_client: Optional[WorkspaceClient] = None,
        cache_manager: Optional[CacheManager] = None,
        genie_client: Optional[GenieClient] = None
    ):
        """
        Initialize query pipeline.

        Args:
            workspace_client: Databricks workspace client
            cache_manager: Cache manager instance
            genie_client: Genie client instance
        """
        self.settings = get_settings()
        self.w = workspace_client or WorkspaceClient()

        # Initialize components
        self.cache_manager = cache_manager or get_cache_manager()
        self.genie_client = genie_client or get_genie_client()

    def query(
        self,
        question: str,
        use_cache: bool = True,
        use_semantic: bool = True,
        similarity_threshold: Optional[float] = None
    ) -> Tuple[GenieQueryResult, QueryMetrics]:
        """
        Execute query through complete pipeline.

        Pipeline flow:
        1. Normalize question (LangGraph)
        2. Check static cache (exact match)
        3. Check semantic cache (similarity match)
        4. Call Genie API (with retry)
        5. Update both cache layers
        6. Return result + metrics

        Args:
            question: User's original question
            use_cache: Whether to use cache (True for production)
            use_semantic: Whether to use semantic cache on static miss
            similarity_threshold: Minimum similarity for semantic cache

        Returns:
            Tuple of (GenieQueryResult, QueryMetrics)
        """
        start_time = time.time()
        metrics = QueryMetrics(
            original_question=question,
            query_time=datetime.now()
        )

        logger.info(f"=" * 60)
        logger.info(f"Query Pipeline START: '{question}'")
        logger.info(f"=" * 60)

        try:
            # Multi-tier caching strategy:
            # L0: Simple normalization Phase 1 (basic cleanup) - 1ms
            # L1: Simple normalization Phase 2 (morpheme) - 11ms
            # L2: LLM normalization + semantic search - 200ms+
            # L3: Genie API - 5s+

            cache_entry = None
            cache_source = CacheSource.NONE
            normalized_question = question
            normalization_method = "none"

            if use_cache:
                # L0: Try Phase 1 simple normalization (basic cleanup)
                logger.info("[1/5] L0: Simple normalization Phase 1 (~1ms)...")
                phase1_normalized = simple_normalize_phase1(question)
                logger.info(f"  Phase 1: '{question}' -> '{phase1_normalized}'")

                cache_key_phase1 = self.cache_manager.static_cache.generate_cache_key(phase1_normalized)
                cache_entry = self.cache_manager.static_cache.get(cache_key_phase1)

                if cache_entry:
                    logger.info("  ✓ L0 Static cache HIT (Phase 1)")
                    normalized_question = phase1_normalized
                    normalization_method = "phase1"
                    metrics.static_cache_hit = True
                    cache_source = CacheSource.STATIC
                else:
                    logger.info("  ✗ L0 Cache MISS")

                    # L1: Try Phase 2 simple normalization (morpheme-based)
                    logger.info("[2/5] L1: Simple normalization Phase 2 (~11ms)...")
                    phase2_normalized = simple_normalize_phase2(question)
                    logger.info(f"  Phase 2: '{question}' -> '{phase2_normalized}'")

                    cache_key_phase2 = self.cache_manager.static_cache.generate_cache_key(phase2_normalized)
                    cache_entry = self.cache_manager.static_cache.get(cache_key_phase2)

                    if cache_entry:
                        logger.info("  ✓ L1 Static cache HIT (Phase 2)")
                        normalized_question = phase2_normalized
                        normalization_method = "phase2"
                        metrics.static_cache_hit = True
                        cache_source = CacheSource.STATIC
                    else:
                        logger.info("  ✗ L1 Cache MISS")

                        # L2: Try LLM normalization + semantic cache
                        logger.info("[3/5] L2: LLM normalization (~200ms)...")
                        normalizer_state = normalize_question(question)
                        llm_normalized = normalizer_state.normalized_question or question
                        logger.info(f"  LLM: '{question}' -> '{llm_normalized}'")

                        # Check static cache with LLM normalized key
                        cache_key_llm = self.cache_manager.static_cache.generate_cache_key(llm_normalized)
                        cache_entry = self.cache_manager.static_cache.get(cache_key_llm)

                        if cache_entry:
                            logger.info("  ✓ L2 Static cache HIT (LLM normalized)")
                            normalized_question = llm_normalized
                            normalization_method = "llm"
                            metrics.static_cache_hit = True
                            cache_source = CacheSource.STATIC
                        else:
                            logger.info("  ✗ L2 Static cache MISS")

                            # Try semantic cache
                            if use_semantic:
                                logger.info("  Checking semantic cache...")
                                cache_entry, cache_source = self.cache_manager.get(
                                    normalized_question=llm_normalized,
                                    original_question=question,
                                    use_semantic=True,
                                    similarity_threshold=similarity_threshold
                                )

                                if cache_source == CacheSource.SEMANTIC:
                                    logger.info(f"  ✓ L2 Semantic cache HIT (similarity: {cache_entry.confidence_score:.3f})")
                                    normalized_question = llm_normalized
                                    normalization_method = "llm"
                                    metrics.semantic_cache_hit = True
                                    metrics.similarity_score = cache_entry.confidence_score
                                else:
                                    logger.info("  ✗ L2 Semantic cache MISS")
                                    normalized_question = llm_normalized
                                    normalization_method = "llm"
            else:
                # No cache - use LLM normalization directly
                logger.info("[1/5] Normalizing question (LLM)...")
                normalizer_state = normalize_question(question)
                normalized_question = normalizer_state.normalized_question or question
                normalization_method = "llm"

            metrics.normalized_question = normalized_question
            logger.info(f"  Final normalized: '{normalized_question}' (method: {normalization_method})")

            # L3: Call Genie API if cache miss
            if cache_entry is None:
                logger.info("[4/5] L3: Calling Genie API (~5s)...")
                metrics.genie_api_called = True

                # Call Genie with normalized question
                genie_result = self.genie_client.ask(
                    question=normalized_question,
                    timeout_seconds=120
                )

                if not genie_result.success:
                    logger.error(f"  ✗ Genie API failed: {genie_result.error}")
                    metrics.error_message = genie_result.error
                    response_time = int((time.time() - start_time) * 1000)
                    metrics.response_time_ms = response_time
                    return genie_result, metrics

                logger.info(f"  ✓ Genie API success: {genie_result.row_count} rows")

                # Step 5: Update cache with new result
                logger.info("[5/5] Updating cache layers...")
                cache_entry = CacheEntry(
                    cache_key=self.cache_manager.static_cache.generate_cache_key(normalized_question),
                    original_question=question,
                    normalized_question=normalized_question,
                    genie_sql=genie_result.sql,
                    genie_result={
                        "columns": genie_result.columns,
                        "data": genie_result.data,
                        "row_count": genie_result.row_count,
                        "text_response": genie_result.text_response
                    },
                    genie_description=genie_result.description,
                    conversation_id=genie_result.conversation_id,
                    created_at=datetime.now(),
                    accessed_at=datetime.now(),
                    access_count=1,
                    ttl_seconds=self.settings.static_cache_ttl_seconds,
                    confidence_score=1.0,  # Exact match for new entry
                    source=CacheSource.STATIC
                )

                # Store in both cache layers
                success = self.cache_manager.set(cache_entry, update_both=True)
                if success:
                    logger.info("  ✓ Cache updated successfully")
                else:
                    logger.error("  ✗ Cache update failed")

            else:
                # Use cached result
                logger.info("[3/5] Using cached result...")
                genie_result = GenieQueryResult(
                    question=question,
                    conversation_id=cache_entry.conversation_id,
                    status="COMPLETED",
                    sql=cache_entry.genie_sql,
                    description=cache_entry.genie_description,
                    columns=cache_entry.genie_result.get("columns") if cache_entry.genie_result else None,
                    data=cache_entry.genie_result.get("data") if cache_entry.genie_result else None,
                    row_count=cache_entry.genie_result.get("row_count", 0) if cache_entry.genie_result else 0,
                    text_response=cache_entry.genie_result.get("text_response") if cache_entry.genie_result else None
                )

            # Calculate response time
            response_time = int((time.time() - start_time) * 1000)
            metrics.response_time_ms = response_time

            logger.info("[5/5] Query complete!")
            logger.info(f"  Response time: {response_time}ms")
            logger.info(f"  Cache hit: {metrics.cache_hit} (source: {metrics.cache_source.value})")
            logger.info(f"  Genie API called: {metrics.genie_api_called}")
            logger.info("=" * 60)

            return genie_result, metrics

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            metrics.error_message = str(e)
            response_time = int((time.time() - start_time) * 1000)
            metrics.response_time_ms = response_time

            # Return error result
            error_result = GenieQueryResult(
                question=question,
                status="FAILED",
                error=str(e)
            )

            return error_result, metrics

    def query_followup(
        self,
        question: str,
        conversation_id: str
    ) -> Tuple[GenieQueryResult, QueryMetrics]:
        """
        Execute follow-up query (no caching).

        Follow-up queries are context-dependent and not cached.

        Args:
            question: Follow-up question
            conversation_id: Conversation ID from previous query

        Returns:
            Tuple of (GenieQueryResult, QueryMetrics)
        """
        start_time = time.time()
        metrics = QueryMetrics(
            original_question=question,
            query_time=datetime.now(),
            genie_api_called=True
        )

        logger.info(f"Follow-up query: '{question}' (conversation: {conversation_id[:16]}...)")

        try:
            # Call Genie API
            genie_result = self.genie_client.ask_followup(
                question=question,
                conversation_id=conversation_id,
                timeout_seconds=120
            )

            # Calculate response time
            response_time = int((time.time() - start_time) * 1000)
            metrics.response_time_ms = response_time

            if not genie_result.success:
                metrics.error_message = genie_result.error

            logger.info(f"Follow-up complete: {response_time}ms")

            return genie_result, metrics

        except Exception as e:
            logger.error(f"Follow-up error: {e}", exc_info=True)
            metrics.error_message = str(e)
            response_time = int((time.time() - start_time) * 1000)
            metrics.response_time_ms = response_time

            # Return error result
            error_result = GenieQueryResult(
                question=question,
                conversation_id=conversation_id,
                status="FAILED",
                error=str(e)
            )

            return error_result, metrics


# Global pipeline instance (singleton pattern)
_pipeline = None


def get_pipeline() -> QueryPipeline:
    """Get or create pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = QueryPipeline()
    return _pipeline
