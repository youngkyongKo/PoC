# Multi-Agent Supervisor

LangChain 기반의 Supervisor Agent 구현
- Knowledge Assistant를 통한 문서 기반 RAG
- Genie Space를 통한 SQL 기반 데이터 분석

## 구성 요소

1. **knowledge_assistant_tool.py**: Knowledge Assistant RAG 도구
2. **genie_tool.py**: Genie Space 쿼리 툴
3. **supervisor_agent.py**: Supervisor Agent 구현
4. **test_agent.py**: Agent 테스트

## 사용법

### Agent 테스트

```bash
python test_agent.py
```

### 대화형 모드

```bash
python supervisor_agent.py
```

## Agent 구조

```
Supervisor Agent
├── Knowledge Assistant Tool (문서 기반 RAG)
│   └── Databricks KA Endpoint
│       └── Serving Endpoints REST API
│
└── Genie Space Tool (SQL 기반 분석)
    └── Databricks Genie Space API
```

## 설정

`.env` 파일에 다음 항목 설정:

```bash
# Knowledge Assistant (필수)
KA_ENDPOINT_NAME=ka-69e8398a-endpoint
KA_TILE_ID=69e8398a

# Databricks 인증 (필수)
DATABRICKS_HOST=your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...

# Genie Space (선택)
GENIE_SPACE_ID=your_genie_space_id
```

## 예제 질문

**Knowledge Assistant 활용:**
- "보험 상품의 보장 내용에 대해 알려줘"
- "청약 절차가 어떻게 되나요?"

**Genie Space 활용:**
- "지난달 판매 실적은?"
- "상품별 가입자 통계를 보여줘"

**복합 질문:**
- "가장 많이 판매된 상품의 보장 내용은?"

## 문제 해결

### KA API 호출 에러

**403 CSRF 에러 또는 404 NOT_FOUND 에러가 발생하는 경우:**

Databricks 노트북에서는 Serving Endpoints REST API를 사용해야 합니다:

```python
# ✅ 올바름 - Serving Endpoints REST API (PAT 인증)
url = f"https://{host}/serving-endpoints/{endpoint}/invocations"

# ❌ 잘못됨 - CSRF 토큰 필요 (브라우저 전용)
url = f"https://{host}/ajax-serving-endpoints/{endpoint}/invocations"

# ❌ 잘못됨 - 잘못된 경로 (404 에러)
url = f"https://{host}/api/2.0/serving-endpoints/{endpoint}/invocations"
```

**중요 사항:**
- Serving Endpoints는 `/api/2.0/` prefix를 사용하지 않습니다
- Knowledge Assistant endpoint는 REST API로 호출해도 RAG 기능이 유지됩니다

```bash
# Endpoint 상태 확인
databricks serving-endpoints get --name $KA_ENDPOINT_NAME

# 토큰 확인
echo $DATABRICKS_TOKEN
```
