"""Object Lens API — phase 1: text search over Digikala and Torob."""

import json
import uuid
from dataclasses import asdict

import anthropic
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from shops.models import Product

from . import search as search_mod
from .config import settings
from .cost_log import CostLog
from .query import QueryError, build_query

app = FastAPI(title="Object Lens")
cost_log = CostLog()
# Search id -> query; in memory until the `searches` table exists.
searches: dict[str, dict] = {}


def get_claude() -> anthropic.AsyncAnthropic:
    # Reads ANTHROPIC_API_KEY from the environment; never from code.
    return anthropic.AsyncAnthropic()


class QueryIn(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    lang: str = Field(default="fa", pattern="^(fa|en|ar|tr|de|fr)$")


class QueryOut(BaseModel):
    id: str
    search_fa: str
    category_key: str


@app.post("/v1/query", response_model=QueryOut)
async def query(body: QueryIn, claude: anthropic.AsyncAnthropic = Depends(get_claude)):
    search_id = uuid.uuid4().hex
    try:
        result, usage = await build_query(claude, body.text, body.lang)
    except QueryError:
        raise HTTPException(422, "query_not_understood")
    except anthropic.APIError:
        raise HTTPException(503, "query_service_unavailable")
    cost_log.record(search_id, "query", settings.query_model, usage)
    if not result.found:
        raise HTTPException(422, "query_not_understood")
    searches[search_id] = {"search_fa": result.search_fa, "category_key": result.category_key}
    return QueryOut(id=search_id, search_fa=result.search_fa, category_key=result.category_key)


def product_json(p: Product) -> dict:
    return {**asdict(p), "price_irt": p.price_irt}


def sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/v1/search/{search_id}")
async def search(search_id: str, q_fa: str | None = None):
    record = searches.get(search_id)
    if record is None:
        raise HTTPException(404, "unknown_search")
    # q_fa lets the user run the query they edited in the search box.
    query_text = (q_fa or record["search_fa"]).strip()
    if not query_text:
        raise HTTPException(422, "empty_query")

    async def events():
        found: list[Product] = []
        async for shop, products in search_mod.search_shops(query_text):
            found.extend(products)
            yield sse("shop_results", {"shop": shop, "products": [product_json(p) for p in products]})
        yield sse("ranked", {"products": [product_json(p) for p in search_mod.rank_by_price(found)]})

    return StreamingResponse(events(), media_type="text/event-stream")
