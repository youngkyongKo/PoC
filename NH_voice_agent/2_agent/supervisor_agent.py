"""
Supervisor Agent - LangGraph 기반
질문을 분석하여 Knowledge Assistant 또는 Genie Space로 라우팅
"""
import sys
from pathlib import Path
from typing import TypedDict, Annotated, Literal
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, END
from langchain_community.chat_models import ChatDatabricks
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from knowledge_assistant_tool import KnowledgeAssistantTool
from genie_tool import GenieSpaceTool
from config import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """Agent 상태"""
    question: str
    chat_history: list
    route: str  # "knowledge_assistant" or "genie_space"
    answer: str
    sources: list  # 소스 문서 정보
    error: str | None


class SupervisorAgent:
    """LangGraph 기반 Supervisor Agent"""

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
        self.ka_tool = KnowledgeAssistantTool()
        self.genie_tool = GenieSpaceTool()

        # Chat history
        self.chat_history = []

        # Create graph
        self.graph = self._create_graph()

        logger.info("SupervisorAgent initialized with LangGraph")

    def _create_graph(self) -> StateGraph:
        """LangGraph 생성"""

        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("router", self._router_node)
        workflow.add_node("knowledge_assistant", self._knowledge_assistant_node)
        workflow.add_node("genie_space", self._genie_space_node)

        # Add edges
        workflow.set_entry_point("router")

        workflow.add_conditional_edges(
            "router",
            self._route_question,
            {
                "knowledge_assistant": "knowledge_assistant",
                "genie_space": "genie_space"
            }
        )

        workflow.add_edge("knowledge_assistant", END)
        workflow.add_edge("genie_space", END)

        return workflow.compile()

    def _router_node(self, state: AgentState) -> AgentState:
        """
        라우터: 질문을 분석하여 적절한 도구 선택
        """
        question = state["question"]

        # LLM을 사용하여 라우팅 결정
        system_prompt = """당신은 NH 증권 채권 상품 상담을 위한 라우터입니다. 고객의 질문을 분석하여 적절한 도구를 선택합니다.

## 사용 가능한 도구

### 1. genie_space (채권 종목 정보 검색)
**데이터**: 판매 중인 채권 종목의 구조화된 데이터
**사용 시기**:
- 채권을 검색하거나 비교할 때
- 특정 조건(등급, 수익률, 만기)으로 필터링할 때
- 수치 데이터 기반 분석이 필요할 때
- 발행사별 채권 목록을 조회할 때

**예시 질문**:
- "A- 이상 등급인 채권을 찾아줘"
- "수익률 높은 순으로 보여줘"
- "만기 1년 미만인 채권은?"
- "롯데캐피탈 채권을 비교해줘"
- "민평금리보다 싼 회사채는?"

### 2. knowledge_assistant (채권 상품 설명서 검색)
**데이터**: 채권 상품 설명서 PDF 문서
**사용 시기**:
- 발행사에 대한 상세 정보가 필요할 때
- "회사 소개", "사업 내용", "신용평가 요인" 등의 질문
- "어떤 회사인지", "무슨 일을 하는지" 등의 정성적 정보 요청
- 투자 리스크, 재무 상황 관련 질문

**예시 질문**:
- "DL에너지 회사에 대해 알려줘"
- "이 발행사가 무슨 일을 하는 회사야?"
- "신용등급 전망은 어때?"
- "재무 상황이 어때?"
- "투자 리스크는 뭐가 있어?"

## 라우팅 규칙
- 채권 검색, 비교, 수치 분석 → "genie_space"
- 발행사 정보, 회사 소개, 리스크 분석 → "knowledge_assistant"
- 복합 질의는 먼저 필요한 도구부터 사용 (구조화된 데이터가 필요하면 genie_space)

질문을 분석하고 "knowledge_assistant" 또는 "genie_space" 중 하나만 답변하세요."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"질문: {question}\n\n어느 도구를 사용해야 할까요?")
        ]

        try:
            response = self.llm.invoke(messages)
            route_decision = response.content.strip().lower()

            # 키워드 기반 fallback (채권 도메인 특화)
            genie_keywords = ["채권", "종목", "등급", "수익률", "만기", "민평", "비교", "검색", "찾아", "보여"]
            ka_keywords = ["회사", "발행사", "사업", "소개", "전망", "리스크", "재무", "신용평가"]

            if "genie" in route_decision or any(kw in question for kw in genie_keywords):
                route = "genie_space"
            elif "knowledge" in route_decision or any(kw in question for kw in ka_keywords):
                route = "knowledge_assistant"
            else:
                # 기본값: 데이터 검색 우선
                route = "genie_space"

            logger.info(f"Router decision: {route} (question: {question[:50]}...)")
            state["route"] = route

        except Exception as e:
            logger.error(f"Router error: {e}")
            # 기본값: genie_space (채권 검색이 더 일반적)
            state["route"] = "genie_space"

        return state

    def _route_question(self, state: AgentState) -> Literal["knowledge_assistant", "genie_space"]:
        """라우팅 결정 반환"""
        return state["route"]

    def _knowledge_assistant_node(self, state: AgentState) -> AgentState:
        """Knowledge Assistant 노드"""
        question = state["question"]

        try:
            logger.info(f"Calling Knowledge Assistant: {question}")

            # KA 툴 직접 호출하여 상세 정보 얻기
            ka_result = self.ka_tool.query(question)

            if "error" in ka_result:
                state["answer"] = f"오류: {ka_result['error']}"
                state["error"] = ka_result["error"]
                state["sources"] = []
            else:
                state["answer"] = ka_result.get("answer", "")
                state["sources"] = ka_result.get("sources", [])
                state["error"] = None

        except Exception as e:
            logger.error(f"Knowledge Assistant error: {e}")
            state["answer"] = f"Knowledge Assistant 호출 중 오류가 발생했습니다: {str(e)}"
            state["error"] = str(e)
            state["sources"] = []

        return state

    def _genie_space_node(self, state: AgentState) -> AgentState:
        """Genie Space 노드"""
        question = state["question"]

        try:
            logger.info(f"Calling Genie Space: {question}")
            result = self.genie_tool.run(question)
            state["answer"] = result
            state["sources"] = []  # Genie는 소스 정보 없음
            state["error"] = None

        except Exception as e:
            logger.error(f"Genie Space error: {e}")
            state["answer"] = f"Genie Space 호출 중 오류가 발생했습니다: {str(e)}"
            state["error"] = str(e)
            state["sources"] = []

        return state

    def query(self, question: str) -> dict:
        """
        질문 처리

        Args:
            question: 사용자 질문

        Returns:
            응답 결과
        """
        try:
            logger.info(f"Processing question: '{question}'")

            # Initialize state
            initial_state = {
                "question": question,
                "chat_history": self.chat_history.copy(),
                "route": "",
                "answer": "",
                "sources": [],
                "error": None
            }

            # Run graph
            final_state = self.graph.invoke(initial_state)

            # Update chat history
            self.chat_history.append(HumanMessage(content=question))
            self.chat_history.append(AIMessage(content=final_state["answer"]))

            response = {
                "question": question,
                "answer": final_state["answer"],
                "route": final_state["route"],
                "sources": final_state.get("sources", []),
                "success": final_state["error"] is None
            }

            if final_state["error"]:
                response["error"] = final_state["error"]

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

    def clear_history(self):
        """대화 기록 초기화"""
        self.chat_history = []
        logger.info("Chat history cleared")

    def chat(self):
        """대화형 모드"""
        print("=" * 60)
        print("NH Voice Agent - Supervisor Agent (LangGraph)")
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
                    self.clear_history()
                    print("\n대화 기록이 초기화되었습니다.\n")
                    continue

                # Process question
                result = self.query(question)

                # Print response
                print(f"\nRoute: {result.get('route', 'N/A')}")
                print(f"Agent: {result['answer']}\n")
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
        print(f"Route: {result.get('route', 'N/A')}")
        print(f"Answer: {result['answer']}\n")
    else:
        # Interactive mode
        agent.chat()


if __name__ == "__main__":
    main()
