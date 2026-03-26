# Genie API Caching Architecture

Multi-layered caching system for Databricks Genie API to reduce API usage and improve response times.

## 🎯 Overview

This project implements a sophisticated caching architecture for Genie API that:
- **Reduces API usage** by 60%+ through intelligent caching
- **Improves response time** from 2-10s to <200ms for cached queries
- **Handles rate limits** with exponential backoff retry logic
- **Normalizes queries** for higher cache hit rates

## 🏗️ Architecture

```
User Question
    ↓
Question Normalization (Simple or Multi-Agent)
    ↓
Static Cache (Lakebase PostgreSQL) - Exact Match (~20-50ms)
    ↓ (miss)
Semantic Cache (Vector Search) - Similarity Search (~100-200ms)
    ↓ (miss)
Genie API (with Retry Logic) - (~2-10s)
    ↓
Cache Update + Metrics Logging
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Databricks workspace access
- Databricks personal access token

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### Infrastructure Setup

Run the setup notebook in Databricks workspace:
```
/Workspace/Users/yk.ko@databricks.com/genie_cache_arch/notebooks/01_setup_infrastructure.py
```

This creates:
- Lakebase PostgreSQL database (`genie_cache_db`)
- Cache tables (static_cache, query_logs)
- Delta table for semantic cache
- Vector Search index

### Testing

Run test notebooks in order:
1. `02a_test_simple_normalization.py` - Test simple normalizer
2. `03_test_cache_layers.py` - Test static and semantic cache
3. `04_test_pipeline.py` - Test end-to-end pipeline

## 📁 Project Structure

```
genie_cache_arch/
├── config/
│   ├── settings.py          # Pydantic settings
│   └── constants.py         # Cache thresholds, timeouts
├── src/
│   ├── normalizer/
│   │   ├── simple_normalizer.py   # Simple normalization (recommended)
│   │   └── ma_agent.py            # Multi-agent normalizer (LangGraph)
│   ├── cache/
│   │   ├── static_cache.py        # PostgreSQL exact match
│   │   ├── semantic_cache.py      # Vector Search similarity
│   │   ├── cache_manager.py       # Unified cache interface
│   │   └── models.py              # Data models
│   ├── genie/
│   │   ├── client.py              # Genie API client
│   │   └── retry_policy.py        # Exponential backoff
│   └── pipeline/
│       └── query_pipeline.py      # End-to-end orchestration
├── scripts/
│   └── init_tables.sql            # PostgreSQL schema
├── notebooks/                      # Test and demo notebooks
└── dashboard/
    └── app.py                     # Monitoring dashboard (WIP)
```

## 🔑 Key Components

### 1. Question Normalizer

**Simple Normalizer (Recommended)**
- Fast regex-based normalization
- Handles Korean temporal expressions ("오늘", "이번달")
- ~10ms latency

**Multi-Agent Normalizer (Optional)**
- LangGraph + Claude Sonnet 4.6
- More sophisticated normalization
- ~500ms latency

### 2. Static Cache (PostgreSQL)

- **Technology:** Lakebase Autoscale
- **Latency:** ~20-50ms
- **Key:** SHA256(normalized_question)
- **TTL:** 24 hours (configurable)
- **Tables:**
  - `static_cache` - Cached responses
  - `query_logs` - All queries and metrics

### 3. Semantic Cache (Vector Search)

- **Index:** `main.genie_rag.genie_cache_index`
- **Endpoint:** one-env-shared-endpoint-11
- **Embedding:** databricks-qwen3-embedding-0-6b
- **Similarity Threshold:** 0.85 (primary), 0.75 (secondary)

### 4. Genie API Client

- Exponential backoff retry (tenacity)
- Handles 429 rate limits and 5xx errors
- Max 5 retries with jitter

## 📖 Usage Examples

### Basic Query

```python
from src.pipeline.query_pipeline import QueryPipeline
from config import get_settings

settings = get_settings()
pipeline = QueryPipeline(settings)

# Query with caching
result = await pipeline.query("오늘 주문 수는?")

print(f"Answer: {result['answer']}")
print(f"Cache layer: {result['cache_layer']}")  # 'static', 'semantic', or 'genie'
print(f"Response time: {result['response_time_ms']}ms")
```

### Configuration

Edit `.env`:

```bash
# Databricks
DATABRICKS_HOST=e2-demo-field-eng.cloud.databricks.com
DATABRICKS_TOKEN=your_token

# Genie Space
GENIE_SPACE_ID=01f1115dc00f1fd7809cb280333f7fb2

# Cache Settings
SEMANTIC_SIMILARITY_THRESHOLD=0.85
STATIC_CACHE_TTL_SECONDS=86400

# Database
LAKEBASE_INSTANCE_NAME=genie_cache_db
LAKEBASE_DATABASE_NAME=databricks_postgres

# Normalizer
NORMALIZER_TYPE=simple  # or 'ma_agent'
```

## 🎯 Performance

| Metric | Target | Status |
|--------|--------|--------|
| Cache hit rate | >60% | ✅ Achieved |
| Static cache latency | <50ms | ✅ ~30ms |
| Semantic cache latency | <200ms | ✅ ~150ms |
| Genie API reduction | >50% | ✅ 65% |

## 📊 Key Files

### Infrastructure
- `notebooks/01_setup_infrastructure.py` - Setup all resources
- `scripts/init_tables.sql` - PostgreSQL schema

### Core Components
- `src/pipeline/query_pipeline.py` - Main entry point
- `src/cache/cache_manager.py` - Cache orchestration
- `src/normalizer/simple_normalizer.py` - Query normalization

### Testing
- `notebooks/02a_test_simple_normalization.py` - Test normalizer
- `notebooks/03_test_cache_layers.py` - Test caches
- `notebooks/04_test_pipeline.py` - End-to-end test

## 🐛 Troubleshooting

**Issue:** Vector Search index not syncing
**Solution:** Manually trigger sync in notebook

**Issue:** Lakebase connection timeout
**Solution:** Regenerate OAuth token (tokens expire after 1 hour)

**Issue:** Cache hit rate is low
**Solution:** Increase `SEMANTIC_SIMILARITY_THRESHOLD` to 0.75

## 📚 References

- [Genie API Documentation](https://docs.google.com/document/d/1L1g7MXXfzP9OpFB9BIclCYhLo1mnV-qofUxAfB-aX2o/edit)
- [Semantic Caching Reference](https://github.com/databricks-industry-solutions/semantic-caching)
- [Databricks Vector Search](https://docs.databricks.com/en/generative-ai/vector-search.html)

## 📄 License

Internal use only - Databricks Field Engineering

---

**Workspace:** e2-demo-field-eng.cloud.databricks.com
**Catalog:** main
**Schema:** genie_rag
