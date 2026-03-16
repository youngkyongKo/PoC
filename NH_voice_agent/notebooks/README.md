# NH Voice Agent - Databricks Notebooks

## 📚 Notebook 목록

이 디렉토리는 NH Voice Agent PoC를 위한 Databricks Notebook들을 포함합니다.

### 🎯 RAG 구현 - Option 1: Knowledge Assistant

| # | Notebook | 설명 | 소요 시간 |
|---|----------|------|-----------|
| 1 | `01_Setup_Unity_Catalog.py` | Unity Catalog 리소스 설정 (Catalog, Schema, Volume) | 10분 |
| 2 | `02a_Knowledge_Assistant_Setup.py` | Knowledge Assistant 생성 및 한글 성능 테스트 | 1-2시간 |

---

## 🚀 빠른 시작

### Step 1: Databricks Workspace에 업로드

**방법 1: UI 업로드**
```
1. Databricks Workspace 좌측 메뉴 → Workspace
2. 원하는 폴더로 이동 (예: /Users/your_email/)
3. 우측 상단 "Import" 버튼
4. 이 디렉토리의 .py 파일들 선택
5. "Import" 클릭
```

**방법 2: Git 연동**
```
1. Databricks Workspace → Repos
2. "Add Repo" 클릭
3. Git repository URL 입력
4. notebooks/ 폴더로 이동
```

### Step 2: 순서대로 실행

```
01_Setup_Unity_Catalog.py 실행 (필수)
    ↓
02a_Knowledge_Assistant_Setup.py 실행
    ↓
한글 성능 평가
    ↓
    ├─ 성능 OK → Voice App 연동
    └─ 성능 부족 → Custom RAG Pipeline 구현 (향후)
```

---

## 📋 각 Notebook 상세 설명

### 1. 01_Setup_Unity_Catalog.py

**목적**: Unity Catalog 기본 리소스 설정

**생성 리소스**:
- Catalog: `demo_ykko` (기존 또는 신규)
- Schema: `demo_ykko.nh_voice_agent`
- Volume: `demo_ykko.nh_voice_agent.documents`

**주요 작업**:
- Unity Catalog 환경 확인
- Schema 및 Volume 생성
- 파일 업로드 테스트 (한글 인코딩 확인)

**실행 시간**: 5-10분

**사전 요구사항**:
- Unity Catalog 활성화된 workspace
- CREATE CATALOG, CREATE SCHEMA, CREATE VOLUME 권한

---

### 2. 02a_Knowledge_Assistant_Setup.py

**목적**: Databricks Knowledge Assistant를 사용한 RAG 구축 및 한글 성능 검증

**주요 작업**:
1. 한글 PDF 문서 준비 및 Volume 업로드
2. Knowledge Assistant 생성 (UI 또는 API)
3. 프로비저닝 대기 (2-5분)
4. 한글 질문으로 성능 테스트
5. 결과 평가 및 다음 단계 의사결정

**테스트 질문 예시**:
- "재무제표의 주요 구성 요소는 무엇인가요?"
- "당기순이익은 어떻게 계산하나요?"
- "유동자산과 비유동자산의 차이를 설명해주세요"

**평가 기준**:
- ✅ 한글 질문 이해도
- ✅ 관련 문서 검색 정확도
- ✅ 한글 답변 자연스러움
- ✅ 출처 문서 명시 여부

**실행 시간**: 1-2시간 (PDF 준비 + 테스트 + 평가)

**사전 요구사항**:
- `01_Setup_Unity_Catalog.py` 완료
- 한글 PDF 문서 2-3개 준비

**다음 단계**:
- 성능 OK → Voice App 연동
- 성능 부족 → Custom RAG Pipeline 구현

---

## 🎯 Knowledge Assistant란?

Databricks Knowledge Assistant는 **자동화된 RAG 시스템**입니다:

| 특징 | 설명 |
|------|------|
| **자동 인덱싱** | Volume의 문서를 자동으로 임베딩 및 인덱싱 |
| **빠른 구축** | 코드 없이 2-5분 내 프로비저닝 |
| **관리 용이** | UI에서 손쉬운 생성/업데이트 |
| **통합** | Supervisor Agent에 바로 연결 가능 |

### 장점
- ✅ 빠른 프로토타이핑 (1-2시간)
- ✅ 자동 관리 (업데이트, 스케일링)
- ✅ 내장 평가 기능

### 제약사항
- ⚠️ Embedding model 선택 불가 (기본 모델 사용)
- ⚠️ 한글 성능 검증 필요
- ⚠️ 커스터마이징 제한

---

## 🔧 문제 해결

### Unity Catalog 권한 에러
```sql
-- 관리자에게 권한 요청
GRANT CREATE SCHEMA ON CATALOG demo_ykko TO `your_user@email.com`;
GRANT CREATE VOLUME ON SCHEMA demo_ykko.nh_voice_agent TO `your_user@email.com`;
```

### Volume 파일 업로드 실패
- UI를 통한 업로드 권장 (Data → Volumes → Upload)
- 파일 크기 제한 확인 (일반적으로 100MB 이하 권장)

### Knowledge Assistant 프로비저닝 실패
- Workspace 리소스 확인 (quota, capacity)
- Volume 경로가 올바른지 확인
- 10분 이상 PROVISIONING 상태면 관리자에게 문의

### 한글 답변 품질 부족
- PDF 문서의 한글 텍스트 품질 확인
- 더 명확한 지침(instructions) 추가
- Custom RAG Pipeline으로 전환 고려

---

## 💡 추천 작업 흐름

### 1단계: 빠른 검증 (Option 1 - Knowledge Assistant)
```
목표: 한글 성능 빠르게 확인

1. Unity Catalog 설정 (10분)
2. 한글 PDF 2-3개 준비 및 업로드 (30분)
3. Knowledge Assistant 생성 (10분)
4. 프로비저닝 대기 (5분)
5. 한글 질문 테스트 (30분)
6. 성능 평가 (15분)

합계: 약 1.5-2시간
```

### 2단계: 의사결정
```
성능 평가 결과에 따라:

✅ KA 성능 우수
   → Voice App 연동 (1시간)
   → 총 시간: 2-3시간

⚠️ KA 성능 부족
   → Custom RAG Pipeline 구현 (3-4시간)
   → Qwen3 embedding 명시적 사용
   → 총 시간: 5-6시간
```

---

## 📝 다음 단계 (향후 추가 예정)

### Option 2: Custom RAG Pipeline (필요시)
- `02b_Custom_RAG_Pipeline.py` - PDF 파싱, 청킹, Vector Search (Qwen3)
- `03_RAG_Query_Optimization.py` - 검색 파라미터 튜닝

### Integration
- `04_Voice_App_Integration.py` - Voice App과 RAG 연동
- `05_End_to_End_Test.py` - 전체 플로우 테스트

---

## 📚 참고 자료

### Databricks 문서
- [Unity Catalog](https://docs.databricks.com/unity-catalog/index.html)
- [Knowledge Assistants](https://docs.databricks.com/machine-learning/ai-agents/knowledge-assistants.html)
- [Vector Search](https://docs.databricks.com/vector-search/index.html)

### 프로젝트 문서
- `../RAG_IMPLEMENTATION_PLAN.md` - RAG 구현 전략
- `../SESSION_NOTES.md` - 작업 세션 노트
- `../NEXT_STEPS.md` - 다음 작업 가이드

---

**Last Updated**: 2026-03-16
**Status**: Knowledge Assistant notebooks 생성 완료
**Next**: Databricks Workspace에 업로드 후 실행
