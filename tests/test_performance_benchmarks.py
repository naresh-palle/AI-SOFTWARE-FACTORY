"""
Automated Performance & Scalability Test Gate.
Verifies that API throughput and latency meet production SLAs under concurrent load.
"""

import pytest
from scripts.performance_benchmark import PerformanceBenchmarkRunner


@pytest.mark.asyncio
async def test_api_performance_sla_benchmark():
    """Verify production API throughput and latency SLAs under concurrency."""
    result = await PerformanceBenchmarkRunner.benchmark_endpoint(
        endpoint="/api/v1/saas/subscriptions/plans",
        total_requests=50,
        concurrency=5
    )

    assert result["error_percentage"] == 0.0
    assert result["requests_per_second"] > 10.0
    assert result["latency_ms"]["p50"] < 500.0  # p50 under 500ms
