"""Simple text normalization without LLM (Phase 1 & 2)."""

import re
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Singleton Kiwi instance (expensive to initialize)
_kiwi_instance = None


def get_kiwi():
    """Get or create Kiwi instance (lazy initialization)."""
    global _kiwi_instance
    if _kiwi_instance is None:
        try:
            from kiwipiepy import Kiwi
            _kiwi_instance = Kiwi()
            logger.info("Kiwi morpheme analyzer initialized")
        except Exception as e:
            logger.warning(f"Could not initialize Kiwi: {e}")
            _kiwi_instance = None
    return _kiwi_instance


# ============================================================================
# Phase 1: Basic Normalization (0.1ms)
# ============================================================================

def basic_normalize(text: str) -> str:
    """
    Basic text normalization without external libraries.

    - Unicode normalization (NFC)
    - Whitespace cleanup
    - Punctuation removal
    - Special character cleanup

    Args:
        text: Input text

    Returns:
        Normalized text

    Example:
        "오늘  주문   수는???" -> "오늘 주문 수는"
    """
    # 1. Unicode normalization (NFC - Canonical Composition)
    text = unicodedata.normalize('NFC', text)

    # 2. Whitespace normalization
    text = re.sub(r'\s+', ' ', text.strip())

    # 3. Remove trailing punctuation
    text = re.sub(r'[?!.~,;]+$', '', text)

    # 4. Clean up special characters (keep Korean, alphanumeric, spaces)
    text = re.sub(r'[^\w\s가-힣0-9]', '', text)

    return text.strip()


# ============================================================================
# Phase 1: Temporal Expression Normalization (0.5ms)
# ============================================================================

def get_temporal_patterns() -> Dict[str, str]:
    """
    Get temporal expression patterns with current date.

    Returns:
        Dictionary of regex patterns to replacement strings
    """
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    return {
        # 상대적 날짜 표현
        r'오늘': today.strftime('%Y-%m-%d'),
        r'어제': yesterday.strftime('%Y-%m-%d'),
        r'그제': (today - timedelta(days=2)).strftime('%Y-%m-%d'),

        # 주 단위
        r'이번\s*주': 'THIS_WEEK',
        r'지난\s*주': 'LAST_WEEK',
        r'다음\s*주': 'NEXT_WEEK',

        # 월 단위
        r'이번\s*달': 'THIS_MONTH',
        r'지난\s*달': 'LAST_MONTH',
        r'다음\s*달': 'NEXT_MONTH',

        # 연 단위
        r'올해': 'THIS_YEAR',
        r'작년': 'LAST_YEAR',
        r'내년': 'NEXT_YEAR',
    }


def normalize_temporal(text: str) -> str:
    """
    Normalize temporal expressions to standard format.

    Args:
        text: Input text with temporal expressions

    Returns:
        Text with normalized temporal expressions

    Example:
        "오늘 주문 수는?" -> "2026-03-25 주문 수는"
        "이번 주 매출" -> "THIS_WEEK 매출"
    """
    patterns = get_temporal_patterns()

    for pattern, replacement in patterns.items():
        text = re.sub(pattern, replacement, text)

    return text


# ============================================================================
# Phase 1: Synonym Replacement (0.2ms)
# ============================================================================

# 동의어 사전
QUESTION_SYNONYMS = {
    # 수량 표현
    '몇 개': '수',
    '몇개': '수',
    '개수': '수',
    '갯수': '수',

    # 금액 표현
    '얼마': '금액',
    '금액은': '금액',

    # 합계 표현
    '합계': '총합',
    '총': '총합',
    '전체': '총합',

    # 질문 동사
    '보여줘': '조회',
    '보여주세요': '조회',
    '알려줘': '조회',
    '알려주세요': '조회',
    '알려주십시오': '조회',
    '알려 주세요': '조회',
    '보여 주세요': '조회',

    # 조사 제거용 (형태소 분석 전 간단 처리)
    '은은': '은',
    '는는': '는',
}


def apply_synonyms(text: str) -> str:
    """
    Replace synonyms with canonical forms.

    Args:
        text: Input text

    Returns:
        Text with synonyms replaced

    Example:
        "주문 몇 개?" -> "주문 수"
        "매출 얼마?" -> "매출 금액"
    """
    for old, new in QUESTION_SYNONYMS.items():
        text = text.replace(old, new)

    return text


# ============================================================================
# Phase 2: Morpheme-based Normalization (10ms)
# ============================================================================

def morpheme_normalize(text: str, use_kiwi: bool = True) -> str:
    """
    Extract key morphemes (nouns, verbs) and create normalized form.

    Args:
        text: Input text
        use_kiwi: Whether to use Kiwi morpheme analyzer

    Returns:
        Space-separated sorted morphemes

    Example:
        "오늘 주문 수는?" -> "수 오늘 주문"
        "주문 수는 오늘?" -> "수 오늘 주문" (same result)
    """
    if not use_kiwi:
        return text

    kiwi = get_kiwi()
    if kiwi is None:
        logger.warning("Kiwi not available, skipping morpheme normalization")
        return text

    try:
        # Tokenize
        tokens = kiwi.tokenize(text)

        # Extract meaningful morphemes (Nouns, Verbs, Adjectives)
        # N: 명사, V: 동사, A: 형용사
        keywords = [
            token.form for token in tokens
            if token.tag[0] in ['N', 'V', 'A'] and len(token.form) > 1
        ]

        # Remove duplicates and sort (order-independent)
        keywords = sorted(set(keywords))

        return ' '.join(keywords)

    except Exception as e:
        logger.error(f"Error in morpheme normalization: {e}")
        return text


# ============================================================================
# Combined Normalization Pipeline
# ============================================================================

def simple_normalize_phase1(text: str) -> str:
    """
    Phase 1 normalization (no external libraries).

    Total time: ~1ms
    Expected hit rate improvement: 40% -> 65%

    Args:
        text: Input text

    Returns:
        Normalized text
    """
    text = basic_normalize(text)
    text = normalize_temporal(text)
    text = apply_synonyms(text)
    return text


def simple_normalize_phase2(text: str) -> str:
    """
    Phase 2 normalization (with kiwipiepy).

    Total time: ~11ms
    Expected hit rate improvement: 65% -> 75%

    Args:
        text: Input text

    Returns:
        Morpheme-normalized text
    """
    text = simple_normalize_phase1(text)
    text = morpheme_normalize(text, use_kiwi=True)
    return text


def simple_normalize(text: str, phase: int = 2) -> str:
    """
    Convenience function for simple normalization.

    Args:
        text: Input text
        phase: Normalization phase (1 or 2)

    Returns:
        Normalized text
    """
    if phase == 1:
        return simple_normalize_phase1(text)
    elif phase == 2:
        return simple_normalize_phase2(text)
    else:
        raise ValueError(f"Invalid phase: {phase}. Must be 1 or 2.")
