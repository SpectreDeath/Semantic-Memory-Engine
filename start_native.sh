#!/bin/bash
# SME Native Startup Script
# Run the full stack natively (no Docker, no sidecar)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  SME v3.0.1 - Native Startup (No Sidecar)"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Copy from .env.example${NC}"
fi

# Create data directory if it doesn't exist
mkdir -p data

echo -e "${GREEN}[1/2] Starting SME Operator (port 8000)...${NC}"
python -m src.api.main &
OPERATOR_PID=$!

echo -e "${GREEN}[2/2] Starting Frontend (port 5173)...${NC}"
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "  All services started!"
echo "=========================================="
echo ""
echo "  Operator:   http://localhost:8000"
echo "  Frontend:   http://localhost:5173"
echo "  API Docs:   http://localhost:8000/api/docs"
echo ""
echo "  Note: AI provider runs inside operator (no sidecar)"
echo ""
echo "  PIDs: Operator=$OPERATOR_PID Frontend=$FRONTEND_PID"
echo ""
echo "  Press Ctrl+C to stop all services"
echo "=========================================="

# Wait for any process to exit
wait
