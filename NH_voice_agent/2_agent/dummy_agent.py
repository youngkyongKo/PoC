"""
Dummy Agent - 테스트용 간단한 Agent
Databricks 연결 없이 음성 인터페이스 테스트
"""
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DummyAgent:
    """테스트용 Dummy Agent"""

    def __init__(self):
        logger.info("DummyAgent initialized")

    def query(self, question: str) -> dict:
        """
        질문 처리 (더미 응답)

        Args:
            question: 사용자 질문

        Returns:
            응답 결과
        """
        logger.info(f"Processing question: '{question}'")

        # 더미 응답 생성
        answer = f"질문이 잘 입력되었고, 질문 내용은 '{question}' 입니다. 에이전트가 처리중입니다. 테스트 답변 드립니다."

        response = {
            "question": question,
            "answer": answer,
            "success": True
        }

        logger.info("Question processed successfully")
        return response

    def chat(self):
        """대화형 모드"""
        print("=" * 60)
        print("Dummy Agent - Test Mode")
        print("=" * 60)
        print("\n명령어:")
        print("  - 질문 입력: 자유롭게 질문하세요")
        print("  - 'quit' 또는 'exit': 종료")
        print("\n" + "=" * 60 + "\n")

        while True:
            try:
                question = input("You: ").strip()

                if not question:
                    continue

                if question.lower() in ["quit", "exit", "종료"]:
                    print("\n종료합니다.")
                    break

                result = self.query(question)
                print(f"\nAgent: {result['answer']}\n")
                print("-" * 60 + "\n")

            except KeyboardInterrupt:
                print("\n\n종료합니다.")
                break
            except Exception as e:
                print(f"\n오류: {e}\n")


if __name__ == "__main__":
    agent = DummyAgent()
    agent.chat()
