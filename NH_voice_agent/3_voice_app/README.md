# 음성 인터페이스 App

음성으로 질문하고 답변을 들을 수 있는 Streamlit 기반 웹 앱

## 기능

1. **음성 입력 (STT)**: 마이크로 질문 입력
2. **Agent 처리**: Supervisor Agent를 통한 질의 처리
3. **음성 출력 (TTS)**: 답변을 음성으로 재생

## 사용법

### 앱 실행

```bash
streamlit run app.py
```

### 사용 방법

1. 웹 브라우저에서 앱 접속
2. "녹음 시작" 버튼 클릭
3. 질문 말하기
4. "녹음 중지" 버튼 클릭
5. Agent가 답변 생성
6. 자동으로 음성 재생

## 지원 음성

- **입력**: 한국어 음성 인식
- **출력**: 한국어 TTS (gTTS)

## 기술 스택

- **Frontend**: Streamlit
- **STT**: OpenAI Whisper / SpeechRecognition
- **TTS**: gTTS (Google Text-to-Speech)
- **Audio**: PyAudio, pydub
