"""Torob search via the JSON API behind torob.com/search."""

import httpx

from .http import get_json
from .models import Product

SHOP = "torob"
SEARCH_URL = "https://api.torob.com/v4/base-product/search/"
SITE = "https://torob.com"


def parse(payload: dict, limit: int = 10) -> list[Product]:
    products = []
    seen = set()
    for item in payload.get("results") or []:
        # The same product can appear twice: once ranked, once as a sponsored slot.
        key = item.get("random_key")
        if key:
            if key in seen:
                continue
            seen.add(key)
        title = item.get("name1") or item.get("name2")
        path = item.get("web_client_absolute_url")
        if not title or not path:
            continue
        price = item.get("price") or None  # toman; 0 means no seller has stock
        products.append(
            Product(
                shop=SHOP,
                title=title,
                image_url=item.get("image_url"),
                product_url=path if path.startswith("http") else SITE + path,
                price=price,
                currency="IRT",
                in_stock=price is not None,
            )
        )
        if len(products) == limit:
            break
    return products


async def search(query: str, client: httpx.AsyncClient | None = None, limit: int = 10) -> list[Product]:
    params = {"q": query, "page": 0, "size": 24, "sort": "popularity", "source": "next_desktop"}
    payload = await get_json(SEARCH_URL, params, client)
    return parse(payload, limit)
