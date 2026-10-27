#!/usr/bin/env python3
"""Small unauthenticated read-only storefront latency smoke test."""

from concurrent.futures import ThreadPoolExecutor
import os
import statistics
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int((len(ordered) - 1) * quantile))
    return ordered[index]


def main() -> int:
    base_url = os.environ.get("BASE_URL", "").rstrip("/")
    store_slug = os.environ.get("STORE_SLUG", "")
    request_count = int(os.environ.get("REQUEST_COUNT", "100"))
    concurrency = int(os.environ.get("CONCURRENCY", "10"))
    if not base_url.startswith(("http://", "https://")) or not store_slug:
        raise SystemExit("Set BASE_URL and STORE_SLUG for a public test store")
    if not 1 <= request_count <= 10_000 or not 1 <= concurrency <= 100:
        raise SystemExit("REQUEST_COUNT must be 1..10000 and CONCURRENCY must be 1..100")

    url = f"{base_url}/api/v1/public/stores/{quote(store_slug, safe='')}/products"

    def sample(_: int) -> tuple[float, int]:
        start = time.perf_counter()
        try:
            with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=10) as response:
                response.read()
                return time.perf_counter() - start, response.status
        except HTTPError as exc:
            exc.read()
            return time.perf_counter() - start, exc.code
        except URLError:
            return time.perf_counter() - start, 0

    wall_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = list(executor.map(sample, range(request_count)))
    elapsed = time.perf_counter() - wall_start
    latencies = [duration for duration, _ in results]
    failures = sum(code != 200 for _, code in results)
    print(f"requests={request_count} concurrency={concurrency} failures={failures}")
    print(
        "latency_ms "
        f"p50={statistics.median(latencies) * 1000:.1f} "
        f"p95={percentile(latencies, 0.95) * 1000:.1f} "
        f"max={max(latencies) * 1000:.1f}"
    )
    print(f"throughput_rps={request_count / elapsed:.1f}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
