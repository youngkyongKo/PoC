#!/usr/bin/env python3
"""
Databricks Job 자동 실행 스크립트 (✅ 권장)

기능:
1. 클러스터 상태 자동 감지 및 시작
2. Job 실행 및 모니터링
3. Job 완료 후 클러스터 자동 종료
4. 에러 처리 및 로깅
5. 비용 추적

사용법:
  python run_job_automated.py --cluster-name "batch-dedicated-cluster" --job-name "demo_job_main"
  python run_job_automated.py --cluster-id "1234-567890-abcd123" --job-id "12347"
"""

import os
import sys
import time
import argparse
from datetime import datetime, timedelta
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.compute import ClusterDetails, State
from databricks.sdk.service.jobs import Run, RunLifeCycleState, RunResultState

# 설정
DBU_PRICE = 0.75  # All-purpose 클러스터 DBU 가격 (USD per DBU)
CLUSTER_DBU_PER_HOUR = 0.75  # i3.xlarge 기준 (인스턴스 타입에 따라 다름)

class Colors:
    """터미널 색상 코드"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def log(message: str, level: str = "INFO"):
    """로그 출력"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = {
        "INFO": Colors.BLUE,
        "SUCCESS": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED
    }.get(level, "")

    print(f"{color}[{timestamp}] {level}: {message}{Colors.RESET}")

def load_config():
    """환경변수에서 설정 로드"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")

    if not host or not token:
        log("DATABRICKS_HOST 및 DATABRICKS_TOKEN 환경변수를 설정해주세요.", "ERROR")
        sys.exit(1)

    return host, token

def get_cluster_by_name(w: WorkspaceClient, cluster_name: str):
    """클러스터 이름으로 클러스터 찾기"""
    log(f"클러스터 검색 중: '{cluster_name}'")

    clusters = [c for c in w.clusters.list() if c.cluster_name == cluster_name]

    if not clusters:
        log(f"클러스터를 찾을 수 없음: {cluster_name}", "ERROR")
        sys.exit(1)

    if len(clusters) > 1:
        log(f"동일한 이름의 클러스터가 {len(clusters)}개 발견됨. 첫 번째 클러스터 사용", "WARNING")

    cluster = clusters[0]
    log(f"클러스터 발견: {cluster.cluster_name} (ID: {cluster.cluster_id})", "SUCCESS")
    return cluster.cluster_id

def get_cluster_state(w: WorkspaceClient, cluster_id: str) -> str:
    """클러스터 현재 상태 확인"""
    cluster_info = w.clusters.get(cluster_id)
    return cluster_info.state.value

def start_cluster_if_needed(w: WorkspaceClient, cluster_id: str):
    """클러스터가 Running 상태가 아니면 시작"""
    state = get_cluster_state(w, cluster_id)
    log(f"현재 클러스터 상태: {state}")

    if state == "RUNNING":
        log("클러스터가 이미 실행 중입니다 ✅", "SUCCESS")
        return 0  # 시작 시간 0초

    if state in ["TERMINATED", "TERMINATING"]:
        log("클러스터 시작 중...")
        start_time = time.time()

        try:
            w.clusters.start(cluster_id)
        except Exception as e:
            log(f"클러스터 시작 실패: {e}", "ERROR")
            sys.exit(1)

        # 클러스터가 RUNNING 상태가 될 때까지 대기
        log("클러스터 준비 대기 중...", "INFO")
        max_wait_time = 600  # 10분
        elapsed = 0

        while elapsed < max_wait_time:
            state = get_cluster_state(w, cluster_id)

            if state == "RUNNING":
                startup_time = time.time() - start_time
                log(f"클러스터 시작 완료 (소요 시간: {format_duration(startup_time)}) ✅", "SUCCESS")
                return startup_time

            if state in ["ERROR", "UNKNOWN"]:
                log(f"클러스터 시작 실패: 상태={state}", "ERROR")
                sys.exit(1)

            time.sleep(10)
            elapsed = time.time() - start_time

            # 진행 상황 표시
            if int(elapsed) % 30 == 0:
                log(f"대기 중... ({format_duration(elapsed)} 경과, 상태: {state})")

        log(f"클러스터 시작 타임아웃 ({max_wait_time}초 초과)", "ERROR")
        sys.exit(1)

    elif state == "PENDING":
        log("클러스터가 이미 시작 중입니다. 대기 중...")
        start_time = time.time()

        while time.time() - start_time < 600:
            state = get_cluster_state(w, cluster_id)
            if state == "RUNNING":
                startup_time = time.time() - start_time
                log(f"클러스터 준비 완료 (대기 시간: {format_duration(startup_time)}) ✅", "SUCCESS")
                return startup_time

            time.sleep(10)

        log("클러스터 시작 타임아웃", "ERROR")
        sys.exit(1)

    else:
        log(f"예상치 못한 클러스터 상태: {state}", "WARNING")
        return 0

def get_job_by_name(w: WorkspaceClient, job_name: str):
    """Job 이름으로 Job 찾기"""
    log(f"Job 검색 중: '{job_name}'")

    jobs = [j for j in w.jobs.list() if j.settings.name == job_name]

    if not jobs:
        log(f"Job을 찾을 수 없음: {job_name}", "ERROR")
        sys.exit(1)

    if len(jobs) > 1:
        log(f"동일한 이름의 Job이 {len(jobs)}개 발견됨. 첫 번째 Job 사용", "WARNING")

    job = jobs[0]
    log(f"Job 발견: {job.settings.name} (ID: {job.job_id})", "SUCCESS")
    return job.job_id

def run_job(w: WorkspaceClient, job_id: str) -> str:
    """Job 실행 및 Run ID 반환"""
    log(f"Job 실행 중 (Job ID: {job_id})...")

    try:
        run = w.jobs.run_now(job_id)
        run_id = run.run_id
        log(f"Job 실행 시작 (Run ID: {run_id}) ✅", "SUCCESS")
        return run_id
    except Exception as e:
        log(f"Job 실행 실패: {e}", "ERROR")
        sys.exit(1)

def monitor_job_run(w: WorkspaceClient, run_id: str):
    """Job 실행 모니터링"""
    log("Job 실행 모니터링 시작...")
    start_time = time.time()
    last_state = None

    while True:
        try:
            run_info = w.jobs.get_run(run_id)
            current_state = run_info.state.life_cycle_state.value

            # 상태 변경 시에만 로그 출력
            if current_state != last_state:
                log(f"Job 상태: {current_state}")
                last_state = current_state

                # Task별 상태 출력
                if run_info.tasks:
                    for task in run_info.tasks:
                        task_name = task.task_key
                        task_state = task.state.life_cycle_state.value if task.state else "UNKNOWN"
                        log(f"  └─ Task '{task_name}': {task_state}")

            # 종료 상태 확인
            if current_state in ["TERMINATED", "SKIPPED", "INTERNAL_ERROR"]:
                runtime = time.time() - start_time
                result_state = run_info.state.result_state.value if run_info.state.result_state else "UNKNOWN"

                if result_state == "SUCCESS":
                    log(f"Job 완료 성공 ✅ (실행 시간: {format_duration(runtime)})", "SUCCESS")
                    return True, runtime
                else:
                    log(f"Job 실행 실패: {result_state} (실행 시간: {format_duration(runtime)})", "ERROR")

                    # 에러 메시지 출력
                    if run_info.state.state_message:
                        log(f"에러 메시지: {run_info.state.state_message}", "ERROR")

                    return False, runtime

            time.sleep(15)  # 15초마다 체크

        except Exception as e:
            log(f"Job 모니터링 중 에러: {e}", "ERROR")
            time.sleep(15)

def terminate_cluster(w: WorkspaceClient, cluster_id: str, grace_period: int = 0):
    """클러스터 종료"""
    if grace_period > 0:
        log(f"클러스터 종료 대기 중 ({grace_period}초)...")
        time.sleep(grace_period)

    log("클러스터 종료 중...")
    start_time = time.time()

    try:
        w.clusters.delete(cluster_id)

        # 종료 확인
        max_wait = 120  # 2분
        while time.time() - start_time < max_wait:
            state = get_cluster_state(w, cluster_id)
            if state == "TERMINATED":
                shutdown_time = time.time() - start_time
                log(f"클러스터 종료 완료 (소요 시간: {format_duration(shutdown_time)}) ✅", "SUCCESS")
                return shutdown_time

            time.sleep(10)

        log("클러스터 종료 타임아웃 (백그라운드에서 종료 진행 중)", "WARNING")
        return time.time() - start_time

    except Exception as e:
        log(f"클러스터 종료 실패: {e}", "ERROR")
        return 0

def format_duration(seconds: float) -> str:
    """초를 읽기 쉬운 형식으로 변환"""
    if seconds < 60:
        return f"{int(seconds)}초"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}분 {secs}초"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}시간 {minutes}분"

def calculate_cost(total_hours: float) -> dict:
    """비용 계산"""
    dbu_consumed = total_hours * CLUSTER_DBU_PER_HOUR
    compute_cost = dbu_consumed * DBU_PRICE

    return {
        "dbu_consumed": round(dbu_consumed, 4),
        "compute_cost": round(compute_cost, 2),
        "total_hours": round(total_hours, 4)
    }

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="Databricks Job 자동 실행 스크립트")
    parser.add_argument("--cluster-name", help="클러스터 이름")
    parser.add_argument("--cluster-id", help="클러스터 ID")
    parser.add_argument("--job-name", help="Job 이름")
    parser.add_argument("--job-id", help="Job ID")
    parser.add_argument("--grace-period", type=int, default=0, help="종료 전 대기 시간(초)")
    parser.add_argument("--no-terminate", action="store_true", help="Job 완료 후 클러스터 종료하지 않음")

    args = parser.parse_args()

    # 파라미터 검증
    if not (args.cluster_name or args.cluster_id):
        print("Error: --cluster-name 또는 --cluster-id 중 하나를 지정해야 합니다.")
        sys.exit(1)

    if not (args.job_name or args.job_id):
        print("Error: --job-name 또는 --job-id 중 하나를 지정해야 합니다.")
        sys.exit(1)

    # 시작
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}  Databricks Job 자동 실행 스크립트{Colors.RESET}")
    print("=" * 80 + "\n")

    overall_start = time.time()

    # 1. Databricks 연결
    host, token = load_config()
    w = WorkspaceClient(host=host, token=token)
    log(f"Databricks 워크스페이스 연결: {host}", "SUCCESS")

    # 2. 클러스터 ID 확인
    cluster_id = args.cluster_id or get_cluster_by_name(w, args.cluster_name)

    # 3. Job ID 확인
    job_id = args.job_id or get_job_by_name(w, args.job_name)

    # 4. 클러스터 시작 (필요 시)
    startup_time = start_cluster_if_needed(w, cluster_id)

    # 5. Job 실행
    run_id = run_job(w, job_id)

    # 6. Job 모니터링
    job_success, job_runtime = monitor_job_run(w, run_id)

    # 7. 클러스터 종료 (옵션)
    shutdown_time = 0
    if not args.no_terminate:
        shutdown_time = terminate_cluster(w, cluster_id, args.grace_period)
    else:
        log("클러스터 종료 건너뜀 (--no-terminate 옵션)", "WARNING")

    # 8. 결과 요약
    overall_time = time.time() - overall_start
    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}  실행 결과 요약{Colors.RESET}")
    print("=" * 80)

    print(f"\n⏱️  실행 시간:")
    print(f"  - 클러스터 시작: {format_duration(startup_time)}")
    print(f"  - Job 실행: {format_duration(job_runtime)}")
    print(f"  - 클러스터 종료: {format_duration(shutdown_time)}")
    print(f"  - 전체 시간: {format_duration(overall_time)}")

    # 비용 계산
    active_time = startup_time + job_runtime
    if not args.no_terminate:
        active_time += shutdown_time

    cost_info = calculate_cost(active_time / 3600)

    print(f"\n💰 예상 비용:")
    print(f"  - 활성 시간: {cost_info['total_hours']} 시간")
    print(f"  - DBU 소비: {cost_info['dbu_consumed']} DBU")
    print(f"  - 컴퓨팅 비용: ${cost_info['compute_cost']}")
    print(f"    (All-purpose: {CLUSTER_DBU_PER_HOUR} DBU/시간 × ${DBU_PRICE}/DBU)")

    # 상시 실행 대비 절감액
    daily_hours = 24
    monthly_hours = daily_hours * 30
    monthly_cost_always_on = calculate_cost(monthly_hours)
    monthly_cost_optimized = calculate_cost(cost_info['total_hours'] * 30)  # 1일 1회 실행 가정

    print(f"\n📊 월간 비용 비교 (1일 1회 실행 가정):")
    print(f"  - 상시 실행: ${monthly_cost_always_on['compute_cost']}/월")
    print(f"  - 최적화 실행: ${monthly_cost_optimized['compute_cost']}/월")
    savings = monthly_cost_always_on['compute_cost'] - monthly_cost_optimized['compute_cost']
    savings_pct = (savings / monthly_cost_always_on['compute_cost']) * 100
    print(f"  - 절감액: ${savings:.2f}/월 ({savings_pct:.1f}% 절감) 💰")

    print("\n" + "=" * 80)

    if job_success:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ Job 실행 성공!{Colors.RESET}\n")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ Job 실행 실패{Colors.RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
