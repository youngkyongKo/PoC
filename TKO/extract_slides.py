#!/usr/bin/env python3
"""
TKO FY27 Google Slides 텍스트 추출 스크립트
Google Slides API를 사용하여 프레젠테이션에서 텍스트를 추출합니다.
"""

import json
import subprocess
import sys
from typing import List
import os
import google.auth
import google.auth.transport.requests

# README에서 추출한 프레젠테이션 ID
PRESENTATIONS = {
    "keynotes": [
        ("Builder Culture and AI Transformation", "1dHI5TjY9OeCiuoNPj5K-w_8kPmuc1GWVbatAyuJxa_8"),
        ("Ali's Keynote", "1zHrKUbcmyxr7vbyhN-XDpgQyKbdu7A1WHOOl_KswNII"),
        ("Day 1 Reyden", "1uEnl_9J3TDc97nBOa5olM2PGNAnr_f6vA0CKgvMmzmU"),
        ("Genie, DB One, AIBI", "1qLbdHpDlxyU8e-5o1_Jm3uMiikz1uIo-wepwWqx3heQ"),
        ("DW", "10NLYLfSQKj-lp0x6ZB4UdxGasYdp9zXQ4BJNfHE_Y3s"),
        ("Agent Bricks", "1XX7ctUSbM2m6uD916aAULXiLqng0c4w3116F3p_IoZo"),
        ("Genie Code", "14Z-jbZ38fnJfd94RybW6DtScDpi0I8lbKSAt_Bxr2IA"),
        ("Lakebase Keynote", "1aOkyfO4YmWk0N-_Ya07fdlu2L5El2vhejm0aX9a8aZA"),
    ],
    "product_sessions": [
        ("Databricks Apps", "13uMoP1ET_PjiljvXMjFnhyEDQTJOuYDqc562p2pI4AQ"),
        ("Lakeflow Connect", "1u23hxUS-uzSRWwq87uTTPvP8I0fEPgj3n21ZYr3mgJ8"),
        ("Lakeflow SDP Roadmap", "1NXeji-sZx0uNLXT3wtr1HJawrQ6WcKPSQIn4ek3CY6o"),
        ("Managed Tables & DR", "14WMhb9k9DOiqMZ6XY4Gi908u_vVy9Eyy9yv7w3ZBf4Y"),
        ("UC ABAC", "1PdXImloA-l72J_2l4v41Z5CjPQ2hLhqD3SDuwbmcDok"),
        ("Hyperscalers Positioning", "1NezV2eTRXZdhKCITHQxPlXWGkChg-NLDisyfiomiZNQ"),
    ],
    "deep_dives": [
        ("AI/BI + Genie", "1tezCL5kFUoQqo8s4qmsbIowAPFiGge49V2-DbaVOOfA"),
        ("Lakebase AI", "1tfAQF9ZOCqwlyqwGONopEH8PxRxTOMo9gVX9DsYbK3o"),
        ("Lakebridge", "1mHYX2D9-h86VEMytd9uw85fUEdUpMbiHuhwrQJ1PTdg"),
        ("Lakeflow SDP", "1pG3SgUhEjFvI2KGJ0eNQfq3jU3pR1EggGe2q1aVyVjI"),
        ("Apps", "1mw4uhjhgQ2Ttgz3FIP3nDh0ZClqBEiIKqZyEBrX7p-Q"),
        ("Enablement AI Engineering", "1bM4fWbvJBcIJpf19Qx2umsTiouKXN09GGJZ8TqK-rgI"),
        ("Lakeflow Connect Community Connectors", "1iG4bx4EYFDaor618_AeFmVbaD-fISGDCpYg43juuh0g"),
        ("Open Lakehouse", "1W2Vmo8JQw9iOzQ3FRMog3xUBLa5AELEJtnFZBY7eeCM"),
        ("Expo MFG", "1ZCRUDKvWP7G3mcMUXHXXiwwf9oUh5azL_uEXowbeKi4"),
        ("FINS Lakebase", "1E2mQZ2f00YSRL8sqhJC31i_qSoVVuEf0X1d568JF8lg"),
        ("Lakebase HLS", "1DmA9jzUuNc12GdvjJczBhie7_gsYN2OoLS32rkjP8nc"),
    ]
}


def get_access_token() -> str:
    """Application Default Credentials에서 액세스 토큰 가져오기"""
    import google.auth
    import google.auth.transport.requests

    try:
        # Application Default Credentials 사용
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/presentations.readonly']
        )

        # 토큰 새로고침
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)

        return credentials.token
    except Exception as e:
        print(f"Error getting access token: {e}", file=sys.stderr)
        print("Please run: gcloud auth application-default login --scopes=https://www.googleapis.com/auth/presentations.readonly", file=sys.stderr)
        sys.exit(1)


def extract_text_from_presentation(pres_id: str, token: str) -> List[str]:
    """프레젠테이션에서 텍스트 추출"""
    url = f"https://slides.googleapis.com/v1/presentations/{pres_id}?fields=slides.pageElements.shape.text"

    result = subprocess.run(
        ["curl", "-s", url,
         "-H", f"Authorization: Bearer {token}",
         "-H", "x-goog-user-project: gcp-sandbox-field-eng"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Error fetching presentation {pres_id}: {result.stderr}", file=sys.stderr)
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON for {pres_id}: {e}", file=sys.stderr)
        return []

    if 'error' in data:
        print(f"API Error: {data['error'].get('message', 'Unknown error')}", file=sys.stderr)
        return []

    slides_text = []
    for i, slide in enumerate(data.get('slides', [])):
        slide_content = [f"\n=== Slide {i+1} ==="]

        for pe in slide.get('pageElements', []):
            shape = pe.get('shape', {})
            text_obj = shape.get('text', {})
            for elem in text_obj.get('textElements', []):
                text_run = elem.get('textRun', {})
                content = text_run.get('content', '').strip()
                if content:
                    slide_content.append(content)

        if len(slide_content) > 1:  # 헤더 외에 내용이 있으면
            slides_text.extend(slide_content)

    return slides_text


def main():
    """메인 실행 함수"""
    print("Getting access token...")
    token = get_access_token()
    print("✓ Access token obtained\n")

    for category, presentations in PRESENTATIONS.items():
        print(f"\n{'='*60}")
        print(f"Processing {category.upper().replace('_', ' ')}")
        print(f"{'='*60}")

        all_text = []
        all_text.append(f"# TKO FY27 - {category.upper().replace('_', ' ')}\n")

        for title, pres_id in presentations:
            print(f"  Extracting: {title}... ", end='', flush=True)

            text = extract_text_from_presentation(pres_id, token)

            if text:
                all_text.append(f"\n\n{'#'*60}")
                all_text.append(f"# {title}")
                all_text.append(f"{'#'*60}")
                all_text.extend(text)
                print(f"✓ ({len(text)} elements)")
            else:
                print("✗ (failed or empty)")

        # 파일로 저장
        output_file = f"/tmp/tko27_{category}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_text))

        print(f"\n  Saved to: {output_file}")
        print(f"  Total lines: {len(all_text)}")


if __name__ == "__main__":
    main()
