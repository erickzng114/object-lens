"""Search all shops at once and yield each shop's results as soon as they arrive."""

import asyncio
import logging
from collections.abc import AsyncIterator, Callable, Awaitable

import httpx

from shops import digikala, torob
from shops.http import DEFAULT_HEADERS
from shops.models import Product

from .config import settings

log = logging.getLogger("object_lens.search")

ShopSearch = Callable[..., Awaitable[list[Product]]]
DOMESTIC_SHOPS: dict[str, ShopSearch] = {"digikala": digikala.search, "torob": torob.search}


async def search_shops(query: str, shops: dict[str, ShopSearch] | None = None) -> AsyncIterator[tuple[str, list[Product]]]:
    """Yield (shop, products) per shop in completion order.

    A shop that errors, times out or returns nothing is skipped and only logged,
    so it never shows up in results, filters or counts (spec: «فروشگاه بدون نتیجه»).
    """
    shops = shops or DOMESTIC_SHOPS
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS) as client:

        async def run(name: str, fn: ShopSearch):
            try:
                products = await asyncio.wait_for(
                    fn(query, client=client, limit=settings.results_per_shop),
                    settings.shop_timeout_seconds,
                )
            except (httpx.HTTPError, TimeoutError, ValueError) as e:
                log.warning("shop=%s failed: %s: %s", name, type(e).__name__, e)
                return name, []
            if not products:
                log.info("shop=%s no results for %r", name, query)
            return name, products

        for task in asyncio.as_completed([run(n, f) for n, f in shops.items()]):
            name, products = await task
            if products:
                yield name, products


def rank_by_price(products: list[Product]) -> list[Product]:
    # Cheapest first; products without a price go last (spec: «قیمت در دایرکت»).
    return sorted(products, key=lambda p: (p.price_irt is None, p.price_irt or 0))
