#!/usr/bin/env python3
"""
Databricks Job 수동 실행 스크립트 (❌ 비교용)

기능:
- 기본적인 클러스터 시작 및 Job 실행
- 에러 처리 부족
- 상세한 모니터링 없음

이 스크립트는 자동화 스크립트와 비교하기 위한 "개선 전" 방식입니다.
프로덕션에서는 run_job_automated.py를 사용하세요.

사용법:
  python run_job_manual.py --cluster-id "1234-567890-abcd123" --job-id "12347"
"""

import os
import sys
import time
import argparse
from databricks.sdk import WorkspaceClient

def main():
    parser = argparse.ArgumentParser(description="Databricks Job 수동 실행")
    parser.add_argument("--cluster-id", required=True, help="클러스터 ID")
    parser.add_argument("--job-id", required=True, help="Job ID")
    args = parser.parse_args()

    # Databricks 연결
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except:
        pass

    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")

    if not host or not token:
        print("Error: DATABRICKS_HOST and DATABRICKS_TOKEN must be set")
        sys.exit(1)

    w = WorkspaceClient(host=host, token=token)
    print(f"Connected to: {host}")

    # 클러스터 상태 확인
    print(f"Checking cluster {args.cluster_id}...")
    cluster_info = w.clusters.get(args.cluster_id)
    state = cluster_info.state.value

    print(f"Cluster state: {state}")

    # 클러스터 시작 (TERMINATED인 경우)
    if state == "TERMINATED":
        print("Starting cluster...")
        w.clusters.start(args.cluster_id)

        # 간단한 대기 (고정 시간)
        print("Waiting for cluster to start (fixed 180 seconds)...")
        time.sleep(180)  # 3분 대기

        # 상태 재확인 없이 진행 (문제 발생 가능)
        print("Assuming cluster is ready...")

    # Job 실행
    print(f"Running job {args.job_id}...")
    run = w.jobs.run_now(args.job_id)
    print(f"Job started: run_id={run.run_id}")

    # 간단한 완료 대기 (상세한 모니터링 없음)
    print("Waiting for job to complete...")
    while True:
        run_info = w.jobs.get_run(run.run_id)
        state = run_info.state.life_cycle_state.value

        if state in ["TERMINATED", "SKIPPED", "INTERNAL_ERROR"]:
            result = run_info.state.result_state.value if run_info.state.result_state else "UNKNOWN"
            print(f"Job finished: {result}")

            if result == "SUCCESS":
                print("✅ Job completed successfully")
            else:
                print(f"❌ Job failed: {result}")

            break

        time.sleep(30)  # 30초마다 체크 (진행상황 표시 없음)

    # 클러스터 종료
    print(f"Terminating cluster {args.cluster_id}...")
    w.clusters.delete(args.cluster_id)

    print("Done")

if __name__ == "__main__":
    main()
