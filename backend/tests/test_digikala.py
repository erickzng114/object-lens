import httpx
import pytest
import respx

from shops import digikala

QUERY = "ماگ سرامیکی سفید دسته‌دار ۳۵۰ میلی‌لیتر"


def test_parse_maps_fields_and_converts_rial_to_toman(load_fixture):
    products = digikala.parse(load_fixture("digikala_search.json"))
    first_in_stock = products[1]
    assert first_in_stock.shop == "digikala"
    assert first_in_stock.title == "ماگ سرامیکی مدل 0"
    assert first_in_stock.image_url == "https://dkstatics-public.digikala.com/p/0.jpg"
    assert first_in_stock.product_url == "https://www.digikala.com/product/dkp-1000/mug-0/"
    assert first_in_stock.price == 189000
    assert first_in_stock.price_irt == 189000
    assert first_in_stock.in_stock


def test_parse_keeps_unavailable_product_without_price(load_fixture):
    out = digikala.parse(load_fixture("digikala_search.json"))[0]
    assert out.title == "ماگ ناموجود"
    assert out.price is None
    assert out.image_url is None
    assert not out.in_stock


def test_parse_returns_at_most_ten(load_fixture):
    assert len(digikala.parse(load_fixture("digikala_search.json"))) == 10


def test_parse_empty_payload():
    assert digikala.parse({"data": {"products": []}}) == []
    assert digikala.parse({}) == []


@respx.mock
async def test_search_sends_query_and_parses(load_fixture):
    route = respx.get(digikala.SEARCH_URL).mock(
        return_value=httpx.Response(200, json=load_fixture("digikala_search.json"))
    )
    products = await digikala.search(QUERY)
    assert route.called
    assert route.calls.last.request.url.params["q"] == QUERY
    assert len(products) == 10


@respx.mock
async def test_search_raises_on_http_error():
    respx.get(digikala.SEARCH_URL).mock(return_value=httpx.Response(403))
    with pytest.raises(httpx.HTTPStatusError):
        await digikala.search(QUERY)


@pytest.mark.live
async def test_live_search():
    products = await digikala.search("ماگ سرامیکی")
    assert products, "Digikala returned no results"
    assert all(p.title and p.product_url.startswith("https://www.digikala.com/") for p in products)
