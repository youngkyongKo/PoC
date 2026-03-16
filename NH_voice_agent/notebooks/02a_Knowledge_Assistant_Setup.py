# Databricks notebook source
# MAGIC %md
# MAGIC # Knowledge Assistant 생성 및 테스트 - NH Voice Agent PoC
# MAGIC
# MAGIC ## 📋 목적
# MAGIC 이 노트북은 Databricks Knowledge Assistant(KA)를 사용하여 RAG 시스템을 구축하고, 한글 성능을 테스트합니다.
# MAGIC
# MAGIC ### 수행 작업
# MAGIC 1. **한글 PDF 준비 및 업로드**
# MAGIC 2. **Knowledge Assistant 생성** (UI 또는 API)
# MAGIC 3. **프로비저닝 대기** (2-5분)
# MAGIC 4. **한글 질문으로 성능 테스트**
# MAGIC 5. **결과 평가 및 의사결정**
# MAGIC
# MAGIC ### 예상 소요 시간
# MAGIC - 약 1-2시간 (PDF 준비 + 생성 + 테스트)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## ⚠️ 사전 요구사항
# MAGIC - `01_Setup_Unity_Catalog.py` 노트북 완료
# MAGIC - Unity Catalog Volume: `/Volumes/main/nh_voice_agent/documents`
# MAGIC - 한글 PDF 문서 2-3개 (재무제표, 회계 규정 등)
# MAGIC
# MAGIC ---

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🎯 Knowledge Assistant란?
# MAGIC
# MAGIC Databricks Knowledge Assistant는 **자동화된 RAG 시스템**입니다:
# MAGIC
# MAGIC | 특징 | 설명 |
# MAGIC |------|------|
# MAGIC | **자동 인덱싱** | Volume의 문서를 자동으로 임베딩 및 인덱싱 |
# MAGIC | **빠른 구축** | 코드 없이 2-5분 내 프로비저닝 |
# MAGIC | **관리 용이** | UI에서 손쉬운 생성/업데이트 |
# MAGIC | **통합** | Supervisor Agent에 바로 연결 가능 |
# MAGIC
# MAGIC ### 🔍 한글 지원 검증
# MAGIC - Knowledge Assistant의 기본 embedding 모델 성능 확인
# MAGIC - 한글 질문 → 한글 문서 검색 → 한글 답변 생성
# MAGIC - **이번 노트북의 핵심 목표**: 한글 성능 평가

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: 환경 설정 및 확인

# COMMAND ----------

from databricks.sdk import WorkspaceClient
import time
from datetime import datetime

# Databricks SDK 초기화
client = WorkspaceClient()

# Unity Catalog 경로
CATALOG = "demo_ykko"
SCHEMA = "nh_voice_agent"
VOLUME = "documents"
VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"

print("=" * 60)
print("✅ 환경 설정")
print("=" * 60)
print(f"Catalog: {CATALOG}")
print(f"Schema: {SCHEMA}")
print(f"Volume Path: {VOLUME_PATH}")
print()

# COMMAND ----------

# Volume 상태 확인
print("📁 현재 Volume 파일 목록:")
print()

files = dbutils.fs.ls(VOLUME_PATH)

if not files:
    print("⚠️  Volume이 비어있습니다!")
    print("   한글 PDF 파일을 업로드해주세요.")
else:
    print(f"총 {len(files)}개 파일:")
    for file in files:
        file_type = "📄 PDF" if file.name.endswith('.pdf') else "📝 기타"
        size_mb = file.size / (1024 * 1024)
        print(f"  {file_type} {file.name} ({size_mb:.2f} MB)")
print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: 한글 PDF 업로드
# MAGIC
# MAGIC ### 📤 업로드 방법 (3가지)
# MAGIC
# MAGIC #### 방법 1: Databricks UI (권장 - 가장 쉬움)
# MAGIC ```
# MAGIC 1. 좌측 메뉴 → Data → Volumes
# MAGIC 2. main → nh_voice_agent → documents 클릭
# MAGIC 3. "Upload" 버튼 클릭
# MAGIC 4. PDF 파일 선택 (드래그 앤 드롭 가능)
# MAGIC ```
# MAGIC
# MAGIC #### 방법 2: dbutils.fs.cp (로컬 파일)
# MAGIC ```python
# MAGIC # 아래 셀에서 파일 경로 수정 후 실행
# MAGIC ```
# MAGIC
# MAGIC #### 방법 3: curl/wget (URL에서 다운로드)
# MAGIC ```python
# MAGIC # 공개 URL에서 다운로드하는 경우
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 📋 추천 샘플 PDF
# MAGIC - 재무제표 (2-3 페이지)
# MAGIC - 회계 규정 문서 (5-10 페이지)
# MAGIC - 사업 보고서 (3-5 페이지)
# MAGIC
# MAGIC **중요**: 한글 텍스트가 포함된 PDF를 사용하세요!

# COMMAND ----------

# 방법 2: 로컬 파일 업로드 예시
# 로컬 파일 경로를 수정하여 사용하세요

# 예시 (실제 경로로 수정 필요)
LOCAL_PDF_PATHS = [
    # "/dbfs/tmp/sample1.pdf",
    # "/dbfs/tmp/재무제표_샘플.pdf",
    # "/dbfs/tmp/회계규정.pdf",
]

# 업로드 실행
for local_path in LOCAL_PDF_PATHS:
    try:
        filename = local_path.split("/")[-1]
        dest_path = f"{VOLUME_PATH}/{filename}"

        dbutils.fs.cp(f"file:{local_path}", dest_path)
        print(f"✅ 업로드 완료: {filename}")
    except Exception as e:
        print(f"❌ 업로드 실패 ({filename}): {e}")

print()
print("💡 UI를 사용하는 경우 위 코드는 건너뛰세요.")

# COMMAND ----------

# 업로드 후 재확인
print("📁 업로드 후 Volume 파일 목록:")
print()

files = dbutils.fs.ls(VOLUME_PATH)
pdf_files = [f for f in files if f.name.endswith('.pdf')]

print(f"총 PDF 파일: {len(pdf_files)}개")
for file in pdf_files:
    size_mb = file.size / (1024 * 1024)
    print(f"  📄 {file.name} ({size_mb:.2f} MB)")

if len(pdf_files) == 0:
    print()
    print("⚠️  PDF 파일이 없습니다!")
    print("   위의 방법을 사용하여 PDF를 업로드한 후 다음 단계로 진행하세요.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Knowledge Assistant 생성
# MAGIC
# MAGIC ### 🎯 생성 방법 (2가지)
# MAGIC
# MAGIC #### 방법 1: Databricks UI (권장 ⭐)
# MAGIC
# MAGIC 1. **좌측 메뉴** → **Machine Learning** → **Agent Bricks**
# MAGIC 2. **"Create Agent Brick"** 버튼 클릭
# MAGIC 3. **"Knowledge Assistant"** 선택
# MAGIC 4. 설정 입력:
# MAGIC    - **Name**: `NH_Financial_Assistant`
# MAGIC    - **Description**: `재무제표 및 회계 규정 질의응답 시스템`
# MAGIC    - **Volume Path**: `/Volumes/main/nh_voice_agent/documents`
# MAGIC    - **Instructions** (선택사항):
# MAGIC      ```
# MAGIC      당신은 재무 및 회계 전문가입니다.
# MAGIC      질문에 답할 때:
# MAGIC      1. 항상 출처 문서를 명시하세요
# MAGIC      2. 정확한 숫자와 사실만 제공하세요
# MAGIC      3. 불확실한 경우 명확히 말하세요
# MAGIC      4. 한글로 친절하게 답변하세요
# MAGIC      ```
# MAGIC 5. **"Create"** 버튼 클릭
# MAGIC 6. **프로비저닝 대기** (2-5분)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### 방법 2: API 사용 (고급)
# MAGIC
# MAGIC 아래 셀에서 코드 실행 (현재는 UI 사용 권장)

# COMMAND ----------

# 방법 2: API를 통한 KA 생성 (고급 사용자용)
# 현재 Databricks SDK에는 Agent Bricks 직접 생성 API가 제한적입니다.
# UI 사용을 권장하지만, 향후 API가 제공되면 아래 형식으로 사용 가능:

# from databricks.sdk.service.serving import EndpointCoreConfigInput, ServedEntityInput
#
# # Knowledge Assistant 설정
# KA_NAME = "NH_Financial_Assistant"
# KA_CONFIG = {
#     "name": KA_NAME,
#     "volume_path": VOLUME_PATH,
#     "description": "재무제표 및 회계 규정 질의응답 시스템",
#     "instructions": """
#     당신은 재무 및 회계 전문가입니다.
#     질문에 답할 때:
#     1. 항상 출처 문서를 명시하세요
#     2. 정확한 숫자와 사실만 제공하세요
#     3. 불확실한 경우 명확히 말하세요
#     4. 한글로 친절하게 답변하세요
#     """
# }
#
# print("KA 설정:")
# print(KA_CONFIG)

print("💡 현재는 UI를 통한 생성을 권장합니다.")
print("   위의 '방법 1' 단계를 따라 진행하세요.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Knowledge Assistant 확인
# MAGIC
# MAGIC UI에서 KA를 생성한 후, 여기서 상태를 확인합니다.

# COMMAND ----------

# KA endpoint 찾기
# Knowledge Assistant는 "ka-{tile_id}-endpoint" 형식의 이름을 가집니다

print("🔍 Knowledge Assistant endpoint 검색 중...")
print()

ka_endpoints = []
for endpoint in client.serving_endpoints.list():
    if endpoint.name.startswith("ka-") and endpoint.name.endswith("-endpoint"):
        ka_endpoints.append(endpoint)

if not ka_endpoints:
    print("⚠️  Knowledge Assistant를 찾을 수 없습니다.")
    print("   UI에서 KA를 생성한 후 이 셀을 다시 실행하세요.")
else:
    print(f"✅ {len(ka_endpoints)}개의 Knowledge Assistant 발견:")
    print()

    for endpoint in ka_endpoints:
        print(f"📌 {endpoint.name}")
        print(f"   상태: {endpoint.state.ready if endpoint.state else 'N/A'}")
        print(f"   생성 시간: {endpoint.creation_timestamp}")

        # 태그에서 KA 이름 찾기
        if endpoint.tags:
            for tag in endpoint.tags:
                if tag.key == "DatabricksAgentName":
                    print(f"   이름: {tag.value}")
        print()

# COMMAND ----------

# 특정 KA endpoint 선택
# 위 결과에서 최신 KA 또는 원하는 KA의 이름을 입력하세요

# 예시: 가장 최근에 생성된 KA 선택
if ka_endpoints:
    # 생성 시간 기준 최신순 정렬
    ka_endpoints_sorted = sorted(
        ka_endpoints,
        key=lambda x: x.creation_timestamp if x.creation_timestamp else 0,
        reverse=True
    )

    selected_ka = ka_endpoints_sorted[0]
    KA_ENDPOINT_NAME = selected_ka.name

    print("=" * 60)
    print("✅ 선택된 Knowledge Assistant")
    print("=" * 60)
    print(f"Endpoint: {KA_ENDPOINT_NAME}")
    print(f"상태: {selected_ka.state.ready if selected_ka.state else 'N/A'}")
    print()

    # 상태에 따른 안내
    if selected_ka.state and selected_ka.state.ready == "READY":
        print("🟢 READY: 테스트 준비 완료!")
    elif selected_ka.state and "PROVISIONING" in str(selected_ka.state.ready):
        print("🟡 PROVISIONING: 프로비저닝 중... (2-5분 소요)")
        print("   잠시 후 다시 확인하세요.")
    else:
        print(f"🔴 상태: {selected_ka.state.ready if selected_ka.state else 'UNKNOWN'}")
        print("   문제가 있을 수 있습니다.")
else:
    print("❌ Knowledge Assistant가 없습니다.")
    print("   먼저 UI에서 KA를 생성하세요.")
    KA_ENDPOINT_NAME = None

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: 프로비저닝 대기
# MAGIC
# MAGIC KA가 `PROVISIONING` 상태인 경우 `READY`가 될 때까지 대기합니다.
# MAGIC
# MAGIC ### ⏱️ 예상 시간
# MAGIC - 일반적으로 2-5분 소요
# MAGIC - 최대 10분까지 걸릴 수 있음

# COMMAND ----------

def wait_for_ka_ready(endpoint_name, max_wait_minutes=10):
    """
    KA endpoint가 READY 상태가 될 때까지 대기

    Args:
        endpoint_name: KA endpoint 이름
        max_wait_minutes: 최대 대기 시간 (분)

    Returns:
        bool: READY 상태가 되면 True, 타임아웃이면 False
    """
    print(f"⏳ {endpoint_name} 프로비저닝 대기 중...")
    print(f"   최대 대기 시간: {max_wait_minutes}분")
    print()

    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    check_interval = 30  # 30초마다 확인

    while True:
        elapsed = time.time() - start_time

        if elapsed > max_wait_seconds:
            print(f"❌ 타임아웃: {max_wait_minutes}분 초과")
            return False

        # 상태 확인
        try:
            endpoint = client.serving_endpoints.get(endpoint_name)
            status = endpoint.state.ready if endpoint.state else "UNKNOWN"

            elapsed_min = elapsed / 60
            print(f"[{elapsed_min:.1f}분] 상태: {status}")

            if status == "READY":
                print()
                print("✅ 프로비저닝 완료! READY 상태입니다.")
                return True

            # 대기
            time.sleep(check_interval)

        except Exception as e:
            print(f"❌ 에러: {e}")
            return False

# 실행
if KA_ENDPOINT_NAME:
    is_ready = wait_for_ka_ready(KA_ENDPOINT_NAME, max_wait_minutes=10)

    if not is_ready:
        print()
        print("⚠️  프로비저닝이 완료되지 않았습니다.")
        print("   나중에 다시 확인하거나 Databricks 관리자에게 문의하세요.")
else:
    print("❌ KA endpoint가 선택되지 않았습니다.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: 한글 성능 테스트
# MAGIC
# MAGIC Knowledge Assistant에 한글 질문을 보내고 답변 품질을 평가합니다.
# MAGIC
# MAGIC ### 🎯 평가 기준
# MAGIC 1. **검색 정확도**: 관련 문서를 잘 찾는가?
# MAGIC 2. **답변 품질**: 한글 답변이 자연스러운가?
# MAGIC 3. **출처 표시**: 어떤 문서에서 가져왔는지 명시하는가?
# MAGIC 4. **한글 처리**: 한글 텍스트를 제대로 이해하는가?

# COMMAND ----------

# 한글 테스트 질문 준비
TEST_QUESTIONS_KR = [
    # 재무제표 관련
    "재무제표의 주요 구성 요소는 무엇인가요?",
    "당기순이익은 어떻게 계산하나요?",
    "유동자산과 비유동자산의 차이를 설명해주세요",

    # 회계 규정 관련
    "감가상각 방법에는 어떤 것들이 있나요?",
    "회계 처리 기준은 무엇인가요?",

    # 일반적인 질문
    "이 문서에서 다루는 주요 내용은 무엇인가요?",
]

print("📝 테스트 질문 목록:")
for i, q in enumerate(TEST_QUESTIONS_KR, 1):
    print(f"  {i}. {q}")
print()

# COMMAND ----------

def query_ka_endpoint(endpoint_name, question, debug=False):
    """
    Knowledge Assistant endpoint에 질문 전송

    Args:
        endpoint_name: KA endpoint 이름
        question: 질문 텍스트
        debug: 디버그 모드 (상세 출력)

    Returns:
        dict: 응답 결과
    """
    try:
        # Databricks Model Serving API 호출
        # KA는 OpenAI compatible endpoint를 제공합니다
        import requests
        import json
        import os

        # Databricks workspace URL과 token 가져오기
        workspace_url = spark.conf.get("spark.databricks.workspaceUrl")
        token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

        # API endpoint URL
        url = f"https://{workspace_url}/serving-endpoints/{endpoint_name}/invocations"

        # 요청 페이로드
        payload = {
            "input": [
                {
                    "role": "user",
                    "content": question
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.1  # 낮은 temperature로 일관된 답변
        }

        # 헤더
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        if debug:
            print(f"🔍 Request URL: {url}")
            print(f"🔍 Headers: Authorization: Bearer {token[:10]}...")
            print(f"🔍 Payload: {payload}")
            print()

        # API 호출
        response = requests.post(url, json=payload, headers=headers, timeout=60)

        if debug:
            print(f"🔍 Response Status: {response.status_code}")
            print(f"🔍 Response Headers: {dict(response.headers)}")
            print()

        # 상태 코드 확인
        if response.status_code != 200:
            error_detail = response.text
            return {
                "success": False,
                "error_code": response.status_code,
                "error_message": error_detail,
                "answer": None,
                "debug_info": {
                    "url": url,
                    "endpoint": endpoint_name,
                    "token_prefix": token[:10] if token else "None"
                }
            }

        result = response.json()

        if debug:
            print(f"🔍 Response keys: {list(result.keys())}")
            print(f"🔍 Full Response: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
            print()

        # 다양한 응답 형식 시도
        answer = None

        # 시도 1: choices[0].message.content (OpenAI 형식)
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if isinstance(choice, dict):
                if "message" in choice and "content" in choice["message"]:
                    answer = choice["message"]["content"]
                elif "text" in choice:
                    answer = choice["text"]

        # 시도 2: content 직접 참조
        if not answer and "content" in result:
            answer = result["content"]

        # 시도 3: answer 키
        if not answer and "answer" in result:
            answer = result["answer"]

        # 시도 4: response 키
        if not answer and "response" in result:
            answer = result["response"]

        return {
            "success": True,
            "answer": answer if answer else "",
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
# MAGIC ### 🔍 빠른 연결 테스트 (권장)
# MAGIC
# MAGIC 전체 테스트를 실행하기 전에 먼저 하나의 질문으로 연결을 확인합니다.
# MAGIC
# MAGIC ⚠️ **401 에러가 발생하면 여기서 먼저 해결하세요!**

# COMMAND ----------

# 빠른 연결 테스트
if KA_ENDPOINT_NAME:
    print("=" * 80)
    print("🔍 빠른 연결 테스트")
    print("=" * 80)
    print()
    print(f"Endpoint: {KA_ENDPOINT_NAME}")
    print()

    # 간단한 테스트 질문
    test_question = "안녕하세요. 이 문서에 대해 간단히 설명해주세요."

    print(f"❓ 테스트 질문: {test_question}")
    print()
    print("⏳ 답변 생성 중 (디버그 모드)...")
    print()

    # 디버그 모드로 실행하여 상세 정보 확인
    result = query_ka_endpoint(KA_ENDPOINT_NAME, test_question, debug=True)

    print()
    print("=" * 80)

    if result["success"]:
        print("✅ 연결 성공!")
        print("=" * 80)
        print()
        print("💬 답변:")
        print("-" * 80)
        print(result["answer"])
        print("-" * 80)
        print()
        print("🎉 Knowledge Assistant가 정상 작동합니다!")
        print("   아래의 전체 테스트를 진행하세요.")
    else:
        print("❌ 연결 실패")
        print("=" * 80)
        print()

        if "error_code" in result:
            error_code = result["error_code"]
            print(f"HTTP 상태 코드: {error_code}")
            print(f"에러 메시지: {result.get('error_message', 'Unknown')}")
            print()

            if error_code == 401:
                print("🔧 401 인증 에러 - 해결 방법:")
                print()
                print("1. 이 Notebook이 Databricks Workspace에서 실행 중인지 확인")
                print("   - 로컬 환경에서는 실행 불가")
                print("   - Databricks Notebook에서 실행해야 함")
                print()
                print("2. dbutils와 spark 객체가 정상 작동하는지 확인")
                print("   - 새 셀에서 'spark.version' 실행해보기")
                print("   - 새 셀에서 'dbutils.fs.ls(\"/\")' 실행해보기")
                print()
                print("3. KA endpoint 권한 확인")
                print("   - Workspace 관리자에게 문의")
                print(f"   - 필요 권한: USE ENDPOINT ON {KA_ENDPOINT_NAME}")
                print()
                print("4. Personal Access Token 재생성")
                print("   - User Settings → Developer → Access Tokens")
                print("   - 새 토큰 생성 후 Notebook 재시작")

                if "debug_info" in result:
                    print()
                    print("디버그 정보:")
                    for key, value in result["debug_info"].items():
                        print(f"   {key}: {value}")
            elif error_code == 403:
                print("🔧 403 권한 에러:")
                print(f"   KA endpoint에 대한 접근 권한이 없습니다.")
                print(f"   Workspace 관리자에게 다음 권한을 요청하세요:")
                print(f"   GRANT USE ENDPOINT ON {KA_ENDPOINT_NAME} TO `your_email@domain.com`;")
            elif error_code == 404:
                print("🔧 404 Not Found 에러:")
                print(f"   Endpoint를 찾을 수 없습니다: {KA_ENDPOINT_NAME}")
                print(f"   Step 4로 돌아가서 올바른 endpoint 이름을 확인하세요.")
        else:
            print(f"에러: {result.get('error', 'Unknown')}")

        print()
        print("⚠️  문제를 해결한 후 이 셀을 다시 실행하세요.")
else:
    print("❌ KA_ENDPOINT_NAME이 설정되지 않았습니다.")
    print("   Step 4로 돌아가서 KA를 선택하세요.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 🧪 전체 테스트 실행
# MAGIC
# MAGIC 위의 빠른 테스트가 성공하면 여러 질문으로 한글 성능을 평가합니다.
# MAGIC
# MAGIC 각 질문에 대해 KA의 답변을 확인하고 평가합니다.

# COMMAND ----------

if not KA_ENDPOINT_NAME:
    print("❌ KA endpoint가 설정되지 않았습니다.")
    print("   Step 4로 돌아가서 KA를 선택하세요.")
else:
    print("=" * 80)
    print(f"🧪 Knowledge Assistant 한글 테스트")
    print(f"   Endpoint: {KA_ENDPOINT_NAME}")
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

        # 질문 전송 (첫 번째 질문은 디버그 모드)
        print("⏳ 답변 생성 중...")
        is_first = (i == 1)
        result = query_ka_endpoint(KA_ENDPOINT_NAME, question, debug=is_first)

        if result["success"]:
            answer = result["answer"]
            print()
            print("💬 답변:")
            print("-" * 80)
            print(answer if answer else "(답변이 비어있습니다)")
            print("-" * 80)

            # 답변이 비어있으면 원본 응답 출력
            if not answer and "raw_response" in result:
                print()
                print("⚠️  답변이 비어있습니다. 원본 응답 확인:")
                print("-" * 80)
                import json
                print(json.dumps(result["raw_response"], indent=2, ensure_ascii=False)[:1000])
                print("-" * 80)

            # 평가 기록
            test_results.append({
                "question": question,
                "answer": answer,
                "success": True
            })

        else:
            print(f"\n❌ 에러 발생")

            # 에러 코드가 있는 경우 (HTTP 에러)
            if "error_code" in result:
                error_code = result["error_code"]
                error_msg = result.get("error_message", "Unknown")

                print(f"   HTTP 상태 코드: {error_code}")
                print(f"   에러 메시지: {error_msg}")

                # 401 에러 상세 안내
                if error_code == 401:
                    print()
                    print("🔧 401 인증 에러 해결 방법:")
                    print("   1. Notebook을 Databricks Workspace에서 실행 중인지 확인")
                    print("   2. dbutils와 spark가 정상 작동하는지 확인")
                    print("   3. KA endpoint에 대한 권한이 있는지 확인")
                    print("   4. debug=True로 재실행하여 상세 정보 확인")

                    if "debug_info" in result:
                        debug_info = result["debug_info"]
                        print()
                        print("디버그 정보:")
                        print(f"   URL: {debug_info.get('url', 'N/A')}")
                        print(f"   Endpoint: {debug_info.get('endpoint', 'N/A')}")
                        print(f"   Token 접두사: {debug_info.get('token_prefix', 'N/A')}")
            else:
                # 일반 에러
                print(f"   에러: {result.get('error', 'Unknown')}")

            test_results.append({
                "question": question,
                "answer": None,
                "success": False,
                "error": result.get("error", "Unknown"),
                "error_code": result.get("error_code")
            })

        print()
        time.sleep(2)  # Rate limiting 방지

    print("\n" + "=" * 80)
    print("✅ 테스트 완료!")
    print("=" * 80)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 7: 결과 평가 및 의사결정
# MAGIC
# MAGIC 테스트 결과를 종합하여 Knowledge Assistant의 한글 성능을 평가합니다.

# COMMAND ----------

if 'test_results' in locals():
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

else:
    print("⚠️  테스트 결과가 없습니다.")
    print("   Step 6의 테스트를 먼저 실행하세요.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 8: KA Tile ID 확인 (Supervisor Agent 연동용)
# MAGIC
# MAGIC Knowledge Assistant를 Supervisor Agent에 연동하려면 Tile ID가 필요합니다.

# COMMAND ----------

# KA endpoint에서 tile ID 추출
if KA_ENDPOINT_NAME:
    # Endpoint 이름 형식: ka-{tile_id}-endpoint
    tile_id = KA_ENDPOINT_NAME.replace("ka-", "").replace("-endpoint", "")

    print("=" * 60)
    print("📌 Knowledge Assistant 정보")
    print("=" * 60)
    print(f"Endpoint Name: {KA_ENDPOINT_NAME}")
    print(f"Tile ID: {tile_id}")
    print()

    print("💡 다음 단계에서 사용:")
    print(f"   - Supervisor Agent에 이 KA를 추가할 때 tile_id 필요")
    print(f"   - Voice App에서 직접 KA endpoint 호출")
    print()

    # .env 파일 업데이트용 정보
    print("📝 설정 파일 업데이트:")
    print(f"   KA_ENDPOINT_NAME={KA_ENDPOINT_NAME}")
    print(f"   KA_TILE_ID={tile_id}")
    print()

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ 체크리스트
# MAGIC
# MAGIC 완료된 작업:
# MAGIC - [x] Unity Catalog Volume 확인
# MAGIC - [x] 한글 PDF 업로드
# MAGIC - [x] Knowledge Assistant 생성 (UI)
# MAGIC - [x] 프로비저닝 대기
# MAGIC - [x] 한글 질문 테스트
# MAGIC - [x] 결과 평가
# MAGIC
# MAGIC 다음 단계:
# MAGIC - [ ] 성능 평가에 따라 Option A 또는 B 선택
# MAGIC - [ ] Option A: Voice App 연동
# MAGIC - [ ] Option B: Custom RAG Pipeline 구현 (`02b_Custom_RAG_Pipeline.py`)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 📊 최종 결과
# MAGIC
# MAGIC **평가 결과를 바탕으로 다음 노트북을 선택하세요:**
# MAGIC
# MAGIC - ✅ **KA 성능 우수** → `03a_Voice_App_Integration.py`
# MAGIC - ⚠️ **KA 성능 부족** → `02b_Custom_RAG_Pipeline.py`
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Notebook 완료**

# COMMAND ----------
