"""Constants for Genie Cache Architecture."""

from typing import Final


class CacheConstants:
    """Cache-related constants."""

    # TTL (Time To Live)
    DEFAULT_TTL_SECONDS: Final[int] = 86400  # 24 hours

    # Similarity thresholds
    PRIMARY_SIMILARITY_THRESHOLD: Final[float] = 0.85
    SECONDARY_SIMILARITY_THRESHOLD: Final[float] = 0.75

    # Cache key
    CACHE_KEY_ALGORITHM: Final[str] = "sha256"


class RetryConstants:
    """Retry policy constants for Genie API."""

    # Retry configuration
    MAX_RETRIES: Final[int] = 5
    INITIAL_DELAY: Final[float] = 1.0  # seconds
    MAX_DELAY: Final[float] = 32.0  # seconds
    BACKOFF_MULTIPLIER: Final[float] = 2.0

    # HTTP status codes
    RATE_LIMIT_CODE: Final[int] = 429
    SERVER_ERROR_MIN: Final[int] = 500
    SERVER_ERROR_MAX: Final[int] = 600


class VectorSearchConstants:
    """Vector Search constants."""

    # Embedding model
    EMBEDDING_MODEL: Final[str] = "databricks-qwen3-embedding-0-6b"
    EMBEDDING_DIMENSION: Final[int] = 768

    # Index configuration
    PIPELINE_TYPE: Final[str] = "TRIGGERED"
    INDEX_TYPE: Final[str] = "DELTA_SYNC"

    # Query configuration
    DEFAULT_NUM_RESULTS: Final[int] = 5
    QUERY_TYPE_ANN: Final[str] = "ANN"


class DatabaseConstants:
    """Database-related constants."""

    # Table names
    CACHE_TABLE: Final[str] = "genie_query_cache"
    LOG_TABLE: Final[str] = "query_log"
    EMBEDDINGS_TABLE: Final[str] = "query_embeddings"

    # Connection
    DEFAULT_DATABASE: Final[str] = "databricks_postgres"
    SSL_MODE: Final[str] = "require"
