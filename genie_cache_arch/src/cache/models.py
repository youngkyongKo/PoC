"""Data models for Genie Cache Architecture."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class CacheSource(str, Enum):
    """Cache source types."""
    STATIC = "static"
    SEMANTIC = "semantic"
    NONE = "none"


class CacheEntry(BaseModel):
    """Cache entry model."""

    cache_key: str = Field(description="SHA256 hash of normalized question")
    original_question: str = Field(description="User's original question")
    normalized_question: str = Field(description="Normalized question")
    genie_sql: Optional[str] = Field(default=None, description="Generated SQL")
    genie_result: Optional[Dict[str, Any]] = Field(default=None, description="Query result")
    genie_description: Optional[str] = Field(default=None, description="Genie's interpretation")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for follow-ups")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    accessed_at: datetime = Field(default_factory=datetime.now, description="Last access timestamp")
    access_count: int = Field(default=1, description="Number of times accessed")
    ttl_seconds: int = Field(default=86400, description="TTL in seconds")

    # For semantic cache
    confidence_score: float = Field(default=1.0, description="Similarity score (1.0 for exact match)")
    source: CacheSource = Field(default=CacheSource.NONE, description="Cache source")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QueryMetrics(BaseModel):
    """Query execution metrics."""

    query_time: datetime = Field(default_factory=datetime.now, description="Query timestamp")
    original_question: str = Field(description="Original question")
    normalized_question: Optional[str] = Field(default=None, description="Normalized question")
    static_cache_hit: bool = Field(default=False, description="Static cache hit")
    semantic_cache_hit: bool = Field(default=False, description="Semantic cache hit")
    similarity_score: Optional[float] = Field(default=None, description="Semantic similarity score")
    response_time_ms: Optional[int] = Field(default=None, description="Response time in ms")
    genie_api_called: bool = Field(default=False, description="Genie API called")
    genie_api_retry_count: int = Field(default=0, description="Number of retries")
    error_message: Optional[str] = Field(default=None, description="Error message if any")
    user_id: Optional[str] = Field(default=None, description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")

    @property
    def cache_hit(self) -> bool:
        """Check if any cache was hit."""
        return self.static_cache_hit or self.semantic_cache_hit

    @property
    def cache_source(self) -> CacheSource:
        """Get cache source."""
        if self.static_cache_hit:
            return CacheSource.STATIC
        elif self.semantic_cache_hit:
            return CacheSource.SEMANTIC
        return CacheSource.NONE

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GenieQueryResult(BaseModel):
    """Genie query result model."""

    question: str = Field(description="Original question")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")
    message_id: Optional[str] = Field(default=None, description="Message ID")
    status: str = Field(description="Query status (COMPLETED, FAILED, etc.)")
    sql: Optional[str] = Field(default=None, description="Generated SQL")
    description: Optional[str] = Field(default=None, description="Query description")
    columns: Optional[List[str]] = Field(default=None, description="Result columns")
    data: Optional[List[List[Any]]] = Field(default=None, description="Result data")
    row_count: int = Field(default=0, description="Number of rows")
    text_response: Optional[str] = Field(default=None, description="Natural language response")
    error: Optional[str] = Field(default=None, description="Error message")

    @property
    def success(self) -> bool:
        """Check if query was successful."""
        return self.status == "COMPLETED" and self.error is None


class NormalizerState(BaseModel):
    """State for question normalization LangGraph."""

    original_question: str = Field(description="Original user question")
    normalized_question: Optional[str] = Field(default=None, description="Normalized question")
    semantic_key: Optional[str] = Field(default=None, description="Semantic key")
    temporal_info: Optional[Dict[str, Any]] = Field(default=None, description="Extracted temporal information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Processing timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SemanticSearchResult(BaseModel):
    """Semantic search result from Vector Search."""

    cache_key: str = Field(description="Cache key")
    normalized_question: str = Field(description="Normalized question")
    similarity_score: float = Field(description="Similarity score")
    genie_result: Optional[Dict[str, Any]] = Field(default=None, description="Cached result")
    genie_sql: Optional[str] = Field(default=None, description="Cached SQL")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")
    created_at: Optional[datetime] = Field(default=None, description="Cache entry timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
