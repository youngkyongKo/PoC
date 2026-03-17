# Databricks notebook source
# MAGIC %md
# MAGIC # Knowledge Assistant 테스트 - NH Voice Agent
# MAGIC
# MAGIC ## 📋 목적
# MAGIC Knowledge Assistant를 사용하여 한글 문서 검색 및 답변 생성을 테스트합니다.
# MAGIC
# MAGIC ### 테스트 질문
# MAGIC 1. 회사 홈페이지 URL은?
# MAGIC 2. 보험계약을 중도 해지시 해지환급금은 이미 납입한 보험료보다 적거나 없는 경우, 이유는?
# MAGIC
# MAGIC ### 사전 요구사항
# MAGIC - Knowledge Assistant 생성 완료 (Endpoint: ONLINE 상태)
# MAGIC - PDF 문서 업로드 완료
# MAGIC - KA_ENDPOINT_NAME 설정 완료

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: 환경 설정 및 KA Endpoint 확인

# COMMAND ----------

from databricks.sdk import WorkspaceClient
import requests
import json
import time

# SDK 초기화
client = WorkspaceClient()

# KA Endpoint 이름 (실제 이름으로 변경)
KA_ENDPOINT_NAME = "ka-69e8398a-endpoint"

print("=" * 80)
print("Knowledge Assistant 테스트")
print("=" * 80)
print()

# Endpoint 상태 확인
try:
    endpoint = client.serving_endpoints.get(KA_ENDPOINT_NAME)
    status = endpoint.state.ready if endpoint.state else "UNKNOWN"

    print(f"✅ Endpoint: {KA_ENDPOINT_NAME}")
    print(f"   상태: {status}")
    print()

    if status != "READY":
        print("⚠️  Endpoint가 READY 상태가 아닙니다.")
        print(f"   현재 상태: {status}")
        print("   READY 상태가 될 때까지 기다려주세요.")

except Exception as e:
    print(f"❌ Endpoint 조회 실패: {e}")
    print(f"   Endpoint 이름을 확인하세요: {KA_ENDPOINT_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: API 호출 함수 정의

# COMMAND ----------

def query_knowledge_assistant(endpoint_name, question, debug=False):
    """
    Knowledge Assistant에 질문 전송

    Args:
        endpoint_name: KA endpoint 이름
        question: 질문 텍스트
        debug: 디버그 모드

    Returns:
        dict: 응답 결과
    """
    try:
        # Workspace URL과 Token 가져오기
        workspace_url = spark.conf.get("spark.databricks.workspaceUrl")
        token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

        # Serving Endpoints REST API
        # KA endpoint는 REST API로 호출해도 RAG 기능이 유지됩니다
        url = f"https://{workspace_url}/serving-endpoints/{endpoint_name}/invocations"

        # 요청 페이로드
        payload = {
            "input": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        }

        # 헤더
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        if debug:
            print(f"🔍 Request URL: {url}")
            print(f"🔍 Endpoint: {endpoint_name}")
            print(f"🔍 Question: {question}")
            print()

        # API 호출
        response = requests.post(url, json=payload, headers=headers, timeout=60)

        if debug:
            print(f"🔍 Response Status: {response.status_code}")
            print()

        # 에러 처리
        if response.status_code != 200:
            return {
                "success": False,
                "error_code": response.status_code,
                "error_message": response.text,
                "answer": None
            }

        result = response.json()

        # 답변 추출 (다양한 형식 지원)
        answer = None

        # 시도 1: output[0].content[0].text
        if "output" in result and len(result["output"]) > 0:
            output = result["output"][0]
            if isinstance(output, dict) and "content" in output:
                content_list = output["content"]
                if isinstance(content_list, list) and len(content_list) > 0:
                    content_item = content_list[0]
                    if isinstance(content_item, dict) and "text" in content_item:
                        answer = content_item["text"]

        # 시도 2: choices[0].message.content
        if not answer and "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if isinstance(choice, dict):
                if "message" in choice and "content" in choice["message"]:
                    answer = choice["message"]["content"]

        # 시도 3: 기타 형식
        if not answer:
            for key in ["answer", "content", "response"]:
                if key in result:
                    answer = result[key]
                    break

        # RAG 소스 사용 여부 확인
        sources_used = False
        if "custom_outputs" in result and isinstance(result["custom_outputs"], dict):
            sources_used = result["custom_outputs"].get("sources_used", False)

        return {
            "success": True,
            "answer": answer if answer else "",
            "sources_used": sources_used,
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
# MAGIC ## Step 3: 빠른 연결 테스트
# MAGIC
# MAGIC 먼저 간단한 질문으로 연결을 확인합니다.

# COMMAND ----------

print("=" * 80)
print("🔍 빠른 연결 테스트")
print("=" * 80)
print()

test_question = "안녕하세요. 이 문서에 대해 간단히 설명해주세요."

print(f"❓ 테스트 질문: {test_question}")
print()
print("⏳ 답변 생성 중...")
print()

# 디버그 모드로 실행
result = query_knowledge_assistant(KA_ENDPOINT_NAME, test_question, debug=True)

print("=" * 80)

if result["success"]:
    print("✅ 연결 성공!")
    print("=" * 80)
    print()

    sources_used = result.get("sources_used", False)
    if sources_used:
        print("✅ RAG 검색 활성화: 문서에서 정보를 찾았습니다.")
    else:
        print("⚠️  RAG 검색 비활성화: 문서 검색이 수행되지 않았습니다.")
    print()

    print("💬 답변:")
    print("-" * 80)
    print(result["answer"])
    print("-" * 80)

else:
    print("❌ 연결 실패")
    print("=" * 80)
    print()

    if "error_code" in result:
        print(f"HTTP 상태 코드: {result['error_code']}")
        print(f"에러 메시지: {result.get('error_message', 'Unknown')}")
    else:
        print(f"에러: {result.get('error', 'Unknown')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: NH생명 보험 관련 질문 테스트
# MAGIC
# MAGIC 실제 문서 내용에 대한 질문으로 테스트합니다.

# COMMAND ----------

# 테스트 질문 목록
TEST_QUESTIONS_KR = [
    "회사 홈페이지 URL은?",
    "보험계약을 중도 해지시 해지환급금은 이미 납입한 보험료보다 적거나 없는 경우, 이유는?",
]

print("=" * 80)
print("🧪 Knowledge Assistant 한글 질문 테스트")
print("=" * 80)
print()

# 테스트 결과 저장
test_results = []

for i, question in enumerate(TEST_QUESTIONS_KR, 1):
    print(f"\n{'=' * 80}")
    print(f"질문 {i}/{len(TEST_QUESTIONS_KR)}")
    print(f"{'=' * 80}")
    print(f"❓ {question}")
    print()

    # 질문 전송
    print("⏳ 답변 생성 중...")
    result = query_knowledge_assistant(KA_ENDPOINT_NAME, question, debug=False)

    if result["success"]:
        answer = result["answer"]
        sources_used = result.get("sources_used", False)

        print()
        if sources_used:
            print("✅ 문서 검색 사용됨")
        else:
            print("⚠️  문서 검색 안됨")

        print()
        print("💬 답변:")
        print("-" * 80)
        print(answer if answer else "(답변이 비어있습니다)")
        print("-" * 80)

        # 결과 저장
        test_results.append({
            "question": question,
            "answer": answer,
            "sources_used": sources_used,
            "success": True
        })

    else:
        print(f"\n❌ 에러 발생")

        if "error_code" in result:
            print(f"   HTTP 상태 코드: {result['error_code']}")
            print(f"   에러 메시지: {result.get('error_message', 'Unknown')}")
        else:
            print(f"   에러: {result.get('error', 'Unknown')}")

        test_results.append({
            "question": question,
            "answer": None,
            "sources_used": False,
            "success": False,
            "error": result.get("error", "Unknown")
        })

    print()
    time.sleep(2)  # Rate limiting 방지

print("\n" + "=" * 80)
print("✅ 테스트 완료!")
print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: 결과 요약 및 평가

# COMMAND ----------

print("=" * 80)
print("📊 테스트 결과 요약")
print("=" * 80)
print()

success_count = sum(1 for r in test_results if r["success"])
total_count = len(test_results)
rag_used_count = sum(1 for r in test_results if r.get("sources_used", False))

print(f"✅ 성공: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
print(f"📚 RAG 검색 사용: {rag_used_count}/{success_count}")
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
print("다음 항목을 확인하여 성능을 평가하세요:")
print()
print("1. [ ] 한글 질문을 제대로 이해했는가?")
print("2. [ ] 관련 문서를 정확히 검색했는가? (sources_used=True)")
print("3. [ ] 한글 답변이 자연스러운가?")
print("4. [ ] 답변 내용이 정확한가?")
print("5. [ ] 답변 속도가 적절한가? (60초 이내)")
print()

# 각 질문별 세부 결과
print("-" * 80)
print("📝 질문별 세부 결과")
print("-" * 80)
print()

for i, result in enumerate(test_results, 1):
    print(f"{i}. {result['question']}")
    print(f"   상태: {'✅ 성공' if result['success'] else '❌ 실패'}")
    print(f"   RAG 검색: {'✅ 사용됨' if result.get('sources_used') else '❌ 사용 안됨'}")

    if result['success']:
        answer = result['answer']
        answer_preview = answer[:100] + "..." if len(answer) > 100 else answer
        print(f"   답변 미리보기: {answer_preview}")
    else:
        print(f"   에러: {result.get('error', 'Unknown')}")
    print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🎯 다음 단계
# MAGIC
# MAGIC ### ✅ Knowledge Assistant가 잘 작동하는 경우
# MAGIC - Supervisor Agent에 통합
# MAGIC - Voice App 연동 시작
# MAGIC - 추가 질문 테스트
# MAGIC
# MAGIC ### ⚠️ 문제가 있는 경우
# MAGIC
# MAGIC **RAG 검색이 작동하지 않는 경우 (sources_used=False)**:
# MAGIC - ajax-serving-endpoints 사용 확인
# MAGIC - Volume에 문서가 업로드되었는지 확인
# MAGIC - KA가 문서를 인덱싱했는지 확인 (생성 후 충분한 시간 경과)
# MAGIC
# MAGIC **답변 품질이 낮은 경우**:
# MAGIC - KA Instructions 개선
# MAGIC - 문서 품질 확인 (OCR 필요 여부)
# MAGIC - 청킹 전략 조정
# MAGIC
# MAGIC **인증 에러 (401)**:
# MAGIC - Personal Access Token 확인
# MAGIC - Endpoint 권한 확인
# MAGIC - Databricks Workspace에서 실행 중인지 확인

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC **Notebook 완료**
# MAGIC
# MAGIC 결과를 확인하고 다음 단계로 진행하세요.
