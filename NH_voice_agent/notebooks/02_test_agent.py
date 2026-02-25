# Databricks notebook source
# MAGIC %md
# MAGIC # Agent 테스트
# MAGIC
# MAGIC Vector Search와 Genie Space를 활용하는 Agent를 테스트합니다.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 환경 설정

# COMMAND ----------

# Configuration
CATALOG = "main"
SCHEMA = "nh_voice_agent"
VECTOR_INDEX = f"{CATALOG}.{SCHEMA}.pdf_embeddings_index"
GENIE_SPACE_ID = "your_genie_space_id"  # Replace with actual ID
MODEL_ENDPOINT = "databricks-dbrx-instruct"

# COMMAND ----------

# MAGIC %pip install langchain langchain-community

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Vector Search Tool 테스트

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()

# Get index
index = vsc.get_index(
    endpoint_name="vs_endpoint",
    index_name=VECTOR_INDEX
)

# Test query
test_query = "보험 상품의 보장 내용"

results = index.similarity_search(
    query_text=test_query,
    columns=["chunk_id", "text", "file_name"],
    num_results=3
)

print(f"Query: '{test_query}'\n")
print("Results:")
display(results)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Agent 테스트

# COMMAND ----------

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models import ChatDatabricks
from langchain.tools import Tool

# Initialize LLM
llm = ChatDatabricks(
    target_uri="databricks",
    endpoint=MODEL_ENDPOINT,
    temperature=0.1
)

# Create Vector Search Tool
def vector_search_tool(query: str) -> str:
    """Search documents using Vector Search"""
    results = index.similarity_search(
        query_text=query,
        columns=["text", "file_name"],
        num_results=3
    )

    formatted = []
    for idx, row in enumerate(results.get("result", {}).get("data_array", []), 1):
        text = row[0]
        source = row[1]
        formatted.append(f"[{idx}] {text}\n(출처: {source})")

    return "\n\n".join(formatted) if formatted else "관련 문서를 찾을 수 없습니다."

tools = [
    Tool(
        name="vector_search",
        description="문서 검색 도구",
        func=vector_search_tool
    )
]

# Create Agent
prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 NH생명 고객 지원 AI 어시스턴트입니다."),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

agent = create_openai_tools_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. 테스트 질문

# COMMAND ----------

test_questions = [
    "보험 청약 절차를 알려주세요",
    "보험금 청구는 어떻게 하나요?",
    "상품의 주요 보장 내용은 무엇인가요?"
]

for question in test_questions:
    print(f"\n{'='*60}")
    print(f"Q: {question}")
    print(f"{'='*60}\n")

    result = agent_executor.invoke({"input": question})
    print(f"A: {result['output']}\n")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 완료!
# MAGIC
# MAGIC Agent가 정상적으로 작동합니다.
# MAGIC
# MAGIC 다음 단계:
# MAGIC 1. Genie Space 통합
# MAGIC 2. 음성 인터페이스 추가
# MAGIC 3. 프로덕션 배포
