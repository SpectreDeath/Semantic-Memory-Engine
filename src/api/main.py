"""
Main API Entry Point - SimpleMem Laboratory
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import psutil
import time

from src.api.router import router
from src.api.rate_limiter import RateLimiter
from src.core.logging_system import setup_logging, get_logger, get_log_context
from src.core.tenancy import TenantContext
from src.core.auth import get_current_user, User

# Initialize Structured Logging
setup_logging({"level": "INFO", "log_file": "api_access.log"})
logger = get_logger(__name__)

app = FastAPI(
    title="SimpleMem Laboratory Control Room API",
    description="Backend API for real-time memory management and intelligence synthesis.",
    version="2.0.0"
)

# Initialize Rate Limiter
limiter = RateLimiter(default_limit="100/minute")
app.middleware("http")(limiter.middleware_factory)

# Broadcaster for real-time diagnostics
async def broadcast_diagnostics(websocket: WebSocket):
    try:
        while True:
            # Gather metrics
            cpu_usage = psutil.cpu_percent()
            mem_usage = psutil.virtual_memory().percent
            
            # Send payload
            await websocket.send_json({
                "type": "diagnostics",
                "data": {
                    "cpu": cpu_usage,
                    "memory": mem_usage,
                    "latency": f"{int(time.time() % 100)}ms", # Simulated for now
                    "timestamp": time.time()
                }
            })
            await asyncio.sleep(2)
    except Exception as e:
        logger.debug(f"Broadcaster stopped: {e}")

# Global Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log all unhandled exceptions as structured errors."""
    error_id = str(time.time())
    logger.error(
        f"Unhandled exception: {str(exc)}", 
        exc_info=True,
        error_id=error_id,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred.",
            "error_id": error_id
        }
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
            logger.info(f"Incoming request: {request.method} {request.url.path} (Tenant: {tenant_id})")
            response = await call_next(request)
            logger.info(f"Finished request: {response.status_code}")
            return response
    finally:
        TenantContext.reset(token)

# Configure CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend URL
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
        "ws_diagnostics": "/ws/diagnostics"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
