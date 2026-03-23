"""
Knowledge Assistant Tool
Databricks Knowledge Assistant를 LangChain Tool로 래핑
"""
import sys
from pathlib import Path
from typing import Dict
import logging
import requests

from databricks.sdk import WorkspaceClient
from pydantic import BaseModel, Field
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
        # DATABRICKS_HOST에 https:// prefix 추가
        host = config.DATABRICKS_HOST
        if not host.startswith("http"):
            host = f"https://{host}"

        self.client = WorkspaceClient(
            host=host,
            token=config.DATABRICKS_TOKEN
        )

        self.endpoint_name = endpoint_name or config.KA_ENDPOINT_NAME

        if not self.endpoint_name:
            raise ValueError("KA_ENDPOINT_NAME must be configured")

        logger.info(f"KnowledgeAssistantTool initialized with endpoint: {self.endpoint_name}")

    def query(self, question: str) -> Dict:
        """
        Knowledge Assistant에 질문 전송

        SDK의 저수준 API를 사용하여 직접 POST 요청을 보냅니다.

        Args:
            question: 사용자 질문

        Returns:
            응답 결과
        """
        try:
            logger.info(f"Querying KA: '{question}'")

            # 요청 페이로드
            payload = {
                "input": [
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            }

            # SDK의 저수준 API 사용
            result = self.client.api_client.do(
                method="POST",
                path=f"/serving-endpoints/{self.endpoint_name}/invocations",
                body=payload
            )

            logger.info(f"KA response received")
            logger.info(f"Response type: {type(result)}")
            logger.info(f"Response: {result}")

            # 답변 추출
            answer = self._extract_answer(result)

            # RAG 소스 사용 여부 확인
            sources_used = self._check_sources_used(result)

            # 소스 문서 추출
            sources = self._extract_sources(result)

            logger.info(f"Answer extracted (sources_used: {sources_used}, sources_count: {len(sources)})")

            return {
                "answer": answer,
                "sources_used": sources_used,
                "sources": sources,
                "raw_response": result
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error querying KA: {error_msg}")

            # 상세 오류 로깅
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

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

    def _extract_sources(self, result: Dict) -> list:
        """
        소스 문서 정보 추출

        Args:
            result: API 응답

        Returns:
            소스 문서 리스트
        """
        sources = []

        # 시도 1: output[0].content[].metadata
        if "output" in result and len(result["output"]) > 0:
            output = result["output"][0]
            if isinstance(output, dict) and "content" in output:
                content_list = output["content"]
                if isinstance(content_list, list):
                    for item in content_list:
                        if isinstance(item, dict) and "metadata" in item:
                            metadata = item["metadata"]
                            if isinstance(metadata, dict):
                                sources.append({
                                    "document": metadata.get("document_name", "Unknown"),
                                    "page": metadata.get("page", "N/A"),
                                    "chunk": metadata.get("chunk_id", "N/A")
                                })

        # 시도 2: citations 필드
        if not sources and "citations" in result:
            citations = result["citations"]
            if isinstance(citations, list):
                for citation in citations:
                    if isinstance(citation, dict):
                        sources.append({
                            "document": citation.get("document_name", citation.get("source", "Unknown")),
                            "page": citation.get("page", "N/A"),
                            "chunk": citation.get("chunk_id", "N/A")
                        })

        # 시도 3: custom_outputs.sources
        if not sources and "custom_outputs" in result:
            custom = result["custom_outputs"]
            if isinstance(custom, dict) and "sources" in custom:
                source_list = custom["sources"]
                if isinstance(source_list, list):
                    for source in source_list:
                        if isinstance(source, dict):
                            sources.append({
                                "document": source.get("document_name", source.get("name", "Unknown")),
                                "page": source.get("page", "N/A"),
                                "chunk": source.get("chunk_id", "N/A")
                            })

        return sources

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




if __name__ == "__main__":
    # Test the tool
    print("Testing Knowledge Assistant Tool...\n")

    try:
        tool = KnowledgeAssistantTool()

        # Test query
        test_query = "이 문서의 주요 내용은 무엇인가요?"
        print(f"Query: {test_query}\n")

        result = tool.run(test_query)
        print("Result:")
        print(result)

    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nPlease set KA_ENDPOINT_NAME in your .env file")
