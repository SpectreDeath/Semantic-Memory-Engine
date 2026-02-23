# SME OCR Service

Local-first OCR microservice for Semantic-Memory-Engine (SME). Accepts PDFs or images, runs OCR using PaddleOCR, and returns normalized JSON ready for ingestion into a semantic memory engine.

## Features

- **Multi-format support**: PDF documents and images (PNG, JPEG, BMP, TIFF)
- **GPU acceleration**: Automatic GPU/CPU detection with PaddleOCR
- **Hardware-aware**: Optimized for single GTX 1660 Ti (6GB VRAM)
- **Production-ready**: Health checks, logging, structured JSON output
- **SME-ready output**: Page/block structure with coordinates and confidence scores

## Requirements

- Python 3.11+
- NVIDIA GPU (optional, CPU fallback available)
- Docker (for containerized deployment)

## Quick Start

### 1. Build the Container

```bash
cd sme-ocr-service
docker build -t sme-ocr-service .
```

### 2. Run the Container

**With GPU support:**
```bash
docker run --gpus all -p 8080:8080 sme-ocr-service
```

**CPU-only mode:**
```bash
docker run -p 8080:8080 -e PADDLE_OCR_USE_GPU=0 sme-ocr-service
```

### 3. Test the Service

```bash
# Health check
curl http://localhost:8080/health

# OCR request (PDF)
curl -X POST -F "file=@document.pdf" http://localhost:8080/ocr/file

# OCR request (Image)
curl -X POST -F "file=@image.png" http://localhost:8080/ocr/file
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PADDLE_OCR_USE_GPU` | Auto-detect | Set to `1` for GPU, `0` for CPU |
| `UVICORN_HOST` | `0.0.0.0` | Server host |
| `UVICORN_PORT` | `8080` | Server port |
| `LOG_LEVEL` | `INFO` | Logging level |

## API Endpoints

### `GET /health`

Health check endpoint. Returns service status and GPU availability.

**Response:**
```json
{
  "status": "healthy",
  "gpu_available": true,
  "engine_version": "2.8.1"
}
```

### `POST /ocr/file`

Process a file through OCR.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` - The file to process (PDF or image)

**Response:**
```json
{
  "doc_id": "550e8400-e29b-41d4-a716-446655440000",
  "pages": [
    {
      "page_number": 1,
      "text": "Full page text here...",
      "blocks": [
        {
          "bbox": [10.0, 20.0, 100.0, 80.0],
          "text": "Block text",
          "confidence": 0.95
        }
      ],
      "dimensions": {
        "width": 1700,
        "height": 2200
      }
    }
  ],
  "meta": {
    "source_filename": "document.pdf",
    "content_type": "application/pdf",
    "page_count": 1,
    "engine": "paddleocr",
    "engine_version": "2.8.1",
    "gpu_used": true,
    "processing_time_ms": 1234
  }
}
```

## GPU vs CPU Mode

### GPU Mode (Default)

The service automatically detects CUDA-enabled GPUs. For GTX 1660 Ti:
- Uses CUDA 12.x runtime
- PaddleOCR runs on GPU for faster processing
- VRAM usage: ~2-3GB for models + batch processing

### CPU Fallback

If GPU is not available, the service automatically falls back to CPU mode. To force CPU:
```bash
docker run -p 8080:8080 -e PADDLE_OCR_USE_GPU=0 sme-ocr-service
```

**Note:** CPU mode is significantly slower but works on any machine.

## Integration with SME

From your SME pipeline, call the OCR service:

```python
import httpx
import uuid

async def ingest_document(file_path: str, ocr_url: str = "http://localhost:8080"):
    """Ingest a document through the OCR service."""
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        with open(file_path, 'rb') as f:
            response = await client.post(
                f"{ocr_url}/ocr/file",
                files={"file": (file_path, f, "application/pdf")}
            )
        
        if response.status_code != 200:
            raise Exception(f"OCR failed: {response.text}")
        
        ocr_result = response.json()
        
        # Store in semantic memory
        for page in ocr_result["pages"]:
            await store_in_memory(
                doc_id=ocr_result["doc_id"],
                page_number=page["page_number"],
                text=page["text"],
                blocks=page["blocks"],
                metadata={
                    "source_filename": ocr_result["meta"]["source_filename"],
                    "engine": ocr_result["meta"]["engine"],
                    "gpu_used": ocr_result["meta"]["gpu_used"],
                }
            )
        
        return ocr_result

async def store_in_memory(doc_id: str, page_number: int, text: str, 
                         blocks: list, metadata: dict):
    """
    Store OCR result in SME's semantic memory.
    Customize this based on your SME implementation.
    """
    # Example: chunk text and embed for vector storage
    chunks = chunk_text(text, max_tokens=512)
    
    for i, chunk in enumerate(chunks):
        embedding = await get_embedding(chunk)
        
        await save_to_vector_db(
            id=f"{doc_id}_p{page_number}_c{i}",
            text=chunk,
            embedding=embedding,
            metadata={
                "doc_id": doc_id,
                "page": page_number,
                "chunk": i,
                **metadata
            }
        )
```

### SME Integration Notes

1. **Document ID**: Use `doc_id` from OCR response as the primary key
2. **Text granularity**: 
   - Page-level: `pages[].text` for full page
   - Block-level: `pages[].blocks[]` for precise segments
3. **Confidence filtering**: Consider filtering blocks with `confidence < 0.7`
4. **Coordinates**: Use `bbox` for spatial queries or highlighting
5. **Metadata**: Include `meta` for provenance tracking

## Development

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .

# Run service
python -m uvicorn app.main:app --reload --port 8080
```

### Testing

```bash
# Run tests
pytest tests/

# Test with sample file
curl -X POST -F "file=@tests/sample.pdf" http://localhost:8080/ocr/file
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SME OCR Service                       │
├─────────────────────────────────────────────────────────┤
│  POST /ocr/file                                         │
│         │                                               │
│         ▼                                               │
│  ┌─────────────┐    ┌──────────────┐                   │
│  │   FastAPI   │───▶│ PDF Processor │                   │
│  │   (Uvicorn) │    │   (PyMuPDF)   │                   │
│  └─────────────┘    └───────┬───────┘                   │
│                             │                           │
│                             ▼                           │
│                    ┌──────────────────┐                 │
│                    │  PaddleOCR       │                 │
│                    │  (GPU/CPU)       │                 │
│                    └────────┬─────────┘                 │
│                             │                           │
│                             ▼                           │
│                    ┌──────────────────┐                 │
│                    │  JSON Response   │                 │
│                    │  (SME-ready)     │                 │
│                    └──────────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

## Performance Notes

- **PDF processing**: ~1-2 seconds per page (GPU), ~5-10 seconds (CPU)
- **Image processing**: ~0.5-1 second (GPU), ~2-3 seconds (CPU)
- **VRAM usage**: ~2-3GB with GPU, negligible with CPU
- **Batch processing**: Pages are processed sequentially to manage memory

## Troubleshooting

### GPU not detected

```bash
# Check NVIDIA drivers
nvidia-smi

# Check CUDA availability in container
docker exec <container> nvidia-smi

# Force CPU mode
docker run -e PADDLE_OCR_USE_GPU=0 -p 8080:8080 sme-ocr-service
```

### Out of memory

- Reduce concurrent requests
- Process large PDFs one page at a time
- Use CPU mode for large documents

### Model download issues

PaddleOCR downloads models on first run. Ensure internet access or pre-cache models:

```bash
# Pre-download models
python -c "from paddleocr import PaddleOCR; PaddleOCR()"
```

## License

MIT License - See project root for details.
