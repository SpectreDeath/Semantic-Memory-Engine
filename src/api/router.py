"""
API Router - Maps Laboratory Tools to REST Endpoints
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.core.auth import User, get_current_user
from src.core.batch_processor import get_batch_processor
from src.core.cache import cached
from src.core.factory import ToolFactory
from src.core.resilience import CircuitBreaker, CircuitBreakerError
from src.core.validation import ValidationError, Validator
from src.logic.audit_engine import AuditEngine

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
    items: list[str]
    operation: str = "sentiment"  # or "summarize", etc.


class IngestRequest(BaseModel):
    url: str
    js_render: bool = False
    deep_crawl: bool = False
    max_pages: int = 5


class ProviderUpdateRequest(BaseModel):
    provider_type: str  # 'langflow', 'mock', etc.


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

        return {"summary": kg.get_summary(), "mermaid": kg.to_mermaid(), "json_graph": kg.to_json()}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CircuitBreakerError as e:
        raise HTTPException(status_code=503, detail=f"Service temporarily unavailable: {e!s}")
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

        return {"report_data": report, "markdown": ir.to_markdown(report)}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except CircuitBreakerError as e:
        raise HTTPException(status_code=503, detail=f"Service temporarily unavailable: {e!s}")
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
        raise HTTPException(status_code=503, detail=f"Service temporarily unavailable: {e!s}")
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
        raise HTTPException(status_code=503, detail=f"Service temporarily unavailable: {e!s}")
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


# --- Connection Management ---


@router.get("/connections/status")
async def get_all_connections_status():
    """Get summarized status of all infrastructure connections."""
    try:
        from src.ai.bridge import _get_provider

        status = {
            "api": "online",
            "ai_provider": "offline",
            "database": "offline",
            "tools": ToolFactory.health_check(),
        }

        # Check AI Provider
        try:
            provider = _get_provider()
            status["ai_provider"] = provider.__class__.__name__
        except Exception:
            pass

        # Check Database (Check if we can query the factory's DB instance)
        try:
            db = ToolFactory.create_semantic_db()
            if db:  # placeholder for actual health check
                status["database"] = "online"
        except Exception:
            pass

        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/connections/ai-provider")
async def update_ai_provider(request: ProviderUpdateRequest):
    """Update the global AI provider (persists to environment/settings)."""
    # For now, we'll update the environment variable for the process
    # In a more robust system, this would be written to a settings table
    os.environ["SME_AI_PROVIDER"] = request.provider_type
    return {"status": "success", "active_provider": request.provider_type}


# --- Drift Analysis (AuditEngine) ---


class DriftAnalysisRequest(BaseModel):
    claims: list[dict[str, str]]
    format_type: str = "auto"  # "conceptnet", "custom", "auto"


@router.post("/drift/analyze")
async def analyze_drift(request: DriftAnalysisRequest):
    """Compare claims against the HDF5 knowledge core (drift analysis)."""
    try:
        # Validate input
        if not request.claims:
            raise HTTPException(status_code=400, detail="Claims list cannot be empty")

        # Initialize AuditEngine
        engine = AuditEngine()

        # Run drift analysis
        result = engine.analyze_drift(request.claims)

        return {
            "drift_score": result["drift_score"],
            "verified_count": len(result["verified"]),
            "anomaly_count": len(result["anomalies"]),
            "verified_claims": result["verified"],
            "anomalous_claims": result["anomalies"],
            "analysis_timestamp": result.get("analysis_timestamp", "N/A"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Drift analysis failed: {e!s}")


# --- Ingestion (Harvester) ---


@router.post("/ingestion/crawl")
async def ingest_from_url(request: IngestRequest):
    """Ingest content from a URL using the Harvester engine."""
    try:
        from src.harvester.crawler import HarvesterCrawler

        crawler = HarvesterCrawler()

        if request.deep_crawl:
            # Running deep crawl in a background task would be better
            # For simplicity in this demo endpoint, we'll do it sync with a low page count
            result = crawler.deep_crawl_domain(request.url, max_pages=request.max_pages)
        else:
            result = crawler.fetch_semantic_markdown(request.url, js_render=request.js_render)

        if result.get("status") == "error":
            raise HTTPException(status_code=422, detail=result.get("error"))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Workflow API
# =============================================================================


@router.get("/workflows")
async def list_workflows():
    """List all available workflows."""
    try:
        from src.orchestration.workflow_engine import get_engine

        engine = get_engine()
        workflows = engine.list_workflows()
        return {"workflows": workflows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows")
async def create_workflow(request: dict):
    """Create a new workflow definition."""
    try:
        from src.orchestration.step_registry import get_step_registry
        from src.orchestration.workflow_engine import get_engine

        engine = get_engine()
        registry = get_step_registry()

        for step_def in request.get("steps", []):
            handler_name = step_def.get("handler")
            if handler_name:
                handler = registry.get_handler(handler_name)
                engine.register_step(handler_name, handler)

        workflow = engine.create_workflow(
            name=request["name"],
            description=request.get("description", ""),
            steps=request.get("steps", []),
            parallel=request.get("parallel", False),
        )

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": "created",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get workflow definition."""
    try:
        from src.orchestration.workflow_engine import get_engine

        engine = get_engine()
        workflow = engine.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return workflow
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, input_data: dict):
    """Execute a workflow with input data."""
    try:
        from src.orchestration.step_registry import get_step_registry
        from src.orchestration.workflow_engine import get_engine

        engine = get_engine()
        registry = get_step_registry()

        workflow_def = engine.get_workflow(workflow_id)
        if not workflow_def:
            raise HTTPException(status_code=404, detail="Workflow not found")

        for step_def in workflow_def.get("definition", {}).get("steps", []):
            handler_name = step_def.get("handler")
            if handler_name:
                handler = registry.get_handler(handler_name)
                if handler:
                    engine.register_step(handler_name, handler)

        workflow = engine.create_workflow(
            name=workflow_def["name"],
            description=workflow_def.get("description", ""),
            steps=workflow_def.get("definition", {}).get("steps", []),
            parallel=workflow_def.get("definition", {}).get("parallel", False),
        )

        import asyncio

        result = await engine.execute(workflow, input_data)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/steps")
async def list_workflow_steps():
    """List all available workflow steps."""
    try:
        from src.orchestration.step_registry import get_step_registry

        registry = get_step_registry()
        steps = registry.list_steps()
        return {"steps": steps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workflows/generate")
async def generate_workflow(request: dict):
    """Generate a workflow from task description and execute it."""
    try:
        from src.orchestration.workflow_generator import generate_and_execute

        task = request.get("task", "")
        input_data = request.get("input_data", {})

        if not task:
            raise HTTPException(status_code=400, detail="Task description required")

        result = await generate_and_execute(task, input_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/generate/handlers")
async def list_generators():
    """List available workflow step handlers for generation."""
    try:
        from src.orchestration.workflow_generator import get_generator

        generator = get_generator()
        handlers = generator.list_available_handlers()
        return {"handlers": handlers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RouteRequest(BaseModel):
    tool_name: str
    payload: dict | None = None
    mode: str = "auto"


@router.post("/route")
async def route_workload(request: RouteRequest):
    """Dynamically route and dispatch workload between SME and em-cubed nodes."""
    try:
        from gateway.traffic_router import TrafficRouter

        router_engine = TrafficRouter()
        result = router_engine.dispatch_workload(
            tool_name=request.tool_name, payload=request.payload, mode=request.mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AnnBackpropRequest(BaseModel):
    layer_index: int = 1
    trajectory: list[dict] | None = None
    target_objective: str = "graph_synthesis"


@router.post("/ann/backprop")
async def trigger_ann_backprop(request: AnnBackpropRequest):
    """Trigger ANN textual backpropagation (∇text), momentum smoothing, and candidate block validation."""
    try:
        from gateway.candidate_pool import CandidatePoolStorage
        from gateway.momentum_buffer import MomentumBuffer, MultiStageValidationFilter
        from src.logic.textual_gradient import TextualGradientEngine

        traj = request.trajectory or [
            {"task_id": "step_0", "status": "success"},
            {"task_id": "step_1", "status": "error", "error": "Schema mismatch"},
        ]

        engine = TextualGradientEngine()
        g_global = engine.compute_global_gradient(traj, target_objective=request.target_objective)

        initial_block = {
            "block_id": f"layer_{request.layer_index}_block_v1",
            "nodes": {"n1": {"prompt": "Initial prompt instruction"}},
            "edges": [],
        }

        g_local = engine.compute_local_gradient(
            layer_index=request.layer_index,
            team_block=initial_block,
            global_gradient=g_global,
            trajectory=traj,
        )

        candidate_block = engine.apply_textual_gradient(initial_block, g_local)

        buffer = MomentumBuffer()
        smoothed_g_local = buffer.apply_momentum(request.layer_index, g_local)

        validator = MultiStageValidationFilter()
        val_res = validator.validate_candidate_block(candidate_block, baseline_performance=1.0)

        saved = False
        if val_res["is_valid"]:
            pool_storage = CandidatePoolStorage()
            saved = pool_storage.save_block(request.layer_index, candidate_block)

        return {
            "status": "success",
            "layer_index": request.layer_index,
            "global_gradient": g_global.to_dict(),
            "local_gradient": smoothed_g_local.to_dict(),
            "validation_result": val_res,
            "saved_to_pool": saved,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/merkle-root")
async def get_merkle_root():
    """Retrieve current node Merkle tree root hash for audit consensus."""
    try:
        from src.logic.audit_engine import AuditEngine

        engine = AuditEngine()
        return {
            "merkle_root": engine.compute_merkle_root(),
            "integrity": engine.verify_integrity(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/verify")
async def verify_merkle_consensus(remote_root: str):
    """Verify Merkle root consensus against a remote node."""
    try:
        from src.logic.audit_engine import AuditEngine

        engine = AuditEngine()
        return engine.verify_remote_merkle_root(remote_root)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
