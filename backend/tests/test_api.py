import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import main, search as search_mod
from app.query import QueryResult
from shops.models import Product


class FakeMessages:
    def __init__(self, parsed):
        self.parsed = parsed

    async def parse(self, **kwargs):
        return SimpleNamespace(parsed_output=self.parsed, stop_reason="end_turn",
                               usage=SimpleNamespace(input_tokens=100, output_tokens=20))


@pytest.fixture
def client():
    main.searches.clear()
    main.cost_log.rows.clear()
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def use_claude(parsed):
    main.app.dependency_overrides[main.get_claude] = lambda: SimpleNamespace(messages=FakeMessages(parsed))


def parse_sse(text):
    events = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def test_query_returns_id_and_logs_cost(client):
    use_claude(QueryResult(found=True, search_fa="ماگ سرامیکی سفید", category_key="general"))
    r = client.post("/v1/query", json={"text": "white ceramic mug", "lang": "en"})
    assert r.status_code == 200
    body = r.json()
    assert body["search_fa"] == "ماگ سرامیکی سفید"
    assert body["id"] in main.searches
    assert main.cost_log.rows[0].input_tokens == 100


def test_query_not_a_product_is_422(client):
    use_claude(QueryResult(found=False, search_fa="", category_key="general"))
    assert client.post("/v1/query", json={"text": "سلام"}).status_code == 422


def test_query_rejects_unknown_lang(client):
    assert client.post("/v1/query", json={"text": "mug", "lang": "xx"}).status_code == 422


def test_search_streams_shops_then_ranked(client, monkeypatch):
    async def digikala(query, client, limit):
        return [Product("digikala", query, None, "https://d/p", 300000, "IRT", True)]

    async def torob(query, client, limit):
        return [Product("torob", query, None, "https://t/p", 189000, "IRT", True)]

    monkeypatch.setattr(search_mod, "DOMESTIC_SHOPS", {"digikala": digikala, "torob": torob})
    main.searches["abc"] = {"search_fa": "ماگ", "category_key": "general"}

    r = client.get("/v1/search/abc", params={"q_fa": "ماگ سرامیکی"})
    events = parse_sse(r.text)
    assert [e for e, _ in events] == ["shop_results", "shop_results", "ranked"]
    ranked = events[-1][1]["products"]
    assert [p["shop"] for p in ranked] == ["torob", "digikala"]
    assert ranked[0]["title"] == "ماگ سرامیکی"  # edited query was used
    assert ranked[0]["price_irt"] == 189000


def test_search_unknown_id_is_404(client):
    assert client.get("/v1/search/nope").status_code == 404
