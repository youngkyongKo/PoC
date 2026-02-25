# NH Voice Agent PoC

Databricks 플랫폼을 활용한 음성 기반 RAG Agent 시스템

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

- [x] 프로젝트 구조 생성
- [ ] RAG 파이프라인 구현
- [ ] Agent 툴 개발
- [ ] Supervisor Agent 통합
- [ ] 음성 인터페이스 구현
- [ ] 통합 테스트 및 데모

## 라이선스

PoC Project - Internal Use Only
