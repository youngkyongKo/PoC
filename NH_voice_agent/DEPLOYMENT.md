# NH Voice Agent - Multi-Agent Supervisor 배포 가이드

## 배포 완료 내역

### 1. Genie Space
- **Space ID**: `01f128b75fcd1eb8be6fab662cf566f1`
- **테이블**: `demo_ykko.nh_voice_agent.fundinfo`
- **데이터**: 28개 채권 종목 정보
- **Warehouse**: `e2b5c5e3a1193304`

### 2. Knowledge Assistant
- **Endpoint**: `ka-b5edb67b-endpoint`
- **Tile ID**: `b5edb67b-d0c6-4c2b-96ae-9876e4778260`
- **Name**: `ykko_NH_voice_KA`
- **Vector Index**: 채권 상품 설명서 PDF 문서

### 3. Multi-Agent Supervisor
- **위치**: `/Workspace/Users/yk.ko@databricks.com/nh_voice_agent/`
- **구성**:
  - `2_agent/supervisor_agent.py` - LangGraph 기반 Supervisor
  - `2_agent/genie_tool.py` - Genie Space 쿼리 도구
  - `2_agent/knowledge_assistant_tool.py` - Knowledge Assistant RAG 도구
  - `config.py` - 환경 설정

## 라우팅 로직

### Rule 1: 채권 검색 및 비교 → Genie Space
- "A- 이상 등급인 채권을 찾아줘"
- "수익률 높은 순으로 보여줘"
- "만기 1년 미만인 채권은?"
- "롯데캐피탈 채권을 비교해줘"
- "민평금리보다 싼 회사채는?"

### Rule 2: 발행사 정보 조회 → Knowledge Assistant
- "DL에너지 회사에 대해 알려줘"
- "이 발행사가 무슨 일을 하는 회사야?"
- "신용등급 전망은 어때?"
- "재무 상황이 어때?"
- "투자 리스크는 뭐가 있어?"

### Rule 3: 복합 질의 → 순차적 도구 호출
- "DL에너지 채권 자세히 알려줘"
  1. Genie Space: DL에너지 채권 종목 데이터 조회
  2. Knowledge Assistant: DL에너지 회사 소개 조회
  3. 두 정보를 통합하여 응답

## 테스트 방법

### Databricks 노트북에서 테스트

1. **노트북 열기**
   ```
   /Workspace/Users/yk.ko@databricks.com/nh_voice_agent/notebooks/03_test_supervisor.py
   ```

2. **셀 순서대로 실행**
   - 환경 변수 설정
   - Agent 초기화
   - 테스트 질문 실행

3. **주요 테스트 케이스**
   ```python
   # 채권 검색 (Genie Space)
   agent.query("A- 이상 등급인 회사채를 수익률 높은 순으로 보여줘")

   # 발행사 정보 (Knowledge Assistant)
   agent.query("DL에너지 회사에 대해 알려줘")

   # 비교 (Genie Space)
   agent.query("롯데캐피탈에서 발행한 채권을 비교해줘")
   ```

### 로컬에서 테스트

```bash
cd /Users/yk.ko/git/PoC/NH_voice_agent

# 환경 변수 확인
cat .env

# Agent 실행
cd 2_agent
python supervisor_agent.py

# 또는 단일 질문
python supervisor_agent.py --question "A 등급 채권을 찾아줘"
```

## 파일 구조

```
NH_voice_agent/
├── .env                            # 환경 변수
├── config.py                       # 설정 모듈
├── multi_agent_supervisor_prompt.md # Supervisor 프롬프트 문서
├── genie_space_config.md           # Genie Space 구성 가이드
│
├── 2_agent/                        # Agent 코드
│   ├── supervisor_agent.py         # Supervisor Agent (LangGraph)
│   ├── genie_tool.py               # Genie Space Tool
│   ├── knowledge_assistant_tool.py # Knowledge Assistant Tool
│   └── README.md
│
└── notebooks/                      # 테스트 노트북
    ├── 03_test_supervisor.py       # Supervisor 테스트
    └── config.py                   # 노트북용 Config
```

## 환경 변수

`.env` 파일 설정:

```bash
# Databricks
DATABRICKS_HOST=e2-demo-field-eng.cloud.databricks.com
DATABRICKS_TOKEN=dapi***********************************  # Use your own token

# Unity Catalog
UC_CATALOG=demo_ykko
UC_SCHEMA=nh_voice_agent
UC_VOLUME=vol_data

# Genie Space (✓ 설정 완료)
GENIE_SPACE_ID=01f128b75fcd1eb8be6fab662cf566f1
SQL_WAREHOUSE_ID=e2b5c5e3a1193304

# Knowledge Assistant (✓ 설정 완료)
KA_ENDPOINT_NAME=ka-b5edb67b-endpoint
KA_TILE_ID=b5edb67b-d0c6-4c2b-96ae-9876e4778260
KA_NAME=ykko_NH_voice_KA

# Model
SERVING_ENDPOINT=databricks-claude-sonnet-4-6

# Settings
DEBUG=True
LOG_LEVEL=INFO
```

## Workspace 업로드 내역

다음 파일들이 Databricks workspace에 업로드되었습니다:

1. **Agent 코드**
   - `/Workspace/Users/yk.ko@databricks.com/nh_voice_agent/2_agent/supervisor_agent.py`
   - `/Workspace/Users/yk.ko@databricks.com/nh_voice_agent/2_agent/genie_tool.py`
   - `/Workspace/Users/yk.ko@databricks.com/nh_voice_agent/2_agent/knowledge_assistant_tool.py`
   - `/Workspace/Users/yk.ko@databricks.com/nh_voice_agent/2_agent/README.md`

2. **설정 파일**
   - `/Workspace/Users/yk.ko@databricks.com/nh_voice_agent/config.py`
   - `/Workspace/Users/yk.ko@databricks.com/nh_voice_agent/multi_agent_supervisor_prompt.md`

3. **테스트 노트북**
   - `/Workspace/Users/yk.ko@databricks.com/nh_voice_agent/notebooks/03_test_supervisor.py`
   - `/Workspace/Users/yk.ko@databricks.com/nh_voice_agent/notebooks/config.py`

## 다음 단계

### 1. Genie Space 테스트
```python
from databricks.sdk import WorkspaceClient

client = WorkspaceClient()

# Genie Space에 직접 질문
# (또는 Databricks UI에서 Genie Space 페이지에서 테스트)
```

### 2. Knowledge Assistant 테스트
```python
from knowledge_assistant_tool import KnowledgeAssistantTool

ka = KnowledgeAssistantTool()
result = ka.query("DL에너지 회사에 대해 알려줘")
print(result)
```

### 3. Supervisor Agent 통합 테스트
```python
from supervisor_agent import SupervisorAgent

agent = SupervisorAgent()

# 여러 질문 연속 테스트
questions = [
    "등급 A 이상인 채권을 찾아줘",
    "DL에너지 채권을 자세히 알려줘",
    "롯데캐피탈 채권을 비교해줘"
]

for q in questions:
    result = agent.query(q)
    print(f"Q: {q}")
    print(f"Route: {result['route']}")
    print(f"A: {result['answer']}\n")
```

### 4. Voice App 통합
- 3_voice_app과 연동
- 음성 입력 → Supervisor Agent → 음성 출력 파이프라인 구축

## 트러블슈팅

### Genie API 오류
- Genie Space ID 확인: `01f128b75fcd1eb8be6fab662cf566f1`
- Warehouse ID 확인: `e2b5c5e3a1193304`
- API 엔드포인트 확인

### Knowledge Assistant 오류
- Endpoint 상태 확인: `ka-b5edb67b-endpoint`
- Tile ID 확인: `b5edb67b-d0c6-4c2b-96ae-9876e4778260`
- Serving Endpoints REST API 사용 (CSRF 토큰 불필요)

### 라우팅 오류
- 로그 확인: `DEBUG=True`로 설정
- LLM 응답 확인
- 키워드 기반 fallback 로직 확인

## 성공 기준

✅ Genie Space가 채권 검색 질문에 정확히 응답
✅ Knowledge Assistant가 발행사 정보 질문에 PDF 문서 기반으로 응답
✅ Supervisor Agent가 질문 유형에 따라 올바른 도구로 라우팅
✅ 복합 질의 시 순차적으로 양쪽 도구 모두 활용

## 참고 문서

- `multi_agent_supervisor_prompt.md` - Supervisor 프롬프트 상세 가이드
- `genie_space_config.md` - Genie Space 구성 방법
- `2_agent/README.md` - Agent 아키텍처 설명
