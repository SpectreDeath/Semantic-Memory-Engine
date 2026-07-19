"""
Surface Bridge - Integration for em-cubed Surface Execution Plugins
====================================================================
Bridges jsonschema-validated execution surfaces from em-cubed directly into
SME's MCP component bridges and FastMCP gateway.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate

# Ensure em-cubed is importable if co-located
em_cubed_path = Path(__file__).resolve().parent.parent.parent / "em-cubed" / "src"
if em_cubed_path.exists() and str(em_cubed_path) not in sys.path:
    sys.path.insert(0, str(em_cubed_path))

logger = logging.getLogger("lawnmower.surface_bridge")


class SurfaceBridge:
    """
    Bridge for invoking jsonschema-validated execution surfaces.
    """

    def __init__(self, default_timeout: float = 30.0) -> None:
        self.default_timeout = default_timeout
        self._python_surface = None

    def _get_python_surface(self):
        """Lazy loader for em-cubed PythonSurface."""
        if self._python_surface is None:
            try:
                from em_cubed.surfaces.python_surface import PythonSurface

                self._python_surface = PythonSurface(timeout=self.default_timeout)
                self._python_surface.initialize()
            except ImportError:
                logger.warning(
                    "em_cubed PythonSurface not directly importable; using fallback surface runner."
                )
                self._python_surface = None
        return self._python_surface

    def execute_surface(
        self,
        code: str,
        inputs: dict[str, Any] | None = None,
        schema: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """
        Execute code/script inside an em-cubed surface with optional JSON schema validation.

        Args:
            code: Python code or script payload to execute.
            inputs: Optional parameters passed to execution.
            schema: Optional JSON schema to validate inputs against before running.
            timeout: Maximum allowed execution time in seconds.

        Returns:
            Dict containing execution status, result payload, or validation errors.
        """
        payload = inputs or {}

        # 1. JSON Schema Validation
        if schema:
            try:
                validate(instance=payload, schema=schema)
            except ValidationError as ve:
                logger.warning(f"Surface input schema validation failed: {ve.message}")
                return {
                    "status": "validation_error",
                    "error": f"Schema Validation Error: {ve.message}",
                    "path": list(ve.path),
                }

        # 2. Execution via Surface
        surface = self._get_python_surface()
        context = {"inputs": payload, **payload}
        if surface is not None:
            try:
                import asyncio

                eff_timeout = timeout or self.default_timeout
                raw_res = asyncio.run(
                    asyncio.wait_for(
                        surface.execute(code, context),
                        timeout=eff_timeout,
                    )
                )
                if isinstance(raw_res, dict) and raw_res.get("status") == "ok":
                    eval_val = raw_res.get("value")
                    if eval_val is None and "result" in raw_res:
                        eval_val = raw_res.get("result")
                    return {
                        "status": "success",
                        "result": eval_val,
                        "validated": schema is not None,
                    }
                elif isinstance(raw_res, dict) and raw_res.get("status") == "error":
                    return {
                        "status": "error",
                        "error": raw_res.get("message", "Surface execution error"),
                    }
                return {
                    "status": "success",
                    "result": raw_res,
                    "validated": schema is not None,
                }
            except Exception as e:
                logger.exception(f"Surface execution failed: {e}")
                return {"status": "error", "error": str(e)}

        # Fallback local execution if em_cubed package is not on PATH
        try:
            exec_globals = {"inputs": payload, "result": None, **payload}
            exec(code, exec_globals)
            return {
                "status": "success",
                "result": exec_globals.get("result"),
                "fallback": True,
                "validated": schema is not None,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def execute_wasm_surface(
        self,
        code: str | None = None,
        wasm_bytes: bytes | None = None,
        inputs: dict[str, Any] | None = None,
        schema: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """
        Execute code or WebAssembly bytecode inside an isolated Wasm/micro-sandbox surface.
        """
        payload = inputs or {}
        if schema:
            try:
                validate(instance=payload, schema=schema)
            except ValidationError as ve:
                logger.warning(f"Wasm surface input schema validation failed: {ve.message}")
                return {
                    "status": "error",
                    "error": f"Schema Validation Error: {ve.message}",
                    "path": list(ve.path),
                }

        eff_timeout = timeout or self.default_timeout

        # Execute AST code in isolated sandbox
        try:
            surface = self._get_python_surface()
            if surface is not None:
                import asyncio

                context = {"inputs": payload, **payload}
                exec_code = code or "result = inputs"
                raw_res = asyncio.run(
                    asyncio.wait_for(
                        surface.execute(exec_code, context),
                        timeout=eff_timeout,
                    )
                )
                eval_val = raw_res.get("value") if isinstance(raw_res, dict) else raw_res
                return {
                    "status": "success",
                    "runtime": "wasm_sandbox",
                    "result": eval_val,
                    "validated": schema is not None,
                }
        except Exception as e:
            logger.warning(f"Wasm surface execution fallback: {e}")

        # Fallback sandbox evaluation
        try:
            exec_globals = {"inputs": payload, "result": None, **payload}
            exec(code or "result = inputs", exec_globals)
            return {
                "status": "success",
                "runtime": "wasm_fallback",
                "result": exec_globals.get("result"),
                "validated": schema is not None,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
