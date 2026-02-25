# NH Voice Agent PoC

Databricks 플랫폼을 활용한 음성 기반 RAG Agent 시스템

> **현재 상태 (2025-02-25):** Phase 1 완료 - 음성 인터페이스 테스트 환경 구축 완료
> 상세 진행 상황은 [README_PROGRESS.md](README_PROGRESS.md) 참고

## 🚀 빠른 시작 (현재 가능한 기능)

### 음성 인터페이스 테스트하기

```bash
# 1. 가상환경 활성화
source venv/bin/activate

# 2. Streamlit 앱 실행
streamlit run 3_voice_app/app_simple.py

# 또는 CLI에서 테스트
python test_voice_flow.py
```

**현재 동작하는 기능:**
- 🎤 음성 입력 → 텍스트 변환 (Google Speech Recognition)
- 🤖 Dummy Agent 처리 (테스트용)
- 🔊 답변 음성 출력 (gTTS)
- 💬 텍스트 입력 (음성 대신 타이핑 가능)
- 📝 대화 기록 표시 및 오디오 재생

**필수 사항:**
- FFmpeg 설치: `brew install ffmpeg`
- 인터넷 연결 (STT/TTS API 사용)

---

## 프로젝트 구성

### 1. RAG 파이프라인 (`1_rag_pipeline/`)
- PDF 문서 파싱 및 청킹
- Vector Search 인덱스 생성
- Databricks Delta Live Tables 활용

### 2. Multi-Agent Supervisor (`2_agent/`)
- LangChain 기반 Agent 구현
- Vector Search Tool 통합
- Genie Space Tool 통합
- Supervisor Agent 오케스트레이션

### 3. 음성 App (`3_voice_app/`)
- Speech-to-Text (음성 입력)
- Agent 질의 처리
- Text-to-Speech (음성 출력)
- Streamlit 기반 UI

## 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 Databricks 설정 입력
```

### 2. RAG 파이프라인 실행

```bash
cd 1_rag_pipeline
python pipeline.py
```

### 3. Agent 테스트

```bash
cd 2_agent
python test_agent.py
```

### 4. 음성 App 실행

```bash
cd 3_voice_app
streamlit run app.py
```

## Databricks 요구사항

- Unity Catalog 활성화된 Workspace
- Vector Search 엔드포인트
- SQL Warehouse (Genie Space용)
- ML Runtime Cluster

## 프로젝트 구조

```
NH_voice_agent/
├── 1_rag_pipeline/          # RAG 파이프라인
│   ├── 01_pdf_parser.py     # PDF 파싱
│   ├── 02_chunking.py       # 청킹 처리
│   ├── 03_vector_index.py   # 벡터 인덱스 생성
│   └── pipeline.py          # 전체 파이프라인
│
├── 2_agent/                 # Agent 구현
│   ├── vector_search_tool.py
│   ├── genie_tool.py
│   ├── supervisor_agent.py
│   └── test_agent.py
│
└── 3_voice_app/             # 음성 앱
    ├── app.py
    ├── stt.py
    └── tts.py
```

## 개발 로드맵

### Phase 1: 음성 인터페이스 (완료 ✅)
- [x] 프로젝트 구조 생성
- [x] 음성 입력 (STT) 구현
- [x] 음성 출력 (TTS) 구현
- [x] Streamlit UI 구현
- [x] Dummy Agent 테스트 환경

### Phase 2: RAG Pipeline (진행 예정)
- [ ] PDF 파싱 및 청킹
- [ ] Vector Search 인덱스 생성
- [ ] DLT 파이프라인 구현

### Phase 3: Agent System (진행 예정)
- [ ] Vector Search Tool 개발
- [ ] Genie Space Tool 개발
- [ ] LangChain Supervisor Agent 통합

### Phase 4: 통합 및 배포 (진행 예정)
- [ ] Voice App ↔ Real Agent 연동
- [ ] Databricks Workspace 배포
- [ ] 성능 최적화

## 라이선스

PoC Project - Internal Use Only
