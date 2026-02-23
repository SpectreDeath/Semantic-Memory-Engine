"""
Pydantic schemas for SME OCR Service.
Defines request/response models for the OCR API.
"""

from typing import Optional
from pydantic import BaseModel, Field


class OcrBlock(BaseModel):
    """OCR block with bounding box, text, and confidence."""
    bbox: list[float] = Field(
        description="Bounding box [x1, y1, x2, y2]",
        examples=[[10.0, 20.0, 100.0, 80.0]]
    )
    text: str = Field(description="Extracted text from the block")
    confidence: float = Field(
        description="OCR confidence score (0-1)",
        ge=0.0,
        le=1.0
    )


class OcrPage(BaseModel):
    """OCR result for a single page."""
    page_number: int = Field(description="Page number (1-indexed)")
    text: str = Field(description="Full text of the page (all blocks concatenated)")
    blocks: list[OcrBlock] = Field(description="List of text blocks with coordinates")
    dimensions: Optional[dict[str, int]] = Field(
        default=None,
        description="Page dimensions {width, height} in points"
    )


class OcrMeta(BaseModel):
    """Metadata about the OCR processing."""
    source_filename: str = Field(description="Original filename")
    content_type: str = Field(
        description="MIME type (application/pdf, image/png, etc.)"
    )
    page_count: int = Field(description="Total number of pages processed")
    engine: str = Field(default="paddleocr", description="OCR engine name")
    engine_version: str = Field(description="PaddleOCR version")
    gpu_used: bool = Field(description="Whether GPU was used for OCR")
    processing_time_ms: int = Field(description="Total processing time in milliseconds")


class OcrResponse(BaseModel):
    """Complete OCR response ready for SME ingestion."""
    doc_id: str = Field(description="UUID for this document")
    pages: list[OcrPage] = Field(description="OCR results per page")
    meta: OcrMeta = Field(description="Processing metadata")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(description="Service status")
    gpu_available: bool = Field(description="Whether GPU is detected")
    engine_version: Optional[str] = Field(
        default=None,
        description="PaddleOCR version if available"
    )
