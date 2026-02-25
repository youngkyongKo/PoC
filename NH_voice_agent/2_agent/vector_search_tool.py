"""
Vector Search Tool
Databricks Vector Search를 LangChain Tool로 래핑
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from databricks.sdk import WorkspaceClient
from langchain.tools import Tool
from langchain.pydantic_v1 import BaseModel, Field
from config import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class VectorSearchInput(BaseModel):
    """Vector Search 입력 스키마"""
    query: str = Field(description="검색 쿼리 텍스트")
    num_results: int = Field(default=5, description="반환할 결과 개수")


class VectorSearchTool:
    """Vector Search 검색 툴"""

    def __init__(
        self,
        index_name: str = None,
        embedding_model: str = None
    ):
        """
        Args:
            index_name: Vector Search 인덱스 이름
            embedding_model: 임베딩 모델 엔드포인트
        """
        self.client = WorkspaceClient(
            host=config.DATABRICKS_HOST,
            token=config.DATABRICKS_TOKEN
        )

        self.index_name = index_name or config.VECTOR_INDEX_NAME
        self.embedding_model = embedding_model or config.EMBEDDING_MODEL

        logger.info(f"VectorSearchTool initialized with index: {self.index_name}")

    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Vector Search 검색 수행

        Args:
            query: 검색 쿼리
            num_results: 반환할 결과 개수

        Returns:
            검색 결과 리스트
        """
        try:
            logger.info(f"Searching: '{query}' (top {num_results})")

            # TODO: Implement actual Vector Search query
            # Using Databricks SDK or REST API

            # Placeholder response
            results = [
                {
                    "text": f"검색 결과 샘플 {i+1} for '{query}'",
                    "score": 0.9 - (i * 0.1),
                    "metadata": {
                        "file_name": f"document_{i+1}.pdf",
                        "chunk_id": f"doc_{i+1}_chunk_0"
                    }
                }
                for i in range(min(num_results, 3))
            ]

            logger.info(f"Found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def format_results(self, results: List[Dict]) -> str:
        """
        검색 결과를 텍스트로 포맷팅

        Args:
            results: 검색 결과 리스트

        Returns:
            포맷팅된 텍스트
        """
        if not results:
            return "관련 문서를 찾을 수 없습니다."

        formatted = []
        for idx, result in enumerate(results, 1):
            text = result.get('text', '')
            score = result.get('score', 0)
            metadata = result.get('metadata', {})
            file_name = metadata.get('file_name', 'unknown')

            formatted.append(
                f"[{idx}] (관련도: {score:.2f}, 출처: {file_name})\n{text}\n"
            )

        return "\n".join(formatted)

    def run(self, query: str, num_results: int = 5) -> str:
        """
        Tool 실행 (LangChain 호환)

        Args:
            query: 검색 쿼리
            num_results: 결과 개수

        Returns:
            포맷팅된 검색 결과
        """
        results = self.search(query, num_results)
        return self.format_results(results)


def create_vector_search_tool() -> Tool:
    """
    LangChain Tool 생성

    Returns:
        Vector Search Tool 객체
    """
    vs_tool = VectorSearchTool()

    return Tool(
        name="vector_search",
        description=(
            "문서 검색 도구입니다. "
            "PDF 문서에서 관련 정보를 찾을 때 사용합니다. "
            "보험 상품 정보, 약관, 절차 등을 검색할 수 있습니다. "
            "입력: 검색하려는 내용을 자연어로 입력 (예: '보험 청약 절차')"
        ),
        func=vs_tool.run,
        args_schema=VectorSearchInput
    )


if __name__ == "__main__":
    # Test the tool
    print("Testing Vector Search Tool...\n")

    tool = create_vector_search_tool()

    # Test query
    test_query = "보험 상품의 보장 내용"
    print(f"Query: {test_query}\n")

    result = tool.run(test_query)
    print("Results:")
    print(result)
