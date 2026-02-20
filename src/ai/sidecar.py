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

@app.post("/sentinel/offload")
async def sentinel_offload(payload: dict):
    """Signal from SentinelMonitor to reduce VRAM usage."""
    if hasattr(provider, "offload_to_ram"):
        logger.warning(f"SENTINEL SIGNAL: Offloading layers to RAM. Pressure: {payload.get('vram_pressure')}")
        provider.offload_to_ram()
        return {"status": "offloading_initiated"}
    return {"status": "not_supported"}

@app.post("/sentinel/switch_lens")
async def sentinel_switch_lens(payload: dict):
    """Switch forensic LoRA adapter."""
    lens = payload.get("lens_name")
    if not lens:
        raise HTTPException(status_code=400, detail="Missing lens_name")
    
    if hasattr(provider, "switch_lens"):
        provider.switch_lens(lens)
        return {"status": "lens_shifted", "lens": lens}
    return {"status": "not_supported"}

@app.post("/forensics/nexus_verify")
async def verify_nexus(payload: dict):
    """
    Extracts named entities from content for forensic verification.
    Uses spaCy NER if available, falls back to heuristic noun-phrase extraction.
    """
    content = payload.get("new_content", "")

    entities = []
    try:
        # Prefer the operator's entity linker via HTTP when available
        import httpx
        operator_url = os.getenv("SME_OPERATOR_URL", "http://sme-operator:8000")
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{operator_url}/api/v1/link_entities",
                json={"text": content, "knowledge_base": "custom"}
            )
            if resp.status_code == 200:
                data = resp.json()
                entities = [e.get("entity", e) for e in data.get("entities", [])]
    except Exception:
        # Fallback: simple word-tokeniser filtering stopwords and short tokens
        import string
        stopwords = {
            "the", "a", "an", "is", "are", "was", "were", "in", "on", "at",
            "to", "of", "and", "or", "but", "for", "with", "that", "this",
            "it", "he", "she", "they", "we", "i", "my", "your", "our"
        }
        tokens = content.translate(str.maketrans("", "", string.punctuation)).split()
        entities = list({
            t for t in tokens
            if len(t) > 3 and t[0].isupper() and t.lower() not in stopwords
        })

    return {
        "status": "verified",
        "entities_found": entities,
        "entity_count": len(entities),
        "recommendation": "proceed" if len(entities) > 0 else "flag"
    }

if __name__ == "__main__":
    import uvicorn
    # Defaulting to 8089 to avoid conflicts with Gephi (8080) or other services
    port = int(os.getenv("SME_SIDECAR_PORT", 8089))
    # Bind to 0.0.0.0 so the sidecar is reachable from other Docker containers.
    # 127.0.0.1 (loopback) is only reachable within the same container.
    uvicorn.run(app, host="0.0.0.0", port=port)
