# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog 설정 - NH Voice Agent PoC
# MAGIC
# MAGIC ## 📋 목적
# MAGIC 이 노트북은 NH Voice Agent PoC를 위한 Unity Catalog 리소스를 설정합니다.
# MAGIC
# MAGIC ### 생성할 리소스
# MAGIC - **Catalog**: `main` (기존 사용 또는 신규 생성)
# MAGIC - **Schema**: `nh_voice_agent` (프로젝트 전용 스키마)
# MAGIC - **Volume**: `documents` (PDF 문서 저장용)
# MAGIC
# MAGIC ### 예상 소요 시간
# MAGIC - 약 5-10분
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## ⚠️ 사전 요구사항
# MAGIC - Unity Catalog가 활성화된 Databricks Workspace
# MAGIC - `CREATE CATALOG`, `CREATE SCHEMA`, `CREATE VOLUME` 권한
# MAGIC
# MAGIC ---

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: 현재 환경 확인
# MAGIC
# MAGIC Unity Catalog가 활성화되어 있는지, 그리고 어떤 Catalog가 이미 존재하는지 확인합니다.

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 현재 사용 가능한 Catalog 목록 확인
# MAGIC SHOW CATALOGS;

# COMMAND ----------

# MAGIC %md
# MAGIC ### 📊 결과 해석
# MAGIC
# MAGIC 위 결과에서:
# MAGIC - `main` catalog이 있으면 → 기존 것 사용
# MAGIC - `main` catalog이 없으면 → 신규 생성 필요
# MAGIC
# MAGIC **일반적으로 `main` catalog은 기본으로 제공됩니다.**

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Catalog 생성 (필요시)
# MAGIC
# MAGIC `main` catalog이 없는 경우에만 실행합니다.
# MAGIC
# MAGIC ### 💡 참고
# MAGIC - `IF NOT EXISTS`를 사용하므로 이미 있어도 에러 없음
# MAGIC - Catalog은 최상위 네임스페이스입니다

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Catalog 생성 (이미 있으면 skip)
# MAGIC CREATE CATALOG IF NOT EXISTS main
# MAGIC   COMMENT 'Main catalog for production workloads';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 생성 확인
# MAGIC DESCRIBE CATALOG main;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Schema 생성
# MAGIC
# MAGIC NH Voice Agent 프로젝트 전용 Schema를 생성합니다.
# MAGIC
# MAGIC ### 📁 네이밍 규칙
# MAGIC - Schema 이름: `nh_voice_agent`
# MAGIC - 전체 경로: `main.nh_voice_agent`
# MAGIC
# MAGIC ### 💡 Schema란?
# MAGIC - Database와 동일한 개념
# MAGIC - 테이블, 뷰, Volume을 그룹화하는 논리적 컨테이너

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Schema 생성
# MAGIC CREATE SCHEMA IF NOT EXISTS main.nh_voice_agent
# MAGIC   COMMENT 'NH Voice Agent PoC - RAG 및 Agent 리소스';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Schema 정보 확인
# MAGIC DESCRIBE SCHEMA EXTENDED main.nh_voice_agent;

# COMMAND ----------

# MAGIC %sql
# MAGIC -- 현재 사용 중인 Schema 전환
# MAGIC USE SCHEMA main.nh_voice_agent;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Volume 생성
# MAGIC
# MAGIC PDF 문서를 저장할 Volume을 생성합니다.
# MAGIC
# MAGIC ### 📦 Volume이란?
# MAGIC - Unity Catalog의 파일 저장 공간
# MAGIC - Delta Table과 달리 **파일 그대로 저장** (PDF, CSV, JSON 등)
# MAGIC - 경로: `/Volumes/{catalog}/{schema}/{volume}/`
# MAGIC
# MAGIC ### 🎯 사용 목적
# MAGIC - PDF 원본 문서 저장
# MAGIC - Knowledge Assistant가 이 Volume을 스캔하여 자동 인덱싱

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Volume 생성
# MAGIC CREATE VOLUME IF NOT EXISTS main.nh_voice_agent.documents
# MAGIC   COMMENT 'PDF documents for Knowledge Assistant RAG';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Volume 정보 확인
# MAGIC DESCRIBE VOLUME main.nh_voice_agent.documents;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Volume 경로 확인 및 테스트
# MAGIC
# MAGIC Volume이 정상적으로 생성되었는지, 그리고 파일 업로드가 가능한지 확인합니다.

# COMMAND ----------

# Volume 경로 확인
volume_path = "/Volumes/main/nh_voice_agent/documents"

print(f"✅ Volume 경로: {volume_path}")
print()

# Volume 디렉토리 확인 (현재는 비어있음)
try:
    files = dbutils.fs.ls(volume_path)
    print(f"📁 현재 파일 수: {len(files)}")

    if files:
        print("\n현재 파일 목록:")
        for file in files:
            print(f"  - {file.name} ({file.size} bytes)")
    else:
        print("📭 Volume이 비어있습니다 (정상)")
        print("   다음 단계에서 PDF를 업로드하세요.")
except Exception as e:
    print(f"❌ 에러: {e}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: 테스트 파일 업로드 (선택사항)
# MAGIC
# MAGIC Volume에 파일을 업로드할 수 있는지 테스트합니다.
# MAGIC
# MAGIC ### 💡 참고
# MAGIC - 실제 PDF는 다음 노트북에서 업로드합니다
# MAGIC - 여기서는 간단한 텍스트 파일로 테스트만 수행

# COMMAND ----------

# 테스트 텍스트 파일 생성
test_content = """
NH Voice Agent PoC
테스트 문서

이것은 Unity Catalog Volume 테스트용 파일입니다.
한글이 정상적으로 저장되고 읽히는지 확인합니다.

재무제표 분석
회계 규정 준수
내부 감사 절차
"""

# 임시 파일로 저장
test_file_path = "/tmp/test_document.txt"
with open(test_file_path, "w", encoding="utf-8") as f:
    f.write(test_content)

print("✅ 테스트 파일 생성 완료")

# COMMAND ----------

# Volume에 업로드
dbutils.fs.cp(
    f"file:{test_file_path}",
    f"{volume_path}/test_document.txt"
)

print("✅ Volume에 업로드 완료")
print(f"   경로: {volume_path}/test_document.txt")

# COMMAND ----------

# 업로드된 파일 확인
files = dbutils.fs.ls(volume_path)

print("📁 Volume 파일 목록:")
for file in files:
    print(f"  - {file.name}")
    print(f"    크기: {file.size} bytes")
    print(f"    경로: {file.path}")
    print()

# COMMAND ----------

# 파일 읽기 테스트 (한글 인코딩 확인)
content = dbutils.fs.head(f"{volume_path}/test_document.txt")
print("📄 파일 내용:")
print(content)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: 생성된 리소스 요약
# MAGIC
# MAGIC 모든 Unity Catalog 리소스가 정상적으로 생성되었습니다!

# COMMAND ----------

print("=" * 60)
print("✅ Unity Catalog 설정 완료!")
print("=" * 60)
print()

print("📦 생성된 리소스:")
print(f"  • Catalog: main")
print(f"  • Schema: main.nh_voice_agent")
print(f"  • Volume: main.nh_voice_agent.documents")
print()

print("📁 Volume 경로:")
print(f"  /Volumes/main/nh_voice_agent/documents")
print()

print("🎯 다음 단계:")
print("  1. 한글 PDF 문서를 준비합니다")
print("  2. Volume에 PDF를 업로드합니다")
print("  3. Knowledge Assistant를 생성합니다")
print()

print("📓 다음 노트북:")
print("  → 02a_Knowledge_Assistant_Setup.py")
print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ 체크리스트
# MAGIC
# MAGIC 완료된 작업:
# MAGIC - [x] Catalog 확인/생성 (`main`)
# MAGIC - [x] Schema 생성 (`main.nh_voice_agent`)
# MAGIC - [x] Volume 생성 (`main.nh_voice_agent.documents`)
# MAGIC - [x] Volume 경로 확인 (`/Volumes/main/nh_voice_agent/documents`)
# MAGIC - [x] 파일 업로드 테스트 (한글 인코딩 확인)
# MAGIC
# MAGIC 다음 단계:
# MAGIC - [ ] 한글 PDF 준비
# MAGIC - [ ] PDF를 Volume에 업로드
# MAGIC - [ ] Knowledge Assistant 생성
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Notebook 완료**
# MAGIC
# MAGIC 다음 노트북 `02a_Knowledge_Assistant_Setup.py`를 실행하세요!

# COMMAND ----------
