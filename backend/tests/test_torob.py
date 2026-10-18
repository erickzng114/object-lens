import httpx
import pytest
import respx

from shops import torob

QUERY = "ماگ سرامیکی سفید دسته‌دار ۳۵۰ میلی‌لیتر"


def test_parse_maps_fields(load_fixture):
    first_in_stock = torob.parse(load_fixture("torob_search.json"))[1]
    assert first_in_stock.shop == "torob"
    assert first_in_stock.title == "ماگ سرامیکی 0"
    assert first_in_stock.image_url == "https://image.torob.com/base/images/0.jpg"
    assert first_in_stock.product_url == "https://torob.com/p/uuid-0/mug-0/"
    assert first_in_stock.price == 189000
    assert first_in_stock.in_stock


def test_parse_zero_price_means_unavailable(load_fixture):
    out = torob.parse(load_fixture("torob_search.json"))[0]
    assert out.title == "ماگ ناموجود"
    assert out.price is None
    assert not out.in_stock


def test_parse_skips_items_without_link_and_caps_at_ten(load_fixture):
    products = torob.parse(load_fixture("torob_search.json"))
    assert len(products) == 10
    assert all(p.title != "بدون لینک" for p in products)


def test_parse_empty_payload():
    assert torob.parse({"results": []}) == []
    assert torob.parse({}) == []


@respx.mock
async def test_search_sends_query_and_parses(load_fixture):
    route = respx.get(torob.SEARCH_URL).mock(
        return_value=httpx.Response(200, json=load_fixture("torob_search.json"))
    )
    products = await torob.search(QUERY)
    assert route.calls.last.request.url.params["q"] == QUERY
    assert len(products) == 10


@respx.mock
async def test_search_raises_on_timeout():
    respx.get(torob.SEARCH_URL).mock(side_effect=httpx.ConnectTimeout("timeout"))
    with pytest.raises(httpx.TimeoutException):
        await torob.search(QUERY)


@pytest.mark.live
async def test_live_search():
    products = await torob.search("ماگ سرامیکی")
    assert products, "Torob returned no results"
    assert all(p.title and p.product_url.startswith("https://torob.com/") for p in products)
