"""
Vector Search 인덱스 생성
청크된 문서를 임베딩하여 Vector Search 인덱스 생성
"""
import sys
from pathlib import Path
from typing import List, Dict
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from databricks.sdk import WorkspaceClient
from config import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class VectorIndexBuilder:
    """Vector Search 인덱스 생성 클래스"""

    def __init__(self):
        self.client = WorkspaceClient(
            host=config.DATABRICKS_HOST,
            token=config.DATABRICKS_TOKEN
        )

    def create_vector_search_endpoint(self, endpoint_name: str = None):
        """
        Vector Search 엔드포인트 생성

        Args:
            endpoint_name: 엔드포인트 이름
        """
        if endpoint_name is None:
            endpoint_name = config.VECTOR_SEARCH_ENDPOINT

        try:
            # Check if endpoint exists
            try:
                endpoint = self.client.vector_search_endpoints.get_endpoint(endpoint_name)
                logger.info(f"Endpoint '{endpoint_name}' already exists")
                return endpoint
            except:
                pass

            # Create endpoint
            logger.info(f"Creating Vector Search endpoint: {endpoint_name}")
            endpoint = self.client.vector_search_endpoints.create_endpoint(
                name=endpoint_name,
                endpoint_type="STANDARD"
            )

            logger.info(f"Endpoint created: {endpoint_name}")
            return endpoint

        except Exception as e:
            logger.error(f"Error creating endpoint: {e}")
            raise

    def create_delta_sync_index(
        self,
        source_table: str,
        index_name: str = None,
        endpoint_name: str = None,
        embedding_source_column: str = "text",
        primary_key: str = "chunk_id"
    ):
        """
        Delta Sync Vector Index 생성

        Args:
            source_table: 소스 Delta Table (catalog.schema.table)
            index_name: 인덱스 이름
            endpoint_name: Vector Search 엔드포인트
            embedding_source_column: 임베딩할 텍스트 컬럼
            primary_key: Primary key 컬럼
        """
        if index_name is None:
            index_name = config.VECTOR_INDEX_NAME

        if endpoint_name is None:
            endpoint_name = config.VECTOR_SEARCH_ENDPOINT

        try:
            logger.info(f"Creating Vector Index: {index_name}")

            # Create index configuration
            index_config = {
                "name": index_name,
                "endpoint_name": endpoint_name,
                "primary_key": primary_key,
                "index_type": "DELTA_SYNC",
                "delta_sync_index_spec": {
                    "source_table": source_table,
                    "embedding_source_columns": [
                        {
                            "name": embedding_source_column,
                            "embedding_model_endpoint_name": config.EMBEDDING_MODEL
                        }
                    ],
                    "pipeline_type": "TRIGGERED"
                }
            }

            # TODO: Implement using Databricks SDK
            # Currently the Python SDK doesn't have full vector search support
            # Use REST API or wait for SDK update

            logger.info("Vector Index creation initiated")
            logger.info(f"Index: {index_name}")
            logger.info(f"Source: {source_table}")
            logger.info(f"Embedding column: {embedding_source_column}")

            # Placeholder for actual implementation
            logger.warning("Vector Index creation not fully implemented")
            logger.info("Please create the index using Databricks UI or REST API with:")
            logger.info(f"  - Index name: {index_name}")
            logger.info(f"  - Endpoint: {endpoint_name}")
            logger.info(f"  - Source table: {source_table}")
            logger.info(f"  - Embedding column: {embedding_source_column}")
            logger.info(f"  - Embedding model: {config.EMBEDDING_MODEL}")

        except Exception as e:
            logger.error(f"Error creating vector index: {e}")
            raise

    def sync_index(self, index_name: str = None):
        """
        Vector Index 동기화 트리거

        Args:
            index_name: 인덱스 이름
        """
        if index_name is None:
            index_name = config.VECTOR_INDEX_NAME

        try:
            logger.info(f"Triggering sync for index: {index_name}")

            # TODO: Implement using Databricks SDK or REST API
            logger.warning("Index sync not fully implemented")

        except Exception as e:
            logger.error(f"Error syncing index: {e}")
            raise


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Create Vector Search index")
    parser.add_argument(
        "--table",
        default="chunked_docs",
        help="Source Delta Table name (within configured catalog.schema)"
    )
    parser.add_argument(
        "--index_name",
        default=config.VECTOR_INDEX_NAME,
        help="Vector index name"
    )
    parser.add_argument(
        "--endpoint",
        default=config.VECTOR_SEARCH_ENDPOINT,
        help="Vector Search endpoint name"
    )
    parser.add_argument(
        "--embedding_column",
        default="text",
        help="Column to embed"
    )
    parser.add_argument(
        "--primary_key",
        default="chunk_id",
        help="Primary key column"
    )

    args = parser.parse_args()

    # Build full table name
    source_table = f"{config.uc_full_path}.{args.table}"

    # Create vector index
    builder = VectorIndexBuilder()

    # Create endpoint
    builder.create_vector_search_endpoint(args.endpoint)

    # Create index
    builder.create_delta_sync_index(
        source_table=source_table,
        index_name=args.index_name,
        endpoint_name=args.endpoint,
        embedding_source_column=args.embedding_column,
        primary_key=args.primary_key
    )

    print(f"\n✓ Vector Search index configuration:")
    print(f"  - Index: {args.index_name}")
    print(f"  - Source: {source_table}")
    print(f"  - Endpoint: {args.endpoint}")
    print(f"\n⚠️  Please complete the index creation in Databricks UI")


if __name__ == "__main__":
    main()
