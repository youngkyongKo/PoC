# Databricks Job 실행 비용 최적화 데모
## All-purpose 클러스터 라이프사이클 자동화

## 📋 개요

기존 RunJob 구조를 유지하면서 **All-purpose 클러스터를 필요한 시간만 구동**하여 비용을 절감하는 방법을 안내합니다.

### 🎯 목표
- ✅ 기존 Job 설정 수정 최소화 (RunJob 구조 그대로 유지)
- ✅ 클러스터 시작 시간 오버헤드 제거 (Job 클러스터 대비)
- ✅ 작업 필요 기간만 클러스터 구동으로 비용 절감
- ✅ 안정적이고 유지보수 쉬운 자동화 구현

### 💰 예상 비용 절감 효과

| 구분 | Before (상시 Running) | After (자동 관리) | 절감률 |
|------|----------------------|------------------|--------|
| 1일 사용 시간 | 24시간 | 1시간 | **96%** |
| 월간 DBU (0.75/시간) | 540 DBU | 22.5 DBU | **96%** |
| 월간 비용 예상* | ~$405 | ~$17 | **96%** |

*DBU당 $0.75 가정

---

## 📂 데모 구조

```
job_cost_optimization_demo/
├── README.md                          # 이 파일
├── notebooks/
│   └── sample_sleep_task.py           # 샘플 노트북 (sleep 10)
├── jobs/
│   ├── job_sub1.json                  # 서브 Job 1 정의
│   ├── job_sub2.json                  # 서브 Job 2 정의
│   └── job_main.json                  # 메인 Job 정의
├── scripts/
│   ├── setup_demo.py                  # 데모 환경 구축
│   ├── run_job_automated.py           # ✅ 자동화 스크립트 (권장)
│   ├── run_job_manual.py              # ❌ 수동 방식 (비교용)
│   └── cleanup.py                     # 리소스 정리
└── docs/
    ├── STEP_BY_STEP.md                # 단계별 실행 가이드
    └── ARCHITECTURE.md                # 아키텍처 설명
```

---

## 🏗️ 아키텍처

### 현재 시나리오

```
┌─────────────────────────────────────────┐
│  All-purpose Cluster (배치 작업 전용)    │
│  - 이름: batch-dedicated-cluster        │
│  - 자동 종료: 60분 idle timeout         │
│  - 타입: Standard_DS3_v2 (또는 유사)    │
└─────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────┐
│  job_main                                │
│  ├─ task1: RunJob → job_sub1            │
│  │   └─ subtask1-1: Notebook            │
│  │   └─ subtask1-2: Notebook            │
│  ├─ task2: SQL (SQL Warehouse)          │
│  └─ task3: RunJob → job_sub2            │
│      └─ subtask3-1: Notebook            │
│      └─ subtask3-2: Notebook            │
└─────────────────────────────────────────┘
```

### 자동화 워크플로우

```
1. 클러스터 상태 확인
   ├─ Running → 바로 Job 실행
   └─ Stopped/Terminated → 시작 후 Ready 대기

2. Job 실행
   └─ job_main 실행 및 완료 대기

3. 클러스터 종료
   └─ Job 완료 후 자동 종료
```

---

## 🚀 빠른 시작

### 사전 요구사항

```bash
# 필수 패키지 설치
pip install databricks-sdk python-dotenv

# Databricks 인증 설정 (.env 파일 또는 환경변수)
cat > .env << EOF
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-token-here
EOF
```

### Step 1: 데모 환경 구축

```bash
cd job_cost_optimization_demo

# 1. 샘플 노트북, Job, 클러스터 생성
python scripts/setup_demo.py

# 출력 예시:
# ✅ Cluster created: batch-dedicated-cluster (cluster-id: 1234-567890-abcd123)
# ✅ Notebook uploaded: /Shared/demo/sample_sleep_task
# ✅ Job created: job_sub1 (job-id: 12345)
# ✅ Job created: job_sub2 (job-id: 12346)
# ✅ Job created: job_main (job-id: 12347)
```

### Step 2: 수동 방식 실행 (비교용)

```bash
# ❌ 수동으로 클러스터 관리하는 방식
python scripts/run_job_manual.py --cluster-id 1234-567890-abcd123
```

**문제점:**
- 에러 처리 부족 (클러스터 시작 실패, Job 실패 시 대응 어려움)
- 수동으로 상태 확인 필요
- 종료 시점 판단 어려움

### Step 3: 자동화 방식 실행 (권장) ✅

```bash
# ✅ 완전 자동화 방식
python scripts/run_job_automated.py \
  --cluster-name "batch-dedicated-cluster" \
  --job-name "job_main"

# 또는 ID로 지정
python scripts/run_job_automated.py \
  --cluster-id "1234-567890-abcd123" \
  --job-id "12347"
```

**개선점:**
- ✅ 클러스터 상태 자동 감지 및 시작
- ✅ Job 완료까지 모니터링
- ✅ 완료 후 자동 종료
- ✅ 에러 시 재시도 로직 및 알림
- ✅ 실행 로그 및 비용 추적

### Step 4: 스케줄 실행 (Cron/Airflow/Databricks Workflows)

```bash
# Cron 예시: 매일 오전 2시 실행
crontab -e
# 0 2 * * * cd /path/to/demo && python scripts/run_job_automated.py --cluster-name "batch-dedicated-cluster" --job-name "job_main" >> /var/log/databricks_job.log 2>&1
```

---

## 📊 실행 결과 예시

### 자동화 스크립트 출력

```
[2026-03-12 14:30:00] INFO: Starting automated job execution
[2026-03-12 14:30:01] INFO: Cluster 'batch-dedicated-cluster' found (ID: 1234-567890-abcd123)
[2026-03-12 14:30:01] INFO: Current cluster state: TERMINATED
[2026-03-12 14:30:02] INFO: Starting cluster...
[2026-03-12 14:32:45] INFO: Cluster is RUNNING (startup time: 2m43s)
[2026-03-12 14:32:46] INFO: Triggering job 'job_main' (ID: 12347)
[2026-03-12 14:32:47] INFO: Job run started (run-id: 987654)
[2026-03-12 14:32:50] INFO: Task 'task1' (RunJob: job_sub1) started
[2026-03-12 14:33:15] INFO: Task 'task1' completed successfully
[2026-03-12 14:33:16] INFO: Task 'task2' (SQL) started
[2026-03-12 14:33:25] INFO: Task 'task2' completed successfully
[2026-03-12 14:33:26] INFO: Task 'task3' (RunJob: job_sub2) started
[2026-03-12 14:33:50] INFO: Task 'task3' completed successfully
[2026-03-12 14:33:51] INFO: Job 'job_main' completed successfully (total runtime: 1m4s)
[2026-03-12 14:33:52] INFO: Terminating cluster...
[2026-03-12 14:34:10] INFO: Cluster terminated successfully
[2026-03-12 14:34:10] INFO: ✅ Total execution time: 4m10s (startup: 2m43s, job: 1m4s, shutdown: 23s)
[2026-03-12 14:34:10] INFO: 💰 Estimated cost: ~$0.053 (0.07 DBU @ $0.75/DBU)
```

---

## 💡 핵심 기능

### 1. 지능형 클러스터 관리

```python
# 클러스터 상태에 따른 분기 처리
if cluster_state == "RUNNING":
    print("✅ Cluster already running")
elif cluster_state in ["TERMINATED", "TERMINATING"]:
    print("🔄 Starting cluster...")
    start_cluster_and_wait()
elif cluster_state == "PENDING":
    print("⏳ Waiting for cluster to be ready...")
    wait_until_running()
```

### 2. Job 실행 모니터링

```python
# Real-time job progress tracking
while not job_completed:
    run_status = get_run_status(run_id)
    for task in run_status.tasks:
        print(f"  - {task.name}: {task.state} ({task.runtime})")
    time.sleep(10)
```

### 3. 에러 처리 및 재시도

```python
# 클러스터 시작 실패 시 재시도
@retry(max_attempts=3, backoff=exponential)
def start_cluster_with_retry():
    try:
        w.clusters.start(cluster_id)
    except Exception as e:
        log_error(f"Cluster start failed: {e}")
        raise
```

### 4. 비용 추적

```python
# 실행 시간 및 비용 계산
total_runtime_hours = (end_time - start_time) / 3600
dbu_consumed = total_runtime_hours * cluster_dbu_per_hour
estimated_cost = dbu_consumed * dbu_price
```

---

## 🔧 구성 옵션

### config.yaml 예시

```yaml
cluster:
  name: "batch-dedicated-cluster"
  # 또는 cluster_id: "1234-567890-abcd123"

  # 시작 타임아웃 (초)
  start_timeout: 600

  # 재시도 설정
  max_retries: 3
  retry_delay: 30

job:
  name: "job_main"
  # 또는 job_id: "12347"

  # Job 실행 타임아웃 (초)
  run_timeout: 3600

  # 실패 시 알림
  notify_on_failure: true
  email: "admin@example.com"

shutdown:
  # Job 완료 후 클러스터 종료
  terminate_after_job: true

  # 대기 시간 (초) - 다른 작업 시작 대기
  grace_period: 60

logging:
  level: "INFO"
  file: "/var/log/databricks_automation.log"
```

---

## 📈 모니터링 및 알림

### Slack 알림 통합

```python
# scripts/run_job_automated.py에 Slack 알림 추가
def send_slack_notification(message, status="info"):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if webhook_url:
        payload = {
            "text": f"[{status.upper()}] {message}",
            "username": "Databricks Job Automation"
        }
        requests.post(webhook_url, json=payload)

# 사용 예시
send_slack_notification("✅ Job 'job_main' completed successfully", "success")
send_slack_notification("❌ Job 'job_main' failed", "error")
```

### 비용 대시보드

```sql
-- 실행 이력 및 비용 추적 테이블 생성
CREATE TABLE IF NOT EXISTS job_execution_logs (
  execution_id STRING,
  cluster_id STRING,
  cluster_name STRING,
  job_id STRING,
  job_name STRING,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  duration_seconds INT,
  dbu_consumed DECIMAL(10, 4),
  estimated_cost DECIMAL(10, 2),
  status STRING,
  error_message STRING
);
```

---

## 🧹 리소스 정리

```bash
# 데모 리소스 삭제
python scripts/cleanup.py

# 선택적 삭제
python scripts/cleanup.py --keep-cluster  # 클러스터는 유지
python scripts/cleanup.py --keep-jobs     # Job은 유지
```

---

## 📚 다음 단계

### 1. 프로덕션 적용 체크리스트

- [ ] 클러스터 자동 종료 정책 설정 (60분 idle timeout)
- [ ] Job 실패 시 알림 설정 (email, Slack)
- [ ] 비용 추적 대시보드 구축
- [ ] 백업 실행 전략 수립 (클러스터 시작 실패 시)
- [ ] 로그 보관 정책 수립

### 2. 추가 최적화 고려사항

**단기 (현재 구조 유지):**
- Instance Profile 최적화 (적절한 VM 크기 선택)
- Spot 인스턴스 적용 (70% 추가 절감, 단 중단 가능성 고려)
- 여러 Job을 하나의 클러스터에서 순차 실행

**중장기 (아키텍처 개선):**
- Job 클러스터로 전환 (DBU 87% 절감)
- Delta Live Tables로 마이그레이션 (파이프라인 단순화)
- Serverless Compute 활용 (관리 부담 제거)

---

## 🤔 FAQ

### Q1: Job 클러스터로 전환하지 않는 이유는?

**A:** 현재 상황에서는 All-purpose 클러스터가 더 적합합니다:
- ✅ 여러 RunJob으로 구성된 복잡한 Job 구조 (설정 변경 최소화)
- ✅ 클러스터 시작 시간이 전체 작업 시간 대비 큰 비중
- ✅ Job들이 빠르게 순차 실행되어 하나의 클러스터 재사용이 효율적

### Q2: 클러스터 종료 전 대기 시간(grace period)이 필요한가?

**A:** 다음 상황에서 유용합니다:
- 동일 클러스터에서 연속으로 여러 Job 실행 예정
- 수동 검증이나 디버깅 시간 확보 필요
- 즉시 종료 시 로그 수집 누락 방지

일반적으로 0~60초 권장합니다.

### Q3: Spot 인스턴스 적용 시 주의사항은?

**A:**
- ✅ 적합: 재시도 가능한 배치 작업, 실행 시간 30분 이상
- ❌ 부적합: 실시간 처리, SLA가 엄격한 작업
- 권장 설정: `availability = "SPOT_WITH_FALLBACK"` (중단 시 On-demand로 자동 전환)

### Q4: 여러 Job을 하나의 스크립트로 관리 가능한가?

**A:** 가능합니다:

```bash
# 복수 Job 순차 실행
python scripts/run_job_automated.py \
  --cluster-name "batch-dedicated-cluster" \
  --job-names "job_main,job_daily_report,job_cleanup"
```

---

## 📞 문의

기술 지원이 필요하시면 Databricks Solution Architect에게 연락하세요.

---

## 📖 참고 자료

- [Databricks Clusters API](https://docs.databricks.com/api/workspace/clusters)
- [Jobs API](https://docs.databricks.com/api/workspace/jobs)
- [클러스터 구성 최적화](https://docs.databricks.com/clusters/configure.html)
- [비용 관리 모범 사례](https://docs.databricks.com/administration-guide/account-settings/usage.html)
