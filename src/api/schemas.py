"""
OpenAPI/Pydantic schemas for SimpleMem API.

Provides type-safe request/response models and auto-generated API documentation.

Usage:
    from fastapi import FastAPI
    from src.api.schemas import AnalysisRequest, AnalysisResponse
    
    app = FastAPI()
    
    @app.post("/api/v1/analyze")
    async def analyze(request: AnalysisRequest) -> AnalysisResponse:
        result = analyzer.analyze(request.text)
        return AnalysisResponse(result=result)
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
import logging

logger = logging.getLogger(__name__)


# ==================== Request Models ====================

class AnalysisRequest(BaseModel):
    """Request model for text analysis."""
    
    text: str = Field(
        ..., 
        min_length=1, 
        max_length=10000,
        description="Text to analyze"
    )
    include_sentiment: bool = Field(
        default=True,
        description="Include sentiment analysis"
    )
    include_summary: bool = Field(
        default=False,
        description="Include text summary"
    )
    include_entities: bool = Field(
        default=False,
        description="Include entity linking"
    )
    summary_ratio: float = Field(
        default=0.3,
        ge=0.1,
        le=0.9,
        description="Summary compression ratio (0.1-0.9)"
    )
    
    @field_validator('text')
    @classmethod
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty or whitespace-only')
        return v


class SearchRequest(BaseModel):
    """Request model for semantic search."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results"
    )
    include_score: bool = Field(
        default=True,
        description="Include similarity scores"
    )


class ClusteringRequest(BaseModel):
    """Request model for document clustering."""
    
    documents: List[str] = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="Documents to cluster"
    )
    num_clusters: Optional[int] = Field(
        default=None,
        ge=2,
        le=100,
        description="Number of clusters (auto if None)"
    )
    algorithm: str = Field(
        default="kmeans",
        description="Clustering algorithm: kmeans, hierarchical, dbscan"
    )


class BatchAnalysisRequest(BaseModel):
    """Request model for batch analysis."""
    
    documents: List[str] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Documents to analyze"
    )
    analysis_type: str = Field(
        default="sentiment",
        description="Type of analysis"
    )


# ==================== Response Models ====================

class SentimentResult(BaseModel):
    """Sentiment analysis result."""
    
    polarity: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Sentiment polarity (-1.0 to 1.0)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)"
    )
    label: str = Field(
        ...,
        description="Sentiment label: very_negative, negative, neutral, positive, very_positive"
    )
    emotions: Optional[Dict[str, float]] = Field(
        default=None,
        description="Detected emotions with scores"
    )


class SummaryResult(BaseModel):
    """Text summarization result."""
    
    original_length: int = Field(..., description="Original text length")
    summary_length: int = Field(..., description="Summary length")
    compression_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Compression ratio (0.0-1.0)"
    )
    summary: str = Field(..., description="Summarized text")
    keywords: List[str] = Field(
        default_factory=list,
        description="Key terms from summary"
    )


class Entity(BaseModel):
    """Named entity."""
    
    text: str = Field(..., description="Entity text")
    entity_type: str = Field(..., description="Entity type")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Recognition confidence"
    )
    start: int = Field(..., ge=0, description="Start position in text")
    end: int = Field(..., ge=0, description="End position in text")


class EntityResult(BaseModel):
    """Entity linking result."""
    
    entities: List[Entity] = Field(default_factory=list, description="Detected entities")
    count: int = Field(..., description="Total entity count")
    types: Dict[str, int] = Field(
        default_factory=dict,
        description="Entity type counts"
    )


class AnalysisResponse(BaseModel):
    """Complete analysis response."""
    
    text_preview: str = Field(..., max_length=200, description="Text preview")
    sentiment: Optional[SentimentResult] = Field(
        default=None,
        description="Sentiment analysis result"
    )
    summary: Optional[SummaryResult] = Field(
        default=None,
        description="Summary result"
    )
    entities: Optional[EntityResult] = Field(
        default=None,
        description="Entity linking result"
    )
    processing_time_ms: float = Field(
        ...,
        ge=0,
        description="Processing time in milliseconds"
    )


class SearchResult(BaseModel):
    """Single search result."""
    
    id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Document text preview")
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity score"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )


class SearchResponse(BaseModel):
    """Search response."""
    
    query: str = Field(..., description="Search query")
    results: List[SearchResult] = Field(
        default_factory=list,
        description="Search results"
    )
    total: int = Field(..., ge=0, description="Total results found")
    processing_time_ms: float = Field(
        ...,
        ge=0,
        description="Query processing time"
    )


class ClusterInfo(BaseModel):
    """Information about a cluster."""
    
    cluster_id: int = Field(..., ge=0, description="Cluster identifier")
    size: int = Field(..., ge=1, description="Number of documents in cluster")
    label: Optional[str] = Field(None, description="Cluster label/topic")
    silhouette_score: Optional[float] = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="Silhouette score"
    )


class ClusteringResponse(BaseModel):
    """Document clustering response."""
    
    num_clusters: int = Field(..., ge=2, description="Number of clusters")
    clusters: List[ClusterInfo] = Field(
        default_factory=list,
        description="Cluster information"
    )
    assignments: List[int] = Field(
        default_factory=list,
        description="Document cluster assignments"
    )
    silhouette_avg: Optional[float] = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="Average silhouette score"
    )
    processing_time_ms: float = Field(
        ...,
        ge=0,
        description="Processing time"
    )


# ==================== Error Models ====================

class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    status_code: int = Field(..., ge=400, le=599, description="HTTP status code")
    request_id: Optional[str] = Field(
        None,
        description="Request ID for tracking"
    )


# ==================== Health & Status Models ====================

class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Service status: healthy, degraded, unhealthy")
    version: str = Field(..., description="API version")
    timestamp: str = Field(..., description="Response timestamp")
    components: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of individual components"
    )


class StatsResponse(BaseModel):
    """API statistics response."""
    
    uptime_seconds: int = Field(..., ge=0, description="Uptime in seconds")
    requests_total: int = Field(..., ge=0, description="Total requests processed")
    requests_per_second: float = Field(..., ge=0, description="Current RPS")
    error_rate_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Error rate percentage"
    )
    avg_response_time_ms: float = Field(..., ge=0, description="Average response time")
    cache_hit_rate_percent: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Cache hit rate"
    )
