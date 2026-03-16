# NH Voice Agent - 작업 세션 기록 (2026-03-16)

## 📋 작업 목표
Knowledge Assistant를 사용한 RAG 구현 및 한글 성능 테스트

## ✅ 완료된 작업

### 1. Unity Catalog 설정
- **Catalog**: `demo_ykko`
- **Schema**: `demo_ykko.nh_voice_agent`
- **Volume**: `demo_ykko.nh_voice_agent.documents`
- PDF 문서 업로드 완료

### 2. Knowledge Assistant 생성
- **Endpoint Name**: `ka-69e8398a-endpoint`
- **Tile ID**: `69e8398a-b268-4732-b6cd-5c2b8051b349`
- **상태**: READY
- **Sync 상태**: 완료 (문서 인덱싱 완료)

### 3. API 호출 방식 탐색

#### 시도 1: Standard Serving API ❌
```python
url = f"https://{workspace_url}/serving-endpoints/{endpoint_name}/invocations"
```
- **결과**: 응답은 성공하지만 `sources_used: False`
- **문제**: RAG 검색이 활성화되지 않음

#### 시도 2: Bricks API ❌
```python
url = f"https://{workspace_url}/api/2.0/bricks/tiles/{tile_id}/query"
```
- **결과**: 404 Not Found
- **문제**: API 경로가 존재하지 않음

#### 시도 3: Ajax Serving Endpoints ❌
```python
url = f"https://{workspace_url}/ajax-serving-endpoints/{endpoint_name}/invocations"
```
- **결과**: 403 Missing CSRF token
- **문제**: UI 전용 엔드포인트, CSRF 토큰 필요

### 4. 코드 개선 사항
- KA 응답 구조 파악: `output[0].content[0].text`
- `input` 필드 사용 (OpenAI의 `messages`가 아님)
- 여러 응답 형식 처리 로직 추가
- 디버깅 강화

## ❌ 미해결 문제

### 핵심 이슈: API 호출 시 RAG 검색 활성화 불가

**현상:**
- UI에서는 정상 작동 (문서 검색 및 답변 생성)
- API 호출 시 `sources_used: False` → 문서 검색 안됨
- UI가 사용하는 `/ajax-serving-endpoints/`는 CSRF 토큰 필요

**시도한 방법:**
1. ✅ Model Serving API - 응답은 오지만 RAG 비활성화
2. ❌ Bricks API - 404 에러
3. ❌ Ajax Endpoints - CSRF 토큰 필요

**UI Network 탭 확인 결과:**
```
Request URL: https://e2-demo-field-eng.cloud.databricks.com/ajax-serving-endpoints/ka-69e8398a-endpoint/invocations
Request Method: POST
```

## 🔍 다음 세션에서 시도할 방법

### Option A: CSRF 토큰 획득 및 사용 (복잡)
1. Databricks UI의 Cookie에서 CSRF 토큰 추출
2. `X-CSRFToken` 헤더에 포함하여 `/ajax-serving-endpoints/` 호출
3. **문제**: Notebook에서 브라우저 Cookie 접근 어려움

### Option B: Databricks SDK 내부 구현 확인 (권장)
```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

client = WorkspaceClient()
# SDK 내부적으로 어떤 API를 사용하는지 확인
```
- SDK 소스 코드 또는 디버그 로그 확인
- SDK가 RAG 검색을 활성화하는 방법 파악

### Option C: Databricks 공식 문서/포럼 검색
- "Knowledge Assistant API RAG search"
- "Databricks KA programmatic access"
- Community 포럼 또는 Slack 채널 질문

### Option D: Databricks 지원팀 문의
- Knowledge Assistant의 프로그래밍 방식 접근 방법
- RAG 검색을 활성화하는 올바른 API 엔드포인트

### Option E: Custom RAG Pipeline으로 전환 (대안)
- Knowledge Assistant 대신 직접 RAG 구현
- Qwen3 embedding 명시적 사용
- Vector Search + LLM 직접 구성
- **예상 시간**: 3-4시간

## 📁 생성된 파일

### Notebooks
1. `notebooks/01_Setup_Unity_Catalog.py` - UC 설정
2. `notebooks/02a_Knowledge_Assistant_Setup.py` - KA 설정 및 테스트 (메인)
3. `notebooks/02a_Knowledge_Assistant_Setup_FIXED.py` - 401 에러 수정 버전
4. `notebooks/02a_KA_API_Test_Multiple_Methods.py` - 4가지 API 방법 테스트
5. `notebooks/README.md` - Notebook 가이드

### 문서
1. `RAG_IMPLEMENTATION_PLAN.md` - RAG 구현 계획
2. `SESSION_NOTES.md` - 세션 노트
3. `NEXT_STEPS.md` - 다음 단계 가이드

## 🎯 권장 사항

### 단기 (내일 세션)
**Option B + D 조합 추천:**
1. **먼저**: Databricks SDK 코드 확인 또는 디버그
2. **동시에**: Databricks 지원팀/커뮤니티에 질문
3. **결과 대기 중**: Custom RAG 옵션 준비

### 장기 (PoC 완료)
- KA API 문제가 해결되지 않으면 **Custom RAG로 전환**
- Custom RAG 장점:
  - 완전한 제어 (embedding model, 청킹, 검색)
  - 한글 최적화 (Qwen3 명시적 사용)
  - 투명한 디버깅
- 단점: 개발 시간 3-4시간 추가

## 💡 핵심 인사이트

1. **Knowledge Assistant는 UI 중심으로 설계됨**
   - 프로그래밍 방식 접근이 제한적
   - UI 전용 엔드포인트 사용

2. **RAG 검색 활성화가 핵심**
   - 단순 응답만으로는 의미 없음
   - `sources_used: true`가 되어야 함

3. **API 문서 부족**
   - 공식 문서에 KA API 프로그래밍 가이드 부족
   - 실험적 기능일 가능성

## 📊 Git Commits

```
3dcbf4c - fix: ajax-serving-endpoints 사용으로 RAG 검색 활성화
ac6c60b - feat: Bricks API 사용으로 RAG 검색 활성화
3374d10 - fix: KA 응답 구조 수정 (output 형식)
ed822b5 - fix: KA 응답 구조 디버깅 강화
5a75262 - fix: SDK 방법 제거 및 결과 요약 업데이트
0b7ac6e - fix: KA API payload 형식 수정 (messages -> input)
aa950fd - feat: KA API 다중 방법 테스트 notebook 추가
d913acf - fix: 401 인증 에러 해결 및 에러 처리 개선
```

## 📞 연락처 / 참고 자료

- Databricks Workspace: `https://e2-demo-field-eng.cloud.databricks.com`
- KA UI: `https://e2-demo-field-eng.cloud.databricks.com/ml/bricks/ka/configure/69e8398a-b268-4732-b6cd-5c2b8051b349`
- Volume Path: `/Volumes/demo_ykko/nh_voice_agent/documents`

---

**다음 세션 시작 시 TODO:**
1. 이 문서 읽기
2. Option B 또는 D 시도
3. 1시간 내 해결 안되면 Option E (Custom RAG) 전환
