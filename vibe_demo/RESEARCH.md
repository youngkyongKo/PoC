# Multi-Agent Supervisor 데모 구현 자료 조사

## 개요

Databricks 플랫폼에서 RAG와 Genie space를 활용한 multi-agent Supervisor 데모 구현을 위한 기술 조사 문서입니다.

날짜: 2026-03-06

## 요구사항 요약

1. **음성 인터페이스**: 음성 입력(STT) 및 출력(TTS) 지원
2. **RAG 에이전트**: PDF 문서 기반 질의응답
3. **Genie Space**: 정형 테이블 기반 자연어 SQL 쿼리
4. **Supervisor**: 질문 라우팅 및 응답 생성
5. **TTS 최적화**: 응답을 TTS에 적합하게 변환 및 축약
6. **간단하고 직관적인 UI**: 이해와 설명이 쉬운 구조

---

## 1. 아키텍처 개요

### 1.1 전체 구조

```
User Input (Text/Voice)
    ↓
Speech-to-Text (if voice)
    ↓
Supervisor Agent (MAS)
    ├─→ Knowledge Assistant (RAG on PDFs)
    └─→ Genie Space (SQL on Tables)
    ↓
Response Synthesis
    ↓
TTS Response Adapter (축약/변환)
    ↓
Text-to-Speech
    ↓
UI (Text + Voice Output)
```

### 1.2 Databricks 컴포넌트

| 컴포넌트 | 역할 | Databricks 서비스 |
|---------|------|------------------|
| **STT** | 음성 → 텍스트 | Foundation Model API (외부 API 통합) |
| **TTS** | 텍스트 → 음성 | Foundation Model API (외부 API 통합) |
| **Vector Search** | PDF 임베딩 & 검색 | Databricks Vector Search |
| **Knowledge Assistant** | RAG 에이전트 | Agent Brick (KA) |
| **Genie Space** | 자연어 SQL | Genie Space |
| **Supervisor** | 멀티 에이전트 라우팅 | Agent Brick (MAS) |
| **Response Adapter** | TTS용 응답 변환 | Custom PyFunc Model |
| **Demo UI** | 사용자 인터페이스 | Databricks App (APX or Dash) |

---

## 2. RAG 파이프라인 (PDF → Vector Search)

### 2.1 PDF 처리 워크플로우

```
1. PDF Upload → Volume
2. PDF Parsing → ai_parse_document (Databricks 문서 파싱 API)
3. Chunking → LangChain TextSplitter (1000 chars, 200 overlap)
4. Embedding → BGE-M3 계열 모델 (한국어 최적화)
5. Vector Index → Delta Sync Index
6. Serving Endpoint → Vector Search Endpoint
```

**핵심 변경 사항**:
- **PDF 파싱**: Databricks의 `ai_parse_document` API 사용으로 문서 구조 인식 향상
- **임베딩 모델**: BGE-M3 계열 사용으로 한국어 텍스트 임베딩 품질 개선

### 2.2 Vector Search 구성

**인덱스 타입**: Delta Sync (Self-Managed Embeddings)

BGE-M3 모델은 Databricks가 직접 제공하지 않으므로, 별도 임베딩 모델 엔드포인트를 배포하거나 사전 계산된 임베딩을 사용합니다.

```python
# 소스 테이블 스키마 (임베딩 포함)
CREATE TABLE catalog.schema.pdf_chunks (
    id STRING,              -- Primary key
    content STRING,         -- 청크 텍스트
    embedding ARRAY<FLOAT>, -- BGE-M3 임베딩 (1024 dim)
    metadata STRING,        -- JSON: {file_name, page_num, chunk_idx}
    created_at TIMESTAMP
)

# Vector Search 인덱스 생성 (Self-Managed Embeddings)
w.vector_search_indexes.create_index(
    name="catalog.schema.pdf_chunks_index",
    endpoint_name="my-vs-endpoint",
    primary_key="id",
    index_type="DELTA_SYNC",
    delta_sync_index_spec={
        "source_table": "catalog.schema.pdf_chunks",
        "embedding_vector_columns": [{
            "name": "embedding",
            "embedding_dimension": 1024  # BGE-M3 dimension
        }],
        "pipeline_type": "TRIGGERED"
    }
)
```

**한국어 임베딩 모델 옵션**:
- **BGE-M3**: 다국어 지원, 한국어 성능 우수 (1024 dim)
- **multilingual-e5-large**: 다국어 임베딩 (1024 dim)
- **커스텀 배포**: HuggingFace 모델을 Model Serving 엔드포인트로 배포

### 2.3 PDF 파싱 및 청킹 구현 (ai_parse_document 활용)

**Python 노트북** (`01_pdf_ingestion.py`):

```python
from databricks.sdk import WorkspaceClient
from langchain.text_splitter import RecursiveCharacterTextSplitter
from datetime import datetime
from sentence_transformers import SentenceTransformer
import uuid
import json

w = WorkspaceClient()

# 1. PDF 파싱 (ai_parse_document 사용)
def parse_pdf_with_ai(volume_path, file_name):
    """
    Databricks ai_parse_document 사용하여 PDF 파싱
    문서 구조(제목, 표, 이미지 등) 인식 가능
    """
    # SQL 함수로 호출 또는 SDK 사용
    parsed_result = spark.sql(f"""
        SELECT ai_parse_document(
            '{volume_path}/{file_name}',
            'pdf'
        ) AS parsed_doc
    """).collect()[0]["parsed_doc"]

    # 파싱된 결과는 구조화된 JSON
    # 예: {"text": "...", "pages": [...], "tables": [...]}
    return parsed_result

# 2. BGE-M3 임베딩 모델 로드
embedding_model = SentenceTransformer('BAAI/bge-m3')

# 3. 청킹 및 임베딩
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = []
for file_name in pdf_files:
    # PDF 파싱
    parsed_doc = parse_pdf_with_ai("/Volumes/catalog/schema/docs_volume/pdfs", file_name)

    # 텍스트 추출 및 청킹
    full_text = parsed_doc.get("text", "")
    page_chunks = text_splitter.split_text(full_text)

    for idx, chunk in enumerate(page_chunks):
        # BGE-M3 임베딩 생성
        embedding = embedding_model.encode(chunk, normalize_embeddings=True).tolist()

        chunks.append({
            "id": str(uuid.uuid4()),
            "content": chunk,
            "embedding": embedding,  # 1024 차원
            "metadata": json.dumps({
                "file_name": file_name,
                "chunk_idx": idx
            }),
            "created_at": datetime.now()
        })

# 4. Delta 테이블에 저장
spark.createDataFrame(chunks).write.mode("append").saveAsTable("catalog.schema.pdf_chunks")

# 5. Vector Search 동기화
w.vector_search_indexes.sync_index(index_name="catalog.schema.pdf_chunks_index")
```

**ai_parse_document 장점**:
- 문서 레이아웃 인식 (제목, 단락, 표, 이미지)
- 한국어 문서 처리 최적화
- 텍스트 품질 향상 (OCR 포함)
- Databricks 네이티브 통합

### 2.4 Knowledge Assistant 생성

**옵션 1: Agent Brick (KA) - 권장**

간단하고 빠른 구축을 위해 Agent Brick 사용:

```python
# Volume에 PDF 업로드
# /Volumes/catalog/schema/docs_volume/pdfs/

# KA 생성
manage_ka(
    action="create_or_update",
    name="PDF Knowledge Base",
    volume_path="/Volumes/catalog/schema/docs_volume/pdfs",
    description="한국어 문서 기반 지식 베이스",
    instructions="간결하고 정확하게 한국어로 답변하세요. 출처를 포함하세요.",
    add_examples_from_volume=True
)
```

**참고**: KA는 내부적으로 Vector Search를 자동 구성하지만, 임베딩 모델 선택에 제약이 있습니다.

**옵션 2: 커스텀 RAG Agent (한국어 최적화 필요 시)**

BGE-M3 임베딩을 사용하는 커스텀 RAG 에이전트:

```python
from databricks_langchain import ChatDatabricks
from langchain.chains import RetrievalQA
from langchain.vectorstores import DatabricksVectorSearch

# BGE-M3 임베딩을 사용하는 Vector Store 연결
vector_store = DatabricksVectorSearch(
    endpoint="my-vs-endpoint",
    index_name="catalog.schema.pdf_chunks_index",
    embedding_function=embedding_model  # BGE-M3
)

# RAG Chain 구성
llm = ChatDatabricks(endpoint="databricks-meta-llama-3-3-70b-instruct")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)
```

**선택 기준**:
- **Agent Brick**: 빠른 프로토타입, 데모용
- **커스텀 RAG**: 한국어 성능 최적화 필요 시

---

## 3. Genie Space 구성 (Metric View 활용)

### 3.1 Metric View 생성

Metric View는 비즈니스 메트릭을 정의하는 Unity Catalog 객체입니다.

```sql
-- 예: 매출 메트릭 뷰
CREATE METRIC VIEW catalog.schema.sales_metrics AS
SELECT
    date,
    SUM(amount) AS total_sales,
    COUNT(DISTINCT customer_id) AS unique_customers,
    AVG(amount) AS avg_order_value
FROM catalog.schema.orders
GROUP BY date;
```

### 3.2 Genie Space 생성

```python
# 테이블 확인
get_table_details(
    catalog="catalog",
    schema="schema",
    table_stat_level="SIMPLE"
)

# Genie Space 생성
create_or_update_genie(
    display_name="Sales Analytics Genie",
    table_identifiers=[
        "catalog.schema.orders",
        "catalog.schema.customers",
        "catalog.schema.sales_metrics"  # Metric View 포함
    ],
    description="매출 데이터를 자연어로 분석할 수 있는 Genie Space",
    sample_questions=[
        "지난달 총 매출은 얼마인가요?",
        "상위 10명의 고객은 누구인가요?",
        "일별 평균 주문 금액 추이를 보여주세요"
    ]
)
```

### 3.3 Genie Conversation API 테스트

```python
# Genie에 질문
result = ask_genie(
    space_id="<genie_space_id>",
    question="지난 7일간 총 매출은?"
)

# 결과: SQL, 데이터, 행 수
print(result["query_result"]["statement_response"]["result"]["data_array"])
```

---

## 4. Supervisor Agent 구성

### 4.1 Multi-Agent System (MAS) 생성

Supervisor Agent는 질문을 분석하여 적절한 서브 에이전트로 라우팅합니다.

```python
# 1. KA 생성 (위에서 생성됨 - tile_id 필요)
ka_tile_id = "f32c5f73-466b-..."  # manage_ka 결과에서 얻음

# 2. Genie Space 생성 (위에서 생성됨 - space_id 필요)
genie_space_id = "01abc123..."  # create_or_update_genie 결과에서 얻음

# 3. Supervisor Agent 생성
manage_mas(
    action="create_or_update",
    name="General Q&A Supervisor",
    agents=[
        {
            "name": "document_qa",
            "ka_tile_id": ka_tile_id,
            "description": "PDF 문서 내용에 대한 질문 처리 (정책, 절차, 매뉴얼 등)"
        },
        {
            "name": "data_analytics",
            "genie_space_id": genie_space_id,
            "description": "정형 데이터 분석 및 SQL 기반 통계 쿼리 (매출, 고객, 트렌드)"
        }
    ],
    description="문서 질의와 데이터 분석을 지능적으로 라우팅하는 Supervisor",
    instructions="""
    질문의 맥락을 파악하여 라우팅:
    1. 문서 내용, 정책, 절차 관련 → document_qa
    2. 데이터 분석, 통계, 트렌드 → data_analytics

    복합 질문의 경우:
    - 먼저 문서에서 정보 수집 (document_qa)
    - 그 다음 데이터로 검증 (data_analytics)
    """,
    examples=[
        {
            "question": "회사 휴가 정책은?",
            "guideline": "document_qa 사용 - 정책 문서 참조"
        },
        {
            "question": "지난달 매출 증가율은?",
            "guideline": "data_analytics 사용 - 매출 테이블 쿼리"
        }
    ]
)
```

### 4.2 Supervisor 라우팅 로직

Supervisor Agent는 내부적으로 LLM을 사용하여 자동 라우팅을 수행합니다:

1. **질문 분석**: 사용자 질문의 의도 파악
2. **에이전트 선택**: 각 에이전트의 `description`을 기반으로 매칭
3. **도구 호출**: 선택된 에이전트의 엔드포인트 호출
4. **응답 합성**: 결과를 최종 응답으로 통합

**예시 호출**:

```python
# Supervisor 엔드포인트 쿼리
response = query_serving_endpoint(
    name="general_q_a_supervisor_endpoint",
    messages=[
        {"role": "user", "content": "지난달 매출이 전월 대비 증가했나요? 그 이유는?"}
    ]
)

# 내부 동작:
# 1. "매출", "증가" 키워드 → data_analytics 선택
# 2. Genie로 SQL 실행 → 매출 데이터 획득
# 3. 필요 시 document_qa 호출 → 비즈니스 컨텍스트 추가
# 4. 최종 답변 생성
```

---

## 5. 음성 인터페이스 (STT/TTS)

### 5.1 Speech-to-Text (STT)

Databricks Foundation Model API는 직접적인 STT를 제공하지 않습니다. 외부 API 통합이 필요합니다.

**옵션 1: OpenAI Whisper API**

```python
import openai

def transcribe_audio(audio_file_path):
    with open(audio_file_path, "rb") as audio:
        transcript = openai.Audio.transcribe(
            model="whisper-1",
            file=audio,
            language="ko"  # 한국어 지정
        )
    return transcript["text"]
```

**옵션 2: Google Cloud Speech-to-Text**

```python
from google.cloud import speech

def transcribe_audio_google(audio_file_path):
    client = speech.SpeechClient()

    with open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="ko-KR"
    )

    response = client.recognize(config=config, audio=audio)
    return response.results[0].alternatives[0].transcript
```

### 5.2 Text-to-Speech (TTS)

**옵션 1: OpenAI TTS API**

```python
import openai

def text_to_speech(text, output_path):
    response = openai.Audio.create_speech(
        model="tts-1-hd",  # 고품질
        voice="nova",  # 또는 "alloy", "echo", "fable", "onyx", "shimmer"
        input=text,
        language="ko"  # 한국어
    )

    with open(output_path, "wb") as f:
        f.write(response.content)

    return output_path
```

**옵션 2: Google Cloud TTS**

```python
from google.cloud import texttospeech

def text_to_speech_google(text, output_path):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name="ko-KR-Standard-A"  # 여성 목소리
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    with open(output_path, "wb") as f:
        f.write(response.audio_content)

    return output_path
```

### 5.3 TTS 응답 어댑터 (Response Adapter)

에이전트의 장문 응답을 TTS에 적합하게 변환하는 컴포넌트입니다.

**목적**:
- 긴 텍스트 축약 (2-3 문장으로)
- 특수 문자 제거 (마크다운, 기호)
- 숫자 표현 정리 (예: "1,234" → "천이백삼십사")
- 자연스러운 음성 표현으로 변환

**구현 방법 1: LLM 기반 변환**

```python
def adapt_for_tts(agent_response):
    prompt = f"""
    다음 응답을 음성으로 읽기에 적합하게 변환하세요:
    - 2-3 문장으로 요약
    - 마크다운, 특수문자 제거
    - 자연스러운 한국어 구어체로 변환

    원문:
    {agent_response}

    변환된 응답:
    """

    response = chat_completion(
        model="databricks-meta-llama-3-3-70b-instruct",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )

    return response["choices"][0]["message"]["content"]
```

**구현 방법 2: PyFunc Model 래핑**

```python
import mlflow
from mlflow.pyfunc import PythonModel

class TTSAdapter(PythonModel):
    def load_context(self, context):
        from databricks_langchain import ChatDatabricks
        self.llm = ChatDatabricks(endpoint="databricks-meta-llama-3-3-70b-instruct")

    def predict(self, context, model_input):
        # model_input: {"text": "agent response"}
        text = model_input["text"][0]

        # LLM 기반 축약
        adapted = self.llm.predict(
            f"다음을 2-3 문장으로 음성 출력에 적합하게 요약: {text}"
        )

        return {"adapted_text": adapted}

# 모델 로깅 및 배포
mlflow.pyfunc.log_model(
    artifact_path="tts_adapter",
    python_model=TTSAdapter(),
    registered_model_name="catalog.schema.tts_adapter"
)
```

---

## 6. 데모 UI 구현

### 6.1 UI 아키텍처

**옵션 1: Databricks App (APX - FastAPI + React)**
- 장점: 풀스택 제어, 음성 녹음/재생 용이
- 단점: React 개발 필요

**옵션 2: Databricks App (Dash/Streamlit)**
- 장점: Python만으로 빠른 개발
- 단점: 음성 처리 제약

**추천**: APX (FastAPI + React) - 음성 인터페이스에 적합

### 6.2 UI 컴포넌트 구조

```
┌─────────────────────────────────────┐
│  Header: "Multi-Agent Q&A Demo"    │
├─────────────────────────────────────┤
│  [🎤 Record]  [Text Input Box]     │ ← 음성/텍스트 입력
│  [Send]                             │
├─────────────────────────────────────┤
│  Chat History                       │
│  ┌─────────────────────────────┐   │
│  │ User: 지난달 매출은?         │   │
│  │ Agent: 지난달 매출은...      │   │
│  │   [🔊 Play Audio]            │   │ ← TTS 재생 버튼
│  │   [Chart/Visualization]      │   │ ← 시각화 (선택적)
│  └─────────────────────────────┘   │
├─────────────────────────────────────┤
│  Status: "Routing to data_analytics"│ ← 라우팅 상태 표시
└─────────────────────────────────────┘
```

### 6.3 백엔드 API (FastAPI)

**app.py**:

```python
from fastapi import FastAPI, UploadFile
from databricks.sdk import WorkspaceClient
import openai

app = FastAPI()
w = WorkspaceClient()

@app.post("/ask")
async def ask_question(question: str):
    # 1. Supervisor에 질문 전송
    response = w.serving_endpoints.query(
        name="general_q_a_supervisor_endpoint",
        dataframe_records=[{"messages": [{"role": "user", "content": question}]}]
    )

    agent_response = response.predictions[0]["choices"][0]["message"]["content"]

    # 2. TTS 어댑터 호출
    adapted = w.serving_endpoints.query(
        name="tts_adapter_endpoint",
        dataframe_records=[{"text": agent_response}]
    )

    adapted_text = adapted.predictions[0]["adapted_text"]

    # 3. TTS 생성
    audio_path = text_to_speech(adapted_text, "output.mp3")

    return {
        "text_response": agent_response,
        "audio_response": adapted_text,
        "audio_url": f"/audio/{audio_path}"
    }

@app.post("/transcribe")
async def transcribe(audio: UploadFile):
    # STT 호출
    text = transcribe_audio(audio.file)
    return {"text": text}
```

### 6.4 프론트엔드 (React)

**App.jsx**:

```jsx
import React, { useState } from 'react';
import AudioRecorder from './AudioRecorder';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);

  const handleSend = async (text) => {
    // 사용자 메시지 추가
    setMessages([...messages, { role: 'user', content: text }]);

    // API 호출
    const response = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: text })
    });

    const data = await response.json();

    // 에이전트 응답 추가
    setMessages([...messages,
      { role: 'user', content: text },
      { role: 'assistant', content: data.text_response, audio: data.audio_url }
    ]);
  };

  const handleVoiceInput = async (audioBlob) => {
    // STT 호출
    const formData = new FormData();
    formData.append('audio', audioBlob);

    const response = await fetch('/transcribe', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();
    handleSend(data.text);
  };

  return (
    <div className="app">
      <h1>Multi-Agent Q&A Demo</h1>

      <div className="chat-history">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <p>{msg.content}</p>
            {msg.audio && <button onClick={() => playAudio(msg.audio)}>🔊 Play</button>}
          </div>
        ))}
      </div>

      <div className="input-area">
        <AudioRecorder onRecordingComplete={handleVoiceInput} />
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend(input)}
        />
        <button onClick={() => handleSend(input)}>Send</button>
      </div>
    </div>
  );
}
```

---

## 7. 구현 단계별 체크리스트

### Phase 1: 데이터 준비 (1-2일)

- [ ] **PDF 문서 수집/생성**
  - 샘플 PDF 준비 또는 `databricks-unstructured-pdf-generation` 스킬 사용
  - Volume에 업로드: `/Volumes/catalog/schema/docs_volume/pdfs/`

- [ ] **정형 테이블 생성**
  - `databricks-synthetic-data-generation`으로 데이터 생성
  - `databricks-spark-declarative-pipelines`로 bronze/silver/gold 테이블 구축

- [ ] **Metric View 생성**
  - Unity Catalog에 metric view 정의
  - 샘플 쿼리로 검증

### Phase 2: 에이전트 구축 (2-3일)

- [ ] **Vector Search 구성**
  - Endpoint 생성: `create_vs_endpoint(name="demo-vs-endpoint", endpoint_type="STANDARD")`
  - PDF 파싱 노트북 실행
  - Delta Sync 인덱스 생성

- [ ] **Knowledge Assistant 생성**
  - `manage_ka(action="create_or_update", ...)` 호출
  - 엔드포인트 상태 확인: `ONLINE` 대기
  - 샘플 질문으로 테스트

- [ ] **Genie Space 생성**
  - `create_or_update_genie(...)` 호출
  - 샘플 질문 큐레이션
  - Conversation API 테스트

- [ ] **Supervisor Agent 생성**
  - **우선**: Agent Bricks MAS 사용 (`manage_mas(...)` 호출)
  - KA와 Genie를 묶어 라우팅 구성
  - 라우팅 instructions 최적화 (한국어 의도 파악)
  - 복합 질문으로 테스트
  - **대안**: 요구사항 미충족 시 커스텀 LangGraph Supervisor 구현

### Phase 3: 음성 인터페이스 (2일)

- [ ] **STT 통합**
  - OpenAI Whisper 또는 Google STT API 설정
  - 테스트 오디오로 transcription 검증

- [ ] **TTS 통합**
  - OpenAI TTS 또는 Google TTS API 설정
  - 샘플 텍스트로 음성 생성 테스트

- [ ] **TTS Response Adapter**
  - LLM 기반 축약 로직 구현
  - PyFunc 모델로 래핑 및 배포 (선택)

### Phase 4: UI 개발 (3-4일)

- [ ] **백엔드 API (FastAPI)**
  - `/ask` 엔드포인트: 질문 → Supervisor → TTS Adapter
  - `/transcribe` 엔드포인트: 오디오 → STT → 텍스트
  - 오디오 파일 서빙 엔드포인트

- [ ] **프론트엔드 (React)**
  - 채팅 인터페이스 구현
  - 음성 녹음 컴포넌트 (`react-media-recorder` 활용)
  - 오디오 재생 기능
  - 상태 표시 (라우팅, 로딩)

- [ ] **Databricks App 배포**
  - `app.yaml` 구성
  - `databricks apps deploy`

### Phase 5: 테스트 및 최적화 (1-2일)

- [ ] **End-to-End 테스트**
  - 텍스트 질문 → 응답 확인
  - 음성 질문 → 응답 확인
  - 복합 질문 (RAG + Genie) 테스트

- [ ] **성능 최적화**
  - Supervisor 라우팅 정확도 개선
  - TTS 응답 품질 조정
  - UI 응답 속도 개선

- [ ] **데모 준비**
  - 시나리오별 샘플 질문 준비
  - 오류 처리 추가
  - UI 폴리싱

---

## 8. 기술 스택 요약

### 8.1 Databricks 서비스

| 서비스 | 용도 | 필수 여부 |
|--------|------|----------|
| **Unity Catalog** | 테이블, 볼륨 관리 | 필수 |
| **Vector Search** | PDF 임베딩 인덱스 | 필수 |
| **Agent Bricks (KA)** | RAG 에이전트 | 필수 |
| **Genie Space** | 자연어 SQL | 필수 |
| **Agent Bricks (MAS)** | Supervisor | 필수 |
| **Model Serving** | TTS Adapter (선택) | 선택 |
| **Databricks Apps** | UI 호스팅 | 필수 |
| **MLflow** | 실험 추적, 모델 관리 | 권장 |

### 8.2 외부 API

| API | 용도 | 대안 |
|-----|------|-----|
| **OpenAI Whisper** | STT | Google Cloud Speech-to-Text, Azure Speech |
| **OpenAI TTS** | TTS | Google Cloud TTS, Azure TTS, ElevenLabs |

### 8.3 Python 패키지

```
# requirements.txt
mlflow==3.6.0
databricks-sdk
databricks-langchain
langgraph==0.3.4
databricks-agents
pydantic
sentence-transformers   # BGE-M3 임베딩
langchain-text-splitters # 청킹
openai                  # STT/TTS
fastapi                 # 백엔드 API
uvicorn                 # ASGI 서버
python-multipart        # 파일 업로드
```

### 8.4 프론트엔드

```
# package.json (React)
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "react-media-recorder": "^1.6.6"
  }
}
```

---

## 9. 주요 설계 결정 사항

### 9.1 Vector Search vs Knowledge Assistant

**결정**: Knowledge Assistant (Agent Brick) 사용

**이유**:
- KA는 Vector Search를 내부적으로 자동 구성
- 간단한 API (`manage_ka`)로 빠른 구축
- 자동 엔드포인트 배포 및 관리

**Trade-off**: 커스터마이징 제약
- 청킹 로직 고정
- 임베딩 모델 선택 제한 (Databricks 제공 모델만)
- **한국어 최적화**: KA가 한국어 처리에 제약이 있다면, 커스텀 RAG 에이전트 + BGE-M3 임베딩 사용 권장

### 9.2 Metric View vs 일반 테이블

**결정**: Metric View 사용

**이유**:
- 비즈니스 메트릭을 명시적으로 정의
- Genie Space의 쿼리 정확도 향상
- 재사용 가능한 메트릭 레이어

**Trade-off**: 추가 생성 단계 필요

### 9.3 TTS Adapter 위치

**결정**: 백엔드 API에서 LLM 직접 호출

**이유**:
- PyFunc 모델 배포는 추가 오버헤드
- 단순 프롬프트 기반 변환으로 충분
- 실시간 조정 용이

**Trade-off**: API 레이턴시 증가 (+ 1-2초)

### 9.4 UI 프레임워크

**결정**: APX (FastAPI + React)

**이유**:
- 음성 녹음/재생에 최적
- 풀스택 제어 가능
- 프로덕션 확장성

**Trade-off**: React 개발 시간 소요

---

## 10. 예상 구현 시간

| 단계 | 소요 시간 | 누적 |
|------|----------|------|
| 데이터 준비 | 1-2일 | 2일 |
| 에이전트 구축 | 2-3일 | 5일 |
| 음성 인터페이스 | 2일 | 7일 |
| UI 개발 | 3-4일 | 11일 |
| 테스트 및 최적화 | 1-2일 | 13일 |

**총 예상 시간**: 2-3주 (1인 작업 기준)

---

## 11. 주요 참고 자료

### Databricks 문서

- [Vector Search Documentation](https://docs.databricks.com/en/generative-ai/vector-search.html)
- [Agent Framework](https://docs.databricks.com/en/generative-ai/agent-framework/)
- [Genie Spaces](https://docs.databricks.com/en/genie/)
- [Model Serving](https://docs.databricks.com/en/machine-learning/model-serving/)
- [Foundation Model APIs](https://docs.databricks.com/en/machine-learning/foundation-model-apis/)
- [Databricks Apps](https://docs.databricks.com/en/dev-tools/databricks-apps/)

### 외부 API

- [OpenAI Whisper API](https://platform.openai.com/docs/guides/speech-to-text)
- [OpenAI TTS API](https://platform.openai.com/docs/guides/text-to-speech)
- [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text/docs)
- [Google Cloud Text-to-Speech](https://cloud.google.com/text-to-speech/docs)

### Python 라이브러리

- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- [PDFPlumber](https://github.com/jsvine/pdfplumber)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React Media Recorder](https://github.com/0x006F/react-media-recorder)

---

## 12. 한국어 최적화 전략

### 12.1 핵심 고려사항

| 컴포넌트 | 한국어 최적화 방안 |
|---------|------------------|
| **PDF 파싱** | ai_parse_document 사용 (한국어 레이아웃 인식) |
| **임베딩** | BGE-M3 또는 multilingual-e5 (한국어 지원 우수) |
| **LLM** | databricks-meta-llama-3-3-70b-instruct (다국어) |
| **Genie Space** | 한국어 샘플 질문 및 instructions 제공 |
| **TTS** | Google TTS ko-KR 또는 OpenAI TTS (자연스러운 한국어) |
| **STT** | OpenAI Whisper (한국어 인식률 우수) |

### 12.2 테스트 체크리스트

- [ ] 한국어 PDF 문서 파싱 정확도 검증
- [ ] 한국어 쿼리에 대한 Vector Search 재현율 측정
- [ ] Genie Space 한국어 SQL 생성 정확도 확인
- [ ] Supervisor 한국어 의도 파악 및 라우팅 검증
- [ ] TTS 한국어 발음 및 자연스러움 평가
- [ ] STT 한국어 음성 인식률 테스트

---

## 13. 다음 단계

1. **프로젝트 구조 설계**: 디렉토리 구조 및 모듈 분리
2. **개발 환경 설정**: Databricks 워크스페이스, 로컬 개발 환경
3. **한국어 모델 검증**: BGE-M3 임베딩 성능 테스트
4. **Phase 1 시작**: PDF 및 테이블 데이터 준비
5. **프로토타입 개발**: 최소 기능 구현 (텍스트 입력 → Supervisor → 텍스트 출력)
6. **점진적 확장**: 음성 인터페이스 및 고도화

---

## 변경 이력

- 2026-03-06: 초안 작성 (Databricks 스킬 문서 기반 조사)
- 2026-03-06: 한국어 최적화 반영 (ai_parse_document, BGE-M3, MAS 우선 사용)
