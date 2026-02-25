"""
Supervisor Agent
Vector Search와 Genie Space를 활용하는 Multi-Agent Supervisor
"""
import sys
from pathlib import Path
from typing import List, Dict
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatDatabricks
from langchain.memory import ConversationBufferMemory

from vector_search_tool import create_vector_search_tool
from genie_tool import create_genie_tool
from config import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class SupervisorAgent:
    """Supervisor Agent 클래스"""

    def __init__(self, model_endpoint: str = None):
        """
        Args:
            model_endpoint: LLM 모델 엔드포인트
        """
        self.model_endpoint = model_endpoint or config.SERVING_ENDPOINT

        # Initialize LLM
        self.llm = ChatDatabricks(
            target_uri="databricks",
            endpoint=self.model_endpoint,
            temperature=0.1
        )

        # Initialize tools
        self.tools = [
            create_vector_search_tool(),
            create_genie_tool()
        ]

        # Create agent
        self.agent_executor = self._create_agent()

        logger.info("SupervisorAgent initialized")

    def _create_agent(self) -> AgentExecutor:
        """Agent 생성"""

        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        # Create agent
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        # Create executor
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=memory,
            verbose=config.DEBUG,
            handle_parsing_errors=True
        )

        return agent_executor

    def _get_system_prompt(self) -> str:
        """시스템 프롬프트"""
        return """당신은 NH생명 고객 지원 AI 어시스턴트입니다.

사용 가능한 도구:
1. vector_search: 보험 상품 정보, 약관, 절차 등을 문서에서 검색
2. genie_space: 판매 실적, 통계 등의 데이터를 분석

도구 사용 가이드:
- 문서나 정책 관련 질문 → vector_search 사용
- 데이터 분석이나 통계 질문 → genie_space 사용
- 복합적인 질문은 두 도구를 순차적으로 사용

응답 가이드:
- 친절하고 전문적인 톤으로 답변
- 검색 결과를 기반으로 정확한 정보 제공
- 불확실한 경우 명확히 표현
- 한국어로 답변
"""

    def query(self, question: str) -> Dict:
        """
        질문 처리

        Args:
            question: 사용자 질문

        Returns:
            응답 결과
        """
        try:
            logger.info(f"Processing question: '{question}'")

            result = self.agent_executor.invoke({"input": question})

            response = {
                "question": question,
                "answer": result.get("output", ""),
                "success": True
            }

            logger.info("Question processed successfully")
            return response

        except Exception as e:
            logger.error(f"Error processing question: {e}")
            return {
                "question": question,
                "answer": f"오류가 발생했습니다: {str(e)}",
                "success": False,
                "error": str(e)
            }

    def chat(self):
        """대화형 모드"""
        print("=" * 60)
        print("NH Voice Agent - Supervisor Agent")
        print("=" * 60)
        print("\n명령어:")
        print("  - 질문 입력: 자유롭게 질문하세요")
        print("  - 'quit' 또는 'exit': 종료")
        print("  - 'clear': 대화 기록 초기화")
        print("\n" + "=" * 60 + "\n")

        while True:
            try:
                # Get user input
                question = input("You: ").strip()

                if not question:
                    continue

                # Handle commands
                if question.lower() in ["quit", "exit", "종료"]:
                    print("\n종료합니다.")
                    break

                if question.lower() in ["clear", "초기화"]:
                    self.agent_executor.memory.clear()
                    print("\n대화 기록이 초기화되었습니다.\n")
                    continue

                # Process question
                result = self.query(question)

                # Print response
                print(f"\nAgent: {result['answer']}\n")
                print("-" * 60 + "\n")

            except KeyboardInterrupt:
                print("\n\n종료합니다.")
                break
            except Exception as e:
                print(f"\n오류: {e}\n")


def main():
    """메인 실행 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Run Supervisor Agent")
    parser.add_argument(
        "--model",
        default=config.SERVING_ENDPOINT,
        help="LLM model endpoint"
    )
    parser.add_argument(
        "--question",
        help="Single question to ask"
    )

    args = parser.parse_args()

    # Create agent
    agent = SupervisorAgent(model_endpoint=args.model)

    if args.question:
        # Single question mode
        result = agent.query(args.question)
        print(f"\nQuestion: {result['question']}")
        print(f"Answer: {result['answer']}\n")
    else:
        # Interactive mode
        agent.chat()


if __name__ == "__main__":
    main()
