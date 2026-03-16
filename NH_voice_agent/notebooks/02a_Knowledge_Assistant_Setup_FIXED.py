# Databricks notebook source
# MAGIC %md
# MAGIC # Knowledge Assistant API 호출 - 인증 문제 해결
# MAGIC
# MAGIC ## 🔧 401 에러 해결 방법
# MAGIC
# MAGIC ### 문제
# MAGIC ```
# MAGIC {"error_code":401,"message":"Credential was not sent or was of an unsupported type"}
# MAGIC ```
# MAGIC
# MAGIC ### 원인
# MAGIC - API 토큰이 올바르게 전달되지 않음
# MAGIC - 토큰 형식 오류
# MAGIC - KA endpoint에 대한 권한 부족
# MAGIC
# MAGIC ### 해결
# MAGIC - Databricks Notebook 내장 인증 사용
# MAGIC - 올바른 헤더 형식 적용

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: 환경 설정 및 KA Endpoint 확인

# COMMAND ----------

from databricks.sdk import WorkspaceClient
import requests
import json

# SDK 초기화 (자동 인증)
client = WorkspaceClient()

# KA Endpoint 이름 (실제 이름으로 변경)
KA_ENDPOINT_NAME = "ka-69e8398a-endpoint"

print("=" * 80)
print("Knowledge Assistant 정보")
print("=" * 80)

# Endpoint 상태 확인
try:
    endpoint = client.serving_endpoints.get(KA_ENDPOINT_NAME)
    print(f"✅ Endpoint: {KA_ENDPOINT_NAME}")
    print(f"   상태: {endpoint.state.ready if endpoint.state else 'UNKNOWN'}")
    print()
except Exception as e:
    print(f"❌ Endpoint 조회 실패: {e}")
    print(f"   Endpoint 이름을 확인하세요: {KA_ENDPOINT_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: 인증 토큰 가져오기
# MAGIC
# MAGIC ### 🔑 중요: Databricks Notebook에서 안전한 토큰 가져오기

# COMMAND ----------

# 방법 1: Databricks Notebook Context에서 토큰 가져오기 (권장)
def get_databricks_token():
    """
    Databricks Notebook에서 안전하게 토큰 가져오기

    Returns:
        str: API Token
    """
    try:
        # Notebook context에서 토큰 가져오기
        token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
        return token
    except Exception as e:
        print(f"⚠️  Context에서 토큰을 가져올 수 없습니다: {e}")
        print(f"   대안: Personal Access Token을 직접 입력하세요")
        return None

# 토큰 가져오기
api_token = get_databricks_token()

if api_token:
    print("✅ API Token 획득 성공")
    print(f"   Token 길이: {len(api_token)} 문자")
    print(f"   Token 시작: {api_token[:10]}...")
else:
    print("❌ API Token을 가져올 수 없습니다")
    print()
    print("대안: Personal Access Token 직접 입력")
    print("1. User Settings → Developer → Access Tokens")
    print("2. 'Generate New Token' 클릭")
    print("3. 아래 셀에 토큰 입력")

# COMMAND ----------

# 방법 2: Personal Access Token 직접 입력 (방법 1 실패 시)
# 보안상 실제 토큰은 입력하지 말고, Databricks Secrets 사용 권장

# PERSONAL_ACCESS_TOKEN = dbutils.secrets.get(scope="your-scope", key="your-key")
# api_token = PERSONAL_ACCESS_TOKEN

# 또는 임시 테스트용 (보안 주의!)
# api_token = "dapi..."  # 실제 토큰 입력 (커밋하지 말 것!)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Workspace URL 가져오기

# COMMAND ----------

# Workspace URL 가져오기
workspace_url = spark.conf.get("spark.databricks.workspaceUrl")

print(f"✅ Workspace URL: {workspace_url}")

# API Endpoint URL 구성
api_url = f"https://{workspace_url}/serving-endpoints/{KA_ENDPOINT_NAME}/invocations"

print(f"✅ API URL: {api_url}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: API 요청 헤더 구성 (올바른 형식)
# MAGIC
# MAGIC ### 🔑 중요: Authorization 헤더 형식
# MAGIC - 형식: `Bearer {token}` (Bearer 뒤에 공백 필수)
# MAGIC - Content-Type: `application/json`

# COMMAND ----------

# 올바른 헤더 구성
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

print("✅ 헤더 구성 완료:")
print(f"   Authorization: Bearer {api_token[:10]}...")
print(f"   Content-Type: application/json")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: 한글 질문 테스트 함수

# COMMAND ----------

def query_knowledge_assistant(question, debug=False):
    """
    Knowledge Assistant에 질문 전송

    Args:
        question (str): 한글 질문
        debug (bool): 디버그 모드

    Returns:
        dict: 응답 결과
    """
    try:
        # 요청 페이로드
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.1  # 낮은 temperature로 일관된 답변
        }

        if debug:
            print(f"🔍 Request URL: {api_url}")
            print(f"🔍 Headers: {headers}")
            print(f"🔍 Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            print()

        # API 호출
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=60
        )

        # 상태 코드 확인
        if debug:
            print(f"🔍 Response Status: {response.status_code}")
            print(f"🔍 Response Headers: {dict(response.headers)}")
            print()

        # 에러 처리
        if response.status_code != 200:
            error_detail = response.text
            return {
                "success": False,
                "error_code": response.status_code,
                "error_message": error_detail,
                "answer": None
            }

        # 성공 응답 파싱
        result = response.json()
        answer = result.get("choices", [{}])[0].get("message", {}).get("content", "")

        return {
            "success": True,
            "answer": answer,
            "raw_response": result
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Timeout: 요청 시간 초과 (60초)",
            "answer": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "answer": None
        }

print("✅ 쿼리 함수 준비 완료")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: 단일 질문 테스트 (디버그 모드)
# MAGIC
# MAGIC 먼저 하나의 질문으로 연결을 테스트합니다.

# COMMAND ----------

# 테스트 질문
test_question = "이 문서의 주요 내용은 무엇인가요?"

print("=" * 80)
print("🧪 Knowledge Assistant 연결 테스트")
print("=" * 80)
print()
print(f"❓ 질문: {test_question}")
print()
print("⏳ 답변 생성 중...")
print()

# API 호출 (디버그 모드)
result = query_knowledge_assistant(test_question, debug=True)

# 결과 출력
if result["success"]:
    print("=" * 80)
    print("✅ 성공!")
    print("=" * 80)
    print()
    print("💬 답변:")
    print("-" * 80)
    print(result["answer"])
    print("-" * 80)
else:
    print("=" * 80)
    print("❌ 실패")
    print("=" * 80)
    print()
    print(f"에러 코드: {result.get('error_code', 'N/A')}")
    print(f"에러 메시지: {result.get('error_message', result.get('error', 'Unknown'))}")
    print()

    # 401 에러인 경우 추가 안내
    if result.get('error_code') == 401:
        print("🔧 401 에러 해결 방법:")
        print()
        print("1. 토큰 확인:")
        print("   - Personal Access Token이 유효한지 확인")
        print("   - User Settings → Developer → Access Tokens")
        print()
        print("2. 권한 확인:")
        print("   - KA endpoint에 대한 접근 권한이 있는지 확인")
        print("   - Workspace 관리자에게 문의")
        print()
        print("3. Endpoint 이름 확인:")
        print(f"   - 현재 사용 중: {KA_ENDPOINT_NAME}")
        print("   - UI에서 정확한 이름 확인")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: 다중 질문 테스트 (연결 성공 시)
# MAGIC
# MAGIC 단일 질문 테스트가 성공하면 여러 질문으로 한글 성능을 평가합니다.

# COMMAND ----------

# 한글 테스트 질문 목록
TEST_QUESTIONS_KR = [
    "이 문서의 주요 내용은 무엇인가요?",
    "재무제표의 구성 요소를 설명해주세요",
    "당기순이익은 어떻게 계산하나요?",
    "유동자산과 비유동자산의 차이를 설명해주세요",
    "감가상각 방법에는 어떤 것들이 있나요?",
]

print("=" * 80)
print("🧪 Knowledge Assistant 한글 성능 테스트")
print("=" * 80)
print()

# 테스트 결과 저장
test_results = []

for i, question in enumerate(TEST_QUESTIONS_KR, 1):
    print(f"\n{'=' * 80}")
    print(f"질문 {i}/{len(TEST_QUESTIONS_KR)}")
    print('=' * 80)
    print(f"❓ {question}")
    print()

    # 질문 전송
    print("⏳ 답변 생성 중...")
    result = query_knowledge_assistant(question, debug=False)

    if result["success"]:
        answer = result["answer"]
        print()
        print("💬 답변:")
        print("-" * 80)
        print(answer)
        print("-" * 80)

        # 평가 기록
        test_results.append({
            "question": question,
            "answer": answer,
            "success": True
        })
    else:
        print(f"\n❌ 에러: {result.get('error', 'Unknown')}")
        test_results.append({
            "question": question,
            "answer": None,
            "success": False,
            "error": result.get("error", "Unknown")
        })

    print()

    # Rate limiting 방지
    import time
    time.sleep(2)

print("\n" + "=" * 80)
print("✅ 테스트 완료!")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 8: 결과 평가 및 요약

# COMMAND ----------

print("=" * 80)
print("📊 테스트 결과 요약")
print("=" * 80)
print()

success_count = sum(1 for r in test_results if r["success"])
total_count = len(test_results)

print(f"✅ 성공: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
print()

# 실패한 질문
failed = [r for r in test_results if not r["success"]]
if failed:
    print("❌ 실패한 질문:")
    for r in failed:
        print(f"  - {r['question']}")
        print(f"    에러: {r.get('error', 'Unknown')}")
    print()

# 평가 가이드
print("-" * 80)
print("📋 평가 체크리스트")
print("-" * 80)
print()
print("다음 항목을 확인하여 한글 성능을 평가하세요:")
print()
print("1. [ ] 한글 질문을 제대로 이해했는가?")
print("2. [ ] 관련 문서를 정확히 검색했는가?")
print("3. [ ] 한글 답변이 자연스러운가?")
print("4. [ ] 출처 문서를 명시했는가?")
print("5. [ ] 답변 내용이 정확한가?")
print()
print("-" * 80)
print()

# 의사결정 가이드
print("🎯 다음 단계 의사결정")
print()
print("평가 결과에 따라 다음 중 하나를 선택하세요:")
print()
print("✅ Option A: Knowledge Assistant 성능이 우수한 경우")
print("   → 현재 KA를 그대로 사용")
print("   → Voice App에 연동")
print("   → 예상 추가 시간: 1-2시간")
print()
print("⚠️ Option B: Knowledge Assistant 성능이 부족한 경우")
print("   → Custom RAG Pipeline 구현")
print("   → Qwen3 embedding 명시적 사용")
print("   → 청킹/검색 파라미터 튜닝")
print("   → 예상 추가 시간: 3-4시간")
print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔧 문제 해결 가이드
# MAGIC
# MAGIC ### 401 에러가 계속 발생하는 경우
# MAGIC
# MAGIC #### 해결 방법 1: Personal Access Token 재생성
# MAGIC ```
# MAGIC 1. User Settings → Developer → Access Tokens
# MAGIC 2. 기존 토큰 삭제
# MAGIC 3. "Generate New Token" 클릭
# MAGIC 4. Lifetime: 90 days (또는 원하는 기간)
# MAGIC 5. Comment: "NH Voice Agent PoC"
# MAGIC 6. 생성된 토큰을 안전하게 저장
# MAGIC 7. 위의 Step 2에서 토큰 직접 입력
# MAGIC ```
# MAGIC
# MAGIC #### 해결 방법 2: Databricks Secrets 사용 (권장)
# MAGIC ```python
# MAGIC # Secrets scope 생성 (Workspace 관리자)
# MAGIC # databricks secrets create-scope --scope nh-voice-agent
# MAGIC
# MAGIC # Secret 저장
# MAGIC # databricks secrets put --scope nh-voice-agent --key api-token
# MAGIC
# MAGIC # Notebook에서 사용
# MAGIC api_token = dbutils.secrets.get(scope="nh-voice-agent", key="api-token")
# MAGIC ```
# MAGIC
# MAGIC #### 해결 방법 3: Service Principal 사용 (프로덕션)
# MAGIC ```
# MAGIC 1. Service Principal 생성
# MAGIC 2. KA endpoint에 권한 부여
# MAGIC 3. OAuth 인증 사용
# MAGIC ```
# MAGIC
# MAGIC ### 권한 에러가 발생하는 경우
# MAGIC
# MAGIC ```sql
# MAGIC -- Workspace 관리자에게 권한 요청
# MAGIC GRANT USE ENDPOINT ON SERVING ENDPOINT ka-69e8398a-endpoint TO `your_user@email.com`;
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Notebook 완료**

# COMMAND ----------
