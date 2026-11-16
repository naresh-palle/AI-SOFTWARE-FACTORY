"""
Empirical Performance & Load Testing Benchmark Suite.
Measures API throughput (RPS), p50, p95, p99 latency, error rates, and concurrent capacity.
"""

import asyncio
import time
import statistics
from typing import Dict, Any, List
from httpx import ASGITransport, AsyncClient
from factory.api.main import app
from factory.core.database import init_db


class PerformanceBenchmarkRunner:
    """Executes high-concurrency synthetic load tests against the API Gateway."""

    @staticmethod
    async def benchmark_endpoint(
        endpoint: str,
        method: str = "GET",
        total_requests: int = 100,
        concurrency: int = 10,
        payload: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        await init_db()
        from factory.core.database import get_db_session
        from factory.saas.subscription_manager import SubscriptionManager
        async with get_db_session() as s:
            await SubscriptionManager().initialize_plans(s)

        transport = ASGITransport(app=app)
        latencies = []
        errors = 0

        semaphore = asyncio.Semaphore(concurrency)

        async def _worker(client: AsyncClient):
            nonlocal errors
            async with semaphore:
                start_t = time.perf_counter()
                try:
                    if method == "GET":
                        r = await client.get(endpoint, headers=headers)
                    elif method == "POST":
                        r = await client.post(endpoint, headers=headers, json=payload)
                    else:
                        r = await client.request(method, endpoint, headers=headers)
                    
                    elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                    latencies.append(elapsed_ms)
                    if r.status_code >= 400 and r.status_code != 429:
                        errors += 1
                except Exception:
                    errors += 1

        async with AsyncClient(transport=transport, base_url="http://benchmark") as client:
            overall_start = time.perf_counter()
            tasks = [asyncio.create_task(_worker(client)) for _ in range(total_requests)]
            await asyncio.gather(*tasks)
            overall_duration = time.perf_counter() - overall_start

        latencies.sort()
        n = len(latencies)
        p50 = statistics.median(latencies) if latencies else 0.0
        p95 = latencies[int(n * 0.95)] if latencies else 0.0
        p99 = latencies[int(n * 0.99)] if latencies else 0.0
        rps = round(total_requests / overall_duration, 2) if overall_duration > 0 else 0.0

        return {
            "endpoint": endpoint,
            "total_requests": total_requests,
            "concurrency": concurrency,
            "duration_seconds": round(overall_duration, 3),
            "requests_per_second": rps,
            "error_count": errors,
            "error_percentage": round((errors / total_requests) * 100, 2),
            "latency_ms": {
                "min": round(min(latencies), 2) if latencies else 0.0,
                "p50": round(p50, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2),
                "max": round(max(latencies), 2) if latencies else 0.0,
            }
        }


if __name__ == "__main__":
    async def main():
        print("Executing Production API Load Benchmark...")
        res = await PerformanceBenchmarkRunner.benchmark_endpoint(
            endpoint="/api/v1/saas/subscriptions/plans",
            total_requests=100,
            concurrency=10
        )
        import json
        print(json.dumps(res, indent=2))
    asyncio.run(main())
