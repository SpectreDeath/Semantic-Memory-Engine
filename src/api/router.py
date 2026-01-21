"""
API Router - Maps Laboratory Tools to REST Endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from src.core.factory import ToolFactory
from src.core.validation import Validator, ValidationError
from src.core.cache import cached
from src.core.resilience import CircuitBreaker, CircuitBreakerError
from src.core.auth import get_current_user, User
from src.core.batch_processor import get_batch_processor
from fastapi import Depends

# Define circuit breakers for major components
analysis_breaker = CircuitBreaker("analysis_tools", failure_threshold=0.6, recovery_timeout=30)
search_breaker = CircuitBreaker("search_engine", failure_threshold=0.5, recovery_timeout=20)

router = APIRouter()

# --- Models ---

class TextRequest(BaseModel):
    text: str
    context_id: str = "default"

class ConnectionRequest(BaseModel):
    context_id: str
    limit: int = 5

class BatchRequest(BaseModel):
    items: List[str]
    operation: str = "sentiment" # or "summarize", etc.

# --- Analysis Endpoints ---

@router.post("/analysis/graph")
@cached(ttl=600)  # Cache for 10 minutes
async def build_knowledge_graph(request: TextRequest):
    """Generate a knowledge graph from text."""
    try:
        # Validate input
        Validator.validate_text(request.text)
        
        # Call via circuit breaker
        kg = analysis_breaker.call(ToolFactory.create_knowledge_graph)
        kg.build_from_text(request.text, request.context_id)
        
        return {
            "summary": kg.get_summary(),
            "mermaid": kg.to_mermaid(),
            "json_graph": kg.to_json()
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CircuitBreakerError as e:
        raise HTTPException(status_code=503, detail=f"Service temporarily unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analysis/report")
@cached(ttl=900)  # Cache for 15 minutes
async def generate_intelligence_report(request: TextRequest):
    """Generate a narrative intelligence briefing."""
    try:
        # Validate input
        Validator.validate_text(request.text)
        
        # Call via circuit breaker
        ir = analysis_breaker.call(ToolFactory.create_intelligence_reports)
        report = ir.generate_briefing(request.text, title=f"API Briefing - {request.context_id}")
        
        return {
            "report_data": report,
            "markdown": ir.to_markdown(report)
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CircuitBreakerError as e:
        raise HTTPException(status_code=503, detail=f"Service temporarily unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/connections")
async def find_connections(context_id: str = Query(...), limit: int = 5):
    """Find semantic connections between contexts."""
    try:
        # Validate input
        Validator.validate_text(context_id, max_length=100)
        Validator.validate_number(limit, min_val=1, max_val=100)
        
        # Call via circuit breaker
        od = analysis_breaker.call(ToolFactory.create_overlap_discovery)
        connections = od.find_connections(context_id, limit=limit)
        return {"context_id": context_id, "connections": connections}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CircuitBreakerError as e:
        raise HTTPException(status_code=503, detail=f"Service temporarily unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Tool Management ---

@router.get("/tools/status")
async def get_tools_status():
    """Get the health status of all specialized tools."""
    try:
        return ToolFactory.health_check()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools/list")
async def list_active_instances():
    """List all currently instantiated tool objects."""
    return ToolFactory.list_instances()

# --- Search ---

@router.get("/search")
async def semantic_search(query: str = Query(...), limit: int = 5):
    """Perform a semantic search across the laboratory memory."""
    try:
        # Validate input
        Validator.validate_query(query)
        Validator.validate_number(limit, min_val=1, max_val=50)
        
        # Call via circuit breaker
        db = search_breaker.call(ToolFactory.create_semantic_db)
        results = db.search_with_semantic_expansion(query, n_results=limit)
        return results
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CircuitBreakerError as e:
        raise HTTPException(status_code=503, detail=f"Service temporarily unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Batch Processing ---

@router.post("/batch/process")
async def submit_batch_job(request: BatchRequest, user: User = Depends(get_current_user)):
    """Submit a list of items for background processing."""
    processor = get_batch_processor()
    
    # Define task based on operation
    if request.operation == "sentiment":
        async def process_item(text: str):
            analyzer = ToolFactory.create_sentiment_analyzer()
            return analyzer.analyze_sentiment(text)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported operation: {request.operation}")

    job_id = await processor.create_job(request.items, process_item)
    return {"job_id": job_id, "status": "accepted"}

@router.get("/batch/status/{job_id}")
async def get_batch_status(job_id: str, user: User = Depends(get_current_user)):
    """Check the status of a batch job."""
    processor = get_batch_processor()
    status = processor.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@router.get("/batch/results/{job_id}")
async def get_batch_results(job_id: str, user: User = Depends(get_current_user)):
    """Retrieve results of a completed batch job."""
    processor = get_batch_processor()
    results = processor.get_job_results(job_id)
    if not results:
        raise HTTPException(status_code=404, detail="Results not ready or job not found")
    return results
