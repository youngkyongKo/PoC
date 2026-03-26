"""State definitions for Question Normalization LangGraph."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class NormalizerState(BaseModel):
    """State for question normalization LangGraph."""

    # Input
    original_question: str = Field(description="Original user question")

    # Processing
    temporal_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted temporal information"
    )
    normalized_question: Optional[str] = Field(
        default=None,
        description="Normalized question"
    )
    semantic_key: Optional[str] = Field(
        default=None,
        description="Semantic key for caching"
    )

    # Metadata
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Processing timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
