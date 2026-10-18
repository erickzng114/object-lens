import asyncio

import httpx

from app import search as search_mod
from app.config import Settings
from shops.models import Product


def product(shop, price, title="ماگ"):
    return Product(shop=shop, title=title, image_url=None, product_url=f"https://{shop}/p",
                   price=price, currency="IRT", in_stock=price is not None)


async def collect(gen):
    return [item async for item in gen]


async def test_failed_empty_and_slow_shops_are_left_out(monkeypatch):
    monkeypatch.setattr(search_mod, "settings", Settings(shop_timeout_seconds=0.05))

    async def ok(query, client, limit):
        return [product("ok", 1000)]

    async def broken(query, client, limit):
        raise httpx.ConnectError("down")

    async def empty(query, client, limit):
        return []

    async def slow(query, client, limit):
        await asyncio.sleep(1)
        return [product("slow", 1)]

    got = await collect(search_mod.search_shops("ماگ", {"ok": ok, "broken": broken, "empty": empty, "slow": slow}))
    assert [shop for shop, _ in got] == ["ok"]


async def test_results_stream_in_completion_order():
    async def late(query, client, limit):
        await asyncio.sleep(0.05)
        return [product("late", 1)]

    async def early(query, client, limit):
        return [product("early", 2)]

    got = await collect(search_mod.search_shops("ماگ", {"late": late, "early": early}))
    assert [shop for shop, _ in got] == ["early", "late"]


def test_rank_by_price_cheapest_first_unpriced_last():
    ranked = search_mod.rank_by_price([product("a", 300), product("b", None), product("c", 100)])
    assert [p.shop for p in ranked] == ["c", "a", "b"]
