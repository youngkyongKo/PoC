"""
음성 인터페이스 전체 플로우 테스트
STT → Dummy Agent → TTS
"""
import sys
from pathlib import Path

# Add module paths
sys.path.append(str(Path(__file__).parent / "2_agent"))
sys.path.append(str(Path(__file__).parent / "3_voice_app"))

from dummy_agent import DummyAgent
from stt import SpeechToText
from tts import TextToSpeech


def test_full_flow():
    """전체 플로우 테스트"""
    print("=" * 60)
    print("음성 인터페이스 플로우 테스트")
    print("=" * 60)
    print()

    # Initialize components
    print("1️⃣ 컴포넌트 초기화...")
    agent = DummyAgent()
    stt = SpeechToText()
    tts = TextToSpeech()
    print("✓ 초기화 완료\n")

    # Test with text input first
    print("2️⃣ 텍스트 입력 테스트")
    print("-" * 60)
    test_question = "보험 상품에 대해 알려주세요"
    print(f"입력: {test_question}")

    # Agent processing
    print("\n처리 중...")
    result = agent.query(test_question)
    answer = result['answer']
    print(f"\n응답: {answer}\n")

    # TTS
    print("3️⃣ 음성 합성 테스트")
    print("-" * 60)
    audio_file = tts.synthesize(answer)
    if audio_file:
        print(f"✓ 음성 파일 생성: {audio_file}")
        print("🔊 음성 재생 중...")
        tts.play(audio_file)
        print("✓ 재생 완료\n")

        # Clean up
        Path(audio_file).unlink()
    else:
        print("❌ 음성 합성 실패\n")

    # Voice input test
    print("\n" + "=" * 60)
    print("4️⃣ 음성 입력 테스트 (선택사항)")
    print("-" * 60)
    choice = input("마이크로 음성 입력을 테스트하시겠습니까? (y/n): ")

    if choice.lower() == 'y':
        print("\n🎤 5초간 녹음합니다. 질문해주세요...")
        text = stt.recognize_from_microphone(duration=5)

        if text:
            print(f"\n인식된 텍스트: {text}")

            # Process with agent
            result = agent.query(text)
            answer = result['answer']
            print(f"\n응답: {answer}\n")

            # TTS
            audio_file = tts.synthesize(answer)
            if audio_file:
                print("🔊 음성 재생 중...")
                tts.play(audio_file)
                print("✓ 재생 완료")
                Path(audio_file).unlink()
        else:
            print("❌ 음성 인식 실패")

    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_full_flow()
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
