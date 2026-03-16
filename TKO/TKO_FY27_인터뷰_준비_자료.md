# TKO FY27 인터뷰 준비 자료 (한글)

## 📋 목차

1. [Builder Culture & AI Transformation](#1-builder-culture--ai-transformation)
2. [Agent Bricks](#2-agent-bricks)
3. [Genie & AI/BI](#3-genie--aibi)
4. [Lakeflow Connect](#4-lakeflow-connect)
5. [Databricks Apps](#5-databricks-apps)
6. [Lakebase](#6-lakebase)
7. [Unity Catalog ABAC](#7-unity-catalog-abac)
8. [Data Warehousing](#8-data-warehousing)

---

## 1. Builder Culture & AI Transformation

### Q: FY27의 FE 조직 비전은 무엇인가요?

**A:** FE(Field Engineering) 조직의 엘리트 특성을 유지하면서도 규모를 확장하고, 고객과 비즈니스에 더 효율적이고 효과적으로 가치를 전달하는 것입니다. 6B ARR에서 10B, 15B ARR로 성장하려면 기존 방식으로는 부족하고, 점진적인 진화가 필요합니다.

### Q: FY27의 최우선 과제는 무엇인가요?

**A:** 크게 세 가지입니다:

1. **Lakebase** - 차세대 데이터베이스 플랫폼
2. **Genie** - 자연어 데이터 분석
3. **AI Transformation** - AI를 활용한 조직 혁신

### Q: Builder Culture가 뭔가요?

**A:** 모든 FE 직원이 빌더가 되어야 한다는 문화입니다. 핵심 원칙은:

- **End-to-End Outcome Ownership**: 결과에 대한 완전한 책임
- **Show Not Tell**: 말보다 실제 결과물로 보여주기
- **AI-Fueled Productivity**: AI로 생산성 향상
- **Doing > Managing**: 관리보다 직접 실행

### Q: Builder Culture가 아닌 것은?

**A:** 다음은 빌더 문화가 **아닙니다**:

- 바퀴를 재발명하는 것
- 사일로에서 작업하는 것
- 내부 유스케이스에만 집중하는 것
- AI 사용 자체를 성공으로 생각하는 것
- AI를 작은 유스케이스에만 제한하는 것

### Q: AI Transformation이 왜 중요한가요?

**A:** AI는 단순한 도구가 아니라 우리가 일하는 방식의 근본적인 변화입니다. 모든 조직이 AI로 인해 크게 변화될 것이고, 변화는 생각보다 빠르게 일어날 것입니다. 작은 회사들은 이미 처음부터 이렇게 일하고 있어요. 우리는 "기다리고 보자"는 접근이 아니라 선두에 서고 싶습니다.

---

## 2. Agent Bricks

### Q: Agent Bricks가 뭔가요?

**A:** Agent Bricks는 엔터프라이즈 AI 에이전트를 빌드하고 배포하기 위한 통합 플랫폼입니다. CTO Hanlin Tang이 발표한 제품으로, 여러 에이전트를 하나의 플랫폼에서 관리할 수 있게 해줍니다.

### Q: 왜 Agent Bricks가 필요한가요?

**A:** 현재 엔터프라이즈에서 **Agent Sprawl**(에이전트 난립) 문제가 심각합니다:

- Jira MCP, Slack MCP, Support Agent, Legal Agent, Marketing Agent 등 수많은 에이전트가 무분별하게 만들어짐
- 거버넌스가 없음
- 품질 측정이 안 됨
- 잘못된 정보, 만들어진 인용, 잘못된 고객 ID 등 품질 문제
- 너무 많은 벤더
- **고객들은 하나의 통합 에이전트 플랫폼을 원합니다**

### Q: Agent Bricks의 핵심 가치는 무엇인가요?

**A:** **C.U.R.E** 프레임워크로 요약됩니다:

- **C**ontextual reasoning: 맥락을 이해하는 추론
- **U**nified catalog and governance: 통합된 카탈로그와 거버넌스
- **R**uns on any model or framework: 어떤 모델이나 프레임워크에서도 실행
- **E**valuates & improves quality: 품질을 평가하고 개선

### Q: Agent Bricks로 무엇을 할 수 있나요?

**A:** 다양한 에이전트 빌딩 블록을 제공합니다:

- **Supervisor Agent**: 에이전트 오케스트레이션
- **Knowledge Assistant**: 문서 기반 Q&A
- **Information Extraction**: 정보 추출
- **Document Processing**: 문서 처리
- **AI Functions in SQL**: SQL에서 AI 함수 사용
- **Memory (Lakebase)**: 에이전트 메모리
- **Tools & MCP**: 도구 통합
- **Data Reasoning & Retrieval**: 데이터 추론 및 검색

### Q: Foundation Models API는 어떤가요?

**A:** **Multi-AI 전략**을 지원합니다:

- 모든 주요 모델(OpenAI, Anthropic, Google Gemini, Meta Llama 등)을 네이티브로 제공
- 한 번의 커밋으로 모델 간 유연하게 전환 가능
- 이번 분기에 agentic OSS 모델(GLM-5, Deepseek, Qwen) 출시
- 지역 확장 예정 (인도, 한국, 싱가포르, 일본)

### Q: Agent Framework는 어떻게 작동하나요?

**A:** 커스텀 에이전트를 빌드하고 배포할 수 있습니다:

- LangGraph, OpenAI Agent SDK, CrewAI 등 인기 프레임워크 지원
- Memory(Lakebase)와 Tools, MCP 접근 가능
- **중요**: 타임아웃과 UX 문제 해결을 위해 CPU Model Serving 대신 **Databricks Apps** 사용 권장

### Q: 어떤 고객이 이걸 사용하나요?

**A:** 세 가지 win 시나리오:

1. 데이터와 함께 작동하거나 내부 프로세스를 자동화하는 커스텀 에이전트
2. 높은 QPS의 classical ML 및 딥러닝 워크로드
3. Unity Catalog를 통한 모델, 에이전트, MCP 거버넌스

---

## 3. Genie & AI/BI

### Q: Genie와 Genie Code의 차이는 뭔가요?

**A:**

- **Genie**: 비즈니스 사용자를 위한 도구로, 데이터 질문에 답변
- **Genie Code**: 기술 사용자를 위한 도구로, 데이터로 무언가를 빌드

### Q: Databricks One이 뭔가요?

**A:** 비즈니스 사용자를 위한 통합 진입점입니다. 모든 것이 한 곳에, 추가 비용 없이 제공됩니다:

- AI/BI
- Databricks Apps
- Genie
- 모든 spaces, dashboards, 데이터에 대한 단일 채팅 진입점

### Q: AI/BI의 성과는 어떤가요?

**A:** FY26는 대성공의 해였습니다:

- YoY 200% 성장
- **AWS에서 #1 BI 도구**
- 다음 두 개 도구를 합친 것보다 더 많은 $DBU 소비

### Q: Genie의 Agent Mode가 뭔가요?

**A:** 모든 "왜?"에 대한 답을 찾아주는 기능입니다. 단순히 결과를 보여주는 것이 아니라, 데이터를 깊이 분석하고 이유를 설명해줍니다.

### Q: Agentic Semantic Modeling이 뭔가요?

**A:** AI 에이전트가 시맨틱 모델을 자동으로 생성하고 관리하는 기능입니다:

- **Multi-fact support**: 여러 fact 테이블 지원
- **Materialization**: 물리적으로 실체화하여 성능 향상

### Q: 왜 시맨틱 레이어가 중요한가요?

**A:** "올바른 숫자"를 얻는 것이 정말 어렵기 때문입니다:

- 분석가 #1: ARR = $2.5M
- 분석가 #2: ARR = $2.8M
- 데이터 과학자: ARR = $3.2M
- AI Agent: ARR = $2.6M

**모든 곳에서 동일한 숫자를 얻는 것**은 더욱 어렵습니다.

### Q: Databricks의 시맨틱 레이어가 다른 점은?

**A:** **통합된 시맨틱과 거버넌스**를 제공합니다:

- 기존 BI 도구들은 도구별로 다른 시맨틱 레이어를 사용
- Databricks는 Unity Catalog를 통해 하나의 시맨틱 레이어를 제공
- 모든 데이터, 시맨틱, 거버넌스가 한 곳에
- AI/BI Dashboards와 Genie가 모두 동일한 시맨틱을 사용

---

## 4. Lakeflow Connect

### Q: Lakeflow Connect가 뭔가요?

**A:** 다양한 데이터 소스에서 Lakehouse로 데이터를 수집하는 통합 데이터 엔지니어링 솔루션입니다. Point-and-click UI와 간단한 API로 파이프라인을 자동 관리합니다.

### Q: Lakeflow Connect의 핵심 가치는?

**A:** 세 가지입니다:

1. **Simple setup and management**: 간단한 설정과 관리
2. **End-to-end efficiency**: 증분 읽기/쓰기로 다운스트림 처리 지원
3. **Unification with the lakehouse**: 거버넌스, 오케스트레이션, 모니터링 통합

### Q: 어떤 커넥터들이 있나요?

**A:** 크게 세 가지 카테고리:

- **Databases and data warehouses**: SQL Server, PostgreSQL, MySQL, Oracle, Snowflake 등
- **Applications**: Salesforce, SAP, Workday 등
- **File sources**: Excel, CSV, JSON 등
- **Streaming sources**: Kafka, Kinesis 등

### Q: Community Connectors가 뭔가요?

**A:** REST API가 있는 모든 소스에서 데이터를 수집할 수 있는 커스터마이징 가능한 커넥터입니다:

- **Unified governance**: 자격 증명, 파이프라인, 데이터, 계보 통합
- **Built-in tooling**: Observability, SCD Type 2, lineage 등
- **Flexibility**: Managed connectors보다 더 유연

### Q: 성능이 어떻게 개선되었나요?

**A:** 엄청난 개선이 있었습니다:

**증분 수집 개선**:

- **2-3배 빠름**
- **6-10배 저렴**

**데이터베이스 확장성 개선** (출시됨):

- 개선된 autoscaling
- 기본 코어 할당 감소 → **40% 게이트웨이 비용 절감**

**Managed file events** (FY27 계획):

- 10K 파일 수집 시간: 41분 → **1분**
- Max directory size: 10,000 → **무제한**
- Workspace당 file arrival triggers: 50 → **1,000개**

**Listing 성능 개선**:

- **3배** 빠른 디렉터리 listing
- **10배** 빠른 새 파일 발견
- **90%** 빠른 시작 시간
- **2-3배** 빠른 소형 파일 수집

### Q: Excel 지원은 어떤가요?

**A:** 이미 출시되었고 계속 개선 중입니다:

- 모든 주요 인터페이스 지원 (UI, DBSQL, Auto Loader)
- Multi-sheet 파일 지원: 하나의 파일에서 N개의 테이블 생성
- 파일 정리: 데이터 아일랜드, 고유 헤더 등 처리

---

## 5. Databricks Apps

### Q: Databricks Apps가 왜 필요한가요?

**A:** 핵심 가설은 **Data and AI Gravity**입니다:

- 엔터프라이즈 애플리케이션에 필요한 데이터와 AI는 이미 Databricks가 소유
- 데이터를 앱으로 이동시키는 것은 나쁨
- 데이터 과학/엔지니어링 팀은 데이터와 AI를 민주화하고 싶어함
- **앱은 데이터와 AI 옆에 있어야 함** (호스팅, 거버넌스, 인증, observability 포함)

### Q: 엔터프라이즈에서 앱 빌딩이 왜 어려운가요?

**A:** 여러 복잡한 작업이 필요합니다:

- Auth/SSO 통합
- 데이터 거버넌스와 접근 제어 정의
- 앱 인프라/컨테이너 관리
- VPC 통합
- 앱 상태 관리를 위한 데이터베이스 배포
- Observability 도구 통합
- 감사/접근 로그 설정
- 패키지/컨테이너 업그레이드

### Q: FY26 성과는 어떤가요?

**A:** 첫 해인 FY26는 대성공이었습니다:

- **$75M+ ARR** (직접)
- **3,500+ Active Accounts**
- **30,000개 Apps** (간접 $DBU 포함)
- **40,000+ 주간 활성 사용자**

**Apps 사용 분석**:

- 20,000+ Apps with DBSQL
- 10,000+ Apps with Model Serving
- 2,500+ Apps with Lakebase
- 2,000+ Apps with Genie Space
- 9,000+ Apps with Jobs

### Q: Databricks Apps의 장점은?

**A:** 세 가지 핵심 장점:

**1. Data Intelligence 기반**:

- Databricks의 모든 것과 연결 (SQL warehouse, Model Serving, Genie, Vector Search, Jobs 등)
- Out-of-the-box auth와 SSO
- **새로운 AppKit**으로 더 쉬운 통합

**2. Secure and Governed**:

- Databricks 관리형 컨테이너와 인프라 (3개 클라우드, 45+ 리전)
- Unity Catalog을 통한 리소스 레벨 거버넌스
- 기본 제공 auth와 접근 로그

**3. Open Ecosystem**:

- 모든 인기 Python 프레임워크 지원: Streamlit, Gradio, Dash, Shiny, FastAPI, Flask 등
- JavaScript 지원: Node.js/React
- 20개 이상 사전 설치 오픈소스 패키지

### Q: 어떤 종류의 앱을 만들 수 있나요?

**A:** 다양한 엔터프라이즈 앱을 만들 수 있습니다:

- Gen AI 기반 사기 탐지기
- 수요 예측 what-if 모델링 도구
- 제품 Q&A RAG 챗봇
- 항공사 수익 관리 시스템

### Q: Gartner는 어떻게 평가하나요?

**A:** Gartner가 새로운 **AI App Platform Magic Quadrant**를 발표했습니다. 우리는 여기서 선도적인 위치에 있어야 합니다. 우리만 이 기회를 보고 있는 게 아닙니다.

---

## 6. Lakebase

### Q: Lakebase가 뭔가요?

**A:** Databricks의 차세대 관리형 PostgreSQL 서비스입니다. Nikita Shamgunov(전 MemSQL CEO)가 발표했으며, AI 워크로드에 최적화된 데이터베이스입니다.

### Q: 왜 Lakebase가 중요한가요?

**A:** FY27의 최우선 과제 중 하나입니다:

- AI 에이전트의 메모리로 사용
- 애플리케이션 상태 저장
- 벡터 검색 지원
- 완전 관리형 서비스
- 자동 확장 및 고가용성

### Q: Lakebase의 주요 사용 사례는?

**A:**

- **Agent Memory**: AI 에이전트가 대화 컨텍스트와 상태를 저장
- **App Backend**: Databricks Apps의 백엔드 데이터베이스
- **Transactional Workloads**: OLTP 워크로드
- **Vector Store**: AI/ML 워크로드를 위한 벡터 검색

### Q: Lakebase AI가 뭔가요?

**A:** Lakebase에 AI 기능을 통합한 것입니다:

- 벡터 검색 네이티브 지원
- AI 함수 실행
- Lakehouse와의 긴밀한 통합

---

## 7. Unity Catalog ABAC

### Q: ABAC가 뭔가요?

**A:** **Attribute-Based Access Control**의 약자로, 속성 기반 접근 제어입니다. 기존의 역할 기반 접근 제어(RBAC)보다 더 세밀하고 유연한 접근 제어를 제공합니다.

### Q: 왜 ABAC가 필요한가요?

**A:** 복잡한 엔터프라이즈 환경에서:

- 사용자의 부서, 지역, 역할 등 여러 속성을 기반으로 접근 제어 필요
- 동적인 정책 관리
- 더 세밀한 데이터 거버넌스

### Q: Unity Catalog ABAC의 장점은?

**A:**

- **통합된 거버넌스**: 멀티클라우드 환경에서 중앙 집중식 관리
- **세밀한 제어**: Row-level, column-level 접근 제어
- **감사 로그**: 모든 접근 기록
- **데이터 계보**: 데이터 흐름 추적

---

## 8. Data Warehousing

### Q: Databricks의 DW 전략은?

**A:** Lakehouse 아키텍처를 기반으로 한 차세대 데이터 웨어하우스입니다:

- 데이터 레이크의 유연성 + 데이터 웨어하우스의 성능
- 단일 플랫폼에서 BI, AI/ML, Data Engineering 모두 수행
- Photon 엔진으로 최적화된 쿼리 성능

### Q: 기존 DW와의 차이점은?

**A:**

- **개방성**: 오픈 포맷 (Delta Lake, Parquet)
- **비용 효율성**: 스토리지와 컴퓨팅 분리
- **AI/ML 통합**: 동일한 데이터로 BI와 AI/ML 수행
- **멀티클라우드**: AWS, Azure, GCP 모두 지원

---

## 📝 인터뷰 팁

### 각 제품을 설명할 때:

1. **What** (뭔가요?): 한 문장으로 명확하게
2. **Why** (왜 중요한가요?): 고객의 pain point
3. **How** (어떻게 동작하나요?): 핵심 기능
4. **So What** (그래서 뭐?): 비즈니스 임팩트

### 숫자로 말하기:

- FY26 성과 (ARR, 고객 수, 성장률)
- 성능 개선 (N배 빠름, N% 비용 절감)
- 시장 포지션 (#1, 200% YoY 등)

### 경쟁사 대비 강점:

- **통합**: 모든 것이 하나의 플랫폼에
- **개방성**: 오픈 소스, 오픈 포맷
- **거버넌스**: Unity Catalog
- **AI 네이티브**: AI가 모든 곳에 내장

### 피해야 할 것:

- 너무 기술적인 세부 사항
- 약어/전문 용어 남발
- 경쟁사 비방
- 확실하지 않은 로드맵 약속

---

## 🎯 핵심 메시지

**TKO FY27의 핵심 메시지는:**

> "Databricks는 데이터와 AI를 민주화하는 통합 플랫폼입니다. Lakebase, Genie, Agent Bricks를 통해 모든 사용자가 데이터와 AI의 가치를 실현할 수 있게 합니다."

**FY27 전략:**

1. **Lakebase로 Agent 메모리와 App 백엔드 지원**
2. **Genie로 모든 사용자가 데이터 접근**
3. **AI Transformation으로 조직 혁신**
4. **Builder Culture로 FE 조직 강화**

