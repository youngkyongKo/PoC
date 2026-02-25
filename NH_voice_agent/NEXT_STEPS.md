# 다음 작업 세션을 위한 가이드

## 📌 현재까지 완료된 작업

### ✅ Phase 1: 음성 인터페이스 완료 (2025-02-25)

**구현된 기능:**
- 🎤 음성 입력 → 텍스트 변환 (STT)
- 🤖 Dummy Agent 처리
- 🔊 음성 출력 (TTS)
- 💬 텍스트 입력 대체 옵션
- 📝 대화 기록 및 오디오 재생

**해결된 기술 이슈:**
- Audio recorder 무한 루프
- STT 간헐적 실패 (FFmpeg, 포맷 변환)
- TTS 오디오 재생 (session state 저장)

## 🎯 다음 세션에서 할 일

### Option 1: RAG Pipeline 구현 (권장)
실제 Databricks 기능 구현 시작

```bash
# 1. Unity Catalog 설정
python setup_uc.py

# 2. PDF 샘플 준비
mkdir -p 1_rag_pipeline/sample_docs/
# PDF 파일들을 sample_docs/에 복사

# 3. RAG 파이프라인 구현
# - 1_rag_pipeline/01_pdf_parser.py
# - 1_rag_pipeline/02_chunking.py
# - 1_rag_pipeline/03_vector_index.py
```

**필요한 정보:**
- Unity Catalog 이름 (catalog, schema, volume)
- Vector Search endpoint 이름
- Embedding 모델 선택 (databricks-bge-large-en)

### Option 2: Agent Tools 구현
LangChain 기반 실제 에이전트 개발

```bash
# Vector Search Tool
vim 2_agent/tools/vector_search_tool.py

# Genie Space Tool
vim 2_agent/tools/genie_tool.py

# Supervisor Agent
vim 2_agent/supervisor_agent.py
```

### Option 3: Voice App 개선
현재 음성 인터페이스 고도화

- 다국어 지원 (영어/한국어 전환)
- Premium TTS 엔진 (SSML, 감정 표현)
- 음성 품질 향상 (노이즈 제거)
- UI/UX 개선

## 🚀 빠른 재시작

### 환경 설정
```bash
cd /Users/yk.ko/git/PoC/NH_voice_agent
source venv/bin/activate
```

### 현재 기능 테스트
```bash
# Streamlit 앱
streamlit run 3_voice_app/app_simple.py

# CLI 테스트
python test_voice_flow.py
```

### Git 동기화
```bash
# Remote에 푸시 (권장)
git push origin main

# Databricks Workspace에서 Pull
# Repos → [your repo] → Pull
```

## 📚 참고 문서

- **상세 진행 상황:** [README_PROGRESS.md](README_PROGRESS.md)
- **프로젝트 개요:** [README.md](README.md)
- **설정 파일:** `.env`, `config.py`

## 🔧 필요한 도구 확인

### 로컬 환경
- [x] Python 3.10+ with venv
- [x] FFmpeg (`brew list ffmpeg`)
- [x] Git
- [ ] Databricks CLI (필요시)

### Databricks Workspace
- [ ] Unity Catalog 설정
- [ ] Vector Search endpoint
- [ ] SQL Warehouse (Genie)
- [ ] ML Runtime Cluster

## 💡 다음 작업 추천 순서

1. **Git Push** (현재 작업 백업)
   ```bash
   git push origin main
   ```

2. **RAG Pipeline 시작** (핵심 기능)
   - Unity Catalog 구조 설계
   - PDF 파싱 모듈 구현
   - Vector Search 인덱스 생성

3. **Agent Tools 개발** (실제 AI 기능)
   - Vector Search Tool
   - Genie Space Tool
   - LangChain Supervisor

4. **통합 테스트** (End-to-End)
   - Voice App ↔ Real Agent 연동
   - 전체 플로우 검증

## ❓ 질문이 있다면

1. Databricks 연결 이슈
   ```bash
   python check_models.py
   ```

2. 음성 인식 문제
   - FFmpeg 설치 확인: `ffmpeg -version`
   - 마이크 권한 확인 (브라우저 설정)

3. 프로젝트 구조 이해
   - README_PROGRESS.md 전체 읽기
   - 각 모듈 README 확인

---

**Last Updated:** 2025-02-25
**Current Branch:** main
**Last Commit:** feat: 음성 인터페이스 Phase 1 완료
