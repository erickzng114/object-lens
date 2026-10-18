from types import SimpleNamespace

import pytest

from app.query import QueryError, QueryResult, build_query


class FakeMessages:
    def __init__(self, parsed, stop_reason="end_turn"):
        self.parsed, self.stop_reason, self.calls = parsed, stop_reason, []

    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            parsed_output=self.parsed,
            stop_reason=self.stop_reason,
            usage=SimpleNamespace(input_tokens=120, output_tokens=30),
        )


def fake_claude(parsed, stop_reason="end_turn"):
    return SimpleNamespace(messages=FakeMessages(parsed, stop_reason))


async def test_build_query_returns_parsed_result_and_usage():
    want = QueryResult(found=True, search_fa="کلید شیشه بالابر زانتیا دوتایی ۵ پین", category_key="auto_parts")
    claude = fake_claude(want)
    result, usage = await build_query(claude, "xantia window switch 5 pin", "en")
    assert result == want
    assert usage.input_tokens == 120
    call = claude.messages.calls[0]
    assert call["model"] == "claude-haiku-5-5"
    assert call["output_format"] is QueryResult
    assert "xantia window switch 5 pin" in call["messages"][0]["content"]


async def test_build_query_raises_on_refusal():
    with pytest.raises(QueryError):
        await build_query(fake_claude(None, stop_reason="refusal"), "x", "fa")


async def test_build_query_raises_when_nothing_parsed():
    with pytest.raises(QueryError):
        await build_query(fake_claude(None), "x", "fa")
