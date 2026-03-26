"""Settings management without pydantic dependency."""

import os
from functools import lru_cache
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Databricks
        self.databricks_host: str = os.getenv(
            "DATABRICKS_HOST",
            "e2-demo-field-eng.cloud.databricks.com"
        )
        self.databricks_token: Optional[str] = os.getenv("DATABRICKS_TOKEN")

        # Genie
        self.genie_space_id: str = os.getenv(
            "GENIE_SPACE_ID",
            "01f1115dc00f1fd7809cb280333f7fb2"
        )

        # Model Serving Endpoint (for LLM normalization)
        self.serving_endpoint_name: str = os.getenv(
            "SERVING_ENDPOINT_NAME",
            "databricks-gpt-5-4"
        )

        # Vector Search
        self.vector_search_endpoint: str = os.getenv(
            "VECTOR_SEARCH_ENDPOINT",
            "one-env-shared-endpoint-11"
        )
        self.vector_search_index: str = os.getenv(
            "VECTOR_SEARCH_INDEX",
            "demo_ykko.genie_cache.semantic_cache_index"
        )

        # Lakebase (Autoscale)
        self.lakebase_project_name: str = os.getenv(
            "LAKEBASE_PROJECT_NAME",
            "ykko-genie-cache-db"
        )
        self.lakebase_branch: str = os.getenv(
            "LAKEBASE_BRANCH",
            "production"
        )
        self.lakebase_endpoint: str = os.getenv(
            "LAKEBASE_ENDPOINT",
            "primary"
        )
        self.lakebase_schema: str = os.getenv(
            "LAKEBASE_SCHEMA",
            "geniecache"
        )
        self.lakebase_host: Optional[str] = os.getenv("LAKEBASE_HOST")
        self.lakebase_port: int = int(os.getenv("LAKEBASE_PORT", "5432"))
        self.lakebase_user: Optional[str] = os.getenv("LAKEBASE_USER")

        # Cache Configuration
        self.static_cache_ttl_seconds: int = int(os.getenv(
            "STATIC_CACHE_TTL_SECONDS",
            "86400"
        ))
        self.semantic_similarity_threshold: float = float(os.getenv(
            "SEMANTIC_SIMILARITY_THRESHOLD",
            "0.85"
        ))
        self.semantic_similarity_secondary_threshold: float = float(os.getenv(
            "SEMANTIC_SIMILARITY_SECONDARY_THRESHOLD",
            "0.75"
        ))

        # Retry Configuration
        self.genie_max_retries: int = int(os.getenv("GENIE_MAX_RETRIES", "5"))
        self.genie_initial_delay: float = float(os.getenv("GENIE_INITIAL_DELAY", "1.0"))
        self.genie_max_delay: float = float(os.getenv("GENIE_MAX_DELAY", "32.0"))
        self.genie_backoff_multiplier: float = float(os.getenv("GENIE_BACKOFF_MULTIPLIER", "2.0"))

        # Unity Catalog
        self.uc_catalog: str = os.getenv("UC_CATALOG", "demo_ykko")
        self.uc_schema: str = os.getenv("UC_SCHEMA", "genie_cache")

    def get_lakebase_project_resource_name(self) -> str:
        """Get the Lakebase project resource name."""
        return f"projects/{self.lakebase_project_name}"

    def get_lakebase_branch_resource_name(self) -> str:
        """Get the Lakebase branch resource name."""
        return f"{self.get_lakebase_project_resource_name()}/branches/{self.lakebase_branch}"

    def get_lakebase_endpoint_resource_name(self) -> str:
        """Get the Lakebase endpoint resource name."""
        return f"{self.get_lakebase_branch_resource_name()}/endpoints/{self.lakebase_endpoint}"

    def get_full_table_name(self, table_name: str) -> str:
        """Get fully qualified table name."""
        return f"{self.uc_catalog}.{self.uc_schema}.{table_name}"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
