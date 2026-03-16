# Databricks notebook source
# MAGIC %md
# MAGIC # Sample Task Notebook
# MAGIC
# MAGIC 이 노트북은 데모용 샘플 작업을 수행합니다.
# MAGIC - 실행 시간: 약 10초
# MAGIC - 작업 내용: Sleep 및 간단한 로그 출력

# COMMAND ----------

import time
from datetime import datetime

# COMMAND ----------

# MAGIC %md
# MAGIC ## Task Execution

# COMMAND ----------

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Task started")
print(f"Running on cluster: {spark.conf.get('spark.databricks.clusterUsageTags.clusterId')}")

# COMMAND ----------

# 작업 시뮬레이션: 10초 대기
print("Processing data...")
time.sleep(10)

# COMMAND ----------

# 간단한 Spark 작업 (옵션)
df = spark.range(0, 100)
count = df.count()
print(f"Processed {count} records")

# COMMAND ----------

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Task completed successfully ✅")
