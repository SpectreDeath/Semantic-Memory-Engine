# Lawnmower Man Gateway Dockerfile
#
# Builds the MCP gateway container for Project Lawnmower Man.
# This container exposes SME's forensic toolkit to LLM agents.

FROM python:3.11-slim

LABEL maintainer="Project Lawnmower Man"
LABEL description="MCP Gateway to SME Forensic Toolkit"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install FastMCP for the gateway
RUN pip install --no-cache-dir fastmcp

# Copy the entire project
COPY . .

# Install SME in editable mode
RUN pip install -e .

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default port for HTTP mode (MCP typically uses stdio)
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from gateway.tool_registry import get_registry; print(len(get_registry().list_tools()))" || exit 1

# Run the MCP server
CMD ["python", "-m", "gateway.mcp_server"]
