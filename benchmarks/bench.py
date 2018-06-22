import argparse
import asyncio
import math
import random
import subprocess
import sys
import time
from pprint import pprint

import aiohttp

random.seed(1337)


def build_image(name):
    return subprocess.run(f"docker build -t bench_{name} -f Dockerfile_{name} .", shell=True)


def run_container(name):
    return subprocess.run(f"docker run -d --rm --name bench_{name} -p8000:8000 bench_{name}", shell=True)


def stop_container(name):
    return subprocess.run(f"docker kill bench_{name}", shell=True)


async def get_index(session):
    async with session.get("http://127.1:8000") as response:
        await response.text()


async def get_404(session):
    async with session.get("http://127.1:8000/idontexist") as response:
        await response.text()


async def get_hello(session):
    async with session.get("http://127.1:8000/hello/Jim/24") as response:
        await response.text()


TASKS = [
    get_404,
    get_index,
    get_hello,
]


async def do_bench(session):
    start_time = time.monotonic()
    res = "n/a"

    try:
        await random.choice(TASKS)(session)
        res = "ok"

    except Exception as e:
        res = "err"

    finally:
        return res, time.monotonic() - start_time


async def benchmark(duration=30, concurrency=50, warmup=100):
    async with aiohttp.ClientSession() as session:
        results = []

        print("Warming up...")
        for _ in range(warmup):
            await do_bench(session)

        print("Benchmarking...")
        start_time = time.monotonic()
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            tasks = (do_bench(session) for _ in range(concurrency))
            results.extend(await asyncio.gather(*tasks))

        duration = time.monotonic() - start_time
        minimum, maximum, total, errors = float("inf"), float("-inf"), 0, 0
        for res, req_duration in results:
            minimum = min(minimum, req_duration)
            maximum = max(maximum, req_duration)
            errors += 1 if res == "err" else 0
            total += req_duration

        durations = sorted(d for _, d in results)

        def qtile(n):
            return durations[math.ceil(len(results) * n / 100)]

        pprint({
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
        })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("framework")
    parser.add_argument("--concurrency", "-c", default=50, type=int)
    parser.add_argument("--duration", "-d", default=30, type=int)
    args = parser.parse_args()

    build_image(args.framework)
    run_container(args.framework)
    time.sleep(3)

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(benchmark(
            duration=args.duration,
            concurrency=args.concurrency,
        ))
    finally:
        stop_container(args.framework)

    return 0


if __name__ == "__main__":
    sys.exit(main())
