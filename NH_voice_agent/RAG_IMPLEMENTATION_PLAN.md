# RAG 구현 계획 - 업데이트 (2026-03-16)

## 🔍 Databricks Agent Bricks & Embedding Models 검토 결과

### ✅ 발견한 한글 지원 Embedding Models

Databricks workspace에서 한글 처리가 우수한 embedding 모델들을 확인했습니다:

| 모델 | Status | 한글 지원 | 추천도 |
|------|--------|----------|--------|
| **databricks-qwen3-embedding-0-6b** | READY | ⭐⭐⭐⭐⭐ 최우수 | **1순위** |
| **bge_m3_embedding** (system.ai.bge_m3) | READY | ⭐⭐⭐⭐⭐ 최우수 | **1순위** |
| databricks-gte-large-en | READY | ⭐⭐⭐ 보통 | 3순위 |
| databricks-bge-large-en | READY | ⭐⭐ 낮음 (영어 특화) | 4순위 |

**핵심 발견:**
- ✅ **Qwen3 Embedding**: Alibaba Qwen 계열, 한중일 언어 최적화
- ✅ **BGE-M3**: 100+ 언어 지원 multilingual 모델, 한글 성능 검증됨
- ✅ 두 모델 모두 Databricks Foundation Models로 즉시 사용 가능

---

## 🎯 두 가지 구현 옵션

### Option A: Databricks Knowledge Assistant (KA) 사용 🚀

#### 특징
- **자동화된 RAG 시스템**: PDF 업로드만으로 RAG 구축 완료
- **관리 용이**: UI에서 손쉬운 생성/관리
- **빠른 프로토타이핑**: 2-5분 내 프로비저닝
- **자동 인덱싱**: Volume의 문서를 자동으로 임베딩 및 인덱싱

#### 장점
✅ **개발 속도**: 코드 없이 UI/API로 즉시 생성
✅ **유지보수**: 자동 업데이트, 자동 스케일링
✅ **통합 용이**: Supervisor Agent에 바로 연결 가능
✅ **평가 기능**: 내장 evaluation 도구

#### 단점
⚠️ **Embedding Model 선택 불가**: 기본 모델 사용 (어떤 모델인지 불명확)
⚠️ **커스터마이징 제약**: 청킹, 검색 파라미터 조정 제한
⚠️ **한글 성능 검증 필요**: 실제 테스트 전까지 성능 불확실

#### 구현 단계
```python
# 1. Volume에 PDF 업로드
# 2. Knowledge Assistant 생성
from databricks.sdk import WorkspaceClient

client = WorkspaceClient()

# KA 생성 (manage_ka 도구 사용)
# volume_path: /Volumes/main/nh_voice_agent/documents
# name: NH_Financial_Assistant
# description: 재무제표 및 회계 규정 Q&A

# 3. 프로비저닝 대기 (2-5분)
# 4. 한글 질문 테스트
```

**예상 소요 시간**: 1-2시간 (PDF 준비 + 생성 + 테스트)

---

### Option B: Custom RAG Pipeline (Qwen3/BGE-M3 명시적 사용) ⚙️

#### 특징
- **완전한 제어**: Embedding model, 청킹, 검색 로직 모두 커스터마이징
- **한글 최적화**: Qwen3 또는 BGE-M3 명시적 선택
- **투명성**: 전체 파이프라인 코드 레벨 이해 및 디버깅

#### 장점
✅ **Embedding Model 선택**: Qwen3/BGE-M3 등 한글 최적화 모델 명시
✅ **파라미터 튜닝**: 청크 크기, overlap, top-k 등 세밀 조정
✅ **디버깅**: 각 단계별 결과 확인 가능
✅ **학습 효과**: RAG 원리 깊이 이해

#### 단점
⚠️ **개발 시간**: 4-5시간 소요 (파싱, 청킹, 인덱싱, 쿼리)
⚠️ **유지보수**: 수동 관리 필요 (업데이트, 스케일링)
⚠️ **복잡도**: 더 많은 코드와 설정

#### 구현 단계
```python
# Phase 1: PDF 파싱
# - pdfplumber로 한글 PDF 파싱
# - Delta Table 저장

# Phase 2: 텍스트 청킹
# - LangChain RecursiveCharacterTextSplitter
# - 한글 토큰 고려 (512 tokens)

# Phase 3: Vector Search Index 생성
# - Embedding Model: databricks-qwen3-embedding-0-6b
# - Delta Sync Index 생성

# Phase 4: RAG 쿼리 구현
# - Vector Search API로 검색
# - LLM으로 답변 생성
```

**예상 소요 시간**: 4-5시간 (전체 파이프라인 구축)

---

## 🎯 추천 전략: 하이브리드 접근

### Phase 1: Knowledge Assistant로 빠른 검증 (1-2시간)
```
목적: 한글 성능 빠르게 확인
1. 샘플 한글 PDF 2-3개 준비
2. Knowledge Assistant 생성
3. 한글 질문으로 성능 테스트
4. 결과 평가
```

**판단 기준:**
- ✅ **KA 한글 성능 우수** → KA 그대로 사용, Voice App 연동
- ⚠️ **KA 한글 성능 부족** → Custom RAG Pipeline으로 전환

### Phase 2a: KA 성능 우수 시 (추가 1시간)
```
1. KA를 Supervisor Agent에 통합
2. Voice App에서 KA 호출
3. 전체 플로우 테스트
```

### Phase 2b: KA 성능 부족 시 (추가 3-4시간)
```
1. Custom RAG Pipeline 구현
2. Qwen3 embedding 명시적 사용
3. 청킹/검색 파라미터 최적화
4. Voice App 연동
```

---

## 📋 즉시 실행 가능한 다음 단계

### Step 1: 샘플 PDF 준비 (10분)
```bash
cd /Users/yk.ko/git/PoC/NH_voice_agent
mkdir -p data/raw

# 한글 PDF 2-3개 복사
# 예: 재무제표, 회계 규정, 사업 보고서
```

### Step 2: Unity Catalog 설정 (10분)
```sql
-- Databricks Notebook에서 실행
CREATE CATALOG IF NOT EXISTS main;
CREATE SCHEMA IF NOT EXISTS main.nh_voice_agent
  COMMENT 'NH Voice Agent PoC';
CREATE VOLUME IF NOT EXISTS main.nh_voice_agent.documents
  COMMENT 'PDF documents for RAG';
```

### Step 3: PDF를 Volume에 업로드 (10분)
```python
# Databricks Notebook
import os

# 로컬 PDF를 Volume에 복사
dbutils.fs.cp("file:/path/to/sample.pdf",
              "/Volumes/main/nh_voice_agent/documents/sample.pdf")

# 확인
display(dbutils.fs.ls("/Volumes/main/nh_voice_agent/documents/"))
```

### Step 4a: Knowledge Assistant 생성 (5분 + 대기 5분)
```python
# manage_ka 도구 사용
# 또는 Databricks UI에서 생성

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ServingEndpointDataTaskSpec

client = WorkspaceClient()

# KA 생성은 UI 또는 manage_ka 도구 권장
```

### Step 4b: 한글 테스트 (20분)
```python
# 테스트 질문들
test_questions = [
    "재무제표의 주요 항목은 무엇인가요?",
    "당기순이익 계산 방법을 설명해주세요",
    "유동자산과 비유동자산의 차이는?",
    "회계 규정에 따른 감가상각 방법은?"
]

# KA endpoint에 질문 전송 (UI 또는 API)
# 답변 품질 평가
```

---

## 💡 최종 추천

### 🚀 **1순위: Knowledge Assistant로 시작**

**이유:**
1. **빠른 검증**: 1-2시간 내 한글 성능 확인
2. **리스크 관리**: 성능 부족 시 Custom으로 전환 가능
3. **학습 효과**: KA 사용 경험 후 Custom 필요성 판단
4. **시간 효율**: PoC 단계에서 빠른 결과 도출

**진행 순서:**
```
1. [30분] Unity Catalog + Volume 설정
2. [30분] 한글 PDF 준비 및 업로드
3. [10분] Knowledge Assistant 생성
4. [5분] 프로비저닝 대기
5. [30분] 한글 질문 테스트 및 평가
---
합계: 약 2시간

결과에 따라:
- 성능 OK → Voice App 연동 (1시간)
- 성능 부족 → Custom RAG로 전환 (4시간)
```

### 🔧 **2순위: Custom RAG Pipeline (필요시)**

**조건:**
- KA 한글 성능이 기대에 못 미치는 경우
- 청킹/검색 로직의 세밀한 튜닝이 필요한 경우
- Qwen3 embedding을 명시적으로 사용해야 하는 경우

**Embedding Model 선택:**
- **1순위**: `databricks-qwen3-embedding-0-6b` (한중일 최적화)
- **2순위**: `bge_m3_embedding` (system.ai.bge_m3, 100+ 언어)

---

## 📝 Databricks Notebook 형식 코드 생성 계획

각 단계별로 고객이 이해하기 쉽도록 주석과 설명이 풍부한 Notebook을 생성하겠습니다:

### Notebook 1: `01_Setup_Unity_Catalog.py` (Databricks)
- Unity Catalog 리소스 생성
- Volume 설정 및 확인
- 권한 설정

### Notebook 2a: `02a_Knowledge_Assistant_Setup.py` (Databricks)
- PDF 업로드
- KA 생성
- 한글 테스트

### Notebook 2b: `02b_Custom_RAG_Pipeline.py` (Databricks)
- PDF 파싱 (pdfplumber)
- 텍스트 청킹 (LangChain)
- Vector Index 생성 (Qwen3)
- RAG 쿼리 테스트

### Notebook 3: `03_Integration_Test.py` (Databricks)
- Voice App 연동 테스트
- End-to-End 플로우 검증

---

## ❓ 다음 결정 사항

**어떤 방식으로 진행하시겠습니까?**

1. **Knowledge Assistant로 시작** (추천, 빠른 검증)
   - Unity Catalog 설정부터 시작
   - Notebook 1 + 2a 생성

2. **Custom RAG Pipeline 직접 구축** (완전한 제어)
   - Qwen3 embedding 명시적 사용
   - Notebook 1 + 2b 생성

3. **두 가지 모두 구현** (비교 평가)
   - Notebook 1 + 2a + 2b 모두 생성
   - 성능 비교 후 최종 선택

**결정해주시면 해당 Notebook 코드를 생성하겠습니다!**

---

**Last Updated**: 2026-03-16
**Status**: Knowledge Assistant 검토 완료, 한글 embedding 모델 확인됨
**Next**: Unity Catalog 설정 및 KA/Custom RAG 구현 시작
