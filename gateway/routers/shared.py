"""
gateway/routers/shared.py
=========================
Shared helpers, Pydantic request schemas, and utility factories used by all
router modules. Nothing in this file registers MCP tools — it only provides
building blocks.
"""

import json
import logging
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger("lawnmower.shared")

# =============================================================================
# Pydantic Request Schemas
# =============================================================================


class AuthorshipProRequest(BaseModel):
    text: str = Field(..., min_length=50, description="The forensic sample to analyze.")
    comparison_id: str = Field(
        "Suspect_Alpha_Vector", description="The ID of the baseline vector."
    )


class InfluenceRequest(BaseModel):
    entity_name: str = Field(
        ..., description="The name of the entity to analyze for centrality."
    )


class JustifyRequest(BaseModel):
    claim: str = Field(..., description="The forensic conclusion to audit.")
    evidence_sources: List[Dict[str, str]] = Field(
        ..., description="List of source metadata with 'id' and optional 'context'."
    )


class WitnessStatementRequest(BaseModel):
    case_id: str = Field("CASE_REF_001", description="Unique reference for the forensic case.")


class AutonomousAuditRequest(BaseModel):
    text: str = Field(..., min_length=50, description="The primary forensic evidence text.")
    case_id: str = Field("CASE_REF_001", description="Unique reference for the investigation.")


class RedTeamRequest(BaseModel):
    text: str = Field(..., description="The baseline text to simulate attacks against.")
    iterations: int = Field(5, description="Number of adversarial samples to generate and test.")


class HarvestRequest(BaseModel):
    path: str = Field(..., description="Directory path to scan for evidence.")
    suspect_id: str = Field(..., description="Unique identifier for the suspect.")


# =============================================================================
# Result Serialiser
# =============================================================================


def serialize_result(obj: Any) -> Any:
    """
    Recursively serialize any result object to a JSON-compatible structure.
    Handles dataclasses, Enums (keys and values), and objects with to_dict().
    """
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {
            (k.value if isinstance(k, Enum) else k): serialize_result(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [serialize_result(item) for item in obj]
    if isinstance(obj, Enum):
        return obj.value
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: serialize_result(v) for k, v in asdict(obj).items()}
    if hasattr(obj, "to_dict"):
        return serialize_result(obj.to_dict())
    if hasattr(obj, "__dict__"):
        return {k: serialize_result(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return obj


# =============================================================================
# safe_tool_call Factory
# =============================================================================


def make_safe_tool_call(registry: Any, metrics_manager: Any) -> Callable:
    """
    Return a bound safe_tool_call helper that uses the provided registry and
    metrics_manager. Each router calls this once at the top of register().

    Example::

        safe_tool_call = make_safe_tool_call(registry, metrics_manager)
        result = safe_tool_call("semantic_search", "search", query)
    """
    _log = logging.getLogger("lawnmower.safe_tool_call")

    def safe_tool_call(tool_name: str, method_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Safely call a registry tool method with circuit-breaker metrics."""
        start_time = time.perf_counter()
        try:
            metrics_manager.track_call(tool_name, "general")

            tool = registry.get_tool(tool_name)
            if tool is None:
                metrics_manager.track_error(tool_name, "tool_unavailable")
                return {"error": f"{tool_name} not available", "status": "tool_unavailable"}

            method = getattr(tool, method_name, None)
            if method is None:
                for alt in ("analyze", "process", "execute", "run"):
                    method = getattr(tool, alt, None)
                    if method:
                        break

            if method is None:
                metrics_manager.track_error(tool_name, "method_not_found")
                return {"error": f"Method '{method_name}' not found on {tool_name}"}

            result = method(*args, **kwargs)
            duration = time.perf_counter() - start_time
            metrics_manager.observe_latency(tool_name, duration)
            return {"success": True, "data": serialize_result(result)}

        except Exception as e:
            _log.error(f"Tool call failed: {tool_name}.{method_name} - {e}")
            metrics_manager.track_error(tool_name, type(e).__name__)
            return {"error": str(e), "tool": tool_name, "status": "error"}

    return safe_tool_call


# =============================================================================
# Auth / Rate-limit helper
# =============================================================================


def validate_access(
    token: Optional[str],
    client_id: str,
    auth_manager: Any,
    rate_limiter: Any,
) -> Optional[str]:
    """Return a JSON error string if access is denied, else None."""
    allowed, _ = rate_limiter.is_allowed(client_id)
    if not allowed:
        return json.dumps({"error": "Rate limit exceeded", "retry_after": "60s"})
    if token:
        payload = auth_manager.verify_token(token)
        if not payload:
            return json.dumps({"error": "Invalid or expired token"})
    return None
