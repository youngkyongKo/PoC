# Databricks notebook source
# MAGIC %md
# MAGIC # NH Voice Agent - Multi-Agent Supervisor 테스트
# MAGIC
# MAGIC Genie Space와 Knowledge Assistant를 활용한 Multi-Agent Supervisor 테스트

# COMMAND ----------

# MAGIC %pip install -q langchain langgraph langchain-community python-dotenv

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 환경 변수 설정

# COMMAND ----------

import os

# Databricks 환경 변수
os.environ["DATABRICKS_HOST"] = "e2-demo-field-eng.cloud.databricks.com"
os.environ["DATABRICKS_TOKEN"] = dbutils.secrets.get(scope="ykko", key="databricks_token")

# Unity Catalog
os.environ["UC_CATALOG"] = "demo_ykko"
os.environ["UC_SCHEMA"] = "nh_voice_agent"
os.environ["UC_VOLUME"] = "vol_data"

# Genie Space
os.environ["GENIE_SPACE_ID"] = "01f128b75fcd1eb8be6fab662cf566f1"
os.environ["SQL_WAREHOUSE_ID"] = "e2b5c5e3a1193304"

# Knowledge Assistant
os.environ["KA_ENDPOINT_NAME"] = "ka-b5edb67b-endpoint"
os.environ["KA_TILE_ID"] = "b5edb67b-d0c6-4c2b-96ae-9876e4778260"

# Model
os.environ["SERVING_ENDPOINT"] = "databricks-claude-sonnet-4-6"
os.environ["LLM_MODEL"] = "databricks-claude-sonnet-4-6"

# Settings
os.environ["DEBUG"] = "True"
os.environ["LOG_LEVEL"] = "INFO"

print("✓ 환경 변수 설정 완료")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Config 모듈 생성

# COMMAND ----------

# MAGIC %run ./config

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Supervisor Agent 로드

# COMMAND ----------

import sys
sys.path.append("/Workspace/Users/yk.ko@databricks.com/nh_voice_agent")

from supervisor_agent import SupervisorAgent

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Agent 초기화

# COMMAND ----------

try:
    agent = SupervisorAgent()
    print("✓ Supervisor Agent 초기화 완료")
except Exception as e:
    print(f"✗ Agent 초기화 실패: {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. 테스트 질문

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5.1 채권 검색 질문 (Genie Space)

# COMMAND ----------

question1 = "A- 이상 등급인 회사채를 수익률 높은 순으로 보여줘"
print(f"질문: {question1}\n")

result1 = agent.query(question1)
print(f"라우팅: {result1['route']}")
print(f"답변:\n{result1['answer']}\n")
print("-" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5.2 발행사 정보 질문 (Knowledge Assistant)

# COMMAND ----------

question2 = "DL에너지 회사에 대해 알려줘"
print(f"질문: {question2}\n")

result2 = agent.query(question2)
print(f"라우팅: {result2['route']}")
print(f"답변:\n{result2['answer']}\n")

# 소스 문서 정보
if result2.get('sources'):
    print("\n📚 참조 문서:")
    for src in result2['sources'][:3]:
        print(f"  - {src['document']} (Page {src['page']})")

print("-" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5.3 비교 질문 (Genie Space)

# COMMAND ----------

question3 = "롯데캐피탈에서 발행한 채권을 비교해줘"
print(f"질문: {question3}\n")

result3 = agent.query(question3)
print(f"라우팅: {result3['route']}")
print(f"답변:\n{result3['answer']}\n")
print("-" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 5.4 만기 검색 질문 (Genie Space)

# COMMAND ----------

question4 = "만기가 1년 미만 남은 채권 중 수익률이 높은 종목은?"
print(f"질문: {question4}\n")

result4 = agent.query(question4)
print(f"라우팅: {result4['route']}")
print(f"답변:\n{result4['answer']}\n")
print("-" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. 대화형 테스트

# COMMAND ----------

# 대화 기록 초기화
agent.clear_history()

# 연속 질문
questions = [
    "등급 A 이상인 채권을 찾아줘",
    "그 중에서 DL에너지 채권에 대해 자세히 알려줘",
    "이 회사가 무슨 일을 하는 회사야?"
]

for i, q in enumerate(questions, 1):
    print(f"\n{'='*80}")
    print(f"질문 {i}: {q}")
    print('='*80)

    result = agent.query(q)
    print(f"라우팅: {result['route']}")
    print(f"답변:\n{result['answer']}\n")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. 성능 측정

# COMMAND ----------

import time

test_questions = [
    ("채권 검색", "A+ 등급 채권을 보여줘"),
    ("발행사 정보", "대한항공 회사에 대해 알려줘"),
    ("비교", "신용등급 A 이상인 채권을 비교해줘"),
]

results = []

for category, question in test_questions:
    start = time.time()
    result = agent.query(question)
    elapsed = time.time() - start

    results.append({
        "category": category,
        "question": question,
        "route": result['route'],
        "success": result['success'],
        "time": f"{elapsed:.2f}s"
    })

# 결과 출력
print("\n성능 측정 결과:")
print("-" * 80)
for r in results:
    print(f"{r['category']:15} | {r['route']:20} | {r['time']:8} | {'✓' if r['success'] else '✗'}")
print("-" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. 결과 요약

# COMMAND ----------

print("""
✅ Multi-Agent Supervisor 배포 완료

구성 요소:
1. Genie Space (채권 종목 정보)
   - Space ID: 01f128b75fcd1eb8be6fab662cf566f1
   - 테이블: demo_ykko.nh_voice_agent.fundinfo (28개 채권)

2. Knowledge Assistant (채권 상품 설명서)
   - Endpoint: ka-69e8398a-endpoint
   - Vector Index: 상품 설명서 PDF 문서

3. Supervisor Agent (LangGraph)
   - Router: 질문 유형에 따라 적절한 도구 선택
   - 채권 검색/비교 → Genie Space
   - 발행사 정보/리스크 → Knowledge Assistant

다음 단계:
- Voice App과 통합
- 복합 질의 처리 (순차적 도구 호출)
- 수익 계산 로직 추가
""")
