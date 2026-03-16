# 🚀 빠른 시작 가이드 (5분)

## 1️⃣ 패키지 설치 (1분)

```bash
pip install databricks-sdk python-dotenv
```

## 2️⃣ 인증 설정 (1분)

```bash
cd job_cost_optimization_demo

# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (본인의 워크스페이스 정보 입력)
# DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
# DATABRICKS_TOKEN=dapi...
```

**토큰 생성 방법**:
1. Databricks 워크스페이스 접속
2. 우측 상단 사용자 아이콘 클릭 → **User Settings**
3. **Access tokens** → **Generate new token**
4. Comment 입력 (예: "Job Automation") → **Generate**
5. 생성된 토큰 복사하여 `.env` 파일에 붙여넣기

## 3️⃣ 데모 환경 구축 (2분)

```bash
python scripts/setup_demo.py
```

생성되는 리소스:
- ✅ All-purpose 클러스터 1개
- ✅ 샘플 노트북
- ✅ Job 3개 (job_sub1, job_sub2, job_main)

## 4️⃣ 자동화 실행 (1분)

```bash
python scripts/run_job_automated.py \
  --cluster-name "batch-dedicated-cluster" \
  --job-name "demo_job_main"
```

**예상 출력**:
```
✅ 클러스터 시작 완료 (2분 43초)
✅ Job 실행 완료 (1분 3초)
✅ 클러스터 종료 완료 (18초)

💰 예상 비용: $0.04
📊 월간 절감액: $403.86 (99.7% 절감)
```

## ✅ 완료!

이제 다음을 확인하세요:
1. Databricks UI → **Workflows** → `demo_job_main` 실행 이력
2. Databricks UI → **Compute** → `batch-dedicated-cluster` 상태 (TERMINATED)

---

## 📚 다음 단계

- 📖 [단계별 가이드](docs/STEP_BY_STEP.md) - 상세 설명
- 🏗️ [아키텍처 가이드](docs/ARCHITECTURE.md) - 설계 및 확장
- 🧹 [리소스 정리](scripts/cleanup.py) - 데모 완료 후 실행

---

## 💡 자주 묻는 질문

**Q: 클러스터 시작에 왜 3분이 걸리나요?**
A: All-purpose 클러스터의 정상적인 시작 시간입니다. 클러스터 풀을 사용하면 1분으로 단축 가능합니다.

**Q: 월 $400 절감이 실제로 가능한가요?**
A: 24시간 상시 실행 대비 1일 1회 4분 실행 시 계산된 값입니다. 실제 절감액은 실행 횟수와 시간에 따라 다릅니다.

**Q: 프로덕션에 바로 적용 가능한가요?**
A: 네, 에러 처리 및 재시도 로직이 포함되어 있습니다. Slack 알림 등을 추가하시면 더욱 안정적입니다.

---

## 📞 문의

문제가 발생하면 Databricks Solution Architect에게 연락하세요.
