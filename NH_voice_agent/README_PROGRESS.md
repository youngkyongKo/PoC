# NH Voice Agent - 진행 상황

## 📌 현재 상태 (2025-02-25)

### ✅ 완료된 작업

#### 1. 프로젝트 구조 설정
- 3개 모듈 구조 생성: `1_rag_pipeline/`, `2_agent/`, `3_voice_app/`
- 환경 설정 파일 (`config.py`, `.env`, `requirements.txt`)
- Git 저장소 초기화 및 `.gitignore` 설정

#### 2. 음성 인터페이스 구현 ✅ **완료**
**구성 요소:**
- `2_agent/dummy_agent.py` - 테스트용 더미 에이전트
- `3_voice_app/stt.py` - Speech-to-Text (Google Speech Recognition)
- `3_voice_app/tts.py` - Text-to-Speech (gTTS)
- `3_voice_app/app_simple.py` - Streamlit 음성 인터페이스 앱
- `test_voice_flow.py` - 전체 플로우 테스트 스크립트

**해결된 이슈:**
1. ✅ Audio Recorder 무한 루프 문제
   - 원인: `st.rerun()` 반복 호출
   - 해결: `session_state.last_audio_bytes`로 중복 처리 방지

2. ✅ STT 간헐적 실패 문제
   - 원인: FFmpeg 미설치, 오디오 포맷 불일치 (WebM → WAV)
   - 해결: FFmpeg 설치, pydub 오디오 변환 추가, 에러 처리 개선

3. ✅ TTS 오디오 재생 문제
   - 원인: `st.rerun()` 후 오디오 데이터 손실
   - 해결: `session_state.audio_responses`에 오디오 저장, 채팅 히스토리에 표시

**현재 동작:**
```
사용자 음성 입력 → STT (Google) → Dummy Agent → TTS (gTTS) → 오디오 재생
     또는
사용자 텍스트 입력 → Dummy Agent → TTS (gTTS) → 오디오 재생
```

#### 3. 개발 환경 설정
- Python 가상환경 설정
- 필수 패키지 설치:
  - Databricks SDK
  - Streamlit, audio-recorder-streamlit
  - SpeechRecognition, gTTS, pydub
  - FFmpeg (brew install ffmpeg)

### 🚧 진행 예정 작업

#### Phase 1: RAG Pipeline 구현
**목표:** PDF 문서를 처리하여 Vector Search 인덱스 생성

1. **PDF 파싱 및 청킹**
   - `1_rag_pipeline/pdf_parser.py` 구현
   - `1_rag_pipeline/chunker.py` 구현

2. **Vector Search 설정**
   - Unity Catalog 설정 (catalog, schema, volume)
   - Embedding 모델 endpoint 확인
   - Delta Sync Index 생성

3. **DLT 파이프라인**
   - `1_rag_pipeline/dlt_pipeline.py` 구현
   - Databricks Notebook 배포

#### Phase 2: Multi-Agent Supervisor 구현
**목표:** LangChain 기반 에이전트 시스템 구성

1. **Vector Search Tool**
   - `2_agent/tools/vector_search_tool.py` 구현
   - RAG 쿼리 기능

2. **Genie Space Tool**
   - `2_agent/tools/genie_tool.py` 구현
   - SQL 기반 데이터 쿼리

3. **Supervisor Agent**
   - `2_agent/supervisor_agent.py` 구현
   - Multi-agent orchestration
   - `dummy_agent.py`를 실제 agent로 교체

#### Phase 3: 통합 및 배포
1. Voice App과 실제 Agent 연동
2. Databricks Workspace 배포
3. 성능 최적화 및 테스트

## 🎯 다음 세션 시작 방법

### 1. 환경 활성화
```bash
cd /Users/yk.ko/git/PoC/NH_voice_agent
source venv/bin/activate
```

### 2. 현재 Voice App 테스트
```bash
# 전체 플로우 테스트 (음성 입력/출력)
python test_voice_flow.py

# Streamlit 앱 실행
streamlit run 3_voice_app/app_simple.py
```

### 3. RAG Pipeline 작업 시작
```bash
# Databricks 연결 확인
python check_models.py

# RAG 구현 시작
# - 1_rag_pipeline/pdf_parser.py 구현
# - 1_rag_pipeline/chunker.py 구현
# - Unity Catalog 설정
```

## 📁 주요 파일 설명

### 설정 파일
- `.env` - 환경 변수 (Databricks 접속 정보, 모델 설정)
- `config.py` - 중앙 설정 관리
- `requirements.txt` - Python 패키지 목록

### 음성 인터페이스 (완료)
- `2_agent/dummy_agent.py` - 더미 에이전트 (테스트용)
- `3_voice_app/stt.py` - Speech-to-Text
- `3_voice_app/tts.py` - Text-to-Speech
- `3_voice_app/app_simple.py` - Streamlit 앱

### 테스트
- `test_voice_flow.py` - 음성 전체 플로우 테스트
- `check_models.py` - Databricks 모델 endpoint 확인

## 🔧 기술 스택

### 현재 사용 중
- **STT**: Google Speech Recognition API
- **TTS**: gTTS (Google Text-to-Speech)
- **Audio**: pydub, FFmpeg
- **UI**: Streamlit, audio-recorder-streamlit
- **Agent**: Custom (dummy → LangChain으로 전환 예정)

### 향후 사용 예정
- **Databricks**: Unity Catalog, Vector Search, Model Serving
- **LangChain**: Multi-agent supervisor, Tools
- **RAG**: PDF parsing, chunking, embeddings

## 📝 참고 사항

### Audio 처리
- 브라우저에서 WebM 포맷으로 녹음됨
- pydub로 WAV (16kHz, mono)로 변환
- FFmpeg 필수 설치 필요

### Streamlit Session State
- `messages` - 채팅 히스토리
- `agent` - 에이전트 인스턴스
- `last_audio_bytes` - 마지막 처리된 오디오 (중복 방지)
- `audio_responses` - 각 메시지의 오디오 데이터

### Databricks 연결
- `.env` 파일에 `DATABRICKS_HOST`, `DATABRICKS_TOKEN` 설정
- Unity Catalog 구조: `{catalog}.{schema}.{table/volume}`
- Model Serving endpoint: `databricks-bge-large-en` (embedding)

## 🐛 알려진 제한사항

1. **STT 정확도**
   - 조용한 환경 필요
   - 3-5초 이상 명확한 발음 권장
   - 네트워크 연결 필요 (Google API)

2. **TTS 품질**
   - gTTS는 기본 품질 (향후 premium TTS로 업그레이드 가능)
   - 인터넷 연결 필요

3. **Dummy Agent**
   - 실제 AI 처리 없음
   - 고정된 응답 패턴

## 🎉 성공 기준

### Phase 1 (현재) ✅
- [x] 음성 입력 → 텍스트 변환
- [x] 더미 에이전트 응답
- [x] 텍스트 → 음성 변환 및 재생
- [x] Streamlit UI

### Phase 2 (진행 예정)
- [ ] PDF 파싱 및 Vector Search 인덱싱
- [ ] LangChain 에이전트 구현
- [ ] Vector Search Tool 연동
- [ ] Genie Space Tool 연동

### Phase 3 (진행 예정)
- [ ] 전체 시스템 통합
- [ ] Databricks Workspace 배포
- [ ] 성능 최적화
