"""
gateway/routers/__init__.py
============================
Package entry point. Exposes a single register_all_routers() function
that the main mcp_server.py calls to wire all domain routers together.
"""

from __future__ import annotations

from typing import Any

from gateway.routers import forensic, intelligence, memory, nlp, system


def register_all_routers(
    mcp: Any,
    sme_core: Any,
    registry: Any,
    session_manager: Any,
    metrics_manager: Any,
    auth_manager: Any,
    rate_limiter: Any,
    extension_manager: Any,
    get_hsm: Any,
    get_nexus: Any,
) -> None:
    """
    Register all domain routers with the FastMCP instance in dependency order.

    Execution order matters:
    1. forensic first — it returns the EpistemicValidator instance needed by intelligence.
    2. All other routers are order-independent.
    """
    epistemic_tool = forensic.register(
        mcp=mcp,
        sme_core=sme_core,
        registry=registry,
        session_manager=session_manager,
        metrics_manager=metrics_manager,
    )

    memory.register(
        mcp=mcp,
        registry=registry,
        session_manager=session_manager,
        metrics_manager=metrics_manager,
    )

    nlp.register(
        mcp=mcp,
        registry=registry,
        session_manager=session_manager,
        metrics_manager=metrics_manager,
    )

    intelligence.register(
        mcp=mcp,
        sme_core=sme_core,
        registry=registry,
        session_manager=session_manager,
        metrics_manager=metrics_manager,
        epistemic_tool=epistemic_tool,
    )

    system.register(
        mcp=mcp,
        registry=registry,
        session_manager=session_manager,
        metrics_manager=metrics_manager,
        auth_manager=auth_manager,
        rate_limiter=rate_limiter,
        extension_manager=extension_manager,
        get_hsm=get_hsm,
        get_nexus=get_nexus,
    )
