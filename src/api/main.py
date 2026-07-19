"""
Main API Entry Point - SimpleMem Laboratory
"""

import asyncio
import os
import time

import psutil
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.rate_limiter import RateLimiter
from src.api.router import router
from src.core.logging_system import get_log_context, get_logger, setup_logging
from src.core.tenancy import TenantContext

# Initialize Structured Logging
setup_logging({"level": "INFO", "log_file": "api_access.log"})
logger = get_logger(__name__)

app = FastAPI(
    title="SimpleMem Laboratory Control Room API",
    description="Backend API for real-time memory management and intelligence synthesis.",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Initialize Rate Limiter
limiter = RateLimiter(default_limit="100/minute")
app.middleware("http")(limiter.middleware_factory)


# Broadcaster for real-time diagnostics
async def broadcast_diagnostics(websocket: WebSocket):
    try:
        from gateway.nexus_db import get_nexus
        from gateway.traffic_router import NODE_EM_CUBED_DISTRIBUTED, TrafficRouter

        traffic_router = TrafficRouter()
        nexus = get_nexus()

        while True:
            # Gather system metrics
            cpu_usage = psutil.cpu_percent() if psutil else 0.0
            mem_usage = psutil.virtual_memory().percent if psutil else 0.0

            # Measure actual round-trip latency
            _t0 = time.perf_counter()
            if psutil:
                psutil.disk_io_counters()
            latency_ms = round((time.perf_counter() - _t0) * 1000, 2)

            # Gather sub-system telemetry
            em_health = traffic_router.probe_node_health(NODE_EM_CUBED_DISTRIBUTED)
            nexus_status = nexus.get_status()

            from gateway.candidate_pool import CandidatePoolStorage
            from gateway.mimo_bridge import MimoControlBridge

            mimo_bridge = MimoControlBridge()
            harness_cfg = mimo_bridge.get_harness_config(task_type="default")
            pool_storage = CandidatePoolStorage()
            candidate_count = len(pool_storage.get_pool(layer_index=1))

            await websocket.send_json(
                {
                    "type": "diagnostics",
                    "data": {
                        "cpu": cpu_usage,
                        "memory": mem_usage,
                        "latency_ms": latency_ms,
                        "timestamp": time.time(),
                        "routing": {
                            "mode": traffic_router.default_mode,
                            "em_cubed_node": em_health.get("status", "unknown"),
                        },
                        "nexus": {
                            "attached_databases": len(nexus_status.get("attached", [])),
                        },
                        "mimo_6d": harness_cfg.to_dict(),
                        "ann_framework": {
                            "candidate_blocks_layer_1": candidate_count,
                            "optimizer": "TextualBackpropagation",
                        },
                    },
                }
            )
            await asyncio.sleep(2)
    except Exception as e:
        logger.debug(f"Broadcaster stopped: {e}")


# Global Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log all unhandled exceptions as structured errors."""
    error_id = str(time.time())
    logger.error(
        f"Unhandled exception: {exc!s}",
        exc_info=True,
        error_id=error_id,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred.",
            "error_id": error_id,
        },
    )


# Context Propagation & Tenancy Middleware
@app.middleware("http")
async def add_logging_and_tenant_context(request: Request, call_next):
    """Add request metadata and tenant context to all logs and operations."""
    request_id = request.headers.get("X-Request-ID", str(time.time()))

    # Identify tenant from headers (simple for now)
    tenant_id = request.headers.get("X-Tenant-ID", "default")

    # Propagate for both logging and for data isolation
    token = TenantContext.set_tenant(tenant_id)
    try:
        with get_log_context(request_id=request_id, path=request.url.path, tenant_id=tenant_id):
            logger.info(
                f"Incoming request: {request.method} {request.url.path} (Tenant: {tenant_id})"
            )
            response = await call_next(request)
            logger.info(f"Finished request: {response.status_code}")
            return response
    finally:
        TenantContext.reset(token)


# Configure CORS for the frontend.
# Origins are read from SME_CORS_ORIGINS (comma-separated).
# Falls back to localhost only — never a wildcard in production.
_raw_origins = os.environ.get("SME_CORS_ORIGINS", "http://localhost:80,http://localhost:5173")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include tool routes
app.include_router(router, prefix="/api/v1")


@app.websocket("/ws/diagnostics")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        await broadcast_diagnostics(websocket)
    except WebSocketDisconnect:
        logger.info("Client disconnected from diagnostics socket")


@app.get("/")
async def root():
    """Health check and service info."""
    return {
        "service": "SimpleMem Laboratory Control Room",
        "status": "online",
        "api_v1": "/api/v1",
        "ws_diagnostics": "/ws/diagnostics",
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
