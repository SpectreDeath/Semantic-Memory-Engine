"""
Advanced input validation with Pydantic models and sanitization.

Provides comprehensive validation for all API inputs with schema enforcement,
automatic sanitization, and detailed error reporting.

Features:
- Pydantic models for type safety
- Custom validators for business logic
- Automatic input sanitization
- Detailed error messages
- Rate limiting integration

Usage:
    from src.core.validation import SearchQuery, validate_input, ValidationError
    
    # Define schema
    query = SearchQuery(text="hello", limit=10)
    
    # Or use validation function
    try:
        validate_input(data, schema_class=SearchQuery)
    except ValidationError as e:
        print(e.errors())
"""

from typing import Any, Dict, List, Optional, Type, TypeVar
import re
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import Pydantic, fallback to simple validation
try:
    from pydantic import BaseModel, Field, field_validator, ValidationError as PydanticValidationError, ConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    logger.warning("Pydantic not available, using basic validation")


class ValidationError(ValueError):
    """Custom validation error with detailed information."""

    def __init__(self, message: str, errors: Optional[List[Dict]] = None):
        """Initialize validation error."""
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            "error": "validation_error",
            "message": self.message,
            "details": self.errors,
        }

    def __str__(self) -> str:
        """String representation."""
        if self.errors:
            return f"{self.message}: {self.errors}"
        return self.message


if PYDANTIC_AVAILABLE:

    T = TypeVar("T", bound=BaseModel)

    # ============================================================================
    # Pydantic Models
    # ============================================================================

    class SearchQuery(BaseModel):
        """Schema for semantic search queries."""

        text: str = Field(..., min_length=1, max_length=1000, description="Search query text")
        limit: int = Field(default=10, ge=1, le=100, description="Max results to return")
        threshold: float = Field(
            default=0.5, ge=0.0, le=1.0, description="Similarity threshold"
        )
        offset: int = Field(default=0, ge=0, description="Result offset for pagination")

        @field_validator("text")
        @classmethod
        def text_not_empty(cls, v: str) -> str:
            """Validate text is not empty or just whitespace."""
            if not v.strip():
                raise ValueError("Text cannot be empty or whitespace only")
            return v.strip()

        model_config = ConfigDict(
            json_schema_extra={
                "example": {
                    "text": "machine learning",
                    "limit": 20,
                    "threshold": 0.7,
                    "offset": 0,
                }
            }
        )

    class DocumentInput(BaseModel):
        """Schema for document input."""

        title: str = Field(..., min_length=1, max_length=500, description="Document title")
        content: str = Field(..., min_length=1, max_length=50000, description="Document content")
        metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional metadata")
        tags: List[str] = Field(default_factory=list, description="Document tags")

        @field_validator("content")
        @classmethod
        def content_not_empty(cls, v: str) -> str:
            """Validate content is not empty."""
            if not v.strip():
                raise ValueError("Content cannot be empty")
            return v.strip()

        @field_validator("tags")
        @classmethod
        def tags_limit(cls, v: List[str]) -> List[str]:
            """Limit number of tags."""
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            return v

        model_config = ConfigDict(
            json_schema_extra={
                "example": {
                    "title": "AI Research",
                    "content": "Recent advances in machine learning...",
                    "metadata": {"source": "arxiv", "year": 2024},
                    "tags": ["ai", "ml", "research"],
                }
            }
        )

    class AnalysisRequest(BaseModel):
        """Schema for text analysis requests."""

        text: str = Field(..., min_length=1, max_length=10000, description="Text to analyze")
        analysis_types: List[str] = Field(
            default=["sentiment"], description="Types of analysis to perform"
        )
        language: str = Field(default="en", min_length=2, max_length=5, description="Language code")

        @field_validator("analysis_types")
        @classmethod
        def validate_analysis_types(cls, v: List[str]) -> List[str]:
            """Validate analysis types."""
            valid_types = {"sentiment", "entities", "summary", "keywords"}
            invalid = [t for t in v if t not in valid_types]
            if invalid:
                raise ValueError(
                    f"Invalid analysis types: {invalid}. Valid: {valid_types}"
                )
            return v

        model_config = ConfigDict(
            json_schema_extra={
                "example": {
                    "text": "This product is amazing!",
                    "analysis_types": ["sentiment", "keywords"],
                    "language": "en",
                }
            }
        )

    class CacheConfig(BaseModel):
        """Cache configuration schema."""

        enabled: bool = Field(default=True, description="Enable caching")
        backend: str = Field(default="lru", description="Cache backend (lru or redis)")
        max_size: int = Field(default=1000, ge=10, le=100000, description="Max cache entries")
        default_ttl: int = Field(default=3600, ge=60, le=86400, description="Default TTL in seconds")
        redis_host: Optional[str] = Field(default="localhost", description="Redis host")
        redis_port: int = Field(default=6379, ge=1, le=65535, description="Redis port")

        model_config = ConfigDict(
            json_schema_extra={
                "example": {
                    "enabled": True,
                    "backend": "redis",
                    "max_size": 5000,
                    "default_ttl": 1800,
                    "redis_host": "localhost",
                    "redis_port": 6379,
                }
            }
        )

    def validate_input(
        data: Any, schema_class: Type[T], strict: bool = False
    ) -> Optional[T]:
        """Validate input against Pydantic schema."""
        try:
            return schema_class.model_validate(data)
        except PydanticValidationError as e:
            errors = []
            for error in e.errors():
                errors.append({
                    "field": ".".join(str(x) for x in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                })

            if strict:
                raise ValidationError(
                    f"Validation failed for {schema_class.__name__}",
                    errors=errors,
                )

            return None

else:
    # Fallback validation without Pydantic
    
    def validate_input(data: Any, schema_class: Type = None, strict: bool = False) -> Optional[Dict]:
        """Fallback validation without Pydantic."""
        logger.warning("Pydantic not available, using basic validation")
        return data


# ============================================================================
# Universal Validator Class (Pydantic or not)
# ============================================================================


class Validator:
    """Input validation utilities - works with or without Pydantic."""
    
    # Constants
    MAX_TEXT_LENGTH = 10000
    MAX_QUERY_LENGTH = 500
    MAX_BATCH_SIZE = 1000
    
    # Patterns for injection detection
    SQL_INJECTION_PATTERN = re.compile(
        r"(\bUNION\b|\bSELECT\b|\bDROP\b|\bINSERT\b|\bDELETE\b|\bUPDATE\b|\b--\b)", 
        re.IGNORECASE
    )
    XSS_PATTERN = re.compile(
        r"(<script|<iframe|javascript:|onerror=|onload=)", 
        re.IGNORECASE
    )
    
    @staticmethod
    def validate_text(text: str, max_length: int = MAX_TEXT_LENGTH, 
                     min_length: int = 1) -> str:
        """Validate text input."""
        if not isinstance(text, str):
            raise ValidationError(f"Text must be string, got {type(text).__name__}")
        
        if len(text) < min_length:
            raise ValidationError(
                f"Text too short (min {min_length}, got {len(text)})")
        
        if len(text) > max_length:
            raise ValidationError(
                f"Text too long (max {max_length}, got {len(text)})")
        
        if not text.strip():
            raise ValidationError("Text cannot be empty or whitespace-only")
        
        logger.debug(f"Text validation passed: {len(text)} chars")
        return text
    
    @staticmethod
    def validate_query(query: str, max_length: int = MAX_QUERY_LENGTH) -> str:
        """Validate search query for safety."""
        Validator.validate_text(query, max_length=max_length, min_length=1)
        
        if Validator.SQL_INJECTION_PATTERN.search(query):
            logger.warning(f"Potential SQL injection detected: {query[:50]}")
            raise ValidationError("Query contains suspicious SQL patterns")
        
        if Validator.XSS_PATTERN.search(query):
            logger.warning(f"Potential XSS detected: {query[:50]}")
            raise ValidationError("Query contains suspicious HTML/JS patterns")
        
        logger.debug(f"Query validation passed: {query[:50]}...")
        return query
    
    @staticmethod
    def validate_number(value: Any, min_val: Optional[float] = None, 
                       max_val: Optional[float] = None) -> float:
        """Validate numeric input."""
        try:
            num = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Expected number, got {type(value).__name__}")
        
        if min_val is not None and num < min_val:
            raise ValidationError(f"Number too small (min {min_val})")
        
        if max_val is not None and num > max_val:
            raise ValidationError(f"Number too large (max {max_val})")
        
        return num
    
    @staticmethod
    def validate_batch(documents: List[str], 
                      max_size: int = MAX_BATCH_SIZE) -> List[str]:
        """Validate batch of documents."""
        if not isinstance(documents, list):
            raise ValidationError(f"Expected list, got {type(documents).__name__}")
        
        if len(documents) > max_size:
            raise ValidationError(
                f"Batch too large (max {max_size}, got {len(documents)})")
        
        if len(documents) == 0:
            raise ValidationError("Batch cannot be empty")
        
        validated = []
        for i, doc in enumerate(documents):
            try:
                validated.append(Validator.validate_text(doc))
            except ValidationError as e:
                raise ValidationError(f"Document {i} invalid: {e}")
        
        logger.debug(f"Batch validation passed: {len(validated)} documents")
        return validated
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text by removing/escaping dangerous characters."""
        # Remove control characters
        text = ''.join(c for c in text if ord(c) >= 32 or c.isspace())
        
        # Remove known injection patterns
        text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'onerror=', '', text, flags=re.IGNORECASE)
        text = re.sub(r'onload=', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @staticmethod
    def validate_config(config: Dict[str, Any], schema: Dict[str, type]) -> Dict:
        """Validate configuration against schema."""
        for key, expected_type in schema.items():
            if key not in config:
                raise ValidationError(f"Missing required config key: {key}")
            
            if not isinstance(config[key], expected_type):
                raise ValidationError(
                    f"Config key '{key}' should be {expected_type.__name__}, "
                    f"got {type(config[key]).__name__}")
        
        logger.debug("Config validation passed")
        return config
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError(f"Invalid email format: {email}")
        return email
