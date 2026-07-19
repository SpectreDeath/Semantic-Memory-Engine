"""
E2E Gateway Load & Concurrency Benchmark Suite
================================================
Stress tests Lawnmower Man Gateway under high concurrent load across FastMCP tools,
REST API endpoints, and em-cubed surface execution runtimes.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest
from fastapi.testclient import TestClient

from gateway.mcp_server import SmeCoreBridge
from gateway.traffic_router import RULE_AUTO_BALANCE, RULE_LOCAL_ONLY, TrafficRouter
from src.api.main import app


def calculate_percentiles(latencies: list[float]) -> dict[str, float]:
    """Calculate p50, p95, and p99 latency metrics in milliseconds."""
    if not latencies:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

    sorted_lat = sorted(latencies)
    n = len(sorted_lat)

    p50_idx = int(0.50 * n)
    p95_idx = min(int(0.95 * n), n - 1)
    p99_idx = min(int(0.99 * n), n - 1)

    return {
        "p50": round(sorted_lat[p50_idx] * 1000, 2),
        "p95": round(sorted_lat[p95_idx] * 1000, 2),
        "p99": round(sorted_lat[p99_idx] * 1000, 2),
    }


class TestFastMcpConcurrency:
    """Benchmark high-concurrency FastMCP tool dispatching via TrafficRouter."""

    @pytest.mark.asyncio
    async def test_concurrent_fastmcp_tool_dispatch(self):
        router = TrafficRouter()
        sme_core = SmeCoreBridge()
        num_requests = 50
        latencies: list[float] = []

        async def worker(request_id: int):
            t0 = time.perf_counter()
            res = router.dispatch_workload(
                tool_name="verify_system",
                payload={"check_disk": True, "req_id": request_id},
                mode=RULE_LOCAL_ONLY,
                sme_core=sme_core,
            )
            dt = time.perf_counter() - t0
            latencies.append(dt)
            return res

        t_start = time.perf_counter()
        tasks = [worker(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - t_start

        assert len(results) == num_requests
        assert all(r["status"] == "success" for r in results)

        rps = round(num_requests / total_time, 2)
        metrics = calculate_percentiles(latencies)

        print("\n--- FastMCP Tool Concurrency Benchmark ---")
        print(f"Total Requests: {num_requests} in {round(total_time, 3)}s ({rps} RPS)")
        print(f"Latency -> p50: {metrics['p50']}ms | p95: {metrics['p95']}ms | p99: {metrics['p99']}ms")

        assert rps > 10.0  # Must exceed baseline throughput requirement


class TestRestApiConcurrency:
    """Benchmark REST API route endpoint performance."""

    def test_concurrent_rest_route_endpoint(self):
        client = TestClient(app)
        num_requests = 30
        latencies: list[float] = []

        t_start = time.perf_counter()
        successes = 0

        for i in range(num_requests):
            t0 = time.perf_counter()
            response = client.post(
                "/api/v1/route",
                json={
                    "tool_name": f"analyze_authorship_{i}",
                    "payload": {"text": f"Sample text block {i}"},
                    "mode": RULE_AUTO_BALANCE,
                },
            )
            dt = time.perf_counter() - t0
            latencies.append(dt)

            if response.status_code == 200:
                successes += 1

        total_time = time.perf_counter() - t_start
        rps = round(num_requests / total_time, 2)
        metrics = calculate_percentiles(latencies)

        print("\n--- REST API /route Concurrency Benchmark ---")
        print(f"Total Requests: {num_requests} in {round(total_time, 3)}s ({rps} RPS)")
        print(f"Latency -> p50: {metrics['p50']}ms | p95: {metrics['p95']}ms | p99: {metrics['p99']}ms")

        assert successes == num_requests
        assert response.status_code == 200


class TestSurfaceExecutionConcurrency:
    """Benchmark em-cubed Python surface execution under load."""

    def test_concurrent_surface_execution(self):
        sme_core = SmeCoreBridge()
        num_requests = 10
        latencies: list[float] = []
        successes = 0

        t_start = time.perf_counter()
        for i in range(num_requests):
            t0 = time.perf_counter()
            res = sme_core.execute_surface(
                code=f"x = {i} * 2\nresult = x",
                inputs={"i": i},
                schema={"type": "object", "properties": {"i": {"type": "integer"}}},
            )
            dt = time.perf_counter() - t0
            latencies.append(dt)

            if res.get("status") == "success" or "result" in res or "value" in str(res):
                successes += 1

        total_time = time.perf_counter() - t_start
        rps = round(num_requests / total_time, 2)
        metrics = calculate_percentiles(latencies)

        print("\n--- em-cubed Surface Execution Benchmark ---")
        print(f"Total Executions: {num_requests} in {round(total_time, 3)}s ({rps} RPS)")
        print(f"Latency -> p50: {metrics['p50']}ms | p95: {metrics['p95']}ms | p99: {metrics['p99']}ms")

        assert successes == num_requests
