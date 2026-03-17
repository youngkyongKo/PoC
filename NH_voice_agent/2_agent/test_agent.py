"""
Agent 테스트 스크립트
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from supervisor_agent import SupervisorAgent
from config import config


def test_knowledge_assistant_queries():
    """Knowledge Assistant 관련 질문 테스트"""
    print("\n" + "=" * 60)
    print("Testing Knowledge Assistant Queries")
    print("=" * 60 + "\n")

    agent = SupervisorAgent()

    test_questions = [
        "보험 상품의 주요 보장 내용은 무엇인가요?",
        "보험 청약 절차를 알려주세요",
        "보험금 청구 방법이 어떻게 되나요?"
    ]

    for question in test_questions:
        print(f"Q: {question}")
        result = agent.query(question)
        print(f"A: {result['answer']}\n")
        print("-" * 60 + "\n")


def test_genie_queries():
    """Genie Space 관련 질문 테스트"""
    print("\n" + "=" * 60)
    print("Testing Genie Space Queries")
    print("=" * 60 + "\n")

    agent = SupervisorAgent()

    test_questions = [
        "지난달 판매 실적을 보여줘",
        "상품별 가입자 통계는 어떻게 되나요?",
        "최근 1주일 신규 가입자 수는?"
    ]

    for question in test_questions:
        print(f"Q: {question}")
        result = agent.query(question)
        print(f"A: {result['answer']}\n")
        print("-" * 60 + "\n")


def test_complex_queries():
    """복합 질문 테스트"""
    print("\n" + "=" * 60)
    print("Testing Complex Queries")
    print("=" * 60 + "\n")

    agent = SupervisorAgent()

    test_questions = [
        "가장 많이 판매된 상품의 보장 내용을 알려주세요",
        "최근 판매 실적과 해당 상품들의 특징을 비교해주세요"
    ]

    for question in test_questions:
        print(f"Q: {question}")
        result = agent.query(question)
        print(f"A: {result['answer']}\n")
        print("-" * 60 + "\n")


def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 60)
    print("NH Voice Agent - Agent Testing")
    print("=" * 60)

    print("\n설정:")
    print(f"  - Model: {config.SERVING_ENDPOINT}")
    print(f"  - KA Endpoint: {config.KA_ENDPOINT_NAME or 'Not configured'}")
    print(f"  - Genie Space: {config.GENIE_SPACE_ID or 'Not configured'}")

    # Run tests
    try:
        print("\n⚠️  이 테스트는 실제 Databricks 리소스가 설정되어 있어야 합니다.\n")

        test_knowledge_assistant_queries()
        test_genie_queries()
        test_complex_queries()

        print("\n✅ All tests completed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
