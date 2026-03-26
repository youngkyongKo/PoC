# Databricks notebook source
# MAGIC %md
# MAGIC # Test Cache Layers (Static + Semantic)
# MAGIC
# MAGIC This notebook tests:
# MAGIC 1. Static Cache (PostgreSQL/Lakebase) - exact match
# MAGIC 2. Semantic Cache (Vector Search) - similarity match
# MAGIC 3. Cache Manager (unified interface)
# MAGIC
# MAGIC Prerequisites:
# MAGIC - Infrastructure setup completed (01_setup_infrastructure)
# MAGIC - Tables created and Vector Search index provisioned

# COMMAND ----------

# MAGIC %pip install psycopg2-binary --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import sys
from pathlib import Path
from datetime import datetime
import time

# Add project root to Python path (Databricks workspace)
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
project_root = "/Workspace" + str(Path(notebook_path).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from databricks.sdk import WorkspaceClient
from src.cache import (
    StaticCache,
    SemanticCache,
    CacheManager,
    get_cache_manager,
    CacheEntry,
    CacheSource
)

w = WorkspaceClient()

print("=" * 60)
print("Cache Layers Test")
print("=" * 60)
print(f"Current time: {datetime.now().isoformat()}")
print("=" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 1: Static Cache - Basic Operations

# COMMAND ----------

print("\n[Test 1] Static Cache - Basic Operations")
print("-" * 60)

static_cache = StaticCache(workspace_client=w)

# Test data
test_question = "오늘 주문 수는?"
cache_key = StaticCache.generate_cache_key(test_question)

print(f"Test question: '{test_question}'")
print(f"Cache key: {cache_key[:16]}...")

# Create test entry
test_entry = CacheEntry(
    cache_key=cache_key,
    original_question=test_question,
    normalized_question=test_question,
    genie_sql="SELECT COUNT(*) FROM orders WHERE date = '2026-03-24'",
    genie_result={
        "columns": ["count"],
        "data": [[42]],
        "row_count": 1
    },
    genie_description="Count of orders today",
    conversation_id="test-conversation-123",
    created_at=datetime.now(),
    accessed_at=datetime.now(),
    access_count=1,
    ttl_seconds=86400,
    confidence_score=1.0,
    source=CacheSource.STATIC
)

# Test SET
print("\n1. Testing SET operation...")
success = static_cache.set(test_entry)
if success:
    print("✓ Entry stored successfully")
else:
    print("✗ Failed to store entry")

# Test GET
print("\n2. Testing GET operation...")
retrieved_entry = static_cache.get(cache_key)
if retrieved_entry:
    print("✓ Entry retrieved successfully")
    print(f"  Original question: '{retrieved_entry.original_question}'")
    print(f"  SQL: {retrieved_entry.genie_sql[:50]}...")
    print(f"  Access count: {retrieved_entry.access_count}")
else:
    print("✗ Failed to retrieve entry")

# Test GET again (access count should increment)
print("\n3. Testing access count increment...")
retrieved_entry2 = static_cache.get(cache_key)
if retrieved_entry2:
    print(f"✓ Access count: {retrieved_entry2.access_count}")
    if retrieved_entry2.access_count > retrieved_entry.access_count:
        print("✓ Access count incremented correctly")
    else:
        print("✗ Access count did NOT increment")

# Test INVALIDATE
print("\n4. Testing INVALIDATE operation...")
invalidated = static_cache.invalidate(cache_key)
if invalidated:
    print("✓ Entry invalidated")

    # Verify it's gone
    retrieved_after_delete = static_cache.get(cache_key)
    if retrieved_after_delete is None:
        print("✓ Entry confirmed deleted")
    else:
        print("✗ Entry still exists after invalidation")
else:
    print("✗ Failed to invalidate entry")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 2: Static Cache - Performance

# COMMAND ----------

print("\n[Test 2] Static Cache - Performance")
print("-" * 60)

# Create test entries
test_entries = []
for i in range(10):
    question = f"테스트 질문 {i}"
    key = StaticCache.generate_cache_key(question)
    entry = CacheEntry(
        cache_key=key,
        original_question=question,
        normalized_question=question,
        genie_sql=f"SELECT * FROM test_{i}",
        genie_result={"data": [[i]]},
        created_at=datetime.now(),
        accessed_at=datetime.now(),
        access_count=1,
        ttl_seconds=86400,
        confidence_score=1.0,
        source=CacheSource.STATIC
    )
    test_entries.append(entry)

# Measure SET performance
print("\n1. Measuring SET performance...")
set_times = []
for entry in test_entries:
    start = time.time()
    static_cache.set(entry)
    elapsed = (time.time() - start) * 1000
    set_times.append(elapsed)

avg_set_time = sum(set_times) / len(set_times)
print(f"Average SET time: {avg_set_time:.0f}ms")

# Measure GET performance
print("\n2. Measuring GET performance...")
get_times = []
for entry in test_entries:
    start = time.time()
    static_cache.get(entry.cache_key)
    elapsed = (time.time() - start) * 1000
    get_times.append(elapsed)

avg_get_time = sum(get_times) / len(get_times)
print(f"Average GET time: {avg_get_time:.0f}ms")

# Target: < 50ms for GET
if avg_get_time < 50:
    print("✓ Static cache GET performance good (< 50ms)")
else:
    print("⚠ Static cache GET performance concern (> 50ms)")

# Cleanup
for entry in test_entries:
    static_cache.invalidate(entry.cache_key)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 3: Static Cache - Statistics

# COMMAND ----------

print("\n[Test 3] Static Cache - Statistics")
print("-" * 60)

stats = static_cache.get_stats()

print(f"Total entries: {stats.get('total_entries', 0)}")
print(f"Active entries: {stats.get('active_entries', 0)}")
print(f"Expired entries: {stats.get('expired_entries', 0)}")

if stats.get('top_queries'):
    print("\nTop queries:")
    for query in stats['top_queries'][:3]:
        print(f"  - '{query['normalized_question'][:50]}...' (accessed {query['access_count']} times)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 4: Semantic Cache - Add and Search

# COMMAND ----------

print("\n[Test 4] Semantic Cache - Add and Search")
print("-" * 60)

semantic_cache = SemanticCache(workspace_client=w)

# Check index status
print("\n1. Checking Vector Search index status...")
index_status = semantic_cache.get_index_status()
print(f"Index name: {index_status.get('name')}")
print(f"Index state: {index_status.get('state')}")
print(f"Pipeline type: {index_status.get('pipeline_type')}")

if index_status.get('state') != 'ONLINE':
    print("\n⚠ Vector Search index is not ONLINE yet")
    print("Please wait for index provisioning to complete")
    print("Check status with: w.vector_search_indexes.get_index(index_name)")
else:
    print("✓ Vector Search index is ONLINE")

    # Add test entry
    print("\n2. Adding test entry to semantic cache...")
    test_semantic_entry = CacheEntry(
        cache_key=StaticCache.generate_cache_key("오늘 주문 수"),
        original_question="오늘 주문 수는?",
        normalized_question="2026-03-24 주문 수",
        genie_sql="SELECT COUNT(*) FROM orders WHERE date = '2026-03-24'",
        genie_result={"columns": ["count"], "data": [[100]], "row_count": 1},
        conversation_id="test-semantic-123",
        created_at=datetime.now(),
        accessed_at=datetime.now(),
        access_count=1,
        ttl_seconds=86400,
        confidence_score=1.0,
        source=CacheSource.SEMANTIC
    )

    success = semantic_cache.add_entry(test_semantic_entry)
    if success:
        print("✓ Entry added to Delta table")
        print("  Note: Vector Search sync may take a few minutes")

        # Trigger sync (for TRIGGERED pipeline)
        print("\n3. Triggering Vector Search index sync...")
        sync_success = semantic_cache.sync_index()
        if sync_success:
            print("✓ Sync triggered (wait ~1-2 minutes for completion)")
        else:
            print("⚠ Sync trigger failed or not needed (CONTINUOUS pipeline)")

    # Search for similar questions (after sync completes)
    print("\n4. Searching for similar questions...")
    print("   Note: This may return empty if sync hasn't completed yet")

    similar_questions = [
        "오늘 주문 수",
        "오늘 주문 건수",
        "오늘 총 주문",
        "completely different question"
    ]

    for question in similar_questions:
        print(f"\n  Query: '{question}'")
        results = semantic_cache.search(
            normalized_question=question,
            num_results=3,
            similarity_threshold=0.7
        )

        if results:
            for result in results:
                print(f"    → '{result.normalized_question}' (score: {result.similarity_score:.3f})")
        else:
            print("    → No results found")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 5: Cache Manager - Unified Interface

# COMMAND ----------

print("\n[Test 5] Cache Manager - Unified Interface")
print("-" * 60)

cache_manager = get_cache_manager()

# Test query
test_question = "오늘 주문 수는?"
normalized_question = "2026-03-24 주문 수"

print(f"Test question: '{test_question}'")
print(f"Normalized: '{normalized_question}'")

# First query (cache miss expected)
print("\n1. First query (expecting MISS)...")
entry, source = cache_manager.get(
    normalized_question=normalized_question,
    original_question=test_question,
    use_semantic=True
)

if entry:
    print(f"✓ Cache HIT from {source.value}")
else:
    print("✓ Cache MISS (as expected)")

    # Store entry
    print("\n2. Storing entry in cache...")
    new_entry = CacheEntry(
        cache_key=StaticCache.generate_cache_key(normalized_question),
        original_question=test_question,
        normalized_question=normalized_question,
        genie_sql="SELECT COUNT(*) FROM orders WHERE date = '2026-03-24'",
        genie_result={"columns": ["count"], "data": [[150]], "row_count": 1},
        conversation_id="test-manager-123",
        created_at=datetime.now(),
        accessed_at=datetime.now(),
        access_count=1,
        ttl_seconds=86400,
        confidence_score=1.0,
        source=CacheSource.STATIC
    )

    success = cache_manager.set(new_entry, update_both=True)
    if success:
        print("✓ Entry stored in both cache layers")

        # Second query (cache hit expected)
        print("\n3. Second query (expecting HIT)...")
        entry2, source2 = cache_manager.get(
            normalized_question=normalized_question,
            original_question=test_question,
            use_semantic=False  # Only static cache for immediate hit
        )

        if entry2:
            print(f"✓ Cache HIT from {source2.value}")
            print(f"  SQL: {entry2.genie_sql[:50]}...")
        else:
            print("✗ Cache MISS (unexpected)")

# Get cache stats
print("\n4. Cache statistics...")
stats = cache_manager.get_stats()
print(f"Static cache total entries: {stats.get('static_cache', {}).get('total_entries', 0)}")
print(f"Semantic cache index state: {stats.get('semantic_cache', {}).get('index_state')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 6: Cache Manager - Similarity Thresholds

# COMMAND ----------

print("\n[Test 6] Cache Manager - Similarity Thresholds")
print("-" * 60)

print("Testing different similarity thresholds...")

# Similar question
similar_question = "오늘 주문 개수는?"
normalized_similar = "2026-03-24 주문 개수"

print(f"\nOriginal: '{test_question}'")
print(f"Similar: '{similar_question}'")

# Test with different thresholds
thresholds = [0.95, 0.85, 0.75, 0.65]

for threshold in thresholds:
    print(f"\nThreshold: {threshold}")
    entry, source = cache_manager.get(
        normalized_question=normalized_similar,
        original_question=similar_question,
        use_semantic=True,
        similarity_threshold=threshold
    )

    if entry:
        print(f"  ✓ HIT from {source.value} (score: {entry.confidence_score:.3f})")
    else:
        print(f"  ✗ MISS")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)
print("""
✓ Test 1: Static cache basic operations tested
✓ Test 2: Static cache performance benchmarked
✓ Test 3: Static cache statistics tested
✓ Test 4: Semantic cache operations tested
✓ Test 5: Cache manager unified interface tested
✓ Test 6: Similarity thresholds tested

📝 Next Steps:
1. Wait for Vector Search index sync (~1-2 minutes)
2. Run semantic cache tests again to verify similarity matching
3. Run notebook 04_test_pipeline for end-to-end testing

⚠ Notes:
- Vector Search sync is asynchronous (TRIGGERED pipeline)
- Semantic cache may show MISS until sync completes
- Use cache_manager.sync_semantic_index() to trigger manual sync
""")
print("=" * 60)
