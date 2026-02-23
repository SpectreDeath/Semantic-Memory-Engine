"""
SME OCR Service - FastAPI Application.
Main entry point for the OCR microservice.
"""

import io
import logging
import time
import uuid
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.ocr_engine import get_ocr_engine
from app.pdf_processor import PdfProcessor
from app.schemas import (
    HealthResponse,
    OcrBlock,
    OcrMeta,
    OcrPage,
    OcrResponse,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SME OCR Service",
    description="Local-first OCR microservice for Semantic-Memory-Engine",
    version="1.0.0",
)

# Initialize processors (lazy-loaded)
_pdf_processor: Optional[PdfProcessor] = None


def get_pdf_processor() -> PdfProcessor:
    """Get PDF processor singleton."""
    global _pdf_processor
    if _pdf_processor is None:
        _pdf_processor = PdfProcessor(dpi=200)
    return _pdf_processor


def process_ocr_result(ocr_result: list) -> tuple[str, list[OcrBlock]]:
    """
    Process raw PaddleOCR result into structured data.

    Args:
        ocr_result: Raw result from PaddleOCR.ocr()

    Returns:
        Tuple of (full_text, blocks)
    """
    full_text_parts = []
    blocks = []

    if not ocr_result or not ocr_result[0]:
        return "", []

    # PaddleOCR returns: [[box, (text, confidence)], ...]
    for line in ocr_result[0]:
        if not line:
            continue

        box = line[0]  # [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
        text_info = line[1]

        if isinstance(text_info, tuple):
            text = text_info[0]
            confidence = float(text_info[1]) if len(text_info) > 1 else 0.0
        else:
            text = str(text_info)
            confidence = 0.0

        # Convert box to [x1, y1, x2, y2] format
        if box and len(box) >= 4:
            bbox = [
                float(min(p[0] for p in box)),
                float(min(p[1] for p in box)),
                float(max(p[0] for p in box)),
                float(max(p[1] for p in box)),
            ]
        else:
            bbox = [0.0, 0.0, 0.0, 0.0]

        block = OcrBlock(bbox=bbox, text=text, confidence=confidence)
        blocks.append(block)

        if text.strip():
            full_text_parts.append(text)

    full_text = "\n".join(full_text_parts)
    return full_text, blocks


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Returns service status and GPU availability.
    """
    gpu_available = False
    engine_version = None

    try:
        ocr_engine = get_ocr_engine()
        gpu_available = ocr_engine.use_gpu
        engine_version = ocr_engine.engine_version
    except Exception as e:
        logger.warning(f"OCR engine not available: {e}")

    return HealthResponse(
        status="healthy",
        gpu_available=gpu_available,
        engine_version=engine_version,
    )


@app.post("/ocr/file", response_model=OcrResponse)
async def ocr_file(file: UploadFile = File(...)):
    """
    Process a file (PDF or image) through OCR.

    Args:
        file: Uploaded file (PDF or image)

    Returns:
        OCR result JSON ready for SME ingestion
    """
    start_time = time.time()
    doc_id = str(uuid.uuid4())

    logger.info(f"Received OCR request: {file.filename} ({file.content_type})")

    # Validate content type
    content_type = file.content_type or "application/octet-stream"
    is_pdf = content_type == "application/pdf" or file.filename.lower().endswith(".pdf")

    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    if len(file_content) == 0:
        raise HTTPException(status_code=400, detail="Empty file provided")

    logger.info(f"File size: {len(file_content)} bytes")

    # Get OCR engine
    try:
        ocr_engine = get_ocr_engine()
    except Exception as e:
        logger.error(f"Failed to initialize OCR engine: {e}")
        raise HTTPException(status_code=500, detail=f"OCR engine initialization failed: {e}")

    pages = []
    page_count = 0

    try:
        if is_pdf:
            # Process PDF
            logger.info("Processing as PDF")
            pdf_processor = get_pdf_processor()

            for page_num, img_bytes, metadata in pdf_processor.pdf_to_images(file_content):
                logger.info(f"Processing page {page_num}")
                page_start = time.time()

                # Run OCR on page image
                ocr_result = ocr_engine.process_image(img_bytes.getvalue())

                # Process results
                text, blocks = process_ocr_result(ocr_result)

                page = OcrPage(
                    page_number=page_num,
                    text=text,
                    blocks=blocks,
                    dimensions={
                        "width": metadata.get("width", 0),
                        "height": metadata.get("height", 0),
                    },
                )
                pages.append(page)
                page_count += 1

                page_time = (time.time() - page_start) * 1000
                logger.info(
                    f"Page {page_num} done: {len(blocks)} blocks, "
                    f"{len(text)} chars, {page_time:.0f}ms"
                )

        else:
            # Process as image
            logger.info("Processing as image")
            ocr_result = ocr_engine.process_image(file_content)
            text, blocks = process_ocr_result(ocr_result)

            page = OcrPage(
                page_number=1,
                text=text,
                blocks=blocks,
            )
            pages.append(page)
            page_count = 1

            logger.info(
                f"Image done: {len(blocks)} blocks, {len(text)} chars"
            )

    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {e}")

    # Calculate processing time
    processing_time_ms = int((time.time() - start_time) * 1000)

    # Build response
    response = OcrResponse(
        doc_id=doc_id,
        pages=pages,
        meta=OcrMeta(
            source_filename=file.filename or "unknown",
            content_type=content_type,
            page_count=page_count,
            engine="paddleocr",
            engine_version=ocr_engine.engine_version,
            gpu_used=ocr_engine.use_gpu,
            processing_time_ms=processing_time_ms,
        ),
    )

    logger.info(
        f"OCR complete: doc_id={doc_id}, pages={page_count}, "
        f"total_time={processing_time_ms}ms, gpu={ocr_engine.use_gpu}"
    )

    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
