# Databricks notebook source
# MAGIC %md
# MAGIC # Knowledge Assistant API 호출 - 여러 방법 테스트
# MAGIC
# MAGIC ## 📋 목적
# MAGIC UI에서는 정상 작동하지만 Notebook API 호출에서 응답이 없는 문제 해결
# MAGIC
# MAGIC ### 테스트할 방법
# MAGIC 1. **Standard Model Serving API** - 기본 방식
# MAGIC 2. **OpenAI Compatible API** - 호환 방식 + 상세 디버깅
# MAGIC 3. **Databricks SDK** - 가장 권장 (안정적)
# MAGIC 4. **Bricks API** - UI가 사용하는 방식
# MAGIC
# MAGIC ---

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: 환경 설정

# COMMAND ----------

import requests
import json
import time

# KA 정보 (실제 값으로 변경)
KA_ENDPOINT_NAME = "ka-69e8398a-endpoint"
KA_TILE_ID = "69e8398a-b268-4732-b6cd-5c2b8051b349"

# 환경 설정
workspace_url = spark.conf.get("spark.databricks.workspaceUrl")
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

print("=" * 80)
print("환경 설정 완료")
print("=" * 80)
print(f"Workspace: {workspace_url}")
print(f"KA Endpoint: {KA_ENDPOINT_NAME}")
print(f"KA Tile ID: {KA_TILE_ID}")
print(f"Token: {token[:10]}...")
print()

# 공통 헤더
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 테스트 질문
test_question = "이 문서의 주요 내용은 무엇인가요?"

print(f"📝 테스트 질문: {test_question}")
print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 방법 1: Standard Model Serving API
# MAGIC
# MAGIC 표준 Model Serving endpoint 방식

# COMMAND ----------

print("=" * 80)
print("📌 방법 1: Standard Model Serving API")
print("=" * 80)
print()

url_v1 = f"https://{workspace_url}/serving-endpoints/{KA_ENDPOINT_NAME}/invocations"

payload_v1 = {
    "input": [
        {
            "role": "user",
            "content": test_question
        }
    ],
    "max_tokens": 500,
    "temperature": 0.1
}

print(f"URL: {url_v1}")
print(f"Method: POST")
print(f"Timeout: 120초")
print()

start_time = time.time()

try:
    print("⏳ 요청 전송 중...")

    response = requests.post(
        url_v1,
        json=payload_v1,
        headers=headers,
        timeout=120,
        stream=False
    )

    elapsed = time.time() - start_time

    print(f"✅ 응답 수신: {response.status_code} (소요: {elapsed:.1f}초)")
    print()

    if response.status_code == 200:
        result = response.json()

        # 답변 추출
        if "choices" in result and len(result["choices"]) > 0:
            answer = result["choices"][0]["message"]["content"]
            print("💬 답변:")
            print("=" * 80)
            print(answer)
            print("=" * 80)
            print()
            print("✅ 방법 1 성공!")
        else:
            print("⚠️  응답 형식이 예상과 다릅니다")
            print("응답 구조:")
            for key in result.keys():
                print(f"  - {key}: {type(result[key])}")
            print()
            print("전체 응답 (처음 500자):")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
    else:
        print(f"❌ HTTP 에러: {response.status_code}")
        print(response.text[:500])

except requests.exceptions.Timeout:
    elapsed = time.time() - start_time
    print(f"❌ Timeout: {elapsed:.1f}초 후 응답 없음")
    print()
    print("가능한 원인:")
    print("- KA의 첫 호출 (워밍업 필요)")
    print("- 리소스 부족")
    print("- 문서 크기 큰 경우")

except Exception as e:
    elapsed = time.time() - start_time
    print(f"❌ 예외 발생 ({elapsed:.1f}초 후): {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 방법 2: OpenAI Compatible API (상세 디버깅)
# MAGIC
# MAGIC OpenAI 형식의 Chat Completions API + 상세한 디버깅 정보

# COMMAND ----------

print("=" * 80)
print("📌 방법 2: OpenAI Compatible API (상세 디버깅)")
print("=" * 80)
print()

url_v2 = f"https://{workspace_url}/serving-endpoints/{KA_ENDPOINT_NAME}/invocations"

payload_v2 = {
    "input": [
        {"role": "user", "content": test_question}
    ],
    "temperature": 0.1,
    "max_tokens": 500,
    "top_p": 0.95,
    "n": 1
}

print(f"URL: {url_v2}")
print(f"Payload:")
print(json.dumps(payload_v2, ensure_ascii=False, indent=2))
print()

start_time = time.time()

try:
    print("⏳ 요청 전송 중...")

    response = requests.post(
        url_v2,
        headers=headers,
        json=payload_v2,
        timeout=120
    )

    elapsed = time.time() - start_time

    print(f"✅ 응답 수신: {response.status_code} (소요: {elapsed:.1f}초)")
    print(f"   Content-Type: {response.headers.get('content-type')}")
    print(f"   Content-Length: {response.headers.get('content-length')} bytes")
    print()

    if response.status_code == 200:
        response_text = response.text
        print(f"응답 본문 길이: {len(response_text)} bytes")
        print()

        try:
            result = response.json()

            # 응답 구조 분석
            print("응답 구조:")
            for key in result.keys():
                print(f"  - {key}: {type(result[key])}")
            print()

            # 답변 추출
            if "choices" in result and len(result["choices"]) > 0:
                answer = result["choices"][0]["message"]["content"]
                print("💬 답변:")
                print("=" * 80)
                print(answer)
                print("=" * 80)
                print()
                print("✅ 방법 2 성공!")
            else:
                print("⚠️  'choices' 키가 없거나 비어있음")
                print("전체 응답:")
                print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])

        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            print(f"응답 내용 (처음 500자):")
            print(response_text[:500])
    else:
        print(f"❌ HTTP 에러: {response.status_code}")
        print(response.text[:500])

except requests.exceptions.Timeout:
    elapsed = time.time() - start_time
    print(f"❌ Timeout: {elapsed:.1f}초 후 응답 없음")

except Exception as e:
    elapsed = time.time() - start_time
    print(f"❌ 예외 발생 ({elapsed:.1f}초 후): {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 방법 3: Databricks SDK (권장)
# MAGIC
# MAGIC Databricks Python SDK를 사용한 가장 안정적인 방법

# COMMAND ----------

print("=" * 80)
print("📌 방법 3: Databricks SDK (권장)")
print("=" * 80)
print()

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

client = WorkspaceClient()

print(f"SDK Endpoint: {KA_ENDPOINT_NAME}")
print()

start_time = time.time()

try:
    print("⏳ SDK를 통한 쿼리 전송...")

    # SDK query
    response = client.serving_endpoints.query(
        name=KA_ENDPOINT_NAME,
        messages=[
            ChatMessage(
                role=ChatMessageRole.USER,
                content=test_question
            )
        ],
        max_tokens=500,
        temperature=0.1
    )

    elapsed = time.time() - start_time

    print(f"✅ 응답 수신 (소요: {elapsed:.1f}초)")
    print()

    # 응답 구조 확인
    print("응답 타입:", type(response))
    print("응답 속성:", [attr for attr in dir(response) if not attr.startswith('_')][:10])
    print()

    # 답변 추출
    if hasattr(response, 'choices') and response.choices:
        answer = response.choices[0].message.content
        print("💬 답변:")
        print("=" * 80)
        print(answer)
        print("=" * 80)
        print()
        print("✅ 방법 3 성공! (SDK 방식 - 가장 권장)")

        # 추가 정보
        if hasattr(response, 'usage'):
            print()
            print("사용량 정보:")
            print(f"  Prompt tokens: {response.usage.prompt_tokens}")
            print(f"  Completion tokens: {response.usage.completion_tokens}")
            print(f"  Total tokens: {response.usage.total_tokens}")
    else:
        print("⚠️  예상과 다른 응답 형식")
        print("응답 전체:")
        print(response)

except Exception as e:
    elapsed = time.time() - start_time
    print(f"❌ SDK 에러 ({elapsed:.1f}초 후): {e}")
    print()
    print("상세 정보:")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 방법 4: Bricks API (UI 방식)
# MAGIC
# MAGIC Databricks UI가 사용하는 Bricks API를 직접 호출

# COMMAND ----------

print("=" * 80)
print("📌 방법 4: Bricks API (UI 방식)")
print("=" * 80)
print()

# Bricks API endpoint
url_bricks = f"https://{workspace_url}/api/2.0/bricks/tiles/{KA_TILE_ID}/query"

payload_bricks = {
    "input": [
        {
            "role": "user",
            "content": test_question
        }
    ]
}

print(f"URL: {url_bricks}")
print(f"Tile ID: {KA_TILE_ID}")
print()

start_time = time.time()

try:
    print("⏳ Bricks API 호출 중...")

    response = requests.post(
        url_bricks,
        headers=headers,
        json=payload_bricks,
        timeout=120
    )

    elapsed = time.time() - start_time

    print(f"✅ 응답 수신: {response.status_code} (소요: {elapsed:.1f}초)")
    print()

    if response.status_code == 200:
        result = response.json()

        print("응답 구조:")
        for key in result.keys():
            print(f"  - {key}: {type(result[key])}")
        print()

        # 다양한 응답 형식 시도
        answer = None

        if "answer" in result:
            answer = result["answer"]
        elif "choices" in result and len(result["choices"]) > 0:
            answer = result["choices"][0]["message"]["content"]
        elif "response" in result:
            answer = result["response"]

        if answer:
            print("💬 답변:")
            print("=" * 80)
            print(answer)
            print("=" * 80)
            print()
            print("✅ 방법 4 성공! (Bricks API - UI와 동일)")
        else:
            print("⚠️  답변을 찾을 수 없음")
            print("전체 응답:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:1000])
    else:
        print(f"❌ HTTP 에러: {response.status_code}")
        print(response.text[:500])

except Exception as e:
    elapsed = time.time() - start_time
    print(f"❌ 에러 ({elapsed:.1f}초 후): {e}")
    import traceback
    traceback.print_exc()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 결과 요약 및 권장사항

# COMMAND ----------

print("=" * 80)
print("📊 테스트 결과 요약")
print("=" * 80)
print()

print("위의 4가지 방법 중 성공한 방법을 확인하세요:")
print()
print("✅ 방법 1 (Standard API) - 표준 방식")
print("✅ 방법 2 (OpenAI API) - 호환 방식")
print("✅ 방법 3 (Databricks SDK) - 가장 권장 ⭐")
print("✅ 방법 4 (Bricks API) - UI 방식")
print()
print("-" * 80)
print()

print("💡 권장사항:")
print()
print("1. 방법 3 (SDK)이 성공했다면:")
print("   → 이후 모든 코드에서 SDK 방식 사용")
print("   → 가장 안정적이고 유지보수 용이")
print()
print("2. 방법 4 (Bricks API)만 성공했다면:")
print("   → UI 전용 API일 가능성")
print("   → Tile ID를 사용한 호출 필요")
print()
print("3. 모두 실패했다면:")
print("   → KA endpoint 권한 확인")
print("   → Workspace 관리자에게 문의")
print("   → Personal Access Token 재생성")
print()

print("=" * 80)
print("다음 단계:")
print("=" * 80)
print()
print("성공한 방법을 02a_Knowledge_Assistant_Setup.py에 적용")
print()

# COMMAND ----------

# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC **Notebook 완료**
# MAGIC
# MAGIC 성공한 방법을 기록하고 이후 코드에 적용하세요!

# COMMAND ----------
