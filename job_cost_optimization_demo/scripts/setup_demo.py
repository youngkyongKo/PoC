#!/usr/bin/env python3
"""
Databricks Job 비용 최적화 데모 - 환경 구축 스크립트

이 스크립트는 다음을 생성합니다:
1. All-purpose 클러스터 (batch-dedicated-cluster)
2. 샘플 노트북 업로드 (/Shared/demo_job_optimization/)
3. Job 정의 3개 (job_sub1, job_sub2, job_main)
"""

import os
import sys
import json
import time
from pathlib import Path
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import ClusterSpec, AutoScale, AwsAttributes, AzureAttributes
from databricks.sdk.service.jobs import Task, NotebookTask, RunJobTask, SqlTask, SqlTaskQuery

# 환경변수에서 인증 정보 로드
def load_config():
    """환경변수 또는 .env 파일에서 설정 로드"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")

    if not host or not token:
        print("❌ Error: DATABRICKS_HOST 및 DATABRICKS_TOKEN 환경변수를 설정해주세요.")
        print("\n설정 방법:")
        print("  export DATABRICKS_HOST='https://your-workspace.cloud.databricks.com'")
        print("  export DATABRICKS_TOKEN='your-token'")
        sys.exit(1)

    return host, token

def create_cluster(w: WorkspaceClient, cluster_name: str = "batch-dedicated-cluster"):
    """All-purpose 클러스터 생성"""
    print(f"\n📦 클러스터 생성 중: {cluster_name}")

    # 기존 클러스터 확인
    existing_clusters = [c for c in w.clusters.list() if c.cluster_name == cluster_name]
    if existing_clusters:
        cluster_id = existing_clusters[0].cluster_id
        print(f"✅ 기존 클러스터 발견: {cluster_name} (ID: {cluster_id})")
        return cluster_id

    # 클라우드 감지 (AWS/Azure/GCP)
    try:
        # Workspace 정보에서 클라우드 타입 감지
        workspace_config = w.workspace.get_status("/")
        cloud_provider = "aws"  # 기본값

        # 간단한 클러스터 설정
        cluster_config = {
            "cluster_name": cluster_name,
            "spark_version": "14.3.x-scala2.12",  # LTS 버전
            "node_type_id": "i3.xlarge" if cloud_provider == "aws" else "Standard_DS3_v2",
            "autoscale": {
                "min_workers": 1,
                "max_workers": 2
            },
            "auto_termination_minutes": 60,  # 60분 idle 후 자동 종료
        }

        # AWS 전용 설정
        if cloud_provider == "aws":
            cluster_config["aws_attributes"] = {
                "availability": "ON_DEMAND",  # SPOT으로 변경 가능
                "zone_id": "auto"
            }

        response = w.clusters.create(**cluster_config)
        cluster_id = response.cluster_id

        print(f"✅ 클러스터 생성 완료: {cluster_name}")
        print(f"   - Cluster ID: {cluster_id}")
        print(f"   - Auto-termination: 60분")

        return cluster_id

    except Exception as e:
        print(f"❌ 클러스터 생성 실패: {e}")
        sys.exit(1)

def upload_notebook(w: WorkspaceClient, notebook_path: str = "/Shared/demo_job_optimization"):
    """샘플 노트북 업로드"""
    print(f"\n📓 노트북 업로드 중: {notebook_path}")

    # 디렉토리 생성
    try:
        w.workspace.mkdirs(notebook_path)
    except Exception:
        pass  # 이미 존재하는 경우 무시

    # 노트북 소스 읽기
    notebook_source_path = Path(__file__).parent.parent / "notebooks" / "sample_sleep_task.py"

    if not notebook_source_path.exists():
        print(f"❌ 노트북 파일을 찾을 수 없음: {notebook_source_path}")
        sys.exit(1)

    with open(notebook_source_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 노트북 업로드
    notebook_full_path = f"{notebook_path}/sample_sleep_task"
    try:
        import base64
        w.workspace.import_(
            path=notebook_full_path,
            format="SOURCE",
            language="PYTHON",
            content=base64.b64encode(content.encode()).decode(),
            overwrite=True
        )
        print(f"✅ 노트북 업로드 완료: {notebook_full_path}")
        return notebook_full_path
    except Exception as e:
        print(f"❌ 노트북 업로드 실패: {e}")
        sys.exit(1)

def get_warehouse_id(w: WorkspaceClient):
    """사용 가능한 SQL Warehouse ID 가져오기"""
    print("\n🏢 SQL Warehouse 확인 중...")

    try:
        warehouses = list(w.warehouses.list())
        if not warehouses:
            print("⚠️  SQL Warehouse가 없습니다. 첫 번째 warehouse를 생성하거나, task2를 수동으로 설정하세요.")
            return None

        # 첫 번째 활성 warehouse 사용
        warehouse = warehouses[0]
        print(f"✅ SQL Warehouse 발견: {warehouse.name} (ID: {warehouse.id})")
        return warehouse.id
    except Exception as e:
        print(f"⚠️  SQL Warehouse 조회 실패: {e}")
        return None

def create_jobs(w: WorkspaceClient, cluster_id: str, notebook_path: str, warehouse_id: str):
    """Job 3개 생성 (job_sub1, job_sub2, job_main)"""
    print("\n⚙️  Job 생성 중...")

    jobs_dir = Path(__file__).parent.parent / "jobs"

    # 1. job_sub1 생성
    print("  - job_sub1 생성 중...")
    with open(jobs_dir / "job_sub1.json", "r") as f:
        job_sub1_config = json.load(f)

    # Cluster ID 치환
    job_sub1_str = json.dumps(job_sub1_config).replace("{{CLUSTER_ID}}", cluster_id)
    job_sub1_config = json.loads(job_sub1_str)

    # Notebook path 치환
    for task in job_sub1_config["tasks"]:
        if "notebook_task" in task:
            task["notebook_task"]["notebook_path"] = notebook_path

    try:
        job_sub1 = w.jobs.create(**job_sub1_config)
        job_sub1_id = job_sub1.job_id
        print(f"    ✅ job_sub1 생성 완료 (ID: {job_sub1_id})")
    except Exception as e:
        print(f"    ❌ job_sub1 생성 실패: {e}")
        sys.exit(1)

    # 2. job_sub2 생성
    print("  - job_sub2 생성 중...")
    with open(jobs_dir / "job_sub2.json", "r") as f:
        job_sub2_config = json.load(f)

    job_sub2_str = json.dumps(job_sub2_config).replace("{{CLUSTER_ID}}", cluster_id)
    job_sub2_config = json.loads(job_sub2_str)

    for task in job_sub2_config["tasks"]:
        if "notebook_task" in task:
            task["notebook_task"]["notebook_path"] = notebook_path

    try:
        job_sub2 = w.jobs.create(**job_sub2_config)
        job_sub2_id = job_sub2.job_id
        print(f"    ✅ job_sub2 생성 완료 (ID: {job_sub2_id})")
    except Exception as e:
        print(f"    ❌ job_sub2 생성 실패: {e}")
        sys.exit(1)

    # 3. job_main 생성
    print("  - job_main 생성 중...")
    with open(jobs_dir / "job_main.json", "r") as f:
        job_main_config = json.load(f)

    # Placeholder 치환
    job_main_str = json.dumps(job_main_config)
    job_main_str = job_main_str.replace("{{JOB_SUB1_ID}}", str(job_sub1_id))
    job_main_str = job_main_str.replace("{{JOB_SUB2_ID}}", str(job_sub2_id))

    if warehouse_id:
        job_main_str = job_main_str.replace("{{WAREHOUSE_ID}}", warehouse_id)
    else:
        # SQL Warehouse가 없으면 task2 제거
        print("    ⚠️  SQL Warehouse가 없어 task2를 제거합니다.")
        job_main_config = json.loads(job_main_str)
        job_main_config["tasks"] = [t for t in job_main_config["tasks"] if t["task_key"] != "task2_sql_query"]
        # task3의 depends_on을 task1로 변경
        for task in job_main_config["tasks"]:
            if task["task_key"] == "task3_run_job_sub2":
                task["depends_on"] = [{"task_key": "task1_run_job_sub1"}]
        job_main_str = json.dumps(job_main_config)

    job_main_config = json.loads(job_main_str)

    try:
        job_main = w.jobs.create(**job_main_config)
        job_main_id = job_main.job_id
        print(f"    ✅ job_main 생성 완료 (ID: {job_main_id})")
    except Exception as e:
        print(f"    ❌ job_main 생성 실패: {e}")
        sys.exit(1)

    return job_sub1_id, job_sub2_id, job_main_id

def save_config(cluster_id: str, job_ids: dict):
    """생성된 리소스 정보를 config 파일로 저장"""
    config_path = Path(__file__).parent.parent / "demo_config.json"

    config = {
        "cluster_id": cluster_id,
        "job_sub1_id": job_ids["sub1"],
        "job_sub2_id": job_ids["sub2"],
        "job_main_id": job_ids["main"],
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n📝 설정 파일 저장: {config_path}")

def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("  Databricks Job 비용 최적화 데모 - 환경 구축")
    print("=" * 70)

    # 1. 인증
    host, token = load_config()
    w = WorkspaceClient(host=host, token=token)
    print(f"✅ Databricks 워크스페이스 연결: {host}")

    # 2. 클러스터 생성
    cluster_id = create_cluster(w)

    # 3. 노트북 업로드
    notebook_path = upload_notebook(w)

    # 4. SQL Warehouse 확인
    warehouse_id = get_warehouse_id(w)

    # 5. Job 생성
    job_sub1_id, job_sub2_id, job_main_id = create_jobs(w, cluster_id, notebook_path, warehouse_id)

    # 6. 설정 저장
    save_config(cluster_id, {
        "sub1": job_sub1_id,
        "sub2": job_sub2_id,
        "main": job_main_id
    })

    # 완료 메시지
    print("\n" + "=" * 70)
    print("  ✅ 데모 환경 구축 완료!")
    print("=" * 70)
    print("\n📋 생성된 리소스:")
    print(f"  - Cluster: batch-dedicated-cluster (ID: {cluster_id})")
    print(f"  - Notebook: {notebook_path}")
    print(f"  - Job: demo_job_sub1 (ID: {job_sub1_id})")
    print(f"  - Job: demo_job_sub2 (ID: {job_sub2_id})")
    print(f"  - Job: demo_job_main (ID: {job_main_id})")

    print("\n🚀 다음 단계:")
    print("  1. 수동 방식 실행:")
    print(f"     python scripts/run_job_manual.py --cluster-id {cluster_id}")
    print("\n  2. 자동화 방식 실행 (권장):")
    print("     python scripts/run_job_automated.py --cluster-name batch-dedicated-cluster --job-name demo_job_main")
    print()

if __name__ == "__main__":
    main()
