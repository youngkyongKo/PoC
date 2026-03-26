"""
Genie Space Tool
Databricks Genie Space를 LangChain Tool로 래핑
"""
import sys
from pathlib import Path
from typing import Dict, Optional
import logging
import requests

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

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

    def query(self, question: str, conversation_id: str = None) -> Dict:
        """
        Genie Space에 질문

        Args:
            question: 자연어 질문
            conversation_id: 대화 ID (follow-up 질문 시)

        Returns:
            쿼리 결과
        """
        try:
            logger.info(f"Querying Genie: '{question}'")

            # Construct REST API URL
            url = f"https://{config.DATABRICKS_HOST}/api/2.0/genie/spaces/{self.space_id}/start-conversation"

            headers = {
                "Authorization": f"Bearer {config.DATABRICKS_TOKEN}",
                "Content-Type": "application/json"
            }

            payload = {
                "content": question
            }

            # Follow-up 질문인 경우
            if conversation_id:
                url = f"https://{config.DATABRICKS_HOST}/api/2.0/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages"

            # API 호출
            import requests
            response = requests.post(url, headers=headers, json=payload, timeout=120)

            if response.status_code != 200:
                logger.error(f"Genie API error: {response.status_code} - {response.text}")
                return {
                    "error": f"API error: {response.status_code}",
                    "question": question
                }

            result_data = response.json()
            logger.info(f"Genie response received: {result_data.get('conversation_id', 'N/A')}")

            # 응답 파싱
            return self._parse_genie_response(result_data, question)

        except Exception as e:
            logger.error(f"Error querying Genie: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "error": str(e),
                "question": question
            }

    def _parse_genie_response(self, response: Dict, question: str) -> Dict:
        """
        Genie API 응답 파싱

        Args:
            response: API 응답
            question: 원본 질문

        Returns:
            파싱된 결과
        """
        result = {
            "question": question,
            "conversation_id": response.get("conversation_id"),
            "message_id": response.get("id"),
        }

        # SQL 쿼리 추출
        if "attachments" in response:
            for attachment in response.get("attachments", []):
                if attachment.get("query"):
                    query_info = attachment["query"]
                    result["sql"] = query_info.get("query")
                    result["description"] = query_info.get("description", "")

                    # 쿼리 결과 추출
                    if "result" in query_info:
                        query_result = query_info["result"]
                        result["columns"] = [col.get("name") for col in query_result.get("schema", {}).get("columns", [])]
                        result["data"] = query_result.get("data_array", [])
                        result["row_count"] = query_result.get("row_count", 0)

        # 텍스트 응답 추출
        result["text_response"] = response.get("content", "")
        result["status"] = response.get("status", "UNKNOWN")

        return result

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
