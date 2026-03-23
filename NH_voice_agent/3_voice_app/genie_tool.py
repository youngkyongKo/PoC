"""
Genie Space Tool
Databricks Genie Space를 LangChain Tool로 래핑
"""
import sys
from pathlib import Path
from typing import Dict, Optional
import logging

from databricks.sdk import WorkspaceClient
from pydantic import BaseModel, Field
from config import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class GenieInput(BaseModel):
    """Genie Space 입력 스키마"""
    question: str = Field(description="자연어 질문")


class GenieSpaceTool:
    """Genie Space 쿼리 툴"""

    def __init__(
        self,
        space_id: str = None,
        warehouse_id: str = None
    ):
        """
        Args:
            space_id: Genie Space ID
            warehouse_id: SQL Warehouse ID
        """
        self.client = WorkspaceClient(
            host=config.DATABRICKS_HOST,
            token=config.DATABRICKS_TOKEN
        )

        self.space_id = space_id or config.GENIE_SPACE_ID
        self.warehouse_id = warehouse_id or config.SQL_WAREHOUSE_ID

        if not self.space_id:
            logger.warning("Genie Space ID not configured")

        logger.info(f"GenieSpaceTool initialized with space_id: {self.space_id}")

    def query(self, question: str) -> Dict:
        """
        Genie Space에 질문

        Args:
            question: 자연어 질문

        Returns:
            쿼리 결과
        """
        try:
            logger.info(f"Querying Genie: '{question}'")

            # TODO: Implement actual Genie Space query
            # Using Databricks SDK or REST API

            # Placeholder response
            result = {
                "question": question,
                "sql": "SELECT * FROM sales_data LIMIT 5",
                "result": [
                    {"product": "상품 A", "sales": 1000},
                    {"product": "상품 B", "sales": 800},
                    {"product": "상품 C", "sales": 600}
                ],
                "summary": f"'{question}'에 대한 분석 결과입니다."
            }

            logger.info("Query successful")
            return result

        except Exception as e:
            logger.error(f"Error querying Genie: {e}")
            return {
                "error": str(e),
                "question": question
            }

    def format_result(self, result: Dict) -> str:
        """
        쿼리 결과를 텍스트로 포맷팅

        Args:
            result: 쿼리 결과

        Returns:
            포맷팅된 텍스트
        """
        if "error" in result:
            return f"오류가 발생했습니다: {result['error']}"

        # Format result as table
        formatted = []

        # Add summary
        if "summary" in result:
            formatted.append(result["summary"])
            formatted.append("")

        # Add data table
        if "result" in result and result["result"]:
            data = result["result"]

            # Get column names
            if data:
                columns = list(data[0].keys())
                formatted.append(" | ".join(columns))
                formatted.append("-" * 50)

                # Add rows
                for row in data[:10]:  # Limit to 10 rows
                    values = [str(row.get(col, "")) for col in columns]
                    formatted.append(" | ".join(values))

        # Add SQL (optional)
        if "sql" in result and config.DEBUG:
            formatted.append("")
            formatted.append(f"실행된 SQL: {result['sql']}")

        return "\n".join(formatted) if formatted else "결과가 없습니다."

    def run(self, question: str) -> str:
        """
        Tool 실행 (LangChain 호환)

        Args:
            question: 자연어 질문

        Returns:
            포맷팅된 결과
        """
        result = self.query(question)
        return self.format_result(result)


if __name__ == "__main__":
    # Test the tool
    print("Testing Genie Space Tool...\n")

    tool = GenieSpaceTool()

    # Test query
    test_question = "최근 1주일 판매 실적을 보여줘"
    print(f"Question: {test_question}\n")

    result = tool.run(test_question)
    print("Result:")
    print(result)
