"""
Databricks에서 사용 가능한 임베딩 모델 확인
"""
from databricks.sdk import WorkspaceClient
from config import config

client = WorkspaceClient(
    host=config.DATABRICKS_HOST,
    token=config.DATABRICKS_TOKEN
)

print("사용 가능한 Model Serving 엔드포인트:\n")
print("-" * 60)

# List all serving endpoints
endpoints = client.serving_endpoints.list()

embedding_endpoints = []
llm_endpoints = []

for endpoint in endpoints:
    name = endpoint.name
    print(f"\n엔드포인트: {name}")
    print(f"  상태: {endpoint.state.ready}")

    # Check if it's an embedding model (heuristic)
    if any(keyword in name.lower() for keyword in ['bge', 'gte', 'embed', 'e5']):
        embedding_endpoints.append(name)
        print(f"  타입: 임베딩 모델 (추정)")
    elif any(keyword in name.lower() for keyword in ['llama', 'dbrx', 'mixtral', 'gpt']):
        llm_endpoints.append(name)
        print(f"  타입: LLM 모델 (추정)")

print("\n" + "=" * 60)
print("\n📊 요약:")
print(f"\n임베딩 모델 엔드포인트 ({len(embedding_endpoints)}):")
for ep in embedding_endpoints:
    print(f"  - {ep}")

print(f"\nLLM 엔드포인트 ({len(llm_endpoints)}):")
for ep in llm_endpoints:
    print(f"  - {ep}")

print("\n" + "=" * 60)
print("\n💡 .env 파일 설정 예시:")
if embedding_endpoints:
    print(f"\nEMBEDDING_MODEL={embedding_endpoints[0]}")
if llm_endpoints:
    print(f"LLM_MODEL={llm_endpoints[0]}")
    print(f"SERVING_ENDPOINT={llm_endpoints[0]}")
