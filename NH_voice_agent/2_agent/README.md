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
│       └── ajax-serving-endpoints (RAG 활성화)
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

### KA 401 인증 에러

ajax-serving-endpoints 사용 시 올바른 토큰 필요:

```bash
# 토큰 확인
echo $DATABRICKS_TOKEN

# Endpoint 상태 확인
databricks serving-endpoints get --name $KA_ENDPOINT_NAME
```

### RAG 검색 비활성화 문제

**중요**: `/ajax-serving-endpoints/` 사용해야 RAG 활성화됩니다.

```
✅ https://{host}/ajax-serving-endpoints/{endpoint}/invocations
❌ https://{host}/serving-endpoints/{endpoint}/invocations
```
