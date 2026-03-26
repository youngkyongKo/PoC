"""
Configuration management for NH Voice Agent
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
project_root = Path(__file__).parent
env_file = project_root / ".env"
load_dotenv(env_file)

class Config:
    """Application configuration"""

    # Project paths
    BASE_DIR = project_root
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"

    # Databricks Configuration
    DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

    # Unity Catalog
    UC_CATALOG = os.getenv("UC_CATALOG", "demo_ykko")
    UC_SCHEMA = os.getenv("UC_SCHEMA", "nh_voice_agent")
    UC_VOLUME = os.getenv("UC_VOLUME", "vol_data")

    @property
    def uc_full_path(self):
        """Get full Unity Catalog path"""
        return f"{self.UC_CATALOG}.{self.UC_SCHEMA}"

    @property
    def volume_path(self):
        """Get volume path"""
        return f"/Volumes/{self.UC_CATALOG}/{self.UC_SCHEMA}/{self.UC_VOLUME}"

    # Vector Search Configuration
    VECTOR_SEARCH_ENDPOINT = os.getenv("VECTOR_SEARCH_ENDPOINT", "one-env-shared-endpoint-11")
    VECTOR_INDEX_NAME = os.getenv(
        "VECTOR_INDEX_NAME",
        f"{UC_CATALOG}.{UC_SCHEMA}.doc_embed_index"
    )

    # Knowledge Assistant Configuration
    KA_ENDPOINT_NAME = os.getenv("KA_ENDPOINT_NAME")
    KA_TILE_ID = os.getenv("KA_TILE_ID")

    # Genie Space Configuration
    GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID")
    SQL_WAREHOUSE_ID = os.getenv("SQL_WAREHOUSE_ID")

    # Model Configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "databricks-qwen3-embedding-0-6b")
    LLM_MODEL = os.getenv("LLM_MODEL", "databricks-claude-sonnet-4-6")
    SERVING_ENDPOINT = os.getenv("SERVING_ENDPOINT", "databricks-claude-sonnet-4-6")

    # Voice Configuration
    SPEECH_LANGUAGE = os.getenv("SPEECH_LANGUAGE", "ko-KR")
    TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "ko")

    # Edge TTS Configuration (Microsoft Neural TTS - Free & High Quality)
    TTS_VOICE_NAME = os.getenv("TTS_VOICE_NAME", "ko-KR-SunHiNeural")
    TTS_SPEAKING_RATE = os.getenv("TTS_SPEAKING_RATE", "+20%")
    TTS_PITCH = os.getenv("TTS_PITCH", "+5Hz")
    AUDIO_SAMPLE_RATE = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))

    # Application Settings
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    def validate(self):
        """Validate required configuration"""
        required = [
            "DATABRICKS_HOST",
            "DATABRICKS_TOKEN",
        ]

        missing = [key for key in required if not getattr(self, key)]

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        return True


# Global config instance
config = Config()


if __name__ == "__main__":
    # Test configuration
    try:
        config.validate()
        print("✓ Configuration validated successfully!")
        print(f"  Unity Catalog Path: {config.uc_full_path}")
        print(f"  Volume Path: {config.volume_path}")
        print(f"  Vector Index: {config.VECTOR_INDEX_NAME}")
        print(f"  Genie Space ID: {config.GENIE_SPACE_ID}")
        print(f"  KA Endpoint: {config.KA_ENDPOINT_NAME}")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
