"""Phase 0 access check: search each shop live and report whether it works.

Run from backend/:  python -m scripts.probe_shops "ماگ سرامیکی"
"""

import asyncio
import sys
import time

import httpx

from shops import digikala, torob

SHOPS = {"digikala": digikala, "torob": torob}


async def probe(name, module, query):
    start = time.monotonic()
    try:
        products = await module.search(query)
    except httpx.HTTPError as e:
        return f"{name}: FAIL ({type(e).__name__}: {e})", []
    took = time.monotonic() - start
    priced = sum(p.price is not None for p in products)
    status = "OK" if products else "EMPTY"
    return f"{name}: {status}, {len(products)} results ({priced} with price) in {took:.1f}s", products


async def main(query):
    results = await asyncio.gather(*(probe(n, m, query) for n, m in SHOPS.items()))
    for line, products in results:
        print(line)
        for p in products:
            price = f"{p.price:,} تومان" if p.price else "—"
            print(f"  {price:>16}  {p.title}\n  {'':>16}  {p.product_url}\n  {'':>16}  {p.image_url}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "ماگ سرامیکی"))
