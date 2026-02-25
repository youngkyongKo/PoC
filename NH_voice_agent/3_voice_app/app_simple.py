"""
NH Voice Agent - Simple Streamlit App (Dummy Agent)
Databricks 연결 없이 음성 인터페이스 테스트
"""
import sys
from pathlib import Path
import logging
import tempfile

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from audio_recorder_streamlit import audio_recorder

from stt import SpeechToText
from tts import TextToSpeech

# Import dummy agent
sys.path.append(str(Path(__file__).parent.parent / "2_agent"))
from dummy_agent import DummyAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Page configuration
st.set_page_config(
    page_title="NH Voice Agent (Test)",
    page_icon="🎤",
    layout="wide"
)


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = None

if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None

if "audio_responses" not in st.session_state:
    st.session_state.audio_responses = {}


def initialize_agent():
    """Agent 초기화"""
    if st.session_state.agent is None:
        st.session_state.agent = DummyAgent()
        logger.info("Dummy Agent initialized")


def process_audio(audio_bytes):
    """
    오디오 데이터 처리

    Args:
        audio_bytes: 오디오 바이트 데이터

    Returns:
        인식된 텍스트
    """
    audio_file = None
    try:
        # Check audio size
        audio_size = len(audio_bytes)
        logger.info(f"Processing audio: {audio_size} bytes")

        if audio_size < 100:
            logger.error("Audio data too small")
            st.error("녹음된 오디오가 너무 짧습니다. 다시 시도해주세요.")
            return None

        # Save audio to temporary file
        # Use .webm extension as it's the common format from browsers
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".webm"
        ) as tmp_file:
            tmp_file.write(audio_bytes)
            audio_file = tmp_file.name

        logger.info(f"Audio saved to: {audio_file}")

        # Speech-to-Text
        stt = SpeechToText()
        text = stt.recognize_from_file(audio_file)

        # Clean up
        if audio_file and Path(audio_file).exists():
            Path(audio_file).unlink()
            logger.info("Temporary audio file cleaned up")

        if text:
            logger.info(f"Successfully recognized: '{text}'")
        else:
            logger.warning("Speech recognition returned no text")

        return text

    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Clean up on error
        if audio_file and Path(audio_file).exists():
            try:
                Path(audio_file).unlink()
            except:
                pass

        return None


def synthesize_response(text: str):
    """
    응답을 음성으로 변환

    Args:
        text: 변환할 텍스트

    Returns:
        오디오 파일 경로
    """
    try:
        tts = TextToSpeech()
        audio_file = tts.synthesize(text)
        return audio_file

    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        return None


def main():
    """메인 앱"""

    # Title
    st.title("🎤 NH Voice Agent (Test Mode)")
    st.markdown("음성으로 질문하고 답변을 들어보세요 (Dummy Agent)")

    # Sidebar
    with st.sidebar:
        st.header("설정")

        st.info("🧪 테스트 모드\n\nDatabricks 연결 없이 음성 인터페이스만 테스트합니다.")

        st.divider()

        # Clear conversation
        if st.button("대화 기록 초기화"):
            st.session_state.messages = []
            st.session_state.last_audio_bytes = None
            st.session_state.audio_responses = {}
            st.success("대화 기록이 초기화되었습니다")
            st.rerun()

        st.divider()

        # Tips
        st.subheader("💡 음성 입력 팁")
        st.markdown("""
        1. **명확하게 발음**하세요
        2. **3-5초 이상** 말씀하세요
        3. 조용한 환경에서 녹음
        4. 마이크 권한 허용 확인
        5. 실패 시 텍스트 입력 사용
        """)

    # Initialize agent
    initialize_agent()

    # Main area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("대화")

        # Display chat history
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Play audio for assistant responses
                if message["role"] == "assistant" and idx in st.session_state.audio_responses:
                    st.audio(st.session_state.audio_responses[idx], format="audio/mp3")

    with col2:
        st.subheader("음성 입력")

        # Audio recorder
        audio_bytes = audio_recorder(
            text="녹음하려면 클릭하세요",
            recording_color="#e74c3c",
            neutral_color="#3498db",
            icon_size="3x"
        )

        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")

            # 중복 처리 방지: 이전과 다른 오디오인 경우에만 처리
            if audio_bytes != st.session_state.last_audio_bytes:
                st.session_state.last_audio_bytes = audio_bytes

                # Process audio
                with st.spinner("음성 인식 중..."):
                    text = process_audio(audio_bytes)
            else:
                # 이미 처리된 오디오
                text = None

            if text:
                st.success(f"인식된 텍스트: {text}")

                # Add user message
                st.session_state.messages.append({
                    "role": "user",
                    "content": text
                })

                # Get agent response
                with st.spinner("답변 생성 중..."):
                    result = st.session_state.agent.query(text)
                    answer = result.get("answer", "")

                # Synthesize response first (before adding to messages)
                with st.spinner("음성 생성 중..."):
                    audio_file = synthesize_response(answer)

                # Store audio data if synthesis succeeded
                audio_data = None
                if audio_file:
                    with open(audio_file, "rb") as f:
                        audio_data = f.read()
                    # Clean up temp file
                    Path(audio_file).unlink()

                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

                # Store audio for this message
                if audio_data:
                    message_idx = len(st.session_state.messages) - 1
                    st.session_state.audio_responses[message_idx] = audio_data

                # Rerun to update chat
                st.rerun()

            elif audio_bytes != st.session_state.last_audio_bytes:
                # 새로운 녹음인데 인식 실패
                st.error("🎤 음성 인식에 실패했습니다")
                st.warning("""
                **다시 시도해보세요:**
                - 더 크고 명확하게 말씀해주세요
                - 3-5초 정도 말씀하신 후 중지하세요
                - 조용한 환경에서 녹음해주세요
                - 또는 아래 텍스트 입력창을 사용하세요
                """)

    # Text input (alternative to voice)
    st.divider()
    st.subheader("텍스트 입력")

    if prompt := st.chat_input("여기에 질문을 입력하세요"):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        # Get agent response
        with st.spinner("답변 생성 중..."):
            result = st.session_state.agent.query(prompt)
            answer = result.get("answer", "")

        # Synthesize response
        with st.spinner("음성 생성 중..."):
            audio_file = synthesize_response(answer)

        # Store audio data if synthesis succeeded
        audio_data = None
        if audio_file:
            with open(audio_file, "rb") as f:
                audio_data = f.read()
            # Clean up temp file
            Path(audio_file).unlink()

        # Add assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        # Store audio for this message
        if audio_data:
            message_idx = len(st.session_state.messages) - 1
            st.session_state.audio_responses[message_idx] = audio_data

        # Rerun to update chat
        st.rerun()

    # Footer
    st.divider()
    st.caption("NH Voice Agent PoC - Test Mode (Dummy Agent)")


if __name__ == "__main__":
    main()
