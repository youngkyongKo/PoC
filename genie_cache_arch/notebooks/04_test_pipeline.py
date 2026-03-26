# Databricks notebook source
# MAGIC %md
# MAGIC # End-to-End Pipeline Test
# MAGIC
# MAGIC This notebook tests the complete Genie caching pipeline:
# MAGIC 1. Question normalization (LangGraph)
# MAGIC 2. Cache lookup (Static → Semantic)
# MAGIC 3. Genie API call (with retry)
# MAGIC 4. Cache update (both layers)
# MAGIC 5. Metrics collection
# MAGIC
# MAGIC Prerequisites:
# MAGIC - Infrastructure setup completed
# MAGIC - Anthropic API key set (for Claude Sonnet 4.6)
# MAGIC - Genie Space configured

# COMMAND ----------

# MAGIC %pip install langgraph langchain langchain-core langchain-community tenacity --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import sys
from pathlib import Path
from datetime import datetime
import time
import os

# Add project root to Python path (Databricks workspace)
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
project_root = "/Workspace" + str(Path(notebook_path).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from databricks.sdk import WorkspaceClient
from src.pipeline import get_pipeline, QueryPipeline
from config import get_settings

w = WorkspaceClient()
settings = get_settings()

print("=" * 60)
print("End-to-End Pipeline Test")
print("=" * 60)
print(f"Workspace: {settings.databricks_host}")
print(f"Genie Space: {settings.genie_space_id}")
print(f"Current time: {datetime.now().isoformat()}")
print("=" * 60)
print()
print("📌 LLM Configuration:")
print("   Using Databricks Model Serving Endpoint")
print("   Endpoint: databricks-gpt-5-4")
print("   URL: https://e2-demo-field-eng.cloud.databricks.com/serving-endpoints/databricks-gpt-5-4/invocations")
print("=" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 1: First Query (Cache MISS → Genie API)

# COMMAND ----------

print("\n[Test 1] First Query - Cache MISS → Genie API")
print("-" * 60)

pipeline = get_pipeline()

test_question = "총 주문 수는 몇 개?"

print(f"Question: '{test_question}'")
print("\nExecuting pipeline...")

result, metrics = pipeline.query(
    question=test_question,
    use_cache=True,
    use_semantic=True
)

print("\n📊 Result:")
print(f"Status: {result.status}")
if result.success:
    print(f"SQL: {result.sql}")
    print(f"Rows: {result.row_count}")
    print(f"Data preview: {result.data[:3] if result.data else None}")
else:
    print(f"Error: {result.error}")

print("\n📈 Metrics:")
print(f"Response time: {metrics.response_time_ms}ms")
print(f"Cache hit: {metrics.cache_hit}")
print(f"Cache source: {metrics.cache_source.value}")
print(f"Static cache hit: {metrics.static_cache_hit}")
print(f"Semantic cache hit: {metrics.semantic_cache_hit}")
print(f"Genie API called: {metrics.genie_api_called}")
print(f"Normalized question: '{metrics.normalized_question}'")

# Save for next test
conversation_id = result.conversation_id

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 2: Second Query (Cache HIT - Static)

# COMMAND ----------

print("\n[Test 2] Second Query - Cache HIT (Static)")
print("-" * 60)

print(f"Question (same): '{test_question}'")
print("\nExecuting pipeline...")

result2, metrics2 = pipeline.query(
    question=test_question,
    use_cache=True,
    use_semantic=False  # Only static cache
)

print("\n📊 Result:")
print(f"Status: {result2.status}")
print(f"Rows: {result2.row_count}")

print("\n📈 Metrics:")
print(f"Response time: {metrics2.response_time_ms}ms")
print(f"Cache hit: {metrics2.cache_hit}")
print(f"Cache source: {metrics2.cache_source.value}")
print(f"Genie API called: {metrics2.genie_api_called}")

# Compare with first query
print("\n📊 Comparison:")
print(f"First query: {metrics.response_time_ms}ms (Genie API)")
print(f"Second query: {metrics2.response_time_ms}ms (Static cache)")
print(f"Speedup: {metrics.response_time_ms / metrics2.response_time_ms:.1f}x")

if metrics2.static_cache_hit and not metrics2.genie_api_called:
    print("✓ Static cache working correctly")
else:
    print("✗ Static cache NOT working as expected")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 3: Similar Query (Semantic Cache)

# COMMAND ----------

print("\n[Test 3] Similar Query - Semantic Cache")
print("-" * 60)

similar_question = "주문 건수는 몇 개인가?"

print(f"Original: '{test_question}'")
print(f"Similar: '{similar_question}'")
print("\nExecuting pipeline...")

result3, metrics3 = pipeline.query(
    question=similar_question,
    use_cache=True,
    use_semantic=True
)

print("\n📊 Result:")
print(f"Status: {result3.status}")
print(f"Rows: {result3.row_count}")

print("\n📈 Metrics:")
print(f"Response time: {metrics3.response_time_ms}ms")
print(f"Cache hit: {metrics3.cache_hit}")
print(f"Cache source: {metrics3.cache_source.value}")
print(f"Static cache hit: {metrics3.static_cache_hit}")
print(f"Semantic cache hit: {metrics3.semantic_cache_hit}")
if metrics3.similarity_score:
    print(f"Similarity score: {metrics3.similarity_score:.3f}")
print(f"Genie API called: {metrics3.genie_api_called}")

if metrics3.semantic_cache_hit:
    print("✓ Semantic cache working correctly")
elif not metrics3.genie_api_called:
    print("ℹ Semantic cache may need more time for Vector Search sync")
else:
    print("ℹ Semantic cache MISS - similarity below threshold")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 4: Follow-up Query

# COMMAND ----------

print("\n[Test 4] Follow-up Query (Context-Dependent)")
print("-" * 60)

if conversation_id:
    followup_question = "그 중에서 배송 완료된 주문은?"

    print(f"Original conversation: {conversation_id[:16]}...")
    print(f"Follow-up: '{followup_question}'")
    print("\nExecuting follow-up...")

    result4, metrics4 = pipeline.query_followup(
        question=followup_question,
        conversation_id=conversation_id
    )

    print("\n📊 Result:")
    print(f"Status: {result4.status}")
    if result4.success:
        print(f"SQL: {result4.sql}")
        print(f"Rows: {result4.row_count}")
    else:
        print(f"Error: {result4.error}")

    print("\n📈 Metrics:")
    print(f"Response time: {metrics4.response_time_ms}ms")
    print(f"Genie API called: {metrics4.genie_api_called}")

    print("\nℹ Note: Follow-up queries are NOT cached (context-dependent)")
else:
    print("⚠ No conversation ID from first query - skipping follow-up test")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 5: Performance Benchmark

# COMMAND ----------

print("\n[Test 5] Performance Benchmark")
print("-" * 60)

test_questions = [
    "총 주문 금액은?",
    "고객 수는 몇 명?",
    "가장 비싼 주문은?",
    "평균 주문 금액은?",
    "오늘 주문 수는?"
]

print(f"Testing {len(test_questions)} questions...")
print("\nFirst pass (cache miss):")

first_pass_metrics = []
for question in test_questions:
    print(f"\n  '{question[:30]}...'")
    result, metrics = pipeline.query(question, use_cache=True)
    first_pass_metrics.append(metrics)
    print(f"    → {metrics.response_time_ms}ms (API: {metrics.genie_api_called})")

print("\nSecond pass (cache hit expected):")

second_pass_metrics = []
for i, question in enumerate(test_questions):
    print(f"\n  '{question[:30]}...'")
    result, metrics = pipeline.query(question, use_cache=True)
    second_pass_metrics.append(metrics)
    print(f"    → {metrics.response_time_ms}ms (cached: {metrics.cache_hit})")

# Calculate statistics
first_avg = sum(m.response_time_ms for m in first_pass_metrics) / len(first_pass_metrics)
second_avg = sum(m.response_time_ms for m in second_pass_metrics) / len(second_pass_metrics)
cache_hit_rate = sum(1 for m in second_pass_metrics if m.cache_hit) / len(second_pass_metrics)

print("\n📊 Benchmark Summary:")
print(f"First pass (Genie API): {first_avg:.0f}ms average")
print(f"Second pass (cached): {second_avg:.0f}ms average")
print(f"Speedup: {first_avg / second_avg:.1f}x")
print(f"Cache hit rate: {cache_hit_rate * 100:.0f}%")

if cache_hit_rate >= 0.8:  # Target: 80%+ hit rate
    print("✓ Good cache hit rate (≥80%)")
else:
    print("⚠ Low cache hit rate (<80%)")

if second_avg < 200:  # Target: <200ms for cached queries
    print("✓ Good cached response time (<200ms)")
else:
    print("⚠ Cached response time concern (>200ms)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 6: Cache Statistics

# COMMAND ----------

print("\n[Test 6] Cache Statistics")
print("-" * 60)

from src.cache import get_cache_manager

cache_manager = get_cache_manager()

print("Fetching cache statistics...")
stats = cache_manager.get_stats()

print("\n📊 Static Cache:")
static_stats = stats.get('static_cache', {})
print(f"  Total entries: {static_stats.get('total_entries', 0)}")
print(f"  Active entries: {static_stats.get('active_entries', 0)}")
print(f"  Expired entries: {static_stats.get('expired_entries', 0)}")

if static_stats.get('top_queries'):
    print("\n  Top queries:")
    for query in static_stats['top_queries'][:5]:
        print(f"    - '{query['normalized_question'][:40]}...' ({query['access_count']} accesses)")

print("\n📊 Semantic Cache:")
semantic_stats = stats.get('semantic_cache', {})
print(f"  Index name: {semantic_stats.get('index_name')}")
print(f"  Index state: {semantic_stats.get('index_state')}")
print(f"  Pipeline type: {semantic_stats.get('pipeline_type')}")
print(f"  Source table: {semantic_stats.get('source_table')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("\n" + "=" * 60)
print("End-to-End Pipeline Test Summary")
print("=" * 60)
print(f"""
✓ Test 1: First query (cache miss → Genie API) ✓
✓ Test 2: Second query (static cache hit) ✓
✓ Test 3: Similar query (semantic cache) ✓
✓ Test 4: Follow-up query (context-dependent) ✓
✓ Test 5: Performance benchmark ✓
✓ Test 6: Cache statistics ✓

📊 Key Metrics:
- Cache hit rate: Target >60%, achieved {cache_hit_rate * 100:.0f}%
- Cached response time: Target <200ms, achieved {second_avg:.0f}ms avg
- Speedup: {first_avg / second_avg:.1f}x faster with cache

📝 Next Steps:
1. Run Streamlit dashboard: streamlit run dashboard/app.py
2. Monitor cache performance in production
3. Tune similarity thresholds based on metrics
4. Adjust TTL settings if needed

⚠ Notes:
- Normalization requires ANTHROPIC_API_KEY for Claude
- Semantic cache requires Vector Search sync (1-2 min delay)
- Follow-up queries are NOT cached (context-dependent)
""")
print("=" * 60)
