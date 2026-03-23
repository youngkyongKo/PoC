"""
NH Voice Agent - Streamlit App
음성으로 질문하고 답변을 들을 수 있는 웹 앱
"""
import sys
from pathlib import Path
import logging
import tempfile
import hashlib
from io import BytesIO

import streamlit as st
from audio_recorder_streamlit import audio_recorder

from stt import SpeechToText
from tts import TextToSpeech
from config import config
from supervisor_agent import SupervisorAgent

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


# Page configuration
st.set_page_config(
    page_title="NH Voice Agent",
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add NH logo to the top left
st.logo("https://www.nhsec.com/images/lay/logo.png")

# NH Securities Brand Colors
NH_NAVY = "#003DA5"
NH_GOLD = "#FF9500"
NH_LIGHT_BLUE = "#E6F2FF"
NH_GRAY = "#F5F5F5"

# Custom CSS for NH branding with 2-column layout
st.markdown(f"""
<style>
    /* Remove default Streamlit padding */
    .main {{
        padding-top: 0 !important;
    }}

    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }}

    /* Main Header */
    .main-header {{
        background: linear-gradient(135deg, {NH_NAVY} 0%, #0052CC 100%);
        padding: 1.5rem 2rem;
        border-radius: 0;
        margin: -1rem -2rem 2rem -2rem;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }}

    .main-header h1 {{
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }}

    .main-header p {{
        color: {NH_LIGHT_BLUE};
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
    }}

    /* Sample Questions Box */
    .sample-questions {{
        background: linear-gradient(135deg, {NH_LIGHT_BLUE} 0%, #FFFFFF 100%);
        border: 2px solid {NH_NAVY};
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0 2rem 0;
        box-shadow: 0 4px 6px rgba(0, 61, 165, 0.1);
    }}

    .sample-questions h3 {{
        color: {NH_NAVY};
        font-size: 1.2rem;
        margin: 0 0 1rem 0;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}

    .sample-questions ul {{
        list-style: none;
        padding: 0;
        margin: 0;
    }}

    .sample-questions li {{
        margin: 0.5rem 0;
        padding-left: 1.5rem;
        position: relative;
    }}

    .sample-questions li:before {{
        content: "▸";
        position: absolute;
        left: 0;
        color: {NH_NAVY};
        font-weight: bold;
    }}

    .sample-question-link {{
        color: {NH_NAVY};
        text-decoration: none;
        font-size: 0.95rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        display: inline-block;
    }}

    .sample-question-link:hover {{
        color: {NH_GOLD};
        text-decoration: underline;
        transform: translateX(3px);
    }}

    /* Style buttons as links inside sample questions */
    .sample-questions .stButton > button {{
        background: none !important;
        border: none !important;
        color: {NH_NAVY} !important;
        padding: 0 !important;
        margin: 0 !important;
        text-align: left !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        box-shadow: none !important;
        width: auto !important;
    }}

    .sample-questions .stButton > button:hover {{
        background: none !important;
        color: {NH_GOLD} !important;
        text-decoration: underline !important;
        transform: none !important;
    }}

    /* Settings Panel */
    .settings-panel {{
        background-color: {NH_GRAY};
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        position: sticky;
        top: 1rem;
    }}

    .settings-panel h3 {{
        color: {NH_NAVY};
        font-size: 1.2rem;
        margin: 0 0 1rem 0;
        font-weight: 700;
    }}

    .settings-panel h4 {{
        color: {NH_NAVY};
        font-size: 1rem;
        margin: 1rem 0 0.5rem 0;
        font-weight: 600;
    }}

    /* Buttons */
    .stButton > button {{
        background-color: {NH_NAVY};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }}

    .stButton > button:hover {{
        background-color: {NH_GOLD};
        box-shadow: 0 4px 8px rgba(255, 149, 0, 0.3);
        transform: translateY(-2px);
    }}

    /* Chat Messages */
    [data-testid="stChatMessage"] {{
        background-color: white;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }}

    /* User Message */
    [data-testid="stChatMessage"][data-testid*="user"] {{
        background-color: {NH_LIGHT_BLUE};
        border-left: 4px solid {NH_NAVY};
    }}

    /* Assistant Message */
    [data-testid="stChatMessage"][data-testid*="assistant"] {{
        background-color: white;
        border-left: 4px solid {NH_GOLD};
    }}

    /* Input Box */
    .stTextArea textarea {{
        background-color: #FFFACD !important;
        border: 2px solid {NH_NAVY} !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
        min-height: 80px !important;
    }}

    .stTextArea textarea:focus {{
        border-color: {NH_GOLD} !important;
        box-shadow: 0 0 0 2px rgba(255, 149, 0, 0.2) !important;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {NH_LIGHT_BLUE};
        border-radius: 8px;
        color: {NH_NAVY};
        font-weight: 600;
    }}

    /* Success/Info Messages */
    .stSuccess {{
        background-color: #D4EDDA;
        border-left: 4px solid #28A745;
        border-radius: 8px;
    }}

    .stInfo {{
        background-color: {NH_LIGHT_BLUE};
        border-left: 4px solid {NH_NAVY};
        border-radius: 8px;
    }}

    /* Error Messages */
    .stError {{
        background-color: #F8D7DA;
        border-left: 4px solid #DC3545;
        border-radius: 8px;
    }}

    /* Warning Messages */
    .stWarning {{
        background-color: #FFF3CD;
        border-left: 4px solid {NH_GOLD};
        border-radius: 8px;
    }}

    /* Divider */
    hr {{
        margin: 1.5rem 0;
        border: none;
        border-top: 2px solid {NH_LIGHT_BLUE};
    }}

    /* Chat container */
    .chat-container {{
        background-color: white;
        border-radius: 15px;
        padding: 1.5rem;
        min-height: 500px;
        max-height: 700px;
        overflow-y: auto;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }}

    /* Input section */
    .input-section {{
        background-color: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin-top: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border-top: 3px solid {NH_NAVY};
    }}

    /* Send button special styling */
    div[data-testid="column"]:last-child .stButton > button {{
        height: 80px !important;
        font-size: 1.1rem !important;
    }}
</style>
""", unsafe_allow_html=True)


# Sample questions
SAMPLE_QUESTIONS = [
    "펀드 C5703의 투자위험등급은?",
    "현대인베스트 코스닥 벤처 증권투자신탁1호(주식혼합)의 투자 자산 비중은?",
    "펀드 환매할 때 손해가 발생하였는데도 왜 세금이 발생하지?"
]


# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = None

if "last_error" not in st.session_state:
    st.session_state.last_error = None

if "processing" not in st.session_state:
    st.session_state.processing = False

if "last_audio_bytes" not in st.session_state:
    st.session_state.last_audio_bytes = None

if "processed_audio" not in st.session_state:
    st.session_state.processed_audio = []

if "last_response_index" not in st.session_state:
    st.session_state.last_response_index = -1

if "last_recognized_text" not in st.session_state:
    st.session_state.last_recognized_text = ""

if "text_input_value" not in st.session_state:
    st.session_state.text_input_value = ""

if "auto_submit" not in st.session_state:
    st.session_state.auto_submit = False

if "selected_question" not in st.session_state:
    st.session_state.selected_question = None


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

    # Custom Header
    st.markdown("""
    <div class="main-header">
        <h1>🎤 NH Voice Agent</h1>
        <p>음성으로 질문하고 답변을 들어보세요 | AI 기반 금융 상담 서비스</p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize agent
    initialize_agent()

    # Main Layout: Left (Chat) + Right (Settings)
    col_chat, col_settings = st.columns([2.5, 1])

    # ==================== LEFT COLUMN: CHAT ====================
    with col_chat:
        # Sample Questions Section with list-style links
        st.markdown('<div class="sample-questions"><h3>💡 샘플 질문</h3>', unsafe_allow_html=True)

        for idx, question in enumerate(SAMPLE_QUESTIONS):
            if st.button(f"▸ {question}", key=f"sample_q{idx}", use_container_width=False):
                st.session_state.selected_question = question
                st.session_state.auto_submit = True
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

        # Chat Section
        st.markdown("### 💬 대화")

        # Display chat history
        for idx, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Assistant 메시지에만 추가 기능 표시
                if message["role"] == "assistant":
                    # 소스 문서 표시
                    if "sources" in message and message["sources"]:
                        with st.expander("📚 참조 문서"):
                            for i, source in enumerate(message["sources"], 1):
                                st.markdown(f"**{i}. {source.get('document', 'Unknown')}**")
                                if source.get('page') != 'N/A':
                                    st.text(f"   페이지: {source.get('page')}")
                                if source.get('chunk') != 'N/A':
                                    st.text(f"   청크: {source.get('chunk')}")

                    # 가장 최근 메시지인 경우 TTS 자동 생성
                    is_latest = (idx == len(st.session_state.messages) - 1)
                    should_autoplay = (is_latest and idx > st.session_state.last_response_index)

                    # TTS 오디오 캐시 키
                    audio_cache_key = f"audio_{idx}_{hashlib.md5(message['content'].encode()).hexdigest()[:8]}"

                    if should_autoplay:
                        # 최근 응답 인덱스 업데이트
                        st.session_state.last_response_index = idx

                        # TTS 생성 시도
                        try:
                            if audio_cache_key not in st.session_state:
                                audio_file = synthesize_response(message["content"])
                                if audio_file:
                                    with open(audio_file, "rb") as f:
                                        audio_data = f.read()
                                    st.session_state[audio_cache_key] = audio_data
                                    Path(audio_file).unlink()

                            # 캐시된 오디오 자동 재생
                            if audio_cache_key in st.session_state:
                                st.audio(st.session_state[audio_cache_key], format="audio/mp3", autoplay=True)
                        except Exception as e:
                            logger.warning(f"TTS autoplay failed: {e}")
                    else:
                        # 이전 메시지는 캐시된 오디오 또는 듣기 버튼 표시
                        if audio_cache_key in st.session_state:
                            st.audio(st.session_state[audio_cache_key], format="audio/mp3")
                        else:
                            tts_button_key = f"tts_{idx}"
                            if st.button("🔊 답변 듣기", key=tts_button_key):
                                try:
                                    audio_file = synthesize_response(message["content"])
                                    if audio_file:
                                        with open(audio_file, "rb") as f:
                                            audio_data = f.read()
                                        st.session_state[audio_cache_key] = audio_data
                                        st.audio(audio_data, format="audio/mp3")
                                        Path(audio_file).unlink()
                                        st.rerun()
                                    else:
                                        st.warning("음성 생성에 실패했습니다.")
                                except Exception as e:
                                    logger.error(f"TTS button error: {e}")
                                    st.warning("음성 생성 중 오류가 발생했습니다.")

        st.markdown("---")

        # Input Section
        st.markdown("### 🎙️ 질문 입력")

        # Show error message if exists
        if st.session_state.last_error:
            st.error(f"오류: {st.session_state.last_error}")
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("재시도", key="retry_button"):
                    st.session_state.last_error = None
                    st.rerun()
            with col2:
                if st.button("에러 무시", key="ignore_error"):
                    st.session_state.last_error = None
                    st.rerun()

        # Input layout: [Mic] [Text Area] [Send Button]
        input_col1, input_col2, input_col3 = st.columns([0.5, 7, 1])

        with input_col1:
            # Audio recorder
            audio_bytes = audio_recorder(
                text="",
                recording_color="#FF9500",  # NH Gold
                neutral_color="#003DA5",    # NH Navy
                icon_size="3x",
                pause_threshold=3.0,
                key="audio_input"
            )

        with input_col2:
            # Update from recognized text or selected question
            if st.session_state.last_recognized_text:
                st.session_state.text_input_value = st.session_state.last_recognized_text
                st.session_state.last_recognized_text = ""

            if st.session_state.selected_question:
                st.session_state.text_input_value = st.session_state.selected_question
                st.session_state.selected_question = None

            text_input = st.text_area(
                "질문을 입력하세요",
                value=st.session_state.text_input_value,
                height=80,
                placeholder="여기에 질문을 입력하거나 음성으로 질문하세요...",
                label_visibility="collapsed"
            )

        with input_col3:
            send_button = st.button("📤\n전송", use_container_width=True, type="primary", key="send_button")

    # ==================== RIGHT COLUMN: SETTINGS ====================
    with col_settings:
        st.markdown('<div class="settings-panel">', unsafe_allow_html=True)

        st.markdown("### ⚙️ 설정")

        # Configuration display
        st.markdown("#### 🔗 연결 정보")
        st.info(f"**Model:** {config.SERVING_ENDPOINT}")
        ka_endpoint = config.KA_ENDPOINT_NAME or "Not configured"
        st.info(f"**KA Endpoint:** {ka_endpoint}")
        genie_space = config.GENIE_SPACE_ID or "Not configured"
        st.info(f"**Genie Space:** {genie_space}")

        st.divider()

        # Clear conversation
        if st.button("🔄 대화 기록 초기화", use_container_width=True):
            st.session_state.messages = []
            st.session_state.processed_audio = []
            st.session_state.last_audio_bytes = None
            st.session_state.last_response_index = -1
            st.session_state.last_recognized_text = ""
            st.session_state.text_input_value = ""
            st.session_state.auto_submit = False
            st.session_state.selected_question = None
            if st.session_state.agent:
                st.session_state.agent.clear_history()
            st.success("대화 기록이 초기화되었습니다")
            st.rerun()

        st.divider()

        # Info section
        st.markdown("#### 📌 사용 방법")
        st.markdown("""
        - 마이크 버튼을 클릭하여 음성으로 질문
        - 샘플 질문을 클릭하여 바로 질문
        - 하단 입력창에 질문을 직접 입력
        """)

        st.markdown('</div>', unsafe_allow_html=True)

    # Process audio input if available
    if audio_bytes:
        # Create a hash of the audio bytes
        audio_hash = hashlib.md5(audio_bytes).hexdigest()

        # Check if this audio has already been processed
        if audio_hash not in st.session_state.processed_audio:
            # Mark as processed
            st.session_state.processed_audio.append(audio_hash)
            if len(st.session_state.processed_audio) > 10:
                st.session_state.processed_audio.pop(0)

            # Process audio to text
            with st.spinner("음성 인식 중..."):
                text = process_audio(audio_bytes)

            if text:
                st.session_state.last_recognized_text = text
                st.session_state.auto_submit = True
                st.rerun()
            else:
                st.error("음성 인식에 실패했습니다")
                if audio_hash in st.session_state.processed_audio:
                    st.session_state.processed_audio.remove(audio_hash)

    # Check if we should auto submit
    should_submit = (send_button or st.session_state.auto_submit) and text_input.strip()

    if should_submit:
        # Clear auto submit flag
        st.session_state.auto_submit = False

        prompt = text_input.strip()

        # Prevent processing if already processing
        if st.session_state.processing:
            st.warning("이미 처리 중입니다...")
        else:
            st.session_state.processing = True
            st.session_state.last_error = None

            try:
                # Add user message
                st.session_state.messages.append({
                    "role": "user",
                    "content": prompt
                })

                # Get agent response
                with st.spinner("답변 생성 중..."):
                    result = st.session_state.agent.query(prompt)

                    # Check for errors
                    if not result.get("success", True):
                        error_msg = result.get("error", "알 수 없는 오류")
                        st.session_state.last_error = error_msg
                        st.session_state.messages.pop()
                        st.session_state.processing = False
                        st.rerun()
                        return

                    answer = result.get("answer", "")

                # Add assistant message with sources
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": result.get("sources", [])
                })

                # Clear the input
                st.session_state.text_input_value = ""
                st.session_state.last_recognized_text = ""
                st.session_state.processing = False
                st.rerun()

            except Exception as e:
                logger.error(f"Error in text input: {e}")
                st.session_state.last_error = str(e)
                if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                    st.session_state.messages.pop()
                st.session_state.processing = False
                st.rerun()


if __name__ == "__main__":
    main()
