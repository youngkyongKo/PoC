# 작업 세션 노트 (2026-03-15)

## ✅ 완료된 작업

### 1. 환경 상태 확인 ✅
**시스템 환경:**
- Python 3.14.3
- FFmpeg 8.0.1
- 가상환경: 456MB (56개 패키지)
- Databricks 연결: 정상

**설치된 패키지:**
- streamlit (1.54.0)
- audio-recorder-streamlit (0.0.10)
- SpeechRecognition (3.14.5)
- gTTS (2.5.4)
- pydub (0.25.1)
- databricks-sdk (0.92.0)

**미설치 (RAG 작업 시 필요):**
- langchain, langchain-community
- sentence-transformers
- PyPDF2, pypdf, pdfplumber

### 2. Voice App 개선 완료 ✅

**기능 추가:**
음성 인식된 텍스트를 입력창에 자동 표시

**변경 사항:**
- `3_voice_app/app_simple.py` 수정
- `st.form` 사용으로 에러 해결
- 음성 인식 → 텍스트 입력창 자동 입력 → 수정 가능 → 전송

**작동 플로우:**
```
1. 음성 녹음 (audio recorder)
2. STT 인식 → "✅ 인식된 텍스트: xxx" 표시
3. 텍스트 입력창에 자동 입력
4. 사용자가 필요시 수정
5. "전송" 버튼 클릭
6. Agent 응답 + TTS 음성
7. 입력창 자동 초기화
```

**해결한 이슈:**
- Session state widget key 충돌 에러
- Form을 사용한 입력 처리로 해결

### 3. RAG 개발 계획 수립 ✅

**사용자 요구사항:**
- 한글 처리가 우수한 **Qwen 임베딩 모델** 사용
- **Databricks-hosted 모델** 선호
- **Option B (Databricks 우선)** 개발 방식 선택

**개발 로드맵 (총 4.5시간 예상):**
1. Phase 1: 환경 설정 (30분)
2. Phase 2: PDF 파싱 구현 (1시간)
3. Phase 3: 텍스트 청킹 (45분)
4. Phase 4: Vector Search 인덱스 생성 (1시간)
5. Phase 5: 파이프라인 통합 (30분)
6. Phase 6: RAG 쿼리 테스트 (30분)

---

## 🎯 다음 세션에서 할 일

### Priority 1: Databricks 리소스 확인 및 설정

#### Step 1: Qwen 임베딩 모델 확인
```python
# Databricks Workspace에서 실행
from databricks.sdk import WorkspaceClient

client = WorkspaceClient()

# Qwen 모델 검색
endpoints = client.serving_endpoints.list()
for endpoint in endpoints:
    if 'qwen' in endpoint.name.lower():
        print(f"Model: {endpoint.name}")
        print(f"Status: {endpoint.state.ready}")
```

**찾아야 할 정보:**
- Qwen 계열 임베딩 모델 endpoint 이름
- 모델 상태 (READY 확인)
- 입력/출력 차원 확인

**대안 모델 (한글 지원):**
- `multilingual-e5-large` (Databricks Foundation Models)
- `intfloat/multilingual-e5-large`
- Custom deployed Qwen model

#### Step 2: Unity Catalog 리소스 생성
```sql
-- Databricks SQL 또는 Notebook에서 실행

-- 1. Catalog 생성 (또는 기존 사용)
CREATE CATALOG IF NOT EXISTS main;

-- 2. Schema 생성
CREATE SCHEMA IF NOT EXISTS main.nh_voice_agent;

-- 3. Volume 생성 (PDF 저장용)
CREATE VOLUME IF NOT EXISTS main.nh_voice_agent.documents;

-- 4. 확인
SHOW VOLUMES IN main.nh_voice_agent;
```

#### Step 3: Vector Search Endpoint 확인
```
Databricks UI → Compute → Vector Search
- Endpoint 이름 확인
- Status: ONLINE 확인
- 없으면 신규 생성 필요
```

#### Step 4: .env 파일 업데이트
```bash
# Unity Catalog
UC_CATALOG=main
UC_SCHEMA=nh_voice_agent
UC_VOLUME=documents

# Vector Search
VECTOR_SEARCH_ENDPOINT=<확인한_endpoint_이름>
VECTOR_INDEX_NAME=main.nh_voice_agent.pdf_embeddings_index

# Embedding Model (Qwen 또는 대안)
EMBEDDING_MODEL=<확인한_qwen_모델_endpoint>

# LLM Model
LLM_MODEL=databricks-dbrx-instruct
SERVING_ENDPOINT=databricks-dbrx-instruct
```

---

### Priority 2: RAG 패키지 설치

```bash
cd /Users/yk.ko/git/PoC/NH_voice_agent
source venv/bin/activate

# RAG 필수 패키지
pip install langchain langchain-community sentence-transformers \
            PyPDF2 pypdf pdfplumber
```

---

### Priority 3: 샘플 PDF 준비

```bash
# 테스트용 PDF 파일 준비
mkdir -p data/raw

# 샘플 PDF 복사 (한글 문서)
# 예: 재무제표, 회계 규정, 기업 보고서 등
cp /path/to/korean_sample.pdf data/raw/
```

**추천 샘플:**
- 한글 재무제표 PDF (2-3개)
- 회계 규정 문서
- 내부 정책 문서

---

### Priority 4: RAG Pipeline 개발 시작

**개발 순서:**

#### 4.1. PDF 파싱 구현
```bash
# 01_pdf_parser.py 완성
# - pdfplumber 사용 (한글 지원 우수)
# - Unity Catalog Volume 업로드
# - Delta Table 저장

python 1_rag_pipeline/01_pdf_parser.py \
    --input_dir data/raw \
    --output_table parsed_docs
```

#### 4.2. 텍스트 청킹 구현
```bash
# 02_chunking.py 완성
# - LangChain RecursiveCharacterTextSplitter
# - 한글 토큰화 고려
# - Chunk size: 512 tokens (조정 가능)

python 1_rag_pipeline/02_chunking.py \
    --input_table parsed_docs \
    --output_table chunked_docs
```

#### 4.3. Vector Index 생성
```bash
# 03_vector_index.py 완성
# - Qwen 임베딩 모델 사용
# - Delta Sync Index 생성

python 1_rag_pipeline/03_vector_index.py \
    --table chunked_docs \
    --index_name pdf_embeddings_index
```

---

## 📚 참고 정보

### Unity Catalog 구조
```
main (catalog)
└── nh_voice_agent (schema)
    ├── documents (volume) - PDF 원본 저장
    ├── parsed_docs (table) - 파싱된 텍스트
    ├── chunked_docs (table) - 청크된 텍스트
    └── pdf_embeddings_index (vector index) - 임베딩 인덱스
```

### 필요한 Databricks 권한
- Unity Catalog: CREATE CATALOG, CREATE SCHEMA, CREATE VOLUME
- Vector Search: CREATE INDEX, QUERY INDEX
- Model Serving: USE ENDPOINT

### 한글 임베딩 모델 옵션
1. **Qwen2.5** (선호)
   - multilingual 지원
   - 한중일 언어 우수
   - Databricks hosted 확인 필요

2. **multilingual-e5-large** (대안)
   - Databricks Foundation Models
   - 100+ 언어 지원
   - 768 차원

3. **Custom deployment**
   - HuggingFace에서 Qwen 모델 다운로드
   - Databricks Model Serving으로 배포

---

## 🔧 개발 환경

### 빠른 재시작
```bash
cd /Users/yk.ko/git/PoC/NH_voice_agent
source venv/bin/activate

# 현재 Voice App 테스트
streamlit run 3_voice_app/app_simple.py

# Databricks 연결 확인
python check_models.py

# Config 검증
python config.py
```

### Git 상태
```
Modified: 3_voice_app/app_simple.py
Untracked: .claude/
```

**다음 세션 시작 시:**
```bash
# Voice App 변경사항 커밋
git add 3_voice_app/app_simple.py
git commit -m "feat: 음성 인식 텍스트 입력창 자동 표시 기능 추가"

# .claude 디렉토리 제외
echo ".claude/" >> .gitignore
git add .gitignore
git commit -m "chore: .claude 디렉토리 제외"

# 원격 저장소 푸시 (선택)
git push origin main
```

---

## 💡 중요 결정 사항

### 1. 임베딩 모델: Qwen (한글 최적화)
- Databricks hosted Qwen 모델 확인 필요
- 없으면 multilingual-e5-large 사용 또는 custom deploy

### 2. 개발 방식: Option B (Databricks 우선)
- Databricks Notebook에서 개발
- Unity Catalog 리소스 먼저 생성
- 로컬 코드와 동기화

### 3. Unity Catalog 구조
- Catalog: `main`
- Schema: `nh_voice_agent`
- Volume: `documents`

---

## ❓ 확인이 필요한 사항

### Databricks 환경
- [ ] Qwen 임베딩 모델 endpoint 확인
- [ ] Vector Search endpoint 존재 여부
- [ ] Unity Catalog 생성 권한
- [ ] Serverless vs Cluster 선택

### 샘플 데이터
- [ ] 테스트용 한글 PDF 준비
- [ ] PDF 개수 및 크기 결정

### 성능 파라미터
- [ ] Chunk size (기본: 512 tokens)
- [ ] Chunk overlap (기본: 50 tokens)
- [ ] Top K results (기본: 5)

---

## 📞 다음 세션 시작 방법

1. **Databricks Workspace 접속**
   - Qwen 모델 확인
   - Unity Catalog 리소스 생성

2. **환경 활성화**
   ```bash
   cd /Users/yk.ko/git/PoC/NH_voice_agent
   source venv/bin/activate
   ```

3. **이 문서 확인**
   ```bash
   cat SESSION_NOTES.md
   ```

4. **Claude에게 알리기**
   "이전 세션 노트(SESSION_NOTES.md)를 보고 RAG 개발을 계속하자"

---

**Last Updated:** 2026-03-15
**Current Branch:** main
**Next Focus:** Databricks 리소스 확인 및 Qwen 임베딩 모델 설정
