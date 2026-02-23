# SME OCR Service - GPU-enabled container for GTX 1660 Ti
# Base: NVIDIA CUDA 12.1 runtime (supports Turing/Volta/Ampere)
# GTX 1660 Ti = Turing architecture, Compute Capability 7.5

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PADDLE_OCR_USE_GPU=1

# Install system dependencies and Python 3.11
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Set Python 3.11 as default
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Install Python dependencies
# Note: We install paddlepaddle-gpu first to get GPU support
# If GPU is not available at runtime, it will gracefully fall back to CPU
RUN pip3.11 install --no-cache-dir \
    paddlepaddle-gpu==2.6.1 \
    paddleocr==2.8.1 \
    fastapi==0.115.0 \
    uvicorn[standard]==0.32.0 \
    python-multipart==0.0.12 \
    PyMuPDF==1.24.10 \
    pydantic==2.9.2 \
    python-dotenv==1.0.1 \
    httpx==0.27.2

# Create app directory
WORKDIR /app

# Copy application code
COPY app/ /app/app/
COPY pyproject.toml /app/

# Create __init__.py files
RUN touch /app/__init__.py /app/app/__init__.py

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import httpx; httpx.get('http://localhost:8080/health')" || exit 1

# Run the service
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
