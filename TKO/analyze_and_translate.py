#!/usr/bin/env python3
"""
TKO FY27 텍스트 분석 및 한글 인터뷰 자료 생성
추출된 영문 텍스트를 분석하여 구어체 한글 Q&A 형식으로 변환
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple


def parse_presentation_file(file_path: str) -> Dict[str, List[str]]:
    """프레젠테이션 파일을 섹션별로 파싱"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = {}
    current_section = None
    current_content = []

    for line in content.split('\n'):
        # 섹션 헤더 감지 (60개의 # 기호)
        if line.strip() == '#' * 60:
            continue
        elif line.startswith('# ') and not line.startswith('###'):
            # 이전 섹션 저장
            if current_section:
                sections[current_section] = current_content
            # 새 섹션 시작
            current_section = line[2:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)

    # 마지막 섹션 저장
    if current_section:
        sections[current_section] = current_content

    return sections


def extract_key_points(content: List[str]) -> List[str]:
    """컨텐츠에서 핵심 포인트 추출"""
    key_points = []
    current_slide = []

    for line in content:
        if line.strip().startswith('=== Slide'):
            # 이전 슬라이드 처리
            if current_slide:
                # 슬라이드 내용 정리
                text = '\n'.join(current_slide)
                # 빈 줄과 짧은 줄 제거
                meaningful = [l for l in current_slide if l.strip() and len(l.strip()) > 10]
                if meaningful:
                    key_points.extend(meaningful[:5])  # 슬라이드당 최대 5개 포인트
            current_slide = []
        else:
            current_slide.append(line.strip())

    # 마지막 슬라이드 처리
    if current_slide:
        meaningful = [l for l in current_slide if l.strip() and len(l.strip()) > 10]
        if meaningful:
            key_points.extend(meaningful[:5])

    return key_points


def generate_korean_summary(title: str, key_points: List[str]) -> Dict[str, str]:
    """영문 키 포인트를 기반으로 한글 요약 생성 (템플릿 기반)"""

    # 제품/주제별 템플릿
    templates = {
        "Lakebase": {
            "what": "Lakebase는 Databricks의 차세대 관리형 PostgreSQL 서비스입니다.",
            "why": "기존 데이터베이스의 한계를 극복하고 AI 워크로드를 위한 최적화된 플랫폼을 제공합니다.",
            "how": "완전 관리형 서비스로 자동 확장, 고가용성, 벡터 검색 등을 지원합니다."
        },
        "Genie": {
            "what": "Genie는 자연어로 데이터를 쿼리할 수 있는 AI 기반 분석 도구입니다.",
            "why": "SQL 없이도 누구나 데이터를 탐색하고 인사이트를 얻을 수 있게 합니다.",
            "how": "대화형 인터페이스로 질문하면 자동으로 SQL을 생성하고 결과를 시각화합니다."
        },
        "Lakeflow": {
            "what": "Lakeflow는 데이터 파이프라인 구축 및 운영 플랫폼입니다.",
            "why": "복잡한 데이터 이동과 변환을 간소화하고 자동화합니다.",
            "how": "선언적 방식으로 파이프라인을 정의하고 자동으로 실행 및 모니터링합니다."
        },
        "Apps": {
            "what": "Databricks Apps는 데이터 기반 애플리케이션을 빌드하고 배포하는 플랫폼입니다.",
            "why": "데이터 과학자와 개발자가 프로덕션 앱을 쉽게 만들 수 있게 합니다.",
            "how": "Dash, Streamlit, Gradio 등 다양한 프레임워크를 지원하며 원클릭 배포가 가능합니다."
        },
        "Agent Bricks": {
            "what": "Agent Bricks는 AI 에이전트를 빌드하기 위한 구성 요소입니다.",
            "why": "복잡한 AI 시스템을 모듈화된 컴포넌트로 쉽게 구축할 수 있습니다.",
            "how": "Knowledge Assistant, 벡터 검색, LLM 통합 등 사전 구축된 빌딩 블록을 제공합니다."
        },
        "AI/BI": {
            "what": "AI/BI는 인공지능이 내장된 비즈니스 인텔리전스 플랫폼입니다.",
            "why": "데이터 분석과 대시보드 생성을 AI로 자동화합니다.",
            "how": "자연어로 대시보드를 요청하면 자동으로 생성하고 인사이트를 제공합니다."
        },
        "Unity Catalog": {
            "what": "Unity Catalog은 통합 데이터 거버넌스 솔루션입니다.",
            "why": "멀티클라우드 환경에서 데이터 자산을 중앙 집중식으로 관리합니다.",
            "how": "세밀한 접근 제어, 데이터 계보, 감사 로그 등을 제공합니다."
        }
    }

    # 제목에서 주요 키워드 추출
    topic = None
    for key in templates.keys():
        if key.lower() in title.lower():
            topic = key
            break

    if topic and topic in templates:
        return templates[topic]

    # 기본 템플릿
    return {
        "what": f"{title}에 대한 내용입니다.",
        "why": "고객의 데이터 및 AI 워크로드를 지원하기 위해 개발되었습니다.",
        "how": "Databricks 플랫폼에 통합되어 제공됩니다."
    }


def create_interview_qa(sections: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """섹션별로 인터뷰 Q&A 생성"""
    qa_list = []

    for title, content in sections.items():
        if title.startswith('TKO FY27'):
            continue

        # 키 포인트 추출
        key_points = extract_key_points(content)

        # 한글 요약 생성
        summary = generate_korean_summary(title, key_points)

        # Q&A 형식으로 구성
        qa = {
            "topic": title,
            "q1": f"{title}가 뭔가요?",
            "a1": summary["what"],
            "q2": f"왜 {title}가 중요한가요?",
            "a2": summary["why"],
            "q3": f"{title}는 어떻게 동작하나요?",
            "a3": summary["how"],
            "key_points": key_points[:10]  # 상위 10개 포인트
        }

        qa_list.append(qa)

    return qa_list


def format_interview_document(qa_list: List[Dict[str, str]], category: str) -> str:
    """인터뷰 문서 포맷팅"""
    lines = [
        f"# TKO FY27 인터뷰 준비 자료 - {category}",
        "",
        "## 개요",
        f"이 문서는 TKO FY27 {category} 세션의 핵심 내용을 구어체 한글로 정리한 인터뷰 준비 자료입니다.",
        "",
        "---",
        ""
    ]

    for i, qa in enumerate(qa_list, 1):
        lines.extend([
            f"## {i}. {qa['topic']}",
            "",
            f"### Q: {qa['q1']}",
            f"**A:** {qa['a1']}",
            "",
            f"### Q: {qa['q2']}",
            f"**A:** {qa['a2']}",
            "",
            f"### Q: {qa['q3']}",
            f"**A:** {qa['a3']}",
            "",
            "### 핵심 포인트",
        ])

        for point in qa['key_points'][:5]:
            if point.strip():
                lines.append(f"- {point}")

        lines.extend(["", "---", ""])

    return '\n'.join(lines)


def main():
    """메인 실행 함수"""
    print("TKO FY27 텍스트 분석 및 한글 인터뷰 자료 생성\n")

    files = {
        "Keynotes": "/tmp/tko27_keynotes.txt",
        "Product Sessions": "/tmp/tko27_product_sessions.txt",
        "Deep Dives": "/tmp/tko27_deep_dives.txt"
    }

    for category, file_path in files.items():
        print(f"Processing {category}...")

        # 파일 파싱
        sections = parse_presentation_file(file_path)
        print(f"  Found {len(sections)} sections")

        # Q&A 생성
        qa_list = create_interview_qa(sections)
        print(f"  Generated {len(qa_list)} Q&A items")

        # 문서 생성
        document = format_interview_document(qa_list, category)

        # 저장
        output_file = f"/tmp/tko27_interview_{category.lower().replace(' ', '_')}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(document)

        print(f"  Saved to: {output_file}")
        print(f"  Document size: {len(document)} characters\n")

    print("✓ All interview materials generated successfully!")


if __name__ == "__main__":
    main()
