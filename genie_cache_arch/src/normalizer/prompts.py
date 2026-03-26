"""Prompts for question normalization (Korean-optimized)."""

from datetime import datetime

# Current date for temporal reference resolution
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")


TEMPORAL_EXTRACTION_PROMPT = f"""You are a temporal reference extraction specialist for Korean language queries.

**Current Date:** {CURRENT_DATE}

**Task:** Extract temporal references from the user's question and convert them to absolute dates.

**Korean Temporal References:**
- "오늘" → {CURRENT_DATE}
- "어제" → (current date - 1 day)
- "내일" → (current date + 1 day)
- "이번 주" → (current week range)
- "지난 주" → (previous week range)
- "이번 달" → (current month range)
- "지난 달" → (previous month range)
- "올해" → (current year range)
- "작년" → (previous year range)

**Output Format (JSON):**
{{
    "has_temporal": true/false,
    "temporal_type": "day|week|month|year|range|none",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "original_phrase": "오늘|어제|...",
    "explanation": "Brief explanation of extraction"
}}

**Example:**
Question: "오늘 주문 수는?"
Output: {{"has_temporal": true, "temporal_type": "day", "start_date": "{CURRENT_DATE}", "end_date": "{CURRENT_DATE}", "original_phrase": "오늘", "explanation": "Current date"}}

**Question:** {{question}}

**Output (JSON only):**"""


STANDARDIZATION_PROMPT = """You are a question standardization specialist for caching optimization.

**Task:** Normalize the question to improve cache hit ratio while preserving semantic meaning.

**Normalization Rules:**
1. **Remove unnecessary words**: Remove filler words, politeness markers, question particles
   - "좀", "요", "한번", "주세요" → remove
   - "있어요?", "있나요?", "있습니까?" → "있는가?"

2. **Standardize question patterns**:
   - "몇 개?", "몇개?", "개수?" → "수"
   - "어떻게?", "어떻게 되나요?" → "방법"
   - "언제?", "언제쯤?" → "시점"

3. **Replace temporal references**: Use extracted temporal info
   - If temporal_info provided, replace temporal phrases with absolute dates
   - "오늘 주문" → "{{start_date}} 주문"

4. **Preserve business entities**: Keep domain-specific terms unchanged
   - Product names, metrics, operations

5. **Lowercase and trim**: Convert to lowercase, remove extra whitespace

**Input:**
- Original question: {{original_question}}
- Temporal info: {{temporal_info}}

**Output Format (JSON):**
{{
    "normalized_question": "standardized question text",
    "changes_made": ["list of normalization changes"],
    "preserved_terms": ["domain-specific terms kept"]
}}

**Output (JSON only):**"""


SEMANTIC_KEY_PROMPT = """You are a semantic key generation specialist.

**Task:** Generate a semantic key that captures the core intent and entities of the question.

**Semantic Key Format:**
`intent|entity1|entity2|temporal_scope`

**Components:**
1. **intent**: What the user wants (count, sum, list, compare, etc.)
2. **entity**: Main business entity (orders, customers, products, etc.)
3. **temporal_scope**: When (today, this_week, this_month, YYYY-MM-DD, etc.)

**Examples:**
- "오늘 주문 수는?" → "count|orders|today"
- "이번 달 매출 합계" → "sum|revenue|this_month"
- "고객 목록 보여줘" → "list|customers|all_time"
- "2024-01-01 주문 건수" → "count|orders|2024-01-01"

**Input:**
- Normalized question: {{normalized_question}}
- Temporal info: {{temporal_info}}

**Output Format (JSON):**
{{
    "semantic_key": "intent|entity|temporal_scope",
    "intent": "count|sum|list|compare|...",
    "entities": ["primary", "secondary"],
    "temporal_scope": "today|this_week|...",
    "confidence": 0.0-1.0
}}

**Output (JSON only):**"""


def get_temporal_extraction_prompt(question: str) -> str:
    """Get temporal extraction prompt with current question."""
    return TEMPORAL_EXTRACTION_PROMPT.replace("{question}", question)


def get_standardization_prompt(
    original_question: str,
    temporal_info: dict
) -> str:
    """Get standardization prompt with question and temporal info."""
    import json
    prompt = STANDARDIZATION_PROMPT.replace("{original_question}", original_question)
    prompt = prompt.replace("{temporal_info}", json.dumps(temporal_info, ensure_ascii=False))
    return prompt


def get_semantic_key_prompt(
    normalized_question: str,
    temporal_info: dict
) -> str:
    """Get semantic key prompt with normalized question and temporal info."""
    import json
    prompt = SEMANTIC_KEY_PROMPT.replace("{normalized_question}", normalized_question)
    prompt = prompt.replace("{temporal_info}", json.dumps(temporal_info, ensure_ascii=False))
    return prompt
