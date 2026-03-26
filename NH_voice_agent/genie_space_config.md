# NH Voice Agent - Genie Space 구성 가이드

## 개요
채권 상품 정보를 자연어로 검색하고 분석할 수 있는 Genie Space를 구성합니다.

## 데이터 소스
- **테이블**: `demo_ykko.nh_voice_agent.fundinfo`
- **데이터**: 28개 채권 종목 정보 (신용등급, 수익률, 만기일, 발행사 등)

## Genie Space 설정

### 1. 기본 정보
- **Display Name**: NH 채권 상품 정보
- **Warehouse**: 사용 가능한 SQL Warehouse 선택

### 2. Description
```
NH 증권의 채권 상품 데이터베이스입니다. 판매 중인 채권 종목의 신용등급, 수익률, 만기일, 발행사 정보 등을 제공합니다. 고객이 투자 조건에 맞는 채권을 검색하고 비교할 수 있도록 지원합니다.
```

### 3. Instructions
```
# 채권 상품 검색 가이드

## 데이터 특성
- **신용등급** (STK_CRD_GRDE_NM): AAA+, AAA, AA+, AA, A+, A, A-, BBB+, BBB 등
- **채권 유형** (BOND_CLS_CODE_NM): 1=국채, 2=지방채, 3=특수채, 4=통안채, 5=금융채, 6=회사채
- **판매 여부** (SALE_ALOW_YN): Y=현재 판매중, N=판매중지
- **수익률**:
  - TRDE_PRFT_RT: 매수수익률 (%)
  - EVLT_ERRT: 민평수익률 (%)
  - TAXA_ERRT: 세후수익률 (%)
- **만기 정보**:
  - REMAIN_DAYS: 잔존일수 (숫자)
  - EXPR_DT: 만기일자

## 검색 조건 처리 규칙

### 1. 등급 필터링
- "A- 이상", "A 이상" → STK_CRD_GRDE_NM IN ('A+', 'A', 'A-', 'AA-', 'AA', 'AA+', 'AAA-', 'AAA', 'AAA+')
- 등급은 문자열이므로 직접 비교 불가. IN 절 사용 필요

### 2. 회사채 필터
- "회사채" → BOND_CLS_CODE_NM = '6'

### 3. 민평금리보다 싼 조건
- "민평금리보다 싸다" → EVLT_ERRT < TRDE_PRFT_RT (민평수익률이 매수수익률보다 낮음)

### 4. 판매 중인 상품
- 명시되지 않아도 기본적으로 → SALE_ALOW_YN = 'Y'

### 5. 만기 조건
- "1년 미만" → REMAIN_DAYS < 365
- "2년 이내" → REMAIN_DAYS <= 730

### 6. 수익률 정렬
- "수익률 높은 순" → ORDER BY TRDE_PRFT_RT DESC
- 특별히 명시하지 않으면 매수수익률(TRDE_PRFT_RT) 기준

### 7. 발행사 검색
- "롯데캐피탈" → ISU_ORGN_NM LIKE '%롯데캐피탈%'

## 응답 형식
- 종목명 (STK_NM), 종목코드 (STK_CODE)
- 신용등급 (STK_CRD_GRDE_NM)
- 매수수익률 (TRDE_PRFT_RT) %
- 민평수익률 (EVLT_ERRT) % 및 차이 (스프레드)
- 잔존만기 (REMAIN_DAYS일 또는 n년 n일 형식)
- 발행사명 (ISU_ORGN_NM)

## 예제 질의

### Q1: "등급 A- 이상인 회사채 중 민평금리보다 싼 거 수익률 높은 순으로 알려줘"
```sql
SELECT STK_NM, STK_CODE, STK_CRD_GRDE_NM, TRDE_PRFT_RT, EVLT_ERRT, REMAIN_DAYS, ISU_ORGN_NM
FROM demo_ykko.nh_voice_agent.fundinfo
WHERE SALE_ALOW_YN = 'Y'
  AND BOND_CLS_CODE_NM = '6'
  AND STK_CRD_GRDE_NM IN ('A-', 'A', 'A+', 'AA-', 'AA', 'AA+', 'AAA-', 'AAA', 'AAA+')
  AND EVLT_ERRT < TRDE_PRFT_RT
ORDER BY TRDE_PRFT_RT DESC
```

### Q2: "만기가 1년 미만 남은 채권"
```sql
SELECT STK_NM, STK_CODE, STK_CRD_GRDE_NM, TRDE_PRFT_RT, REMAIN_DAYS, ISU_ORGN_NM
FROM demo_ykko.nh_voice_agent.fundinfo
WHERE SALE_ALOW_YN = 'Y'
  AND REMAIN_DAYS < 365
ORDER BY TRDE_PRFT_RT DESC
```

### Q3: "롯데캐피탈에서 발행한 채권을 비교해줘"
```sql
SELECT STK_NM, STK_CODE, STK_CRD_GRDE_NM, TRDE_PRFT_RT, EVLT_ERRT,
       INT_RT as 표면금리, REMAIN_DAYS, EXPR_DT, BYDY_SALE_QTY
FROM demo_ykko.nh_voice_agent.fundinfo
WHERE SALE_ALOW_YN = 'Y'
  AND ISU_ORGN_NM LIKE '%롯데캐피탈%'
ORDER BY TRDE_PRFT_RT DESC
```

## 주의사항
1. **등급 비교**: 문자열 직접 비교 불가. IN 절 사용
2. **민평금리 비교**: 수익률이 높을수록 가격이 싸므로 EVLT_ERRT < TRDE_PRFT_RT
3. **만기 계산**: REMAIN_DAYS는 숫자이므로 365일 = 1년으로 계산
4. **NULL 처리**: BYDY_SALE_QTY, GDS_SLCT_RSN은 NULL 가능
```

### 4. Sample Questions
```
1. 등급 A- 이상인 회사채 중 민평금리보다 싼 거 수익률 높은 순으로 알려줘
2. 만기가 1년 미만 남은 채권 중 수익률이 높은 종목은?
3. 롯데캐피탈에서 발행한 채권을 비교해줘
4. DL에너지 채권의 상세 정보를 알려줘
5. 신용등급 A+ 이상이고 잔존만기 2년 이내인 회사채는?
6. 판매량이 많은 채권 순위는?
7. 대한항공 채권 정보를 알려줘
8. 등급 BBB+ 이상, 수익률 3% 이상인 채권은?
```

## Databricks UI에서 Genie Space 생성 방법

1. Databricks 워크스페이스에서 **Genie** 메뉴로 이동
2. **New Space** 클릭
3. 위의 설정 정보를 입력:
   - Display Name
   - Description
   - Instructions
   - Sample Questions
4. **Tables**에 `demo_ykko.nh_voice_agent.fundinfo` 추가
5. **Create** 클릭

## 테스트 쿼리
Genie Space 생성 후 다음 질문들로 테스트:
- "판매중인 회사채를 모두 보여줘"
- "수익률 상위 5개 채권은?"
- "A 등급 채권만 보여줘"
