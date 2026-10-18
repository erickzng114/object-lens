import httpx

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "fa-IR,fa;q=0.9",
}
TIMEOUT_SECONDS = 8.0  # per-shop deadline from the spec


async def get_json(url: str, params: dict, client: httpx.AsyncClient | None = None):
    """GET a JSON endpoint; raises httpx.HTTPError on network or HTTP failure."""
    if client is not None:
        resp = await client.get(url, params=params, headers=DEFAULT_HEADERS, timeout=TIMEOUT_SECONDS)
    else:
        async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=TIMEOUT_SECONDS) as c:
            resp = await c.get(url, params=params)
    resp.raise_for_status()
    return resp.json()
