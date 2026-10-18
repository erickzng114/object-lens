"""Digikala search via the JSON API behind digikala.com/search."""

import httpx

from .http import get_json
from .models import Product

SHOP = "digikala"
SEARCH_URL = "https://api.digikala.com/v1/search/"
SITE = "https://www.digikala.com"


def parse(payload: dict, limit: int = 10) -> list[Product]:
    products = []
    for item in (payload.get("data") or {}).get("products") or []:
        title = item.get("title_fa") or item.get("title_en")
        if not title:
            continue
        uri = (item.get("url") or {}).get("uri") or f"/product/dkp-{item['id']}/"
        images = ((item.get("images") or {}).get("main") or {}).get("url") or []
        # default_variant is [] (not a dict) when the product is unavailable.
        variant = item.get("default_variant")
        rial = (variant.get("price") or {}).get("selling_price") if isinstance(variant, dict) else None
        products.append(
            Product(
                shop=SHOP,
                title=title,
                image_url=images[0] if images else None,
                product_url=SITE + uri,
                price=rial // 10 if rial else None,  # API prices are in rial
                currency="IRT",
                in_stock=bool(rial),
            )
        )
        if len(products) == limit:
            break
    return products


async def search(query: str, client: httpx.AsyncClient | None = None, limit: int = 10) -> list[Product]:
    payload = await get_json(SEARCH_URL, {"q": query, "page": 1}, client)
    return parse(payload, limit)
