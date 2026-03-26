"""Static Cache Layer using Lakebase PostgreSQL."""

import hashlib
import json
import logging
from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from databricks.sdk import WorkspaceClient

from config import get_settings
from .models import CacheEntry, CacheSource

logger = logging.getLogger(__name__)


class StaticCache:
    """Static cache using Lakebase PostgreSQL for exact match queries."""

    def __init__(self, workspace_client: Optional[WorkspaceClient] = None):
        """
        Initialize static cache.

        Args:
            workspace_client: Databricks workspace client (for token generation)
        """
        self.settings = get_settings()
        self.w = workspace_client or WorkspaceClient()
        self._connection = None

    def _get_connection(self) -> psycopg2.extensions.connection:
        """Get or create database connection with fresh token."""
        # Generate new token for each connection (tokens expire after 1 hour)
        cred = self.w.postgres.generate_database_credential(
            endpoint=self.settings.get_lakebase_endpoint_name()
        )

        # Get current user
        current_user = self.w.current_user.me()

        # Create connection
        conn = psycopg2.connect(
            host=self.settings.lakebase_host,
            port=self.settings.lakebase_port,
            dbname=self.settings.lakebase_database,
            user=current_user.user_name,
            password=cred.token,
            sslmode="require"
        )

        return conn

    @staticmethod
    def generate_cache_key(normalized_question: str) -> str:
        """
        Generate deterministic cache key from normalized question.

        Args:
            normalized_question: Normalized question

        Returns:
            SHA256 hash as hex string
        """
        return hashlib.sha256(normalized_question.encode('utf-8')).hexdigest()

    def get(self, cache_key: str) -> Optional[CacheEntry]:
        """
        Retrieve cache entry by key.

        Args:
            cache_key: Cache key (SHA256 hash)

        Returns:
            CacheEntry if found and not expired, None otherwise
        """
        conn = None
        try:
            conn = self._get_connection()

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if entry exists and not expired
                cur.execute("""
                    SELECT *
                    FROM genie_query_cache
                    WHERE cache_key = %s
                    AND (created_at + (ttl_seconds || ' seconds')::INTERVAL) > NOW()
                """, (cache_key,))

                row = cur.fetchone()

                if row:
                    # Update access statistics
                    self._update_access(conn, cache_key)

                    # Convert to CacheEntry
                    entry = CacheEntry(
                        cache_key=row['cache_key'],
                        original_question=row['original_question'],
                        normalized_question=row['normalized_question'],
                        genie_sql=row['genie_sql'],
                        genie_result=row['genie_result'],
                        genie_description=row['genie_description'],
                        conversation_id=row['conversation_id'],
                        created_at=row['created_at'],
                        accessed_at=row['accessed_at'],
                        access_count=row['access_count'],
                        ttl_seconds=row['ttl_seconds'],
                        confidence_score=1.0,  # Exact match
                        source=CacheSource.STATIC
                    )

                    logger.info(f"Static cache HIT for key: {cache_key[:16]}...")
                    return entry

                logger.info(f"Static cache MISS for key: {cache_key[:16]}...")
                return None

        except Exception as e:
            logger.error(f"Error retrieving from static cache: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def set(self, entry: CacheEntry) -> bool:
        """
        Store cache entry.

        Args:
            entry: Cache entry to store

        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = self._get_connection()

            with conn.cursor() as cur:
                # Upsert cache entry
                cur.execute("""
                    INSERT INTO genie_query_cache (
                        cache_key,
                        original_question,
                        normalized_question,
                        genie_sql,
                        genie_result,
                        genie_description,
                        conversation_id,
                        created_at,
                        accessed_at,
                        access_count,
                        ttl_seconds
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (cache_key) DO UPDATE SET
                        accessed_at = EXCLUDED.accessed_at,
                        access_count = genie_query_cache.access_count + 1,
                        genie_result = EXCLUDED.genie_result,
                        genie_sql = EXCLUDED.genie_sql,
                        genie_description = EXCLUDED.genie_description
                """, (
                    entry.cache_key,
                    entry.original_question,
                    entry.normalized_question,
                    entry.genie_sql,
                    json.dumps(entry.genie_result) if entry.genie_result else None,
                    entry.genie_description,
                    entry.conversation_id,
                    entry.created_at,
                    entry.accessed_at,
                    entry.access_count,
                    entry.ttl_seconds
                ))

                conn.commit()
                logger.info(f"Stored entry in static cache: {entry.cache_key[:16]}...")
                return True

        except Exception as e:
            logger.error(f"Error storing to static cache: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def invalidate(self, cache_key: str) -> bool:
        """
        Remove cache entry by key.

        Args:
            cache_key: Cache key to invalidate

        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = self._get_connection()

            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM genie_query_cache
                    WHERE cache_key = %s
                """, (cache_key,))

                deleted_count = cur.rowcount
                conn.commit()

                if deleted_count > 0:
                    logger.info(f"Invalidated cache key: {cache_key[:16]}...")
                    return True
                else:
                    logger.warning(f"Cache key not found: {cache_key[:16]}...")
                    return False

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.

        Returns:
            Number of entries deleted
        """
        conn = None
        try:
            conn = self._get_connection()

            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM genie_query_cache
                    WHERE (created_at + (ttl_seconds || ' seconds')::INTERVAL) < NOW()
                """)

                deleted_count = cur.rowcount
                conn.commit()

                logger.info(f"Cleaned up {deleted_count} expired cache entries")
                return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                conn.close()

    def _update_access(self, conn: psycopg2.extensions.connection, cache_key: str):
        """
        Update access statistics for cache entry.

        Args:
            conn: Database connection
            cache_key: Cache key
        """
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE genie_query_cache
                    SET accessed_at = NOW(),
                        access_count = access_count + 1
                    WHERE cache_key = %s
                """, (cache_key,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating access statistics: {e}")
            conn.rollback()

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        conn = None
        try:
            conn = self._get_connection()

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Total entries
                cur.execute("SELECT COUNT(*) as total FROM genie_query_cache")
                total = cur.fetchone()['total']

                # Expired entries
                cur.execute("""
                    SELECT COUNT(*) as expired
                    FROM genie_query_cache
                    WHERE (created_at + (ttl_seconds || ' seconds')::INTERVAL) < NOW()
                """)
                expired = cur.fetchone()['expired']

                # Most accessed
                cur.execute("""
                    SELECT normalized_question, access_count
                    FROM genie_query_cache
                    ORDER BY access_count DESC
                    LIMIT 5
                """)
                top_queries = cur.fetchall()

                return {
                    "total_entries": total,
                    "expired_entries": expired,
                    "active_entries": total - expired,
                    "top_queries": [dict(q) for q in top_queries]
                }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
        finally:
            if conn:
                conn.close()
