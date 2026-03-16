# 아키텍처 및 설계 가이드

## 📐 전체 아키텍처

### 현재 시나리오 (데모)

```
┌─────────────────────────────────────────────────────────────┐
│                  배치 작업 전용 클러스터                     │
│  - 이름: batch-dedicated-cluster                            │
│  - 타입: All-purpose (0.75 DBU/시간)                        │
│  - 크기: i3.xlarge + 1~2 workers (Autoscale)               │
│  - 자동 종료: 60분 idle timeout                             │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                      demo_job_main                          │
│                                                             │
│  Task 1: RunJob (demo_job_sub1)                            │
│  ├─ subtask1_1: Notebook (sleep 10)                        │
│  └─ subtask1_2: Notebook (sleep 10)                        │
│                                                             │
│  Task 2: SQL Query                                          │
│  └─ SQL Warehouse에서 실행                                  │
│                                                             │
│  Task 3: RunJob (demo_job_sub2)                            │
│  ├─ subtask3_1: Notebook (sleep 10)                        │
│  └─ subtask3_2: Notebook (sleep 10)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 자동화 워크플로우

### 실행 흐름도

```
START
  │
  ├─> [1] Databricks 워크스페이스 연결
  │     └─> 인증 (Token/OAuth)
  │
  ├─> [2] 클러스터 식별
  │     ├─ 클러스터 이름으로 검색
  │     └─ 클러스터 ID 획득
  │
  ├─> [3] 클러스터 상태 확인
  │     ├─ RUNNING? ───────────────┐
  │     ├─ TERMINATED? ───> 시작 ─┤
  │     ├─ PENDING? ──> 대기 ─────┤
  │     └─ ERROR? ──> 종료 ────────┘
  │                                 │
  │     <──────────────────────────┘
  │
  ├─> [4] Job 식별
  │     ├─ Job 이름으로 검색
  │     └─ Job ID 획득
  │
  ├─> [5] Job 실행
  │     ├─ Run 시작
  │     └─ Run ID 획득
  │
  ├─> [6] Job 모니터링
  │     ├─ 15초마다 상태 체크
  │     ├─ Task별 진행 상황 출력
  │     └─ 완료/실패 감지
  │
  ├─> [7] 클러스터 종료 (옵션)
  │     ├─ Grace period 대기
  │     ├─ 종료 명령 실행
  │     └─ TERMINATED 상태 확인
  │
  └─> [8] 결과 요약
        ├─ 실행 시간 계산
        ├─ 비용 추정
        └─ 로그 출력
END
```

---

## 🏗️ 구성 요소

### 1. 클러스터 관리 모듈

**주요 기능**:
- 클러스터 상태 감지 및 시작
- 시작 완료 대기 (Polling)
- 종료 및 정리

**코드 구조**:

```python
def get_cluster_state(w: WorkspaceClient, cluster_id: str) -> str:
    """현재 상태 반환: RUNNING, TERMINATED, PENDING, ERROR 등"""
    cluster_info = w.clusters.get(cluster_id)
    return cluster_info.state.value

def start_cluster_if_needed(w: WorkspaceClient, cluster_id: str):
    """
    상태별 분기 처리:
    - RUNNING: 즉시 반환
    - TERMINATED: 시작 → RUNNING 대기
    - PENDING: RUNNING 대기
    """
    state = get_cluster_state(w, cluster_id)

    if state == "RUNNING":
        return 0

    if state == "TERMINATED":
        w.clusters.start(cluster_id)
        wait_until_running(w, cluster_id)

    # ... (생략)

def terminate_cluster(w: WorkspaceClient, cluster_id: str, grace_period: int):
    """
    Grace period 대기 후 종료
    - 다음 작업 시작 가능성 고려
    - 로그 수집 시간 확보
    """
    time.sleep(grace_period)
    w.clusters.delete(cluster_id)
    wait_until_terminated(w, cluster_id)
```

### 2. Job 실행 모듈

**주요 기능**:
- Job 실행 및 Run ID 획득
- Run 상태 모니터링
- Task별 진행 상황 추적

**코드 구조**:

```python
def run_job(w: WorkspaceClient, job_id: str) -> str:
    """Job 실행 및 Run ID 반환"""
    run = w.jobs.run_now(job_id)
    return run.run_id

def monitor_job_run(w: WorkspaceClient, run_id: str):
    """
    Real-time 모니터링:
    - 15초마다 상태 체크
    - Task별 상태 출력
    - 완료/실패 감지
    """
    while True:
        run_info = w.jobs.get_run(run_id)
        state = run_info.state.life_cycle_state.value

        # Task 상태 출력
        for task in run_info.tasks:
            print(f"  └─ {task.task_key}: {task.state}")

        # 종료 조건
        if state in ["TERMINATED", "SKIPPED", "INTERNAL_ERROR"]:
            return run_info.state.result_state.value == "SUCCESS"

        time.sleep(15)
```

### 3. 비용 추적 모듈

**주요 기능**:
- 실행 시간 계산
- DBU 소비량 계산
- 비용 추정 및 절감액 계산

**비용 계산 공식**:

```python
# 1. 활성 시간 계산
active_time_hours = (startup_time + job_runtime + shutdown_time) / 3600

# 2. DBU 소비량 계산
dbu_consumed = active_time_hours × CLUSTER_DBU_PER_HOUR

# 3. 비용 계산
cost = dbu_consumed × DBU_PRICE

# 4. 월간 절감액 (1일 1회 실행 가정)
monthly_cost_always_on = 24 × 30 × CLUSTER_DBU_PER_HOUR × DBU_PRICE
monthly_cost_optimized = active_time_hours × 30 × CLUSTER_DBU_PER_HOUR × DBU_PRICE
monthly_savings = monthly_cost_always_on - monthly_cost_optimized
```

**DBU 요금표** (참고):

| 클러스터 타입 | DBU/시간 | 절감 가능성 |
|--------------|---------|------------|
| All-purpose | 0.75 | 기준 |
| Job Cluster | 0.10 | 87% ↓ |
| Serverless | 0.07 | 91% ↓ |

---

## 🎛️ 설정 옵션

### 명령줄 인자

```bash
python run_job_automated.py \
  --cluster-name "batch-dedicated-cluster" \  # 클러스터 이름 (또는 --cluster-id)
  --job-name "demo_job_main" \                 # Job 이름 (또는 --job-id)
  --grace-period 60 \                          # 종료 전 대기 시간 (초)
  --no-terminate                               # 종료하지 않음
```

### 환경변수

```bash
# 필수
DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
DATABRICKS_TOKEN="dapi1234567890abcdef"

# 옵션
DBU_PRICE=0.75                    # DBU당 가격 (USD)
CLUSTER_DBU_PER_HOUR=0.75         # 시간당 DBU 소비량
```

### 설정 파일 (config.yaml) - 향후 확장

```yaml
cluster:
  name: "batch-dedicated-cluster"
  start_timeout: 600              # 시작 타임아웃 (초)
  max_retries: 3                  # 재시도 횟수
  retry_delay: 30                 # 재시도 간격 (초)

job:
  name: "demo_job_main"
  run_timeout: 3600               # Job 타임아웃 (초)
  poll_interval: 15               # 모니터링 간격 (초)

shutdown:
  terminate_after_job: true       # Job 완료 후 종료
  grace_period: 60                # 대기 시간 (초)

notifications:
  slack_webhook_url: "https://..."
  email: "admin@example.com"
  notify_on_success: false
  notify_on_failure: true

logging:
  level: "INFO"                   # DEBUG, INFO, WARNING, ERROR
  file: "/var/log/databricks_automation.log"
```

---

## 🔐 보안 고려사항

### 1. 인증 토큰 관리

**권장 방법**:

```bash
# ❌ 나쁜 예: 코드에 하드코딩
token = "dapi1234567890abcdef"

# ✅ 좋은 예: 환경변수 사용
token = os.getenv("DATABRICKS_TOKEN")

# ✅ 더 좋은 예: AWS Secrets Manager
import boto3
client = boto3.client('secretsmanager')
token = client.get_secret_value(SecretId='databricks/token')['SecretString']
```

### 2. 클러스터 권한

**최소 권한 원칙**:
- 클러스터: `Can Restart` (시작/종료만 가능)
- Job: `Can Manage Run` (실행 관리만 가능)
- Workspace: 읽기 전용 (노트북 읽기만)

### 3. 네트워크 격리

- VPC 내부에서만 접근 가능하도록 설정
- IP 화이트리스트 사용
- Private Link (AWS) 또는 Private Endpoint (Azure) 활용

---

## 📊 모니터링 및 알림

### 1. Slack 알림 통합

```python
import requests

def send_slack_notification(message: str, status: str = "info"):
    """Slack으로 알림 전송"""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return

    emoji = {
        "success": ":white_check_mark:",
        "error": ":x:",
        "warning": ":warning:",
        "info": ":information_source:"
    }.get(status, ":speech_balloon:")

    payload = {
        "text": f"{emoji} {message}",
        "username": "Databricks Job Automation"
    }

    requests.post(webhook_url, json=payload)

# 사용 예시
send_slack_notification("Job 'demo_job_main' started", "info")
send_slack_notification("Job completed in 1m 23s", "success")
send_slack_notification("Job failed: timeout", "error")
```

### 2. 비용 추적 테이블

```sql
-- 실행 이력 테이블 생성
CREATE TABLE IF NOT EXISTS default.job_execution_logs (
  execution_id STRING,
  cluster_id STRING,
  cluster_name STRING,
  job_id STRING,
  job_name STRING,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  startup_time_seconds INT,
  job_runtime_seconds INT,
  shutdown_time_seconds INT,
  total_time_seconds INT,
  dbu_consumed DECIMAL(10, 4),
  estimated_cost DECIMAL(10, 2),
  status STRING,
  error_message STRING
) USING DELTA
PARTITIONED BY (date(start_time));

-- 데이터 삽입 (Python에서)
spark.sql(f"""
  INSERT INTO default.job_execution_logs VALUES (
    '{execution_id}',
    '{cluster_id}',
    '{cluster_name}',
    '{job_id}',
    '{job_name}',
    '{start_time}',
    '{end_time}',
    {startup_time},
    {job_runtime},
    {shutdown_time},
    {total_time},
    {dbu_consumed},
    {estimated_cost},
    '{status}',
    '{error_message}'
  )
""")

-- 월간 비용 조회
SELECT
  date_trunc('month', start_time) as month,
  SUM(estimated_cost) as total_cost,
  COUNT(*) as execution_count,
  AVG(total_time_seconds) as avg_runtime_seconds
FROM default.job_execution_logs
WHERE status = 'SUCCESS'
GROUP BY 1
ORDER BY 1 DESC;
```

### 3. 대시보드 (AI/BI Dashboard)

**주요 지표**:
- 일별/월별 실행 횟수
- 평균 실행 시간 추이
- 비용 추이 및 절감액
- 실패율 및 에러 분석

---

## 🚀 성능 최적화

### 1. 클러스터 시작 시간 단축

**방법 1: 클러스터 풀 사용**

```python
# 클러스터 풀 생성 (UI 또는 API)
pool_config = {
    "instance_pool_name": "batch-job-pool",
    "min_idle_instances": 1,        # 항상 1개는 대기
    "max_capacity": 5,
    "idle_instance_autotermination_minutes": 30,
    "node_type_id": "i3.xlarge"
}

# 클러스터 생성 시 풀 지정
cluster_config = {
    "cluster_name": "batch-dedicated-cluster",
    "instance_pool_id": pool_id,    # 시작 시간 1~2분으로 단축
    # ...
}
```

**효과**: 시작 시간 **5분 → 1분**

**방법 2: Delta Cache 활성화**

```python
cluster_config["spark_conf"] = {
    "spark.databricks.io.cache.enabled": "true",
    "spark.databricks.io.cache.maxDiskUsage": "50g",
}
```

### 2. Job 실행 시간 단축

**방법 1: Task 병렬화**

```json
{
  "tasks": [
    {"task_key": "task1", "depends_on": []},
    {"task_key": "task2", "depends_on": []},       // task1과 병렬
    {"task_key": "task3", "depends_on": ["task1"]}, // task1 완료 후
    {"task_key": "task4", "depends_on": ["task2", "task3"]}
  ]
}
```

**효과**: 총 실행 시간 **30% 단축**

**방법 2: 데이터 Caching**

```python
# 자주 읽는 테이블 캐싱
spark.sql("CACHE TABLE my_table")

# 또는 Delta Cache 활용
df = spark.read.format("delta").load("/path/to/table")
df.cache()
```

---

## 💰 추가 비용 절감 전략

### 1. Spot 인스턴스 활용

**설정 방법**:

```python
cluster_config["aws_attributes"] = {
    "availability": "SPOT_WITH_FALLBACK",  # Spot 우선, 실패 시 On-demand
    "spot_bid_price_percent": 100,         # 최대 On-demand 가격의 100%
    "zone_id": "auto"                       # 최적 가용 영역 자동 선택
}
```

**절감 효과**: 컴퓨팅 비용 **최대 70% 절감**

**주의사항**:
- 중단 가능성 있음 (평균 5% 미만)
- Checkpoint/재시작 로직 필요
- 실행 시간 30분 이상 작업 권장

### 2. Autoscaling 최적화

```python
cluster_config["autoscale"] = {
    "min_workers": 0,  # 작업 없을 때 0으로 축소
    "max_workers": 5
}

# Enhanced Autoscaling (빠른 스케일링)
cluster_config["autoscaling_policy_id"] = "enhanced"
```

### 3. Job 클러스터로 전환 (중장기)

**현재**: All-purpose 클러스터 (0.75 DBU/시간)
**개선**: Job 클러스터 (0.10 DBU/시간)

**마이그레이션 단계**:

```python
# 1. Job 정의에 new_cluster 추가
{
  "tasks": [
    {
      "task_key": "task1",
      "new_cluster": {
        "spark_version": "14.3.x-scala2.12",
        "node_type_id": "i3.xlarge",
        "num_workers": 2
      },
      "notebook_task": {...}
    }
  ]
}

# 2. RunJob task는 그대로 유지 가능
```

**절감 효과**: DBU 비용 **87% 절감**

---

## 📈 확장 가능성

### 1. 여러 Job 순차 실행

```python
# 복수 Job 실행
job_list = ["job_main", "job_daily_report", "job_cleanup"]

for job_name in job_list:
    log(f"Running job: {job_name}")
    run_id = run_job(w, get_job_by_name(w, job_name))
    success, runtime = monitor_job_run(w, run_id)

    if not success:
        log(f"Job {job_name} failed. Stopping pipeline.", "ERROR")
        break
```

### 2. 조건부 실행

```python
# 데이터 체크 후 Job 실행
row_count = spark.sql("SELECT COUNT(*) FROM source_table").collect()[0][0]

if row_count > 0:
    run_job(w, job_id)
else:
    log("No data to process. Skipping job.", "INFO")
```

### 3. 재시도 로직

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
def run_job_with_retry(w, job_id):
    run_id = run_job(w, job_id)
    success, runtime = monitor_job_run(w, run_id)

    if not success:
        raise Exception("Job failed")

    return run_id
```

---

## 🎓 모범 사례 요약

### ✅ DO

1. **환경변수로 인증 관리** - 토큰을 코드에 하드코딩하지 않기
2. **실행 로그 저장** - 문제 진단 및 비용 추적
3. **에러 처리 및 재시도** - 일시적 장애 대응
4. **Grace period 설정** - 연속 작업 대비
5. **비용 모니터링** - 실행 이력 및 비용 추적 테이블 구축
6. **알림 설정** - 실패 시 즉시 인지
7. **Spot 인스턴스 활용** - 비용 절감 (적합한 워크로드에)
8. **클러스터 풀 사용** - 시작 시간 단축

### ❌ DON'T

1. **All-purpose 클러스터 상시 실행** - 불필요한 비용 발생
2. **고정 대기 시간** - 상태 확인 없이 sleep만 사용
3. **에러 무시** - 실패 시 대응 없이 진행
4. **과도한 리소스** - 필요 이상의 큰 클러스터 사용
5. **로그 없이 실행** - 문제 발생 시 원인 파악 어려움
6. **수동 개입 의존** - 사람이 시작/종료 해야 하는 구조

---

## 🔮 로드맵

### Phase 1: 현재 (All-purpose 클러스터 자동화)
- ✅ 클러스터 라이프사이클 자동화
- ✅ Job 실행 모니터링
- ✅ 비용 추적

### Phase 2: 단기 (1~2개월)
- 🔄 Spot 인스턴스 적용
- 🔄 클러스터 풀 구축
- 🔄 비용 대시보드 구축
- 🔄 Slack/이메일 알림 통합

### Phase 3: 중기 (3~6개월)
- ⏳ Job 클러스터로 마이그레이션
- ⏳ Task 병렬화 최적화
- ⏳ Delta Live Tables 검토

### Phase 4: 장기 (6개월 이상)
- 📋 Serverless Compute 전환
- 📋 완전 자동화 CI/CD 파이프라인
- 📋 ML 기반 비용 예측 및 최적화

---

## 📞 문의 및 지원

기술 지원이 필요하시면 Databricks Solution Architect에게 연락하세요.
