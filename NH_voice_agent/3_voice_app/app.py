"""
NH Voice Agent - Streamlit App
음성으로 질문하고 답변을 들을 수 있는 웹 앱
"""
import sys
from pathlib import Path
import logging
import tempfile
from io import BytesIO

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from audio_recorder_streamlit import audio_recorder

from stt import SpeechToText
from tts import TextToSpeech
from config import config

# Import agent from parent directory
sys.path.append(str(Path(__file__).parent.parent / "2_agent"))
from supervisor_agent import SupervisorAgent

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


# Page configuration
st.set_page_config(
    page_title="NH Voice Agent",
    page_icon="🎤",
    layout="wide"
)


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = None


def initialize_agent():
    """Agent 초기화"""
    if st.session_state.agent is None:
        with st.spinner("Agent 초기화 중..."):
            try:
                st.session_state.agent = SupervisorAgent()
                logger.info("Agent initialized")
            except Exception as e:
                st.error(f"Agent 초기화 실패: {e}")
                logger.error(f"Agent initialization failed: {e}")


def process_audio(audio_bytes):
    """
    오디오 데이터 처리

    Args:
        audio_bytes: 오디오 바이트 데이터

    Returns:
        인식된 텍스트
    """
    try:
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav"
        ) as tmp_file:
            tmp_file.write(audio_bytes)
            audio_file = tmp_file.name

        # Speech-to-Text
        stt = SpeechToText()
        text = stt.recognize_from_file(audio_file)

        # Clean up
        Path(audio_file).unlink()

        return text

    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
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
    st.title("🎤 NH Voice Agent")
    st.markdown("음성으로 질문하고 답변을 들어보세요")

    # Sidebar
    with st.sidebar:
        st.header("설정")

        # Configuration display
        st.subheader("연결 정보")
        st.text(f"Model: {config.SERVING_ENDPOINT}")
        ka_endpoint = config.KA_ENDPOINT_NAME or "Not configured"
        st.text(f"KA Endpoint: {ka_endpoint}")
        genie_space = config.GENIE_SPACE_ID or "Not configured"
        st.text(f"Genie Space: {genie_space}")

        st.divider()

        # Clear conversation
        if st.button("대화 기록 초기화"):
            st.session_state.messages = []
            if st.session_state.agent:
                st.session_state.agent.agent_executor.memory.clear()
            st.success("대화 기록이 초기화되었습니다")
            st.rerun()

    # Initialize agent
    initialize_agent()

    # Main area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("대화")

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

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

            # Process audio
            with st.spinner("음성 인식 중..."):
                text = process_audio(audio_bytes)

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

                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

                # Synthesize response
                with st.spinner("음성 생성 중..."):
                    audio_file = synthesize_response(answer)

                if audio_file:
                    # Play audio
                    with open(audio_file, "rb") as f:
                        audio_data = f.read()
                    st.audio(audio_data, format="audio/mp3")

                    # Clean up
                    Path(audio_file).unlink()

                # Rerun to update chat
                st.rerun()

            else:
                st.error("음성 인식에 실패했습니다")

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

        # Add assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        # Rerun to update chat
        st.rerun()

    # Footer
    st.divider()
    st.caption("NH Voice Agent PoC - Powered by Databricks")


if __name__ == "__main__":
    main()
