"""
Knowledge Assistant Tool
Databricks Knowledge Assistant를 LangChain Tool로 래핑
"""
import sys
from pathlib import Path
from typing import Dict
import logging
import requests

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from databricks.sdk import WorkspaceClient
from langchain.tools import Tool
from langchain.pydantic_v1 import BaseModel, Field
from config import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class KnowledgeAssistantInput(BaseModel):
    """Knowledge Assistant 입력 스키마"""
    query: str = Field(description="검색할 질문 (자연어)")


class KnowledgeAssistantTool:
    """Knowledge Assistant 쿼리 툴"""

    def __init__(self, endpoint_name: str = None):
        """
        Args:
            endpoint_name: KA 엔드포인트 이름 (예: "ka-69e8398a-endpoint")
        """
        self.client = WorkspaceClient(
            host=config.DATABRICKS_HOST,
            token=config.DATABRICKS_TOKEN
        )

        self.endpoint_name = endpoint_name or config.KA_ENDPOINT_NAME

        if not self.endpoint_name:
            raise ValueError("KA_ENDPOINT_NAME must be configured")

        logger.info(f"KnowledgeAssistantTool initialized with endpoint: {self.endpoint_name}")

    def query(self, question: str) -> Dict:
        """
        Knowledge Assistant에 질문 전송

        Args:
            question: 사용자 질문

        Returns:
            응답 결과
        """
        try:
            logger.info(f"Querying KA: '{question}'")

            # API 엔드포인트 URL
            # ajax-serving-endpoints를 사용하여 RAG 검색 활성화
            url = f"https://{config.DATABRICKS_HOST}/ajax-serving-endpoints/{self.endpoint_name}/invocations"

            # 요청 페이로드 (OpenAI 호환 형식)
            payload = {
                "input": [
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            }

            # 헤더 구성
            headers = {
                "Authorization": f"Bearer {config.DATABRICKS_TOKEN}",
                "Content-Type": "application/json"
            }

            # API 호출
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=60
            )

            # 에러 처리
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"KA API error: {error_msg}")
                return {
                    "error": error_msg,
                    "question": question
                }

            # 응답 파싱
            result = response.json()

            # 답변 추출 (다양한 형식 지원)
            answer = self._extract_answer(result)

            # RAG 소스 사용 여부 확인
            sources_used = self._check_sources_used(result)

            logger.info(f"KA response received (sources_used: {sources_used})")

            return {
                "answer": answer,
                "sources_used": sources_used,
                "raw_response": result
            }

        except requests.exceptions.Timeout:
            error_msg = "Request timeout (60s)"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "question": question
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error querying KA: {error_msg}")
            return {
                "error": error_msg,
                "question": question
            }

    def _extract_answer(self, result: Dict) -> str:
        """
        응답에서 답변 텍스트 추출

        Args:
            result: API 응답

        Returns:
            답변 텍스트
        """
        # 시도 1: output[0].content[0].text (Databricks Agent 형식)
        if "output" in result and len(result["output"]) > 0:
            output = result["output"][0]
            if isinstance(output, dict) and "content" in output:
                content_list = output["content"]
                if isinstance(content_list, list) and len(content_list) > 0:
                    content_item = content_list[0]
                    if isinstance(content_item, dict) and "text" in content_item:
                        return content_item["text"]

        # 시도 2: choices[0].message.content (OpenAI 형식)
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if isinstance(choice, dict):
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
                elif "text" in choice:
                    return choice["text"]

        # 시도 3: 기타 형식
        for key in ["answer", "content", "response"]:
            if key in result:
                return result[key]

        return ""

    def _check_sources_used(self, result: Dict) -> bool:
        """
        RAG 소스 사용 여부 확인

        Args:
            result: API 응답

        Returns:
            소스 사용 여부
        """
        if "custom_outputs" in result and isinstance(result["custom_outputs"], dict):
            return result["custom_outputs"].get("sources_used", False)
        return False

    def format_result(self, result: Dict) -> str:
        """
        결과를 텍스트로 포맷팅

        Args:
            result: 쿼리 결과

        Returns:
            포맷팅된 텍스트
        """
        if "error" in result:
            return f"오류가 발생했습니다: {result['error']}"

        answer = result.get("answer", "")
        sources_used = result.get("sources_used", False)

        formatted = []

        if answer:
            formatted.append(answer)
        else:
            formatted.append("답변을 생성할 수 없습니다.")

        # RAG 소스 사용 여부 표시 (디버그 모드)
        if config.DEBUG and sources_used:
            formatted.append("\n[문서 검색 활성화됨]")

        return "\n".join(formatted)

    def run(self, query: str) -> str:
        """
        Tool 실행 (LangChain 호환)

        Args:
            query: 검색 질문

        Returns:
            포맷팅된 결과
        """
        result = self.query(query)
        return self.format_result(result)


def create_knowledge_assistant_tool() -> Tool:
    """
    LangChain Tool 생성

    Returns:
        Knowledge Assistant Tool 객체
    """
    ka_tool = KnowledgeAssistantTool()

    return Tool(
        name="knowledge_assistant",
        description=(
            "문서 기반 질의응답 도구입니다. "
            "Knowledge Assistant를 사용하여 업로드된 PDF 및 문서에서 정보를 검색합니다. "
            "보험 상품 정보, 약관, 절차, 규정 등을 자연어로 질문할 수 있습니다. "
            "입력: 자연어 질문 (예: '보험 청약 절차는 어떻게 되나요?')"
        ),
        func=ka_tool.run,
        args_schema=KnowledgeAssistantInput
    )


if __name__ == "__main__":
    # Test the tool
    print("Testing Knowledge Assistant Tool...\n")

    try:
        tool = create_knowledge_assistant_tool()

        # Test query
        test_query = "이 문서의 주요 내용은 무엇인가요?"
        print(f"Query: {test_query}\n")

        result = tool.run(test_query)
        print("Result:")
        print(result)

    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nPlease set KA_ENDPOINT_NAME in your .env file")
