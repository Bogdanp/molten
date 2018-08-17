import argparse
import asyncio
import json
import math
import random
import subprocess
import sys
import time
from collections import Counter

import aiohttp
import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
random.seed(1337)


def shell(cmd, *, timeout=120, **opts):
    if not opts:
        opts = dict(stdout=sys.stderr, stderr=sys.stderr)

    return subprocess.run(cmd, shell=True, timeout=timeout, **opts)


def build_image(name, context="."):
    return shell(f"docker build -t bench_{name} -f Dockerfile_{name} {context}")


def run_container(name):
    return shell(f"docker run -d --rm --name bench_{name} -p8000:8000 bench_{name}")


def stop_container(name):
    return shell(f"docker kill bench_{name}")


def get_container_memory_usage(name):
    res = shell(f"docker stats --format '{{{{.MemUsage}}}}' --no-stream bench_{name}", capture_output=True)
    memory_usage = res.stdout.strip().decode()
    current, _, _ = memory_usage.partition("/")
    return current.strip()


async def get_index(session):
    async with session.get("http://127.1:8000") as response:
        await response.text()


async def get_404(session):
    async with session.get("http://127.1:8000/idontexist") as response:
        await response.text()


async def get_hello(session):
    async with session.get("http://127.1:8000/hello/Jim/24") as response:
        await response.text()


async def post_json(session):
    payload = {"nested": {"example": {"array": [1, 2, 3]}}}
    async with session.post("http://127.1:8000/echo", json=payload) as response:
        await response.text()


TASKS = [
    *([get_index] * 100),
    *([post_json] * 50),
    *([get_hello] * 30),
    *([get_404] * 1),
]
random.shuffle(TASKS)


async def do_bench(session):
    start_time = time.monotonic()
    res, task_name = "n/a", None

    try:
        task = random.choice(TASKS)
        task_name = task.__name__
        await task(session)
        res = "ok"

    except Exception as e:
        res = "err"

    finally:
        return res, task_name, time.monotonic() - start_time


async def benchmark(name, duration=30, concurrency=50, warmup=1000):
    async with aiohttp.ClientSession() as session:
        print("Warming up...", file=sys.stderr)
        for _ in range(warmup):
            await do_bench(session)

        print("Benchmarking...", file=sys.stderr)
        start_time = time.monotonic()
        deadline = time.monotonic() + duration
        pending_tasks, results = set(), []
        while time.monotonic() < deadline:
            if len(pending_tasks) < concurrency:
                pending_tasks.add(asyncio.ensure_future(do_bench(session)))

            else:
                done_tasks, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)
                results.extend(t.result() for t in done_tasks)

        done_tasks, _ = await asyncio.wait(pending_tasks)
        results.extend(t.result() for t in done_tasks)

        duration = time.monotonic() - start_time
        minimum, maximum, total, errors = float("inf"), float("-inf"), 0, 0
        for res, _, req_duration in results:
            minimum = min(minimum, req_duration)
            maximum = max(maximum, req_duration)
            errors += 1 if res == "err" else 0
            total += req_duration

        tasks = Counter(t for _, t, _ in results)
        durations = sorted(d for _, _, d in results)

        def qtile(n):
            return durations[math.ceil(len(results) * n / 100)]

        print(json.dumps({
            "memory_usage": get_container_memory_usage(name),
            "duration": f"{duration:.02f}s",
            "qps": f"{len(results) / duration:0.2f}",
            "minimum": f"{minimum * 1000:.02f}ms",
            "maximum": f"{maximum * 1000:.02f}ms",
            "average": f"{total / len(results) * 1000:.02f}ms",
            "p99": f"{qtile(99) * 1000:.02f}ms",
            "p95": f"{qtile(95) * 1000:.02f}ms",
            "p90": f"{qtile(90) * 1000:.02f}ms",
            "p75": f"{qtile(75) * 1000:.02f}ms",
            "p50": f"{qtile(50) * 1000:.02f}ms",
            "requests": len(results),
            "errors": errors,
            "tasks": dict(tasks),
        }, indent=4))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("framework")
    parser.add_argument("--concurrency", "-c", default=50, type=int)
    parser.add_argument("--duration", "-d", default=30, type=int)
    args = parser.parse_args()

    context = "."
    if args.framework == "molten":
        context = ".."

    build_image(args.framework, context)
    run_container(args.framework)
    time.sleep(3)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(benchmark(
            name=args.framework,
            duration=args.duration,
            concurrency=args.concurrency,
        ))
    finally:
        stop_container(args.framework)

    return 0


if __name__ == "__main__":
    sys.exit(main())
