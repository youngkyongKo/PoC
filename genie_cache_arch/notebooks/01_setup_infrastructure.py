# Databricks notebook source
# MAGIC %md
# MAGIC # Infrastructure Setup for Genie Cache Architecture
# MAGIC
# MAGIC This notebook sets up:
# MAGIC 1. Lakebase PostgreSQL database (autoscale)
# MAGIC 2. Unity Catalog schema
# MAGIC 3. Delta table for semantic cache
# MAGIC 4. Vector Search index
# MAGIC
# MAGIC Run this once to initialize the infrastructure.

# COMMAND ----------

# MAGIC %pip install psycopg2-binary databricks-sdk --upgrade --quiet
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

import sys
from pathlib import Path

# Add project root to Python path (Databricks workspace)
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
# notebook_path is like: /Users/yk.ko@databricks.com/POC/genie_cache_arch/notebooks/01_setup_infrastructure
# We need: /Workspace/Users/yk.ko@databricks.com/POC/genie_cache_arch
project_root = "/Workspace" + str(Path(notebook_path).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"📁 Project root: {project_root}")
print(f"✓ Python path configured")

from databricks.sdk import WorkspaceClient
from config import get_settings

settings = get_settings()
w = WorkspaceClient()

print("=" * 60)
print("Genie Cache Architecture - Infrastructure Setup")
print("=" * 60)
print(f"Workspace: {settings.databricks_host}")
print(f"Catalog: {settings.uc_catalog}")
print(f"Schema: {settings.uc_schema}")
print(f"Genie Space ID: {settings.genie_space_id}")
print(f"Vector Search Endpoint: {settings.vector_search_endpoint}")
print("=" * 60)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Get Lakebase Autoscale Connection Details
# MAGIC
# MAGIC **Lakebase Autoscale Configuration:**
# MAGIC - Project: `ykko-genie-cache-db`
# MAGIC - Branch: `production`
# MAGIC - Endpoint: `primary`
# MAGIC - Schema: `geniecache`

# COMMAND ----------

print("\n[1/5] Getting Lakebase Autoscale connection details...")
print(f"Project: {settings.lakebase_project_name}")
print(f"Branch: {settings.lakebase_branch}")
print(f"Endpoint: {settings.lakebase_endpoint}")
print(f"Schema: {settings.lakebase_schema}")
print()

try:
    # Get endpoint details using Databricks API
    endpoint_resource_name = settings.get_lakebase_endpoint_resource_name()
    print(f"Fetching endpoint: {endpoint_resource_name}")

    # Use Postgres API to get endpoint details
    endpoint_response = w.api_client.do(
        "GET",
        f"/api/2.0/postgres/{endpoint_resource_name}"
    )

    # Extract host information
    endpoint_status = endpoint_response.get('status', {})
    endpoint_state = endpoint_status.get('state', 'UNKNOWN')
    hosts = endpoint_status.get('hosts', {})
    lakebase_host = hosts.get('host')

    if not lakebase_host:
        raise ValueError("Could not retrieve Lakebase host from endpoint")

    print(f"\n✓ Lakebase endpoint details:")
    print(f"  State: {endpoint_state}")
    print(f"  Host: {lakebase_host}")
    print(f"  Port: {settings.lakebase_port}")
    print(f"  Default Database: databricks_postgres")
    print(f"  Schema: {settings.lakebase_schema}")

except Exception as e:
    print(f"\n✗ Error getting Lakebase endpoint: {e}")
    print()
    print("Please verify:")
    print(f"  1. Project exists: {settings.lakebase_project_name}")
    print(f"  2. Branch exists: {settings.lakebase_branch}")
    print(f"  3. Endpoint exists: {settings.lakebase_endpoint}")
    print(f"  4. Endpoint is in RUNNING state")
    print()
    print("You can check in the UI:")
    print(f"  https://{settings.databricks_host}/compute/lakebase?o=6051921418418893")
    print()
    print("API endpoint being called:")
    print(f"  GET /api/2.0/postgres/{endpoint_resource_name}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Create PostgreSQL Tables

# COMMAND ----------

print("\n[2/5] Creating PostgreSQL cache tables...")

try:
    import psycopg2
    import subprocess
    import json

    # Get current user
    current_user = w.current_user.me()
    lakebase_user = current_user.user_name

    print("📝 Generating Lakebase credential...")
    print(f"   User: {lakebase_user}")
    print(f"   Endpoint: {endpoint_resource_name}")
    print()

    # Try to generate credential using databricks CLI
    try:
        print("Attempting to generate credential using databricks CLI...")

        # Use databricks CLI to generate token
        cmd = [
            "databricks",
            "api",
            "POST",
            f"/api/2.0/postgres/{endpoint_resource_name}:generateDatabaseCredential",
            "--json", "{}"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            cred_data = json.loads(result.stdout)
            token = cred_data.get('token')
            if token:
                print(f"✓ Credential generated via databricks CLI")
            else:
                raise ValueError("No token in response")
        else:
            raise Exception(f"CLI failed: {result.stderr}")

    except Exception as e:
        print(f"⚠️  Automatic credential generation failed: {e}")
        print()
        print("=" * 60)
        print("MANUAL CREDENTIAL GENERATION REQUIRED")
        print("=" * 60)
        print()
        print("Option 1: Use databricks CLI in terminal:")
        print(f"  databricks api POST \\")
        print(f"    '/api/2.0/postgres/{endpoint_resource_name}:generateDatabaseCredential' \\")
        print(f"    --json '{{}}'")
        print()
        print("Option 2: Get token from Lakebase UI:")
        print(f"  1. Go to: https://{settings.databricks_host}/compute/lakebase")
        print(f"  2. Click on project: {settings.lakebase_project_name}")
        print(f"  3. Click 'Connect' → Copy connection token")
        print()
        print("=" * 60)
        print()

        # Provide manual token input
        token = input("Paste the token here: ").strip()
        if not token:
            raise ValueError("Token is required to connect to Lakebase")
        print(f"✓ Using provided token")

    # Connect to Lakebase
    print(f"\n🔌 Connecting to Lakebase...")
    print(f"   Host: {lakebase_host}")
    print(f"   Port: {settings.lakebase_port}")
    print(f"   Database: databricks_postgres")
    print(f"   Schema: {settings.lakebase_schema}")

    conn = psycopg2.connect(
        host=lakebase_host,
        port=settings.lakebase_port,
        dbname="databricks_postgres",
        user=lakebase_user,
        password=token,
        sslmode="require"
    )

    try:
        # Create schema first
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.lakebase_schema}")
            conn.commit()
            print(f"✓ Schema '{settings.lakebase_schema}' ready")

        # Set search path to use the schema
        with conn.cursor() as cur:
            cur.execute(f"SET search_path TO {settings.lakebase_schema}, public")
            conn.commit()

        # SQL schema (inline for Databricks)
        sql_content = f"""
-- Genie Query Cache Table
CREATE TABLE IF NOT EXISTS {settings.lakebase_schema}.genie_query_cache (
    cache_key VARCHAR(64) PRIMARY KEY,
    original_question TEXT NOT NULL,
    normalized_question TEXT NOT NULL,
    genie_sql TEXT,
    genie_result JSONB,
    genie_description TEXT,
    conversation_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    accessed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    access_count INTEGER NOT NULL DEFAULT 1,
    ttl_seconds INTEGER NOT NULL DEFAULT 86400
);

-- Query Log Table
CREATE TABLE IF NOT EXISTS {settings.lakebase_schema}.query_log (
    id SERIAL PRIMARY KEY,
    query_time TIMESTAMP NOT NULL DEFAULT NOW(),
    original_question TEXT NOT NULL,
    normalized_question TEXT NOT NULL,
    cache_key VARCHAR(64),
    static_cache_hit BOOLEAN DEFAULT FALSE,
    semantic_cache_hit BOOLEAN DEFAULT FALSE,
    similarity_score FLOAT,
    cache_source VARCHAR(20),
    response_time_ms INTEGER,
    genie_api_called BOOLEAN DEFAULT FALSE,
    error_message TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_cache_normalized ON {settings.lakebase_schema}.genie_query_cache(normalized_question);
CREATE INDEX IF NOT EXISTS idx_cache_accessed ON {settings.lakebase_schema}.genie_query_cache(accessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_cache_created ON {settings.lakebase_schema}.genie_query_cache(created_at);
CREATE INDEX IF NOT EXISTS idx_log_query_time ON {settings.lakebase_schema}.query_log(query_time DESC);
CREATE INDEX IF NOT EXISTS idx_log_cache_key ON {settings.lakebase_schema}.query_log(cache_key);

-- Function to cleanup expired cache
CREATE OR REPLACE FUNCTION {settings.lakebase_schema}.cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM {settings.lakebase_schema}.genie_query_cache
    WHERE (created_at + (ttl_seconds || ' seconds')::INTERVAL) < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update cache access
CREATE OR REPLACE FUNCTION {settings.lakebase_schema}.update_cache_access()
RETURNS TRIGGER AS $$
BEGIN
    NEW.accessed_at = NOW();
    NEW.access_count = OLD.access_count + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- View for cache performance summary
CREATE OR REPLACE VIEW {settings.lakebase_schema}.cache_performance_summary AS
SELECT
    COUNT(*) as total_entries,
    COUNT(*) FILTER (WHERE (created_at + (ttl_seconds || ' seconds')::INTERVAL) > NOW()) as active_entries,
    COUNT(*) FILTER (WHERE (created_at + (ttl_seconds || ' seconds')::INTERVAL) <= NOW()) as expired_entries,
    AVG(access_count) as avg_access_count,
    MAX(access_count) as max_access_count
FROM {settings.lakebase_schema}.genie_query_cache;

-- View for top cached queries
CREATE OR REPLACE VIEW {settings.lakebase_schema}.top_cached_queries AS
SELECT
    normalized_question,
    access_count,
    created_at,
    accessed_at,
    EXTRACT(EPOCH FROM (accessed_at - created_at)) / access_count as avg_seconds_between_access
FROM {settings.lakebase_schema}.genie_query_cache
WHERE (created_at + (ttl_seconds || ' seconds')::INTERVAL) > NOW()
ORDER BY access_count DESC
LIMIT 20;
"""

        # Execute schema
        with conn.cursor() as cur:
            cur.execute(sql_content)
            conn.commit()

        # Verify tables
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{settings.lakebase_schema}'
                AND table_name IN ('genie_query_cache', 'query_log')
                ORDER BY table_name
            """)
            tables = cur.fetchall()

        print(f"✓ PostgreSQL tables created in schema '{settings.lakebase_schema}':")
        for table in tables:
            print(f"  - {settings.lakebase_schema}.{table[0]}")
    finally:
        conn.close()

    print(f"\n✓ Lakebase connection info:")
    print(f"  Host: {lakebase_host}")
    print(f"  User: {lakebase_user}")

except Exception as e:
    print(f"✗ Error creating PostgreSQL tables: {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Create Unity Catalog Schema

# COMMAND ----------

print("\n[3/5] Creating Unity Catalog schema...")

try:
    # Check if catalog exists
    try:
        w.catalogs.get(name=settings.uc_catalog)
        print(f"✓ Catalog exists: {settings.uc_catalog}")
    except Exception:
        print(f"✗ Catalog not found: {settings.uc_catalog}")
        print(f"  Please create catalog '{settings.uc_catalog}' in Unity Catalog first")
        raise

    # Create schema if not exists
    try:
        w.schemas.get(full_name=f"{settings.uc_catalog}.{settings.uc_schema}")
        print(f"✓ Schema already exists: {settings.uc_catalog}.{settings.uc_schema}")
    except Exception:
        w.schemas.create(
            name=settings.uc_schema,
            catalog_name=settings.uc_catalog,
            comment="Schema for Genie cache architecture"
        )
        print(f"✓ Schema created: {settings.uc_catalog}.{settings.uc_schema}")

except Exception as e:
    print(f"✗ Error with Unity Catalog schema: {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Create Delta Table for Semantic Cache

# COMMAND ----------

print("\n[4/5] Creating Delta table for semantic cache...")

embeddings_table = settings.get_full_table_name("query_embeddings")

try:
    # Check if table already exists
    try:
        existing_table = w.tables.get(full_name=embeddings_table)
        print(f"✓ Delta table already exists: {embeddings_table}")

        # Enable change data feed if not already enabled
        try:
            spark.sql(f"ALTER TABLE {embeddings_table} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
            print(f"✓ Change data feed enabled")
        except:
            pass

    except Exception:
        # Create Delta table
        print(f"Creating Delta table: {embeddings_table}")

        spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {embeddings_table} (
            cache_key STRING,
            normalized_question STRING NOT NULL,
            genie_sql STRING,
            genie_result STRING,
            conversation_id STRING,
            created_at TIMESTAMP
        ) USING DELTA
        TBLPROPERTIES (
            delta.enableChangeDataFeed = true
        )
        COMMENT 'Embeddings table for semantic cache (Vector Search source)'
        """)

        print(f"✓ Delta table created: {embeddings_table}")

except Exception as e:
    print(f"✗ Error creating Delta table: {e}")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Create Vector Search Index

# COMMAND ----------

print("\n[5/5] Creating Vector Search index...")

try:
    from databricks.sdk.service.vectorsearch import (
        DeltaSyncVectorIndexSpecRequest,
        EmbeddingSourceColumn,
        VectorIndexType,
        PipelineType
    )

    index_name = settings.vector_search_index
    endpoint_name = settings.vector_search_endpoint

    # Check if index already exists
    try:
        existing_index = w.vector_search_indexes.get_index(index_name=index_name)
        index_state = "ONLINE" if existing_index.status.ready else "NOT_READY"
        print(f"✓ Vector Search index already exists: {index_name}")
        print(f"  Status: {index_state}")
    except Exception:
        # Create new index
        print(f"Creating Vector Search index: {index_name}")
        print(f"  Endpoint: {endpoint_name}")
        print(f"  Source table: {embeddings_table}")

        index = w.vector_search_indexes.create_index(
            name=index_name,
            endpoint_name=endpoint_name,
            primary_key="cache_key",
            index_type=VectorIndexType.DELTA_SYNC,
            delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
                source_table=embeddings_table,
                embedding_source_columns=[
                    EmbeddingSourceColumn(
                        name="normalized_question",
                        embedding_model_endpoint_name="databricks-qwen3-embedding-0-6b"
                    )
                ],
                pipeline_type=PipelineType.TRIGGERED
            )
        )

        print(f"✓ Vector Search index created: {index_name}")
        print(f"  Note: Index is being provisioned (may take a few minutes)")
        print(f"  Check status with: w.vector_search_indexes.get_index('{index_name}')")

except Exception as e:
    print(f"✗ Error creating Vector Search index: {e}")
    print(f"  Note: If endpoint '{endpoint_name}' doesn't exist, create it first")
    raise

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

print("\n" + "=" * 60)
print("Infrastructure Setup Complete!")
print("=" * 60)
print("\n✓ Resources created:")
print(f"  1. Lakebase database: {settings.lakebase_database_name}")
print(f"     - Host: {lakebase_host}")
print(f"     - User: {lakebase_user}")
print(f"     - Tables: genie_query_cache, query_log")
print(f"  2. Unity Catalog schema: {settings.uc_catalog}.{settings.uc_schema}")
print(f"  3. Delta table: {embeddings_table}")
print(f"  4. Vector Search index: {settings.vector_search_index}")
print("\n📝 Connection Information:")
print(f"  LAKEBASE_HOST={lakebase_host}")
print(f"  LAKEBASE_USER={lakebase_user}")
print("\n📝 Next steps:")
print("  1. Verify Vector Search index status (may take a few minutes)")
print("  2. Run notebook 02_test_normalization to test question normalizer")
print("  3. Run notebook 03_test_cache_layers to test cache operations")
print("=" * 60)
