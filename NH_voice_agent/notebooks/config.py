# Databricks notebook source
"""
Configuration for NH Voice Agent
"""
import os

class Config:
    """Application configuration"""

    # Databricks Configuration
    DATABRICKS_HOST = os.getenv("DATABRICKS_HOST", "e2-demo-field-eng.cloud.databricks.com")
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

    # Unity Catalog
    UC_CATALOG = os.getenv("UC_CATALOG", "demo_ykko")
    UC_SCHEMA = os.getenv("UC_SCHEMA", "nh_voice_agent")
    UC_VOLUME = os.getenv("UC_VOLUME", "vol_data")

    @property
    def uc_full_path(self):
        return f"{self.UC_CATALOG}.{self.UC_SCHEMA}"

    @property
    def volume_path(self):
        return f"/Volumes/{self.UC_CATALOG}/{self.UC_SCHEMA}/{self.UC_VOLUME}"

    # Vector Search
    VECTOR_SEARCH_ENDPOINT = os.getenv("VECTOR_SEARCH_ENDPOINT", "one-env-shared-endpoint-11")
    VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", f"{UC_CATALOG}.{UC_SCHEMA}.doc_embed_index")

    # Knowledge Assistant
    KA_ENDPOINT_NAME = os.getenv("KA_ENDPOINT_NAME")
    KA_TILE_ID = os.getenv("KA_TILE_ID")

    # Genie Space
    GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID")
    SQL_WAREHOUSE_ID = os.getenv("SQL_WAREHOUSE_ID")

    # Models
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "databricks-qwen3-embedding-0-6b")
    LLM_MODEL = os.getenv("LLM_MODEL", "databricks-claude-sonnet-4-6")
    SERVING_ENDPOINT = os.getenv("SERVING_ENDPOINT", "databricks-claude-sonnet-4-6")

    # Application Settings
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Global config instance
config = Config()
