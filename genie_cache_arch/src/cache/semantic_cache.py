"""Semantic Cache Layer using Databricks Vector Search."""

import json
import logging
from datetime import datetime
from typing import List, Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.catalog import TableInfo

from config import get_settings
from .models import CacheEntry, SemanticSearchResult, CacheSource

logger = logging.getLogger(__name__)


class SemanticCache:
    """Semantic cache using Vector Search for similarity matching."""

    def __init__(self, workspace_client: Optional[WorkspaceClient] = None):
        """
        Initialize semantic cache.

        Args:
            workspace_client: Databricks workspace client
        """
        self.settings = get_settings()
        self.w = workspace_client or WorkspaceClient()

    def search(
        self,
        normalized_question: str,
        num_results: int = 5,
        similarity_threshold: Optional[float] = None
    ) -> List[SemanticSearchResult]:
        """
        Search for similar questions using Vector Search.

        Args:
            normalized_question: Normalized question text
            num_results: Number of results to return
            similarity_threshold: Minimum similarity score (default: primary threshold)

        Returns:
            List of SemanticSearchResult objects sorted by similarity
        """
        threshold = similarity_threshold or self.settings.semantic_similarity_threshold

        try:
            # Query Vector Search index
            results = self.w.vector_search_indexes.query_index(
                index_name=self.settings.vector_search_index,
                columns=["cache_key", "normalized_question", "genie_sql",
                        "genie_result", "conversation_id", "created_at"],
                query_text=normalized_question,
                num_results=num_results
            )

            # Parse results
            search_results = []
            if results.result and results.result.data_array:
                for row in results.result.data_array:
                    # Vector Search returns: [columns..., similarity_score]
                    similarity_score = float(row[-1])

                    # Filter by threshold
                    if similarity_score < threshold:
                        continue

                    # Parse result fields
                    cache_key = row[0]
                    norm_question = row[1]
                    genie_sql = row[2]
                    genie_result_json = row[3]
                    conversation_id = row[4]
                    created_at_str = row[5]

                    # Parse genie_result JSON
                    genie_result = None
                    if genie_result_json:
                        try:
                            genie_result = json.loads(genie_result_json)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse genie_result JSON for key: {cache_key}")

                    # Parse created_at timestamp
                    created_at = None
                    if created_at_str:
                        try:
                            created_at = datetime.fromisoformat(created_at_str)
                        except (ValueError, TypeError):
                            logger.warning(f"Failed to parse created_at for key: {cache_key}")

                    search_results.append(
                        SemanticSearchResult(
                            cache_key=cache_key,
                            normalized_question=norm_question,
                            similarity_score=similarity_score,
                            genie_result=genie_result,
                            genie_sql=genie_sql,
                            conversation_id=conversation_id,
                            created_at=created_at
                        )
                    )

            logger.info(
                f"Semantic search found {len(search_results)} results "
                f"above threshold {threshold:.2f}"
            )
            return search_results

        except Exception as e:
            logger.error(f"Error searching semantic cache: {e}")
            return []

    def get_best_match(
        self,
        normalized_question: str,
        similarity_threshold: Optional[float] = None
    ) -> Optional[SemanticSearchResult]:
        """
        Get best matching cache entry above similarity threshold.

        Args:
            normalized_question: Normalized question text
            similarity_threshold: Minimum similarity score (default: primary threshold)

        Returns:
            Best matching SemanticSearchResult or None
        """
        results = self.search(
            normalized_question=normalized_question,
            num_results=1,
            similarity_threshold=similarity_threshold
        )

        if results:
            best_match = results[0]
            logger.info(
                f"Semantic cache HIT: similarity={best_match.similarity_score:.3f}, "
                f"question='{best_match.normalized_question[:50]}...'"
            )
            return best_match
        else:
            logger.info("Semantic cache MISS")
            return None

    def add_entry(self, entry: CacheEntry) -> bool:
        """
        Add cache entry to Delta table (will be synced to Vector Search).

        Args:
            entry: Cache entry to add

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get warehouse for SQL execution
            warehouses = list(self.w.warehouses.list())
            warehouse = next(
                (wh for wh in warehouses if wh.state.value == "RUNNING"),
                next(iter(warehouses), None)
            )

            if not warehouse:
                logger.error("No SQL warehouse available")
                return False

            embeddings_table = self.settings.get_full_table_name("query_embeddings")

            # Prepare SQL for MERGE (upsert)
            # Note: genie_result is stored as JSON string
            genie_result_json = json.dumps(entry.genie_result) if entry.genie_result else None

            sql = f"""
            MERGE INTO {embeddings_table} AS target
            USING (
                SELECT
                    '{entry.cache_key}' AS cache_key,
                    '{entry.normalized_question.replace("'", "''")}' AS normalized_question,
                    {'NULL' if entry.genie_sql is None else f"'{entry.genie_sql.replace("'", "''")}'"} AS genie_sql,
                    {'NULL' if genie_result_json is None else f"'{genie_result_json.replace("'", "''")}'"} AS genie_result,
                    {'NULL' if entry.conversation_id is None else f"'{entry.conversation_id}'"} AS conversation_id,
                    TIMESTAMP '{entry.created_at.isoformat()}' AS created_at
            ) AS source
            ON target.cache_key = source.cache_key
            WHEN MATCHED THEN
                UPDATE SET
                    normalized_question = source.normalized_question,
                    genie_sql = source.genie_sql,
                    genie_result = source.genie_result,
                    conversation_id = source.conversation_id,
                    created_at = source.created_at
            WHEN NOT MATCHED THEN
                INSERT (cache_key, normalized_question, genie_sql, genie_result, conversation_id, created_at)
                VALUES (source.cache_key, source.normalized_question, source.genie_sql,
                       source.genie_result, source.conversation_id, source.created_at)
            """

            # Execute SQL
            self.w.statement_execution.execute_statement(
                warehouse_id=warehouse.id,
                statement=sql,
                wait_timeout="30s"
            )

            logger.info(f"Added entry to semantic cache: {entry.cache_key[:16]}...")
            return True

        except Exception as e:
            logger.error(f"Error adding entry to semantic cache: {e}")
            return False

    def sync_index(self) -> bool:
        """
        Trigger Vector Search index sync (for TRIGGERED pipeline type).

        Returns:
            True if successful, False otherwise
        """
        try:
            self.w.vector_search_indexes.sync_index(
                index_name=self.settings.vector_search_index
            )
            logger.info(f"Triggered Vector Search index sync: {self.settings.vector_search_index}")
            return True

        except Exception as e:
            logger.error(f"Error syncing Vector Search index: {e}")
            return False

    def get_index_status(self) -> dict:
        """
        Get Vector Search index status.

        Returns:
            Dictionary with index status information
        """
        try:
            index = self.w.vector_search_indexes.get_index(
                index_name=self.settings.vector_search_index
            )

            return {
                "name": index.name,
                "index_type": index.index_type.value if index.index_type else None,
                "primary_key": index.primary_key,
                "state": "ONLINE" if index.status and index.status.ready else "NOT_READY",
                "source_table": (
                    index.delta_sync_index_spec.source_table
                    if index.delta_sync_index_spec else None
                ),
                "pipeline_type": (
                    index.delta_sync_index_spec.pipeline_type.value
                    if index.delta_sync_index_spec and index.delta_sync_index_spec.pipeline_type
                    else None
                )
            }

        except Exception as e:
            logger.error(f"Error getting index status: {e}")
            return {}

    def convert_to_cache_entry(
        self,
        search_result: SemanticSearchResult,
        original_question: str
    ) -> CacheEntry:
        """
        Convert SemanticSearchResult to CacheEntry.

        Args:
            search_result: Search result from Vector Search
            original_question: Original user question

        Returns:
            CacheEntry with semantic cache metadata
        """
        return CacheEntry(
            cache_key=search_result.cache_key,
            original_question=original_question,
            normalized_question=search_result.normalized_question,
            genie_sql=search_result.genie_sql,
            genie_result=search_result.genie_result,
            conversation_id=search_result.conversation_id,
            created_at=search_result.created_at or datetime.now(),
            accessed_at=datetime.now(),
            access_count=1,
            ttl_seconds=self.settings.static_cache_ttl_seconds,
            confidence_score=search_result.similarity_score,
            source=CacheSource.SEMANTIC
        )
