# Databricks notebook source
# MAGIC %md
# MAGIC # NH Voice Agent - RAG 파이프라인 설정
# MAGIC
# MAGIC 이 노트북은 Databricks에서 RAG 파이프라인을 설정합니다:
# MAGIC 1. Unity Catalog 리소스 생성
# MAGIC 2. Vector Search 엔드포인트 및 인덱스 생성
# MAGIC 3. 샘플 데이터 업로드 및 처리

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 환경 설정

# COMMAND ----------

# 설정
CATALOG = "main"
SCHEMA = "nh_voice_agent"
VOLUME = "documents"
VECTOR_ENDPOINT = "vs_endpoint"
VECTOR_INDEX_NAME = f"{CATALOG}.{SCHEMA}.pdf_embeddings_index"
EMBEDDING_MODEL = "databricks-bge-large-en"

print(f"Catalog: {CATALOG}")
print(f"Schema: {SCHEMA}")
print(f"Volume: {VOLUME}")
print(f"Vector Index: {VECTOR_INDEX_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Unity Catalog 리소스 생성

# COMMAND ----------

# Create catalog (if not exists)
spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
print(f"✓ Catalog '{CATALOG}' ready")

# Create schema
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
print(f"✓ Schema '{CATALOG}.{SCHEMA}' ready")

# Create volume
spark.sql(f"""
CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME}
""")
print(f"✓ Volume '{CATALOG}.{SCHEMA}.{VOLUME}' ready")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Vector Search 엔드포인트 생성

# COMMAND ----------

from databricks.vector_search.client import VectorSearchClient

vsc = VectorSearchClient()

# Create endpoint
try:
    endpoint = vsc.create_endpoint(
        name=VECTOR_ENDPOINT,
        endpoint_type="STANDARD"
    )
    print(f"✓ Vector Search endpoint '{VECTOR_ENDPOINT}' created")
except Exception as e:
    print(f"Endpoint may already exist: {e}")

# Check endpoint status
endpoint = vsc.get_endpoint(VECTOR_ENDPOINT)
print(f"Endpoint status: {endpoint}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. 샘플 PDF 업로드

# COMMAND ----------

# Get volume path
volume_path = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"
print(f"Volume path: {volume_path}")

# Upload sample PDFs
# TODO: Upload your PDF files to the volume
print("\n⚠️  Upload PDF files to:")
print(f"   {volume_path}/")
print("\nYou can use:")
print("   - Databricks UI (Data Explorer)")
print("   - Databricks CLI")
print("   - dbutils.fs.cp() command")

# Example: List files
try:
    files = dbutils.fs.ls(volume_path)
    print(f"\nCurrent files in volume:")
    for f in files:
        print(f"  - {f.name}")
except:
    print("Volume is empty or not accessible")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. PDF 파싱 및 청킹

# COMMAND ----------

# Install required packages (if needed)
%pip install PyPDF2 pypdf pdfplumber

# COMMAND ----------

import PyPDF2
from pyspark.sql.functions import col, udf
from pyspark.sql.types import StringType, IntegerType, ArrayType, StructType, StructField

# Parse PDFs and create Delta table
# TODO: Implement PDF parsing logic
# For now, create sample data

sample_data = [
    {
        "chunk_id": "doc1_chunk0",
        "text": "NH생명의 보험 상품은 고객의 다양한 니즈를 충족시킵니다.",
        "file_name": "insurance_products.pdf",
        "page_num": 1
    },
    {
        "chunk_id": "doc1_chunk1",
        "text": "보험 청약 시 건강 상태를 정확히 고지해야 합니다.",
        "file_name": "insurance_products.pdf",
        "page_num": 2
    }
]

# Create DataFrame
df = spark.createDataFrame(sample_data)

# Save to Delta table
table_name = f"{CATALOG}.{SCHEMA}.chunked_docs"
df.write.format("delta").mode("overwrite").saveAsTable(table_name)

print(f"✓ Created table: {table_name}")
print(f"  Rows: {df.count()}")

# Display sample
display(df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Vector Search 인덱스 생성

# COMMAND ----------

# Create Delta Sync Vector Index
try:
    index = vsc.create_delta_sync_index(
        endpoint_name=VECTOR_ENDPOINT,
        index_name=VECTOR_INDEX_NAME,
        source_table_name=f"{CATALOG}.{SCHEMA}.chunked_docs",
        pipeline_type="TRIGGERED",
        primary_key="chunk_id",
        embedding_source_column="text",
        embedding_model_endpoint_name=EMBEDDING_MODEL
    )
    print(f"✓ Vector index '{VECTOR_INDEX_NAME}' created")
except Exception as e:
    print(f"Index creation error: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. 인덱스 동기화

# COMMAND ----------

# Trigger index sync
try:
    vsc.get_index(VECTOR_ENDPOINT, VECTOR_INDEX_NAME).sync()
    print("✓ Index sync triggered")
except Exception as e:
    print(f"Sync error: {e}")

# Check index status
index = vsc.get_index(VECTOR_ENDPOINT, VECTOR_INDEX_NAME)
print(f"\nIndex status: {index.describe()}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. 인덱스 테스트

# COMMAND ----------

# Test query
test_query = "보험 청약 절차"

results = index.similarity_search(
    query_text=test_query,
    columns=["chunk_id", "text", "file_name"],
    num_results=3
)

print(f"Query: '{test_query}'\n")
print("Results:")
for i, result in enumerate(results.get("result", {}).get("data_array", []), 1):
    print(f"\n[{i}]")
    print(f"  Chunk ID: {result[0]}")
    print(f"  Text: {result[1]}")
    print(f"  Source: {result[2]}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 완료!
# MAGIC
# MAGIC RAG 파이프라인이 설정되었습니다:
# MAGIC - ✓ Unity Catalog 리소스
# MAGIC - ✓ Vector Search 엔드포인트
# MAGIC - ✓ Vector Search 인덱스
# MAGIC - ✓ 샘플 데이터
# MAGIC
# MAGIC 다음 단계:
# MAGIC 1. 실제 PDF 파일 업로드
# MAGIC 2. Agent 설정 및 테스트
# MAGIC 3. 음성 앱 통합
