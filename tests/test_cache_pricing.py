"""Caching never freezes a price or reuses counts for changed inputs."""

import json
import sqlite3
from contextlib import contextmanager

import pytest

from src.costs import calculator, pricing
from src.costs.cache import EstimateCache, estimate_key
from src.costs.models import PRICES, get_model_price, get_model_price_info


def test_persistent_cache_reuses_counts_but_reprices(tmp_path, monkeypatch):
    path = tmp_path / "counts.sqlite3"
    cache = EstimateCache(path)
    before = calculator.ai_cost("+hello\n", "gpt-4o", cache=cache)
    cache.close()
    cache = EstimateCache(path)
    monkeypatch.setitem(PRICES, "gpt-4o", {"input": 0.01, "output": 0.02})

    def forbidden(*args):
        pytest.fail("Cached input must not be tokenized again")

    monkeypatch.setattr(calculator._tokenizer, "count_tokens", forbidden)
    after = calculator.ai_cost("+hello\n", "gpt-4o", cache=cache)
    assert before["tokens"] == after["tokens"]
    assert after["cost"] > before["cost"]
    assert after["pricing"]["status"] == "custom"
    assert cache.hits == 1
    cache.close()
    raw = path.read_bytes()
    assert b"+hello" not in raw


def test_cache_keys_invalidate_on_content_model_encoding_and_version(monkeypatch):
    from src.costs import cache

    original = estimate_key("+a", "gpt-4", "cl100k_base")
    assert original != estimate_key("+b", "gpt-4", "cl100k_base")
    assert original != estimate_key("+a", "gpt-4o", "cl100k_base")
    assert original != estimate_key("+a", "gpt-4", "o200k_base")
    monkeypatch.setattr(cache, "ESTIMATOR_VERSION", "next-algorithm")
    assert original != estimate_key("+a", "gpt-4", "cl100k_base")


def test_disabled_corrupt_and_locked_cache_do_not_block_counting(tmp_path, monkeypatch):
    monkeypatch.setenv("COSTS_CACHE", "0")
    path = tmp_path / "disabled.sqlite3"
    cache = EstimateCache(path)
    assert calculator.ai_cost("+a", cache=cache)["tokens"]["output"] == 30
    assert not path.exists()
    monkeypatch.setenv("COSTS_CACHE", "1")
    path.write_bytes(b"not sqlite")
    broken = EstimateCache(path)
    assert calculator.ai_cost("+a", cache=broken)["tokens"]["output"] == 30
    path.unlink()
    cache = EstimateCache(path)
    other = sqlite3.connect(path)
    other.execute("BEGIN EXCLUSIVE")
    try:
        assert calculator.ai_cost("+a", cache=cache)["tokens"]["output"] == 30
    finally:
        other.rollback()
        other.close()
        cache.close()


def test_cache_ttl_row_limit_and_invalid_entries(tmp_path, monkeypatch):
    from src.costs import cache as module

    monkeypatch.setattr(module, "MAX_ENTRIES", 2)
    cache = EstimateCache(tmp_path / "cache.sqlite3")
    for text in ("+one", "+two", "+three"):
        calculator.ai_cost(text, cache=cache)
    assert cache.connection.execute("SELECT count(*) FROM estimates").fetchone()[0] == 2
    key = estimate_key("+three", "claude-3.5-sonnet", "cl100k_base")
    cache.connection.execute("UPDATE estimates SET created = 0")
    cache.connection.commit()
    assert cache.get(key) is None
    cache.connection.execute(
        "UPDATE estimates SET created = ?, value = ?",
        (module.time.time(), '{"tokens": false}'),
    )
    cache.connection.commit()
    assert cache.get(key) is None
    cache.close()


def test_unknown_prices_fail_and_catalog_exposes_source_and_date():
    with pytest.raises(pricing.UnknownModelPrice, match="No price"):
        get_model_price("openrouter/does-not-exist/model")
    info = get_model_price_info("openai/gpt-4o")
    assert info["source"] == pricing.CATALOG_URL
    assert info["retrieved_at"]
    assert info["rates"] == {"input": 2.5e-6, "output": 10e-6}
    assert get_model_price_info("claude-3.5-sonnet")["status"] == "unverified"


def test_long_context_price_tiers():
    assert get_model_price("openrouter/deep/deep-v4-pro") == get_model_price(
        "deepseek/deepseek-v4-pro"
    )
    assert get_model_price("anthropic/claude-sonnet-4", 199_999)["input"] == 3e-6
    assert get_model_price("anthropic/claude-sonnet-4", 200_000)["input"] == 6e-6


def test_refresh_validates_before_replacing_catalog(tmp_path, monkeypatch):
    destination = tmp_path / "prices.json"
    destination.write_text("previous catalog")
    item = {
        "id": "example/model",
        "architecture": {"output_modalities": ["text"]},
        "pricing": {"prompt": "NaN", "completion": "1"},
    }

    class Response:
        def raise_for_status(self):
            pass

        def iter_bytes(self):
            yield json.dumps({"data": [item]}).encode()

    @contextmanager
    def stream(*args, **kwargs):
        yield Response()

    monkeypatch.setattr(pricing.httpx, "stream", stream)
    with pytest.raises(ValueError, match="finite"):
        pricing.refresh_catalog(destination)
    assert destination.read_text() == "previous catalog"
    item["pricing"]["prompt"] = "0.001"
    pricing.refresh_catalog(destination)
    assert (
        pricing.load_catalog(destination)["models"]["example/model"]["input"] == 0.001
    )
