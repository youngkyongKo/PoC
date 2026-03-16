# 단계별 실행 가이드

## 🎯 목표

기존 RunJob 구조를 유지하면서 All-purpose 클러스터의 라이프사이클을 자동화하여 비용을 절감합니다.

---

## 📋 사전 준비

### 1. 필수 패키지 설치

```bash
pip install databricks-sdk python-dotenv
```

### 2. Databricks 인증 설정

#### 방법 1: 환경변수

```bash
export DATABRICKS_HOST="https://your-workspace.cloud.databricks.com"
export DATABRICKS_TOKEN="dapi1234567890abcdef"
```

#### 방법 2: .env 파일 생성

```bash
cd job_cost_optimization_demo
cat > .env << EOF
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi1234567890abcdef
EOF
```

#### 방법 3: Databricks CLI 설정

```bash
databricks configure --token
```

---

## 🚀 Step 1: 데모 환경 구축

```bash
cd job_cost_optimization_demo
python scripts/setup_demo.py
```

### 생성되는 리소스

1. **All-purpose 클러스터**: `batch-dedicated-cluster`
   - Node type: i3.xlarge (또는 Standard_DS3_v2)
   - Workers: 1-2 (Autoscale)
   - Auto-termination: 60분

2. **샘플 노트북**: `/Shared/demo_job_optimization/sample_sleep_task`
   - 실행 시간: 10초
   - 작업 내용: Sleep + 간단한 Spark 작업

3. **Job 3개**:
   - `demo_job_sub1`: 2개의 notebook task (순차 실행)
   - `demo_job_sub2`: 2개의 notebook task (순차 실행)
   - `demo_job_main`: 3개의 task
     - task1: RunJob → demo_job_sub1
     - task2: SQL query
     - task3: RunJob → demo_job_sub2

### 예상 출력

```
======================================================================
  Databricks Job 비용 최적화 데모 - 환경 구축
======================================================================
✅ Databricks 워크스페이스 연결: https://...

📦 클러스터 생성 중: batch-dedicated-cluster
✅ 클러스터 생성 완료: batch-dedicated-cluster
   - Cluster ID: 0123-456789-abcd123
   - Auto-termination: 60분

📓 노트북 업로드 중: /Shared/demo_job_optimization
✅ 노트북 업로드 완료: /Shared/demo_job_optimization/sample_sleep_task

🏢 SQL Warehouse 확인 중...
✅ SQL Warehouse 발견: Starter Warehouse (ID: 1a2b3c4d5e6f7890)

⚙️  Job 생성 중...
  - job_sub1 생성 중...
    ✅ job_sub1 생성 완료 (ID: 12345)
  - job_sub2 생성 중...
    ✅ job_sub2 생성 완료 (ID: 12346)
  - job_main 생성 중...
    ✅ job_main 생성 완료 (ID: 12347)

📝 설정 파일 저장: /Users/.../demo_config.json

======================================================================
  ✅ 데모 환경 구축 완료!
======================================================================

📋 생성된 리소스:
  - Cluster: batch-dedicated-cluster (ID: 0123-456789-abcd123)
  - Notebook: /Shared/demo_job_optimization/sample_sleep_task
  - Job: demo_job_sub1 (ID: 12345)
  - Job: demo_job_sub2 (ID: 12346)
  - Job: demo_job_main (ID: 12347)

🚀 다음 단계:
  1. 수동 방식 실행:
     python scripts/run_job_manual.py --cluster-id 0123-456789-abcd123

  2. 자동화 방식 실행 (권장):
     python scripts/run_job_automated.py --cluster-name batch-dedicated-cluster --job-name demo_job_main
```

---

## 🔄 Step 2: 수동 방식 실행 (비교용)

```bash
# demo_config.json에서 cluster_id 확인
cat demo_config.json

# 수동 방식으로 실행
python scripts/run_job_manual.py \
  --cluster-id "0123-456789-abcd123" \
  --job-id "12347"
```

### 수동 방식의 문제점

❌ **에러 처리 부족**
- 클러스터 시작 실패 시 재시도 없음
- 고정 대기 시간 (180초) - 너무 짧거나 길 수 있음

❌ **모니터링 부족**
- Task별 진행 상황 알 수 없음
- 실행 시간 추적 없음
- 비용 계산 없음

❌ **유지보수 어려움**
- 로그 부족으로 문제 진단 어려움
- 설정 변경 시 코드 수정 필요

---

## ✅ Step 3: 자동화 방식 실행 (권장)

```bash
# 이름으로 지정 (권장)
python scripts/run_job_automated.py \
  --cluster-name "batch-dedicated-cluster" \
  --job-name "demo_job_main"

# 또는 ID로 지정
python scripts/run_job_automated.py \
  --cluster-id "0123-456789-abcd123" \
  --job-id "12347"

# 클러스터 종료하지 않고 유지
python scripts/run_job_automated.py \
  --cluster-name "batch-dedicated-cluster" \
  --job-name "demo_job_main" \
  --no-terminate

# 종료 전 60초 대기 (다음 작업 대기)
python scripts/run_job_automated.py \
  --cluster-name "batch-dedicated-cluster" \
  --job-name "demo_job_main" \
  --grace-period 60
```

### 자동화 방식의 장점

✅ **지능형 클러스터 관리**
- 현재 상태 자동 감지 (RUNNING, TERMINATED, PENDING 등)
- 필요한 경우에만 시작
- 완료 후 자동 종료

✅ **실시간 모니터링**
- Job 및 Task별 진행 상황 표시
- 실행 시간 추적
- 에러 메시지 자동 출력

✅ **비용 추적**
- DBU 소비량 계산
- 예상 비용 표시
- 월간 절감액 계산

✅ **에러 처리**
- 재시도 로직
- 타임아웃 설정
- 상세한 로그

### 예상 출력

```
================================================================================
  Databricks Job 자동 실행 스크립트
================================================================================

[2026-03-12 14:30:00] SUCCESS: Databricks 워크스페이스 연결: https://...
[2026-03-12 14:30:01] INFO: 클러스터 검색 중: 'batch-dedicated-cluster'
[2026-03-12 14:30:02] SUCCESS: 클러스터 발견: batch-dedicated-cluster (ID: 0123-456789-abcd123)
[2026-03-12 14:30:03] INFO: 현재 클러스터 상태: TERMINATED
[2026-03-12 14:30:04] INFO: 클러스터 시작 중...
[2026-03-12 14:30:05] INFO: 클러스터 준비 대기 중...
[2026-03-12 14:32:48] SUCCESS: 클러스터 시작 완료 (소요 시간: 2분 43초) ✅
[2026-03-12 14:32:49] INFO: Job 검색 중: 'demo_job_main'
[2026-03-12 14:32:50] SUCCESS: Job 발견: demo_job_main (ID: 12347)
[2026-03-12 14:32:51] INFO: Job 실행 중 (Job ID: 12347)...
[2026-03-12 14:32:52] SUCCESS: Job 실행 시작 (Run ID: 987654) ✅
[2026-03-12 14:32:53] INFO: Job 실행 모니터링 시작...
[2026-03-12 14:32:54] INFO: Job 상태: RUNNING
[2026-03-12 14:32:54] INFO:   └─ Task 'task1_run_job_sub1': RUNNING
[2026-03-12 14:33:20] INFO:   └─ Task 'task1_run_job_sub1': TERMINATED
[2026-03-12 14:33:21] INFO:   └─ Task 'task2_sql_query': RUNNING
[2026-03-12 14:33:30] INFO:   └─ Task 'task2_sql_query': TERMINATED
[2026-03-12 14:33:31] INFO:   └─ Task 'task3_run_job_sub2': RUNNING
[2026-03-12 14:33:55] INFO:   └─ Task 'task3_run_job_sub2': TERMINATED
[2026-03-12 14:33:56] SUCCESS: Job 완료 성공 ✅ (실행 시간: 1분 3초)
[2026-03-12 14:33:57] INFO: 클러스터 종료 중...
[2026-03-12 14:34:15] SUCCESS: 클러스터 종료 완료 (소요 시간: 18초) ✅

================================================================================
  실행 결과 요약
================================================================================

⏱️  실행 시간:
  - 클러스터 시작: 2분 43초
  - Job 실행: 1분 3초
  - 클러스터 종료: 18초
  - 전체 시간: 4분 4초

💰 예상 비용:
  - 활성 시간: 0.0678 시간
  - DBU 소비: 0.0508 DBU
  - 컴퓨팅 비용: $0.04
    (All-purpose: 0.75 DBU/시간 × $0.75/DBU)

📊 월간 비용 비교 (1일 1회 실행 가정):
  - 상시 실행: $405.00/월
  - 최적화 실행: $1.14/월
  - 절감액: $403.86/월 (99.7% 절감) 💰

================================================================================
✅ Job 실행 성공!
================================================================================
```

---

## 📅 Step 4: 스케줄 실행 설정

### 옵션 1: Cron (Linux/Mac)

```bash
# Cron 편집
crontab -e

# 매일 오전 2시 실행
0 2 * * * cd /path/to/job_cost_optimization_demo && python scripts/run_job_automated.py --cluster-name "batch-dedicated-cluster" --job-name "demo_job_main" >> /var/log/databricks_job.log 2>&1

# 평일 오전 9시 실행
0 9 * * 1-5 cd /path/to/job_cost_optimization_demo && python scripts/run_job_automated.py --cluster-name "batch-dedicated-cluster" --job-name "demo_job_main" >> /var/log/databricks_job.log 2>&1
```

### 옵션 2: Databricks Workflows (권장)

Databricks UI에서:
1. **Workflows** → **Create Job**
2. **Add Task**:
   - Type: Python script
   - Source: Workspace
   - Script: `/Shared/automation/run_job_automated.py` (업로드 필요)
3. **Schedule** 설정:
   - Cron: `0 2 * * *` (매일 오전 2시)
   - Timezone: Asia/Seoul
4. **Cluster** 선택:
   - Job 클러스터 사용 (관리 스크립트용 소형 클러스터)

### 옵션 3: Apache Airflow

```python
# dags/databricks_job_automation.py
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2026, 3, 1),
    'email_on_failure': True,
    'email': ['admin@example.com'],
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'databricks_job_automation',
    default_args=default_args,
    description='Automated Databricks Job execution',
    schedule_interval='0 2 * * *',  # 매일 오전 2시
    catchup=False,
)

run_job_task = BashOperator(
    task_id='run_databricks_job',
    bash_command='cd /path/to/demo && python scripts/run_job_automated.py --cluster-name "batch-dedicated-cluster" --job-name "demo_job_main"',
    dag=dag,
)
```

---

## 🧹 Step 5: 리소스 정리

데모 완료 후 생성된 리소스를 정리합니다:

```bash
# 모든 리소스 삭제
python scripts/cleanup.py

# 클러스터는 유지하고 Job만 삭제
python scripts/cleanup.py --keep-cluster

# Job은 유지하고 클러스터만 삭제
python scripts/cleanup.py --keep-jobs

# 노트북은 유지
python scripts/cleanup.py --keep-notebooks
```

---

## 🔍 문제 해결

### 클러스터 시작 실패

**증상**: "Cluster start failed" 에러

**해결방법**:
1. Databricks UI에서 클러스터 상태 확인
2. 클러스터 설정 (인스턴스 타입, 권한) 확인
3. 클라우드 리소스 쿼터 확인 (EC2 limit 등)

### Job 실행 실패

**증상**: Job이 FAILED 상태로 종료

**해결방법**:
1. Databricks UI에서 Run 로그 확인
2. Task별 에러 메시지 확인
3. Notebook 코드 수정 후 재실행

### 인증 실패

**증상**: "Authentication failed" 에러

**해결방법**:
1. DATABRICKS_HOST 형식 확인 (https:// 포함)
2. DATABRICKS_TOKEN 유효성 확인
3. 토큰 권한 확인 (Workspace access, Cluster access)

---

## 📚 다음 단계

1. ✅ **프로덕션 적용**: 실제 Job에 자동화 스크립트 적용
2. ✅ **모니터링 추가**: Slack 알림, 이메일 알림 설정
3. ✅ **비용 대시보드**: 실행 이력 및 비용 추적 대시보드 구축
4. ✅ **추가 최적화**: Spot 인스턴스, Job 클러스터 전환 검토

자세한 내용은 [ARCHITECTURE.md](ARCHITECTURE.md)를 참고하세요.
