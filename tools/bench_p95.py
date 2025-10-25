# tools/bench_p95.py
import asyncio, aiohttp, time, argparse, json, statistics
from math import floor

def percentile(values, p):
    if not values:
        return 0.0
    xs = sorted(values)
    i = floor(p * (len(xs) - 1))
    return xs[i]

async def worker(session, url, payload, latencies, errors, stop_at):
    while time.time() < stop_at:
        t0 = time.perf_counter()
        try:
            async with session.post(url, json=payload, timeout=10) as resp:
                await resp.read()
                if resp.status >= 400:
                    errors.append(resp.status)
                latencies.append((time.perf_counter() - t0) * 1000.0)
        except Exception:
            errors.append(599)

async def run_load(url, users, duration, payload):
    latencies, errors = [], []
    stop_at = time.time() + duration
    conn = aiohttp.TCPConnector(limit=0)
    async with aiohttp.ClientSession(connector=conn) as session:
        tasks = [asyncio.create_task(worker(session, url, payload, latencies, errors, stop_at)) for _ in range(users)]
        await asyncio.gather(*tasks)
    total = len(latencies)
    p50 = percentile(latencies, 0.50)
    p95 = percentile(latencies, 0.95)
    p99 = percentile(latencies, 0.99)
    avg = statistics.mean(latencies) if latencies else 0
    err_rate = (len(errors) / (total + len(errors))) * 100 if (total + len(errors)) else 0
    print(json.dumps({"total": total, "avg_ms": round(avg,1), "p50_ms": round(p50,1), "p95_ms": round(p95,1), "p99_ms": round(p99,1), "errors": len(errors), "error_rate_pct": round(err_rate,2)}, indent=2))
    print(f"Benchmark (POST /api/query, {users} users, {duration}s): p95={p95:.0f} ms, avg={avg:.0f} ms, errors={len(errors)} ({err_rate:.1f}%).")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000/api/query")
    ap.add_argument("--users", type=int, default=10)
    ap.add_argument("--duration", type=int, default=60)
    ap.add_argument("--query", default="Average salary by department")
    args = ap.parse_args()
    payload = {"query": args.query, "limit": 50, "offset": 0}
    asyncio.run(run_load(args.url, args.users, args.duration, payload))
