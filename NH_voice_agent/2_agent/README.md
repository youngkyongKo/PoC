# Multi-Agent Supervisor

LangChain 기반의 Supervisor Agent 구현
- Vector Search Tool을 통한 문서 검색
- Genie Space Tool을 통한 데이터 분석

## 구성 요소

1. **vector_search_tool.py**: Vector Search 검색 툴
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
├── Vector Search Tool (문서 검색)
│   └── Vector Search Index 쿼리
│
└── Genie Space Tool (데이터 분석)
    └── SQL 기반 자연어 쿼리
```

## 예제 질문

**Vector Search 활용:**
- "보험 상품의 보장 내용에 대해 알려줘"
- "청약 절차가 어떻게 되나요?"

**Genie Space 활용:**
- "지난달 판매 실적은?"
- "상품별 가입자 통계를 보여줘"

**복합 질문:**
- "가장 많이 판매된 상품의 보장 내용은?"
