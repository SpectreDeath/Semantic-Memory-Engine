import sys
import os
import re
import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Robust path injection for Sidecar execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the factory and provider
from src.ai.providers.factory import get_provider

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Sidecar")

app = FastAPI(title="SME AI Sidecar", version="1.0.0")

# Initialize provider once (Warm-Start)
try:
    logger.info("Initializing AI Provider for Warm-Start...")
    provider = get_provider()
    logger.info(f"AI Provider initialized: {provider.__class__.__name__}")
except Exception as e:
    logger.error(f"Failed to initialize AI Provider: {e}")
    provider = None

class AIRequest(BaseModel):
    flow_name: str
    input_data: Any

@app.get("/health")
async def health_check():
    """Check if the sidecar and its provider are ready."""
    return {
        "status": "online",
        "provider": provider.__class__.__name__ if provider else "None",
        "python_version": sys.version
    }

@app.post("/run")
async def run_flow(request: AIRequest):
    """Execute an AI flow through the initialized provider."""
    if not provider:
        raise HTTPException(status_code=503, detail="AI Provider not initialized")
    
    try:
        # Serialize input_data if it's not a string (provider.run expects string/dict usually)
        input_data = request.input_data
        if not isinstance(input_data, (str, dict)):
             input_data = str(input_data)
             
        logger.info(f"Running flow: {request.flow_name}")
        result = provider.run(request.flow_name, input_data)
        return {"result": result}
    except Exception as e:
        logger.exception("Error executing flow in sidecar")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/forensics/nexus_verify")
async def verify_nexus(payload: dict):
    """
    Extracts entities from content for forensic verification.
    """
    content = payload.get("new_content", "")
    # Use regex to grab entities (Capitalized words)
    entities = list(set(re.findall(r'[A-Z][a-z]+', content))) 
    
    return {
        "status": "verified",
        "entities_found": entities,
        "recommendation": "proceed" if len(entities) > 0 else "flag"
    }

if __name__ == "__main__":
    import uvicorn
    # Defaulting to 8089 to avoid conflicts with Gephi (8080) or other services
    port = int(os.getenv("SME_SIDECAR_PORT", 8089))
    uvicorn.run(app, host="127.0.0.1", port=port)
