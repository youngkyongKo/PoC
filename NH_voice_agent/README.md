# NH Voice Agent

AI 기반 음성 채권 상담 서비스 - Databricks Knowledge Assistant와 Genie Space를 활용한 Multi-Agent RAG 시스템

## 프로젝트 개요

NH 증권의 채권 상품 투자 상담을 지원하는 AI 시스템입니다. 채권 종목 정보 검색, 발행사 정보 조회, 투자 상담을 음성과 텍스트로 제공합니다.

### 주요 기능

- 🎤 **음성 인식**: 한국어 음성 질문 지원 (Speech-to-Text)
- 🔊 **음성 합성**: 답변을 자연스러운 음성으로 제공 (Text-to-Speech)
- 📊 **Genie Space**: 채권 종목 정보 검색 및 비교 (SQL 기반)
- 📚 **Knowledge Assistant**: 채권 상품 설명서 검색 (PDF 기반 RAG)
- 🤖 **Multi-Agent Supervisor**: 질문 유형에 따른 적절한 도구 선택 및 라우팅

### 기술 스택

- **플랫폼**: Databricks (Unity Catalog, Vector Search, Model Serving)
- **AI 모델**: Claude Sonnet 4.6, Qwen3 Embedding
- **웹 프레임워크**: Streamlit
- **음성 처리**: Edge TTS (Microsoft Neural TTS)
- **배포**: Databricks Apps

## 프로젝트 구조

```
NH_voice_agent/
├── 1_rag_pipeline/          # RAG 파이프라인 (PDF 처리, 벡터 인덱싱)
│   ├── 01_pdf_parser.py     # PDF 문서 파싱
│   ├── 02_chunking.py       # 문서 청킹
│   ├── 03_vector_index.py   # 벡터 인덱스 생성
│   └── pipeline.py          # 통합 파이프라인
│
├── 2_agent/                 # Agent 구현
│   ├── supervisor_agent.py # 멀티 에이전트 조정
│   ├── knowledge_assistant_tool.py  # KA 도구
│   └── genie_tool.py        # Genie Space 도구
│
├── 3_voice_app/            # Streamlit 음성 앱
│   ├── app.py              # 메인 애플리케이션
│   ├── app.yaml            # Databricks Apps 설정
│   ├── config.py           # 설정 관리
│   ├── stt.py              # Speech-to-Text
│   ├── tts.py              # Text-to-Speech
│   ├── supervisor_agent.py # Agent (앱용)
│   ├── knowledge_assistant_tool.py
│   ├── genie_tool.py
│   └── requirements.txt
│
└── notebooks/              # Jupyter 노트북 (설정 및 테스트)
    ├── 01_Setup_Unity_Catalog.py
    ├── 02a_Knowledge_Assistant_Setup.py
    └── 03_Test_Knowledge_Assistant.py
```

## 설치 및 실행

### 1. RAG 파이프라인 실행

```bash
cd 1_rag_pipeline
pip install -r requirements.txt

# PDF 파싱 및 벡터 인덱스 생성
python pipeline.py
```

### 2. Voice App 로컬 실행

```bash
cd 3_voice_app
pip install -r requirements.txt

# 환경 변수 설정 (.env 파일 생성)
# DATABRICKS_HOST, DATABRICKS_TOKEN 등 설정

# Streamlit 앱 실행
streamlit run app.py
```

### 3. Databricks Apps 배포

```bash
cd 3_voice_app

# 파일 업로드
databricks workspace import-dir . /Workspace/Users/<your-email>/nh_voice_app_v2

# 앱 배포
databricks apps deploy nh-voice-agent \
  --source-code-path /Workspace/Users/<your-email>/nh_voice_app_v2 \
  --mode SNAPSHOT
```

## 환경 변수 설정

`3_voice_app/.env` 파일 또는 `app.yaml`에서 다음 환경 변수를 설정:

```bash
# Unity Catalog
UC_CATALOG=demo_ykko
UC_SCHEMA=nh_voice_agent
UC_VOLUME=vol_data

# Vector Search
VECTOR_SEARCH_ENDPOINT=one-env-shared-endpoint-11
VECTOR_INDEX_NAME=demo_ykko.nh_voice_agent.doc_embed_index

# Knowledge Assistant
KA_ENDPOINT_NAME=ka-69e8398a-endpoint

# Genie Space (선택사항)
GENIE_SPACE_ID=your_genie_space_id
SQL_WAREHOUSE_ID=your_warehouse_id

# Models
EMBEDDING_MODEL=databricks-qwen3-embedding-0-6b
LLM_MODEL=databricks-claude-sonnet-4-6
SERVING_ENDPOINT=databricks-claude-sonnet-4-6

# Voice Settings
SPEECH_LANGUAGE=ko-KR
TTS_LANGUAGE=ko
TTS_VOICE_NAME=ko-KR-SunHiNeural
TTS_SPEAKING_RATE=+20%
TTS_PITCH=+5Hz

# Application
DEBUG=True
LOG_LEVEL=INFO
```

## 사용 방법

1. **음성 입력**: 마이크 버튼을 클릭하여 음성으로 질문
2. **샘플 질문**: 화면의 샘플 질문을 클릭하여 빠른 테스트
3. **텍스트 입력**: 하단 입력창에 직접 질문 입력
4. **답변 듣기**: Assistant 응답이 자동으로 음성으로 재생

### 질문 예시

**채권 검색 (Genie Space)**
- "A- 이상 등급인 회사채를 수익률 높은 순으로 보여줘"
- "만기 1년 미만인 채권 중 수익률이 높은 종목은?"
- "롯데캐피탈에서 발행한 채권을 비교해줘"
- "민평금리보다 싼 회사채는?"

**발행사 정보 (Knowledge Assistant)**
- "DL에너지 회사에 대해 알려줘"
- "이 발행사가 무슨 일을 하는 회사야?"
- "신용등급 전망은 어때?"
- "투자 리스크는 뭐가 있어?"

**복합 질의 (Multi-Agent)**
- "DL에너지 채권을 자세히 알려줘" (종목 정보 + 회사 소개)

## 주요 기능 설명

### Multi-Agent Supervisor (LangGraph)

사용자 질문을 분석하여 적절한 도구를 선택하고 라우팅:

**라우팅 규칙**
- 채권 검색, 비교, 수치 분석 → **Genie Space**
  - 예: "A 등급 채권", "수익률 비교", "만기 조건"
- 발행사 정보, 회사 소개, 리스크 → **Knowledge Assistant**
  - 예: "회사 소개", "사업 내용", "신용평가 요인"
- 복합 질의 → **순차적 도구 호출**
  - 예: "DL에너지 채권 자세히" → Genie + KA

### Genie Space (채권 종목 정보)

- **테이블**: `demo_ykko.nh_voice_agent.fundinfo` (28개 채권)
- **데이터**: 신용등급, 수익률, 만기일, 발행사, 표면금리 등
- **기능**: 자연어 → SQL 변환, 조건 검색, 비교 분석
- **Space ID**: `01f128b75fcd1eb8be6fab662cf566f1`

### Knowledge Assistant (채권 상품 설명서)

- **데이터**: 채권 상품 설명서 PDF 문서
- **내용**: 발행사 소개, 사업 개요, 신용평가 요인, 재무 상황, 리스크
- **기능**: PDF 청킹 → Vector Search → RAG 생성
- **Endpoint**: `ka-69e8398a-endpoint`

### Voice Interface

- **STT**: 브라우저 기반 음성 인식 (ko-KR)
- **TTS**: Microsoft Edge TTS (고품질 한국어 음성)
- 실시간 음성 변환 및 자동 재생

## 배포 정보

- **플랫폼**: Databricks Apps
- **앱 URL**: https://e2-demo-field-eng.cloud.databricks.com/apps/nh-voice-agent
- **컴퓨팅**: Serverless (CPU: 2, Memory: 4Gi)

## 문서

- [DEPLOYMENT.md](DEPLOYMENT.md) - **배포 가이드 및 테스트 방법** ⭐
- [multi_agent_supervisor_prompt.md](multi_agent_supervisor_prompt.md) - Supervisor 프롬프트 상세
- [genie_space_config.md](genie_space_config.md) - Genie Space 구성 가이드
- [TTS_GUIDE.md](TTS_GUIDE.md) - Text-to-Speech 설정 가이드
- [1_rag_pipeline/README.md](1_rag_pipeline/README.md) - RAG 파이프라인 상세
- [2_agent/README.md](2_agent/README.md) - Agent 구현 상세
- [3_voice_app/README.md](3_voice_app/README.md) - Voice App 상세

## 배포 상태

### ✅ 완료된 구성

1. **데이터 준비**
   - ✓ 채권 종목 테이블 생성 (`demo_ykko.nh_voice_agent.fundinfo`)
   - ✓ 28개 채권 샘플 데이터 입력
   - ✓ 채권 상품 설명서 PDF 문서 업로드

2. **Genie Space**
   - ✓ Space 생성 완료 (ID: `01f128b75fcd1eb8be6fab662cf566f1`)
   - ✓ 테이블 연결 및 Instructions 구성
   - ✓ Sample Questions 등록

3. **Knowledge Assistant**
   - ✓ Vector Index 생성
   - ✓ Serving Endpoint 배포 (`ka-69e8398a-endpoint`)
   - ✓ RAG 기능 테스트 완료

4. **Multi-Agent Supervisor**
   - ✓ LangGraph 기반 Supervisor Agent 구현
   - ✓ Genie Tool & Knowledge Assistant Tool 구현
   - ✓ 채권 도메인 특화 라우팅 로직 구현
   - ✓ Databricks Workspace에 배포

### 📋 다음 단계

- [ ] Databricks 노트북에서 통합 테스트
- [ ] Voice App과 연동
- [ ] 복합 질의 처리 개선 (순차적 도구 호출)
- [ ] 수익 계산 로직 추가

## 라이선스

이 프로젝트는 데모 및 PoC 용도로 제작되었습니다.
