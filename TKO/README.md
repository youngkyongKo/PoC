# TKO FY27 인터뷰 준비 가이드

## 개요
Databricks TKO FY27 콘텐츠를 기반으로 AI 인터뷰를 준비하기 위한 자료입니다.
Google Sheet에 정리된 TKO FY27 관련 PPT deck 25개(850+ 슬라이드)를 모두 읽고 인터뷰 질문에 답변하는 용도로 사용됩니다.
대화형으로 말로 답변하기 쉽게 단순 명료한 구어체 문장으로 정리합니다. 

## 소스 데이터
- **Google Sheet**: https://docs.google.com/spreadsheets/d/1KUWdUXgCHi4Ey5vU1qk0dMfxe8KsEHALx-tK59rI9yw/edit?gid=0#gid=0
- **Sheet 제목**: TKO FY27 Content (go/tko-decks)
- **Deck 링크 추출 방법**: Google Sheets API의 `chipRuns.chip.richLinkProperties.uri` 필드에서 하이퍼링크 추출 (일반 `hyperlink` 필드에는 없음)

## 추출된 Deck 목록 (25개)

### Keynotes (8개, 283 슬라이드)
| Session | Speaker | Presentation ID |
|---------|---------|----------------|
| Builder Culture and AI Transformation | Arsalan Tavakoli-Shiraji | 1dHI5TjY9OeCiuoNPj5K-w_8kPmuc1GWVbatAyuJxa_8 |
| Ali's Keynote | Ali Ghodsi | 1zHrKUbcmyxr7vbyhN-XDpgQyKbdu7A1WHOOl_KswNII |
| Day 1 Reyden | Reynold Xin et al. | 1uEnl_9J3TDc97nBOa5olM2PGNAnr_f6vA0CKgvMmzmU |
| Genie, DB One, AIBI | Reynold Xin et al. | 1qLbdHpDlxyU8e-5o1_Jm3uMiikz1uIo-wepwWqx3heQ |
| DW | Reynold Xin et al. | 10NLYLfSQKj-lp0x6ZB4UdxGasYdp9zXQ4BJNfHE_Y3s |
| Agent Bricks | Patrick Wendell, Hanlin Tang | 1XX7ctUSbM2m6uD916aAULXiLqng0c4w3116F3p_IoZo |
| Genie Code | Gal Oshri | 14Z-jbZ38fnJfd94RybW6DtScDpi0I8lbKSAt_Bxr2IA |
| Lakebase Keynote | Nikita Shamgunov | 1aOkyfO4YmWk0N-_Ya07fdlu2L5El2vhejm0aX9a8aZA |

### Product Sessions (6개, 285 슬라이드)
| Session | Speaker | Presentation ID |
|---------|---------|----------------|
| Databricks Apps | Justin DeBrabant | 13uMoP1ET_PjiljvXMjFnhyEDQTJOuYDqc562p2pI4AQ |
| Lakeflow Connect | Elise Georis | 1u23hxUS-uzSRWwq87uTTPvP8I0fEPgj3n21ZYr3mgJ8 |
| Lakeflow SDP Roadmap | Ray Zhu | 1NXeji-sZx0uNLXT3wtr1HJawrQ6WcKPSQIn4ek3CY6o |
| Managed Tables & DR | Sirui Sun | 14WMhb9k9DOiqMZ6XY4Gi908u_vVy9Eyy9yv7w3ZBf4Y |
| UC ABAC | Stefania Leone | 1PdXImloA-l72J_2l4v41Z5CjPQ2hLhqD3SDuwbmcDok |
| Hyperscalers Positioning | David Meyer | 1NezV2eTRXZdhKCITHQxPlXWGkChg-NLDisyfiomiZNQ |

### Deep Dives (8개) + Expo (3개, 475 슬라이드)
| Session | Speaker | Presentation ID |
|---------|---------|----------------|
| AI/BI + Genie | Eric Lind, Afsana Afzal | 1tezCL5kFUoQqo8s4qmsbIowAPFiGge49V2-DbaVOOfA |
| Lakebase AI | Yanic Motte, Firas Farah | 1tfAQF9ZOCqwlyqwGONopEH8PxRxTOMo9gVX9DsYbK3o |
| Lakebridge | Guenia Izquierdo et al. | 1mHYX2D9-h86VEMytd9uw85fUEdUpMbiHuhwrQJ1PTdg |
| Lakeflow SDP | Tomasz Bacewicz | 1pG3SgUhEjFvI2KGJ0eNQfq3jU3pR1EggGe2q1aVyVjI |
| Apps | Pascal Vogel et al. | 1mw4uhjhgQ2Ttgz3FIP3nDh0ZClqBEiIKqZyEBrX7p-Q |
| Enablement AI Engineering | Matthew McCoy | 1bM4fWbvJBcIJpf19Qx2umsTiouKXN09GGJZ8TqK-rgI |
| Lakeflow Connect Community Connectors | Romy Li, Manjul Singhal | 1iG4bx4EYFDaor618_AeFmVbaD-fISGDCpYg43juuh0g |
| Open Lakehouse | Michelle Leon et al. | 1W2Vmo8JQw9iOzQ3FRMog3xUBLa5AELEJtnFZBY7eeCM |
| Expo MFG | Reishin Toolsi et al. | 1ZCRUDKvWP7G3mcMUXHXXiwwf9oUh5azL_uEXowbeKi4 |
| FINS Lakebase | Anindita Mahapatra | 1E2mQZ2f00YSRL8sqhJC31i_qSoVVuEf0X1d568JF8lg |
| Lakebase HLS | Surya Sai Turaga | 1DmA9jzUuNc12GdvjJczBhie7_gsYN2OoLS32rkjP8nc |

## 추출된 텍스트 파일 위치 
- `/tmp/tko27_keynotes.txt` 
- `/tmp/tko27_product_sessions.txt` 
- `/tmp/tko27_deep_dives.txt` 

## 재현 방법

### 1. Google Sheet에서 Deck 링크 추출
```bash
TOKEN=$(gcloud auth application-default print-access-token)
SHEET_ID="1KUWdUXgCHi4Ey5vU1qk0dMfxe8KsEHALx-tK59rI9yw"

# chipRuns에서 링크 추출 (일반 hyperlink 필드에는 없음)
curl -s "https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}?includeGridData=true&ranges=Sheet1%21D4%3AD31" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-goog-user-project: gcp-sandbox-field-eng" | python3 -c "
import json, sys, re
data = json.loads(sys.stdin.read())
rows = data['sheets'][0]['data'][0].get('rowData', [])
for i, row in enumerate(rows):
    for v in row.get('values', [{}]):
        text = v.get('formattedValue', '')
        for chip in v.get('chipRuns', []):
            uri = chip.get('chip', {}).get('richLinkProperties', {}).get('uri', '')
            if uri:
                m = re.search(r'/d/([^/]+)', uri)
                if m: print(f'{text[:60]} -> {m.group(1)}')
"
```

### 2. Google Slides에서 텍스트 추출
```bash
TOKEN=$(gcloud auth application-default print-access-token)
PRES_ID="<presentation_id>"

curl -s "https://slides.googleapis.com/v1/presentations/${PRES_ID}?fields=slides.pageElements.shape.text,slides.slideProperties.notesPage.pageElements.shape.text" \
  -H "Authorization: Bearer $TOKEN" \
  -H "x-goog-user-project: gcp-sandbox-field-eng" | python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
for i, slide in enumerate(data.get('slides', [])):
    print(f'\n=== Slide {i+1} ===')
    for pe in slide.get('pageElements', []):
        for elem in pe.get('shape', {}).get('text', {}).get('textElements', []):
            content = elem.get('textRun', {}).get('content', '').strip()
            if content: print(content)
"
```
