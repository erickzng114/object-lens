"""Turn a user's typed or spoken text into a Persian shop search query (Haiku)."""

from typing import Literal

import anthropic
from pydantic import BaseModel

from .config import settings

CategoryKey = Literal["book", "beauty", "auto_parts", "general"]

SYSTEM_PROMPT = """You turn what an Iranian shopper typed or said into the query they would type into Digikala's search box.

The input can be in any language, may contain typos or speech-to-text mistakes, and may be vague. Write `search_fa` in Persian, 4 to 8 words, ordered like a product title in Iranian shops: product type, brand, model, then 2 to 4 distinguishing specs (material, colour, size or capacity with its unit, pin count, compatible device or car).

Rules:
- Never return a bare noun when the input has more detail ("کلید شیشه بالابر ۵ پین دوتایی", not "کلید").
- Do not add a brand, model, number or spec the user did not give; drop unknown specs instead of guessing.
- No filler words such as «خرید» or «قیمت». Normalise units (گیگابایت، میلی‌لیتر).
- Use the terms Iranian shops actually use.
- For books, include the author, publisher or ISBN if the user gave them.

`category_key` routes the search to specialist shops: book, beauty (cosmetics and personal care), auto_parts, or general for everything else.
If the input does not describe something that can be bought, set `found` to false."""


class QueryResult(BaseModel):
    found: bool
    search_fa: str
    category_key: CategoryKey


class QueryError(Exception):
    """Claude did not return a usable query; the caller should not charge or search."""


async def build_query(client: anthropic.AsyncAnthropic, text: str, lang: str):
    """Return (QueryResult, usage). Raises QueryError or anthropic.APIError."""
    response = await client.messages.parse(
        model=settings.query_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        output_config={"effort": "low"},
        output_format=QueryResult,
        messages=[{"role": "user", "content": f"Interface language: {lang}\nUser input: {text}"}],
    )
    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise QueryError(f"no query (stop_reason={response.stop_reason})")
    return response.parsed_output, response.usage
