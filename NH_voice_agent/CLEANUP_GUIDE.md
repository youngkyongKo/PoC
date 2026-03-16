# 리소스 정리 가이드

## 생성된 리소스 목록

### 1. Knowledge Assistant
- **Endpoint Name**: `ka-69e8398a-endpoint`
- **Tile ID**: `69e8398a-b268-4732-b6cd-5c2b8051b349`
- **위치**: Databricks ML → Agent Bricks

### 2. Unity Catalog
- **Catalog**: `demo_ykko` (기존 사용 중)
- **Schema**: `demo_ykko.nh_voice_agent`
- **Volume**: `demo_ykko.nh_voice_agent.documents`
- **업로드된 파일**: PDF 문서들

---

## 🗑️ 리소스 삭제 방법

### Option A: UI에서 삭제 (권장 - 간단)

#### 1. Knowledge Assistant 삭제

**단계:**
1. Databricks Workspace 좌측 메뉴 → **Machine Learning**
2. **Agent Bricks** 클릭
3. **Knowledge Assistants** 탭 선택
4. `ka-69e8398a-endpoint` 찾기
5. 오른쪽 **⋮** (점 3개) 메뉴 클릭
6. **Delete** 선택
7. 확인 대화상자에서 **Delete** 클릭

**또는 직접 URL 접근:**
```
https://e2-demo-field-eng.cloud.databricks.com/ml/bricks/ka/configure/69e8398a-b268-4732-b6cd-5c2b8051b349
```
- 페이지 우측 상단 **Delete** 버튼 클릭

#### 2. Volume 및 파일 삭제

**단계:**
1. Databricks Workspace 좌측 메뉴 → **Data**
2. **Volumes** 탭 선택
3. `demo_ykko` → `nh_voice_agent` → `documents` 이동
4. 업로드한 PDF 파일들 선택
5. **Delete** 클릭

**Volume 전체 삭제 (선택사항):**
- `documents` volume에서 **⋮** 메뉴 → **Delete volume**

#### 3. Schema 삭제 (선택사항)

**주의**: Schema를 삭제하면 그 안의 모든 리소스가 삭제됩니다.

**단계:**
1. **Data** → **Schemas** 탭
2. `demo_ykko` → `nh_voice_agent` 찾기
3. **⋮** 메뉴 → **Delete schema**

---

### Option B: SQL로 삭제

#### 1. Volume 파일 삭제

Databricks SQL Warehouse나 Notebook에서:

```sql
-- 파일 목록 확인
LIST '/Volumes/demo_ykko/nh_voice_agent/documents/';

-- 개별 파일 삭제 (파일명 확인 후)
-- UI 또는 dbutils.fs.rm() 사용 권장
```

#### 2. Volume 삭제

```sql
DROP VOLUME IF EXISTS demo_ykko.nh_voice_agent.documents;
```

#### 3. Schema 삭제 (Volume 먼저 삭제 필요)

```sql
DROP SCHEMA IF EXISTS demo_ykko.nh_voice_agent CASCADE;
```

**주의**: `CASCADE`는 Schema 내 모든 객체를 함께 삭제합니다.

---

### Option C: Python (Databricks Notebook)으로 삭제

```python
from databricks.sdk import WorkspaceClient

client = WorkspaceClient()

# 1. KA 삭제
# KA는 Serving Endpoint이므로:
try:
    client.serving_endpoints.delete("ka-69e8398a-endpoint")
    print("✅ Knowledge Assistant 삭제 완료")
except Exception as e:
    print(f"⚠️  KA 삭제 실패: {e}")
    print("   UI에서 수동으로 삭제하세요.")

# 2. Volume 파일 삭제
volume_path = "/Volumes/demo_ykko/nh_voice_agent/documents"

# 파일 목록 확인
files = dbutils.fs.ls(volume_path)
print(f"총 {len(files)}개 파일:")
for file in files:
    print(f"  - {file.name}")

# 파일 삭제 (확인 후 주석 해제)
# for file in files:
#     dbutils.fs.rm(file.path)
#     print(f"삭제: {file.name}")

# 3. Volume 삭제
# spark.sql("DROP VOLUME IF EXISTS demo_ykko.nh_voice_agent.documents")

# 4. Schema 삭제 (선택사항)
# spark.sql("DROP SCHEMA IF EXISTS demo_ykko.nh_voice_agent CASCADE")
```

---

## ⚠️ 삭제 시 주의사항

### 삭제하면 안되는 것:
- **Catalog `demo_ykko`**: 기존에 사용 중인 catalog (다른 프로젝트에서 사용 가능)

### 삭제해도 되는 것:
1. ✅ **Knowledge Assistant** (`ka-69e8398a-endpoint`)
   - 테스트용으로만 생성
   - 삭제 후 재생성 가능

2. ✅ **Volume의 PDF 파일들**
   - 테스트용 샘플 파일
   - 필요시 재업로드 가능

3. ✅ **Volume** (`documents`)
   - 이번 PoC 전용
   - 삭제해도 무방

4. ✅ **Schema** (`nh_voice_agent`)
   - 이번 PoC 전용
   - 삭제해도 무방

### 삭제 순서 (권장):
```
1. Knowledge Assistant 삭제
   ↓
2. Volume의 파일들 삭제
   ↓
3. Volume 삭제 (선택)
   ↓
4. Schema 삭제 (선택)
```

---

## 🔄 내일 다시 시작하려면

### 리소스를 유지하는 경우:
- **KA 유지**: 계속 사용 가능 (비용 발생 가능)
- **Volume 유지**: PDF 파일 그대로 유지
- **장점**: 즉시 테스트 재개 가능

### 리소스를 삭제하는 경우:
- **비용 절감**: 사용하지 않는 리소스 삭제
- **내일 재생성 필요**:
  1. Volume 재생성 (1분)
  2. PDF 재업로드 (5분)
  3. KA 재생성 (5분)
  4. Sync 대기 (5분)

**총 재생성 시간**: 약 15-20분

---

## 💰 비용 고려사항

### Knowledge Assistant
- **Serving Endpoint 비용**: 사용하지 않아도 프로비저닝된 상태면 비용 발생
- **권장**: 오늘 삭제, 내일 재생성 (15분 소요)

### Volume (Storage)
- **스토리지 비용**: 매우 적음 (PDF 몇 개)
- **권장**: 유지해도 무방

---

## 📝 권장 정리 방법

### 최소 정리 (권장):
```
✅ Knowledge Assistant만 삭제
❌ Volume/파일은 유지
❌ Schema는 유지
```

**이유**:
- KA는 비용이 발생하지만 Volume은 거의 무료
- 내일 KA만 재생성하면 됨 (5분)

### 완전 정리:
```
✅ Knowledge Assistant 삭제
✅ Volume 파일 삭제
✅ Volume 삭제
✅ Schema 삭제
```

**이유**:
- 깔끔하게 정리
- 내일 처음부터 다시 시작 (20분 소요)

---

## 🚀 빠른 삭제 (UI 방식 - 2분 소요)

1. **KA 삭제** (1분):
   - ML → Agent Bricks → `ka-69e8398a-endpoint` 삭제

2. **(선택) Volume 파일 삭제** (1분):
   - Data → Volumes → `documents` → 파일 선택 후 삭제

**완료!** ✅

---

**질문이 있으면 내일 세션에서 다시 확인하겠습니다.**
