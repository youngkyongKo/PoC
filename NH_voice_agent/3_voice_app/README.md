# NH Voice Agent - Voice UI

음성으로 질문하고 답변을 들을 수 있는 Streamlit 웹 앱

## 구성 요소

1. **app.py**: 메인 Voice Agent 앱 (SupervisorAgent 연동)
2. **app_simple.py**: 테스트용 앱 (Dummy Agent)
3. **stt.py**: Speech-to-Text (Google STT 사용)
4. **tts.py**: Text-to-Speech (gTTS 사용)

## Architecture

```
Voice UI (Streamlit)
    ├── Speech-to-Text (Google STT)
    ├── Supervisor Agent
    │   ├── Knowledge Assistant Tool (문서 RAG)
    │   └── Genie Space Tool (SQL 분석)
    └── Text-to-Speech (gTTS)
```

## 사전 요구사항

### 1. 환경 변수 설정

`.env` 파일에 다음 설정:

```bash
# Databricks 인증
DATABRICKS_HOST=your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...

# Model Serving
SERVING_ENDPOINT=databricks-meta-llama-3-3-70b-instruct

# Knowledge Assistant
KA_ENDPOINT_NAME=ka-69e8398a-endpoint
KA_TILE_ID=69e8398a

# Genie Space (선택)
GENIE_SPACE_ID=your_genie_space_id

# 기타 설정
SPEECH_LANGUAGE=ko-KR
TTS_LANGUAGE=ko
```

### 2. 의존성 설치

```bash
cd /Users/yk.ko/git/PoC/NH_voice_agent
pip install -r requirements.txt
```

### 3. 마이크 권한

브라우저에서 마이크 접근 권한 허용 필요

## 실행 방법

### 메인 앱 실행

```bash
cd 3_voice_app
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 자동 실행

### 테스트 앱 실행

Databricks 연결 없이 UI만 테스트:

```bash
streamlit run app_simple.py
```

## 사용 방법

### 음성 입력

1. **"녹음하려면 클릭하세요"** 버튼 클릭
2. 질문 말하기 (3-5초)
3. 다시 클릭하여 녹음 중지
4. 자동으로 음성 인식 → Agent 응답 → TTS 음성 재생

### 텍스트 입력

- 하단 **"텍스트 입력"** 섹션에서 직접 입력 가능
- 음성 인식 실패 시 대안으로 사용

## 테스트 질문 예시

### Knowledge Assistant 질문

```
회사 홈페이지 URL은?
보험계약을 중도 해지시 해지환급금은 이미 납입한 보험료보다 적거나 없는 경우, 이유는?
```

### Genie Space 질문 (설정 시)

```
지난달 판매 실적은?
상품별 가입자 통계를 보여줘
```

## 문제 해결

### 음성 인식 실패

**증상**: "음성 인식에 실패했습니다" 메시지

**해결책**:
1. 더 크고 명확하게 말씀하세요
2. 3-5초 이상 말씀하세요
3. 조용한 환경에서 녹음하세요
4. 마이크 권한 확인
5. 텍스트 입력 사용

### Agent 초기화 실패

**증상**: "Agent 초기화 실패" 메시지

**해결책**:
```bash
# .env 설정 확인
# KA Endpoint 상태 확인
databricks serving-endpoints get --name $KA_ENDPOINT_NAME
```

### Audio 에러

**macOS**:
```bash
brew install ffmpeg portaudio
pip install --upgrade pyaudio
```

**Linux**:
```bash
sudo apt-get install ffmpeg portaudio19-dev
pip install --upgrade pyaudio
```

## 기술 스택

- **Frontend**: Streamlit, audio-recorder-streamlit
- **STT**: Google Speech Recognition
- **TTS**: gTTS (Google Text-to-Speech)
- **Audio**: PyAudio, pydub
- **Agent**: LangChain + Databricks
