# Databricks notebook source
# MAGIC %md
# MAGIC # Knowledge Assistant Tool 구현
# MAGIC
# MAGIC Databricks Knowledge Assistant를 LangChain Tool로 래핑합니다.
# MAGIC
# MAGIC ## 주요 기능
# MAGIC - ajax-serving-endpoints를 통한 RAG 활성화
# MAGIC - 다양한 응답 형식 자동 파싱
# MAGIC - 에러 처리 및 타임아웃 관리
# MAGIC - LangChain Tool 인터페이스 제공
# MAGIC
# MAGIC ## 사용 방법
# MAGIC ```python
# MAGIC from knowledge_assistant_tool import create_knowledge_assistant_tool
# MAGIC
# MAGIC # Tool 생성
# MAGIC ka_tool = create_knowledge_assistant_tool()
# MAGIC
# MAGIC # 질문 실행
# MAGIC result = ka_tool.run("보험 청약 절차는 어떻게 되나요?")
# MAGIC print(result)
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: 필수 라이브러리 import

# COMMAND ----------

import sys
from pathlib import Path
from typing import Dict
import logging
import requests

from databricks.sdk import WorkspaceClient
from langchain.tools import Tool
from langchain.pydantic_v1 import BaseModel, Field

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("✅ 라이브러리 import 완료")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: 설정 클래스 정의

# COMMAND ----------

class KAConfig:
    """Knowledge Assistant 설정"""

    # Databricks Configuration
    DATABRICKS_HOST = spark.conf.get("spark.databricks.workspaceUrl")
    DATABRICKS_TOKEN = None  # Runtime에 동적으로 가져옴

    # Knowledge Assistant Configuration
    KA_ENDPOINT_NAME = "ka-69e8398a-endpoint"  # 실제 endpoint 이름으로 변경

    # Application Settings
    DEBUG = True
    LOG_LEVEL = "INFO"

    @classmethod
    def get_token(cls):
        """Databricks Token 동적으로 가져오기"""
        if cls.DATABRICKS_TOKEN is None:
            cls.DATABRICKS_TOKEN = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
        return cls.DATABRICKS_TOKEN


config = KAConfig()

print(f"✅ 설정 완료")
print(f"   Workspace: {config.DATABRICKS_HOST}")
print(f"   KA Endpoint: {config.KA_ENDPOINT_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: 입력 스키마 정의

# COMMAND ----------

class KnowledgeAssistantInput(BaseModel):
    """Knowledge Assistant 입력 스키마"""
    query: str = Field(description="검색할 질문 (자연어)")


print("✅ 입력 스키마 정의 완료")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Knowledge Assistant Tool 클래스 구현

# COMMAND ----------

class KnowledgeAssistantTool:
    """Knowledge Assistant 쿼리 툴"""

    def __init__(self, endpoint_name: str = None):
        """
        Args:
            endpoint_name: KA 엔드포인트 이름
        """
        self.client = WorkspaceClient()
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

            # API 엔드포인트 URL (REST API 사용)
            # KA endpoint는 REST API로 호출해도 RAG 기능이 유지됩니다
            url = f"https://{config.DATABRICKS_HOST}/api/2.0/serving-endpoints/{self.endpoint_name}/invocations"

            # 요청 페이로드
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
                "Authorization": f"Bearer {config.get_token()}",
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

            # 답변 추출
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
        """응답에서 답변 텍스트 추출"""

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
        """RAG 소스 사용 여부 확인"""
        if "custom_outputs" in result and isinstance(result["custom_outputs"], dict):
            return result["custom_outputs"].get("sources_used", False)
        return False

    def format_result(self, result: Dict) -> str:
        """결과를 텍스트로 포맷팅"""
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


print("✅ KnowledgeAssistantTool 클래스 정의 완료")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: LangChain Tool 생성 함수

# COMMAND ----------

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


print("✅ Tool 생성 함수 정의 완료")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: 테스트 실행

# COMMAND ----------

print("=" * 80)
print("🧪 Knowledge Assistant Tool 테스트")
print("=" * 80)
print()

try:
    # Tool 생성
    tool = create_knowledge_assistant_tool()
    print("✅ Tool 생성 성공")
    print()

    # 테스트 질문
    test_questions = [
        "회사 홈페이지 URL은?",
        "보험계약을 중도 해지시 해지환급금은 이미 납입한 보험료보다 적거나 없는 경우, 이유는?"
    ]

    for i, query in enumerate(test_questions, 1):
        print(f"[{i}/{len(test_questions)}] 질문: {query}")
        print()

        result = tool.run(query)

        print("답변:")
        print("-" * 80)
        print(result)
        print("-" * 80)
        print()

    print("✅ 테스트 완료!")

except ValueError as e:
    print(f"❌ 설정 오류: {e}")
    print()
    print("KA_ENDPOINT_NAME을 올바르게 설정하세요.")

except Exception as e:
    print(f"❌ 테스트 실패: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 📚 사용 가이드
# MAGIC
# MAGIC ### Supervisor Agent에서 사용
# MAGIC
# MAGIC ```python
# MAGIC from knowledge_assistant_tool import create_knowledge_assistant_tool
# MAGIC
# MAGIC # Tool 생성
# MAGIC ka_tool = create_knowledge_assistant_tool()
# MAGIC
# MAGIC # LangChain Agent에 추가
# MAGIC tools = [ka_tool, other_tools...]
# MAGIC agent = create_agent(tools=tools)
# MAGIC ```
# MAGIC
# MAGIC ### 직접 사용
# MAGIC
# MAGIC ```python
# MAGIC ka_tool = KnowledgeAssistantTool()
# MAGIC result = ka_tool.query("보험 청약 절차는?")
# MAGIC print(result['answer'])
# MAGIC ```
# MAGIC
# MAGIC ### 설정 변경
# MAGIC
# MAGIC ```python
# MAGIC # 다른 endpoint 사용
# MAGIC ka_tool = KnowledgeAssistantTool(endpoint_name="ka-other-endpoint")
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Notebook 완료**
