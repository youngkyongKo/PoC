#!/usr/bin/env python3
"""
데모 리소스 정리 스크립트

생성된 클러스터, Job, 노트북을 삭제합니다.

사용법:
  python cleanup.py                  # 모든 리소스 삭제
  python cleanup.py --keep-cluster   # 클러스터는 유지
  python cleanup.py --keep-jobs      # Job은 유지
"""

import os
import sys
import json
import argparse
from pathlib import Path
from databricks.sdk import WorkspaceClient

def load_config():
    """환경변수 및 demo_config.json 로드"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass

    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")

    if not host or not token:
        print("❌ Error: DATABRICKS_HOST 및 DATABRICKS_TOKEN을 설정해주세요.")
        sys.exit(1)

    # demo_config.json 읽기
    config_path = Path(__file__).parent.parent / "demo_config.json"
    if not config_path.exists():
        print(f"⚠️  Warning: {config_path} 파일을 찾을 수 없습니다.")
        print("   setup_demo.py를 먼저 실행하거나, 수동으로 리소스 ID를 지정하세요.")
        return host, token, None

    with open(config_path, "r") as f:
        demo_config = json.load(f)

    return host, token, demo_config

def delete_cluster(w: WorkspaceClient, cluster_id: str):
    """클러스터 영구 삭제"""
    print(f"  - 클러스터 삭제 중 (ID: {cluster_id})...")
    try:
        # 먼저 종료
        w.clusters.delete(cluster_id)
        import time
        time.sleep(5)

        # 영구 삭제
        w.clusters.permanent_delete(cluster_id)
        print(f"    ✅ 클러스터 삭제 완료")
    except Exception as e:
        print(f"    ⚠️  클러스터 삭제 실패: {e}")

def delete_job(w: WorkspaceClient, job_id: str, job_name: str):
    """Job 삭제"""
    print(f"  - Job 삭제 중: {job_name} (ID: {job_id})...")
    try:
        w.jobs.delete(job_id)
        print(f"    ✅ Job 삭제 완료")
    except Exception as e:
        print(f"    ⚠️  Job 삭제 실패: {e}")

def delete_notebook(w: WorkspaceClient, notebook_path: str):
    """노트북 삭제"""
    print(f"  - 노트북 삭제 중: {notebook_path}...")
    try:
        w.workspace.delete(notebook_path, recursive=True)
        print(f"    ✅ 노트북 삭제 완료")
    except Exception as e:
        print(f"    ⚠️  노트북 삭제 실패: {e}")

def main():
    parser = argparse.ArgumentParser(description="데모 리소스 정리")
    parser.add_argument("--keep-cluster", action="store_true", help="클러스터 유지")
    parser.add_argument("--keep-jobs", action="store_true", help="Job 유지")
    parser.add_argument("--keep-notebooks", action="store_true", help="노트북 유지")
    args = parser.parse_args()

    print("=" * 70)
    print("  Databricks Job 비용 최적화 데모 - 리소스 정리")
    print("=" * 70)

    # 설정 로드
    host, token, demo_config = load_config()
    w = WorkspaceClient(host=host, token=token)
    print(f"✅ 연결: {host}\n")

    if not demo_config:
        print("❌ demo_config.json이 없어 자동 삭제를 진행할 수 없습니다.")
        print("   수동으로 리소스를 삭제하려면 Databricks UI를 사용하세요.")
        sys.exit(1)

    # 리소스 삭제
    print("🗑️  리소스 삭제 시작...\n")

    # 1. Job 삭제
    if not args.keep_jobs:
        print("1️⃣ Job 삭제:")
        delete_job(w, demo_config["job_main_id"], "demo_job_main")
        delete_job(w, demo_config["job_sub1_id"], "demo_job_sub1")
        delete_job(w, demo_config["job_sub2_id"], "demo_job_sub2")
        print()
    else:
        print("1️⃣ Job 삭제 건너뜀 (--keep-jobs)\n")

    # 2. 클러스터 삭제
    if not args.keep_cluster:
        print("2️⃣ 클러스터 삭제:")
        delete_cluster(w, demo_config["cluster_id"])
        print()
    else:
        print("2️⃣ 클러스터 삭제 건너뜀 (--keep-cluster)\n")

    # 3. 노트북 삭제
    if not args.keep_notebooks:
        print("3️⃣ 노트북 삭제:")
        delete_notebook(w, "/Shared/demo_job_optimization")
        print()
    else:
        print("3️⃣ 노트북 삭제 건너뜀 (--keep-notebooks)\n")

    # 4. 설정 파일 삭제
    config_path = Path(__file__).parent.parent / "demo_config.json"
    if config_path.exists():
        config_path.unlink()
        print("✅ demo_config.json 삭제 완료")

    print("\n" + "=" * 70)
    print("  ✅ 리소스 정리 완료!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
