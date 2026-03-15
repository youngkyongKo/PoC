# 다음 작업 세션 가이드

## 📌 현재까지 완료된 작업

### ✅ Phase 1: 음성 인터페이스 완료 (2025-02-25)

**구현된 기능:**
- 🎤 음성 입력 → 텍스트 변환 (STT)
- 🤖 Dummy Agent 처리
- 🔊 음성 출력 (TTS)
- 💬 텍스트 입력 대체 옵션
- 📝 대화 기록 및 오디오 재생

**해결된 기술 이슈:**
- Audio recorder 무한 루프
- STT 간헐적 실패 (FFmpeg, 포맷 변환)
- TTS 오디오 재생 (session state 저장)

### ✅ 음성 인터페이스 개선 (2026-03-15)

**신규 기능:**
- 🎯 음성 인식된 텍스트가 입력창에 자동 표시
- ✏️ 인식된 텍스트 수정 가능
- 📤 Form 기반 전송 (에러 해결)
- 🔄 전송 후 자동 초기화

**작동 플로우:**
```
음성 녹음 → STT 인식 → 입력창 자동 입력 → 수정 가능 → 전송 → 응답 받기
```

---

## 🎯 다음 세션: RAG Pipeline 개발

### 전략: Option B (Databricks 우선)
Databricks Workspace에서 리소스를 먼저 생성하고 개발 진행

### 핵심 결정사항
- **임베딩 모델**: Qwen (한글 최적화) - Databricks hosted 선호
- **Unity Catalog**: `main.nh_voice_agent`
- **Vector Search**: Delta Sync Index 사용

---

## 🚀 다음 세션 시작 체크리스트

### Step 1: Databricks 리소스 확인 (필수)

#### 1.1. Qwen 임베딩 모델 찾기 ⭐ 최우선
```python
# Databricks Notebook에서 실행
from databricks.sdk import WorkspaceClient

client = WorkspaceClient()

# Qwen 또는 한글 지원 모델 검색
endpoints = client.serving_endpoints.list()
for endpoint in endpoints:
    name = endpoint.name.lower()
    if 'qwen' in name or 'multilingual' in name or 'e5' in name:
        print(f"✅ Model: {endpoint.name}")
        print(f"   Status: {endpoint.state.ready}")
        print(f"   Type: {endpoint.config.served_models[0].model_name if endpoint.config else 'N/A'}")
        print()
```

**찾아야 할 것:**
- [ ] Qwen 계열 임베딩 모델 endpoint
- [ ] 모델 상태: READY
- [ ] 입력 형식 및 차원 확인

**대안 (우선순위):**
1. `Qwen2.5-*-Instruct` (임베딩 지원 버전)
2. `multilingual-e5-large` (Databricks Foundation)
3. `intfloat/multilingual-e5-large`

#### 1.2. Unity Catalog 생성
```sql
-- Databricks SQL Warehouse 또는 Notebook에서 실행

-- 1. Catalog (기존 main 사용 또는 신규)
CREATE CATALOG IF NOT EXISTS main;

-- 2. Schema
CREATE SCHEMA IF NOT EXISTS main.nh_voice_agent
  COMMENT 'NH Voice Agent PoC Schema';

-- 3. Volume (PDF 저장용)
CREATE VOLUME IF NOT EXISTS main.nh_voice_agent.documents
  COMMENT 'PDF documents storage';

-- 4. 확인
SHOW VOLUMES IN main.nh_voice_agent;
DESCRIBE VOLUME main.nh_voice_agent.documents;
```

**확인 사항:**
- [ ] Catalog 생성 권한 확인
- [ ] Volume 경로: `/Volumes/main/nh_voice_agent/documents`

#### 1.3. Vector Search Endpoint 확인
```
Databricks UI 경로:
Compute → Vector Search Endpoints

확인 사항:
- [ ] Endpoint 이름 기록
- [ ] Status: ONLINE
- [ ] 없으면 신규 생성 필요 (Serverless 추천)
```

**Endpoint 생성 (필요시):**
```python
from databricks.sdk import WorkspaceClient

client = WorkspaceClient()

# Vector Search Endpoint 생성
client.vector_search_endpoints.create_endpoint(
    name="nh_vs_endpoint",
    endpoint_type="STANDARD"  # 또는 "SERVERLESS"
)
```

---

### Step 2: 로컬 환경 설정

```bash
cd /Users/yk.ko/git/PoC/NH_voice_agent
source venv/bin/activate

# RAG 패키지 설치
pip install langchain==0.3.0 \
            langchain-community==0.3.0 \
            sentence-transformers \
            PyPDF2 \
            pypdf \
            pdfplumber

# 설치 확인
pip list | grep -E "langchain|PyPDF2|pypdf|pdfplumber"
```

---

### Step 3: .env 파일 업데이트

```bash
# .env 파일 편집
vim .env

# 아래 내용 추가/수정
UC_CATALOG=main
UC_SCHEMA=nh_voice_agent
UC_VOLUME=documents

VECTOR_SEARCH_ENDPOINT=<Step 1.3에서 확인한 이름>
VECTOR_INDEX_NAME=main.nh_voice_agent.pdf_embeddings_index

EMBEDDING_MODEL=<Step 1.1에서 확인한 Qwen 모델>
```

**확인:**
```bash
python config.py
```

---

### Step 4: 샘플 PDF 준비

```bash
# 테스트 디렉토리 확인
ls -la data/raw/

# 샘플 PDF 복사 (한글 문서 권장)
# 예시:
cp ~/Documents/재무제표_샘플.pdf data/raw/
cp ~/Documents/회계규정.pdf data/raw/

# 확인
ls -lh data/raw/*.pdf
```

**추천 샘플:**
- 한글 PDF 2-3개
- 재무제표, 회계 규정, 사업 보고서
- 페이지 수: 5-20 페이지 (테스트용)

---

## 📋 RAG Pipeline 개발 순서

### Phase 1: PDF 파싱 (1시간)

```bash
# 1_rag_pipeline/01_pdf_parser.py 구현

# 주요 작업:
# - pdfplumber 사용 (한글 지원 우수)
# - 로컬 PDF 읽기
# - Databricks Volume에 업로드
# - Delta Table 생성 (main.nh_voice_agent.parsed_docs)

# 테스트:
python 1_rag_pipeline/01_pdf_parser.py \
    --input_dir data/raw \
    --output_table parsed_docs
```

**출력 테이블 스키마:**
```
main.nh_voice_agent.parsed_docs
- doc_id (string) - UUID
- file_name (string) - 파일명
- page_number (int) - 페이지 번호
- text (string) - 추출된 텍스트
- created_at (timestamp)
```

---

### Phase 2: 텍스트 청킹 (45분)

```bash
# 1_rag_pipeline/02_chunking.py 구현

# 주요 작업:
# - LangChain RecursiveCharacterTextSplitter
# - 한글 토큰 고려 (512 tokens)
# - Overlap 50 tokens
# - Delta Table 생성 (main.nh_voice_agent.chunked_docs)

# 테스트:
python 1_rag_pipeline/02_chunking.py \
    --input_table parsed_docs \
    --output_table chunked_docs
```

**출력 테이블 스키마:**
```
main.nh_voice_agent.chunked_docs
- chunk_id (string) - UUID
- doc_id (string) - 원본 문서 ID
- file_name (string)
- page_number (int)
- chunk_index (int) - 청크 순서
- chunk_text (string) - 청크 텍스트
- chunk_length (int) - 텍스트 길이
- created_at (timestamp)
```

---

### Phase 3: Vector Index 생성 (1시간)

```bash
# 1_rag_pipeline/03_vector_index.py 구현

# 주요 작업:
# - Qwen 임베딩 모델 사용
# - Delta Sync Index 생성
# - Primary Key: chunk_id
# - Embedding Column: chunk_text

# 테스트:
python 1_rag_pipeline/03_vector_index.py \
    --table chunked_docs \
    --index_name pdf_embeddings_index
```

**Vector Index 설정:**
```python
{
  "name": "main.nh_voice_agent.pdf_embeddings_index",
  "endpoint_name": "<확인한_endpoint>",
  "primary_key": "chunk_id",
  "index_type": "DELTA_SYNC",
  "delta_sync_index_spec": {
    "source_table": "main.nh_voice_agent.chunked_docs",
    "embedding_source_column": "chunk_text",
    "embedding_model_endpoint_name": "<Qwen_모델>"
  }
}
```

---

### Phase 4: 파이프라인 통합 (30분)

```bash
# 1_rag_pipeline/pipeline.py 완성

# 전체 플로우:
python 1_rag_pipeline/pipeline.py --input_dir data/raw

# 실행 순서:
# 1. PDF 파싱
# 2. 청킹
# 3. Vector Index 생성 (또는 Sync)
# 4. 상태 확인
```

---

### Phase 5: RAG 쿼리 테스트 (30분)

```python
# test_rag_query.py 작성

from databricks.sdk import WorkspaceClient

client = WorkspaceClient()

# Vector Search 쿼리
results = client.vector_search_indexes.query_index(
    index_name="main.nh_voice_agent.pdf_embeddings_index",
    query_text="재무제표 분석 방법을 알려주세요",
    num_results=5
)

print(f"검색 결과 {len(results.data_array)} 개:")
for i, result in enumerate(results.data_array):
    print(f"\n[{i+1}] Score: {result[0]}")
    print(f"Text: {result[1][:200]}...")
```

---

## 📝 중요 참고 사항

### 한글 처리 최적화
- **PDF 파싱**: pdfplumber 사용 (PyPDF2보다 한글 지원 우수)
- **토크나이저**: LangChain의 기본 토크나이저 또는 tiktoken
- **청크 크기**: 512 tokens (한글 특성 고려)

### Delta Table vs Volume
- **Volume**: PDF 원본 파일 저장
- **Delta Table**: 처리된 텍스트 데이터 저장
- 이유: Delta는 쿼리 최적화, Volume은 파일 저장

### Vector Index 타입
- **DELTA_SYNC**: 자동 동기화 (추천)
- **DIRECT_ACCESS**: 수동 업데이트

---

## 🛠️ 빠른 재시작 명령어

```bash
# 1. 환경 활성화
cd /Users/yk.ko/git/PoC/NH_voice_agent
source venv/bin/activate

# 2. Git 상태 확인
git status
git log --oneline -5

# 3. 현재 Voice App 실행 (테스트)
streamlit run 3_voice_app/app_simple.py

# 4. Databricks 연결 확인
python check_models.py

# 5. Config 검증
python config.py

# 6. 세션 노트 확인
cat SESSION_NOTES.md
```

---

## 💡 트러블슈팅

### Qwen 모델이 없는 경우
```python
# 대안 1: multilingual-e5-large 사용
EMBEDDING_MODEL=databricks-gte-large-en

# 대안 2: Custom Qwen 배포
# HuggingFace에서 다운로드 후 Model Serving 배포
```

### Unity Catalog 권한 에러
```sql
-- 관리자에게 권한 요청
GRANT CREATE SCHEMA ON CATALOG main TO `your_user`;
GRANT CREATE VOLUME ON SCHEMA main.nh_voice_agent TO `your_user`;
```

### Vector Search Endpoint 없음
```
Databricks UI → Compute → Vector Search → Create Endpoint
- Name: nh_vs_endpoint
- Type: Serverless (추천)
```

---

## 📞 다음 세션 시작 방법

1. **이 파일 읽기**
   ```bash
   cat NEXT_STEPS.md
   cat SESSION_NOTES.md
   ```

2. **Databricks Workspace 접속**
   - Qwen 모델 확인 (최우선!)
   - Unity Catalog 리소스 생성

3. **Claude에게 요청**
   - "SESSION_NOTES.md 확인했어. RAG 개발 시작하자"
   - "Databricks에서 Qwen 모델을 확인했어: [모델명]"

---

**Last Updated:** 2026-03-15
**Current Commit:** feat: 음성 인식 텍스트 입력창 자동 표시 기능
**Next Priority:** Databricks Qwen 임베딩 모델 확인 및 Unity Catalog 설정
