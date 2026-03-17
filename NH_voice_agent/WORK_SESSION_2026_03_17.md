# 작업 세션 - 2026년 3월 17일

## 수행 작업

### 1. Knowledge Assistant Tool 구현

Knowledge Assistant 전용 tool을 새로 생성하여 기존 placeholder 코드를 대체했습니다.

**파일**: `2_agent/knowledge_assistant_tool.py`

**주요 기능**:
- Databricks Knowledge Assistant API 호출
- ajax-serving-endpoints를 사용한 RAG 활성화
- 다양한 응답 형식 자동 파싱 (output, choices, answer 등)
- RAG 소스 사용 여부 확인 (sources_used)
- 에러 처리 및 타임아웃 관리

**API 엔드포인트**:
```python
# ✅ 올바름 - REST API 사용 (PAT 인증)
url = f"https://{host}/api/2.0/serving-endpoints/{endpoint_name}/invocations"

# ❌ 잘못됨 - CSRF 토큰 필요 (브라우저 전용)
url = f"https://{host}/ajax-serving-endpoints/{endpoint_name}/invocations"
```

**중요**: Knowledge Assistant endpoint는 REST API로 호출해도 RAG 기능이 유지됩니다.

### 2. Supervisor Agent 업데이트

기존 vector_search_tool을 knowledge_assistant_tool로 교체했습니다.

**변경 사항**:
- `vector_search_tool` → `knowledge_assistant_tool` import
- Tool 이름: `vector_search` → `knowledge_assistant`
- 시스템 프롬프트 업데이트

### 3. Configuration 업데이트

**config.py**:
```python
# Knowledge Assistant Configuration
KA_ENDPOINT_NAME = os.getenv("KA_ENDPOINT_NAME")
KA_TILE_ID = os.getenv("KA_TILE_ID")
```

**.env.example**:
```bash
# Knowledge Assistant Configuration
KA_ENDPOINT_NAME=ka-xxxxxxxx-endpoint
KA_TILE_ID=xxxxxxxx
```

### 4. 테스트 코드 정리

**test_agent.py**:
- `test_vector_search_queries()` → `test_knowledge_assistant_queries()`
- Mock 데이터 안내 제거
- 설정 출력 업데이트

### 5. 문서 업데이트

**2_agent/README.md**:
- Knowledge Assistant 사용 가이드 추가
- API 엔드포인트 설명 추가
- 문제 해결 섹션 추가
- 예제 질문 정리

## 파일 변경 내역

### 생성
- `2_agent/knowledge_assistant_tool.py` - KA 전용 tool 구현

### 수정
- `config.py` - KA 설정 추가
- `2_agent/supervisor_agent.py` - KA tool 사용
- `2_agent/test_agent.py` - 테스트 함수 이름 변경
- `.env.example` - KA 설정 추가
- `2_agent/README.md` - 문서 업데이트

### 백업
- `2_agent/vector_search_tool.py.backup` - 기존 파일 백업

## 다음 단계

### 즉시 필요한 작업

1. **KA Endpoint 설정**
   ```bash
   # .env 파일에 실제 값 입력
   KA_ENDPOINT_NAME=ka-69e8398a-endpoint
   KA_TILE_ID=69e8398a
   ```

2. **테스트 실행**
   ```bash
   cd /Users/yk.ko/git/PoC/NH_voice_agent
   python 2_agent/knowledge_assistant_tool.py
   python 2_agent/test_agent.py
   ```

### 향후 작업

1. **Genie Tool 실제 구현**
   - 현재 placeholder 코드를 실제 Genie API 호출로 교체
   - Databricks SDK 또는 REST API 사용

2. **Voice App 통합**
   - `3_voice_app/app.py`에 Supervisor Agent 연동
   - STT → Agent → TTS 파이프라인 구성

3. **프로덕션 준비**
   - 에러 처리 강화
   - 로깅 개선
   - 성능 최적화

## 주의사항

### API 엔드포인트 선택

Databricks 노트북 환경에서는 **REST API**를 사용해야 합니다:

```python
# ✅ 올바름 - PAT 인증 (노트북, Python 스크립트)
url = f"https://{host}/api/2.0/serving-endpoints/{endpoint}/invocations"

# ❌ 잘못됨 - CSRF 토큰 필요 (브라우저 AJAX만 가능)
url = f"https://{host}/ajax-serving-endpoints/{endpoint}/invocations"
```

**중요**: KA endpoint는 어느 URL을 사용하든 RAG 기능이 유지됩니다.

### 인증

Databricks Notebook 외부에서 실행 시:
- Personal Access Token 필요
- Endpoint 권한 확인 필요

### 테스트

실제 테스트 전에:
1. KA Endpoint가 ONLINE 상태인지 확인
2. Volume에 PDF 문서가 업로드되었는지 확인
3. `.env` 파일 설정 완료 확인

## 참고 문서

- [Databricks Knowledge Assistant](https://docs.databricks.com/aws/en/generative-ai/agent-bricks/knowledge-assistant)
- [Databricks Genie Space](https://docs.databricks.com/en/genie/index.html)
- [LangChain Agents](https://python.langchain.com/docs/modules/agents/)

## 작업 시간

- 시작: 2026-03-17 (세션 재개)
- 소요 시간: 약 1시간
- 상태: ✅ 완료

---

**다음 세션 시작 시**:
1. 이 문서 검토
2. KA Endpoint 테스트
3. Genie Tool 구현 또는 Voice App 통합 진행
