#!/usr/bin/env python3
"""
Benchmark script for AWS ALB.
- Reads ALB DNS from alb_info.json.
- Sends 1000 requests to /cluster1 and /cluster2.
"""

import asyncio
import aiohttp
import time
import json
import sys


async def call_endpoint_http(session, request_num, url):
    """Send a single HTTP request to the given URL"""
    headers = {"content-type": "application/json"}
    try:
        async with session.get(url, headers=headers) as response:
            status_code = response.status
            response_json = await response.json()
            print(f"Request {request_num}: Status Code: {status_code}")
            return status_code, response_json
    except Exception as e:
        print(f"Request {request_num}: Failed - {str(e)}")
        return None, str(e)


async def benchmark(url: str, num_requests: int = 1000):
    """Benchmark a given endpoint with N requests"""
    print(f"\n🚀 Benchmarking {url} with {num_requests} requests...")
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        tasks = [call_endpoint_http(session, i, url) for i in range(num_requests)]
        await asyncio.gather(*tasks)

    end_time = time.time()
    total_time = end_time - start_time
    print(f"\n✅ Benchmark completed for {url}")
    print(f"⏱️ Total time: {total_time:.2f} seconds")
    print(f"⚡ Avg time per request: {total_time / num_requests:.4f} seconds")


async def main():
    # Load ALB info
    try:
        with open("alb_info.json") as f:
            alb_info = json.load(f)
        base_url = f"http://{alb_info['DNSName']}"
        print(f"🌐 Using ALB DNS: {base_url}")
    except Exception as e:
        print(f"❌ Could not load alb_info.json: {e}")
        sys.exit(1)

    # Build URLs
    cluster1_url = f"{base_url}/cluster1"
    cluster2_url = f"{base_url}/cluster2"

    # Run benchmarks
    await benchmark(cluster1_url, 1000)
    await benchmark(cluster2_url, 1000)


if __name__ == "__main__":
    asyncio.run(main())
