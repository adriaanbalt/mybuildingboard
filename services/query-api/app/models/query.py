"""
Query Request/Response Models

Pydantic models for query API requests and responses.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Query request model."""
    query: str = Field(..., description="User query text", min_length=1, max_length=1000)
    app_id: Optional[str] = Field(None, description="App ID (optional if in JWT or header)")
    top_k: Optional[int] = Field(5, description="Number of chunks to retrieve", ge=1, le=20)
    similarity_threshold: Optional[float] = Field(0.0, description="Minimum similarity score", ge=0.0, le=1.0)
    conversation_id: Optional[str] = Field(None, description="Conversation/thread ID for follow-up questions")
    include_sources: Optional[bool] = Field(True, description="Include source citations in response")
    response_format: Optional[str] = Field("text", description="Response format: 'text', 'html', or 'plain'")


class Source(BaseModel):
    """Source citation model."""
    chunk_id: str
    email_id: str
    email_subject: Optional[str] = None
    attachment_id: Optional[str] = None
    attachment_filename: Optional[str] = None
    similarity: float
    content_preview: Optional[str] = Field(None, description="Preview of chunk content")


class TokenUsage(BaseModel):
    """Token usage statistics."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: Optional[float] = Field(None, description="Estimated cost in USD")


class QueryResponse(BaseModel):
    """Query response model."""
    answer: str = Field(..., description="Generated answer with inline citations")
    sources: List[Source] = Field(default_factory=list, description="Source citations")
    query_id: Optional[str] = Field(None, description="Query ID for logging")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    token_usage: Optional[TokenUsage] = Field(None, description="Token usage statistics")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[dict] = Field(default_factory=dict, description="Error details")
