"""Regression checks for patch correctness, token estimates and aggregation."""

from datetime import datetime, timezone
from types import SimpleNamespace

import httpx
import pytest
import tiktoken

from src.costs import calculator
from src.costs.models import PRICES, get_model_price
from src.costs.tokenizers import GitDiffParser, Tokenizer


@pytest.mark.parametrize(
    "diff,added,deleted",
    [
        ("", 0, 0),
        ("+one\n-two\n", 1, 1),
        (
            "--- a/a\n+++ b/a\n@@ -1,2 +1,2 @@\n--- decrement\n+++ increment\n same\n",
            1,
            1,
        ),
        ("--- /dev/null\n+++ b/a\n@@ -0,0 +1 @@\n+++ literal\n", 1, 0),
        ("--- a/a\n+++ /dev/null\n@@ -1 +0,0 @@\n--- literal\n", 0, 1),
        ("diff --git a/a b/a\nBinary files a/a and b/a differ\n", 0, 0),
        ("@@ -0,0 +1 @@\n+one\u2028+still the same Git line\n", 1, 0),
        (
            "@@ -1 +1 @@\n-old\n+new\n\\ No newline at end of file\n"
            "--- a/b\n+++ b/b\n@@ -0,0 +1 @@\n+next\n",
            2,
            1,
        ),
    ],
)
def test_diff_stats(diff, added, deleted):
    assert GitDiffParser.parse_diff_stats(diff) == {
        "added_lines": added,
        "deleted_lines": deleted,
        "total_changed": added + deleted,
    }


@pytest.mark.parametrize(
    "model,encoding",
    [
        ("gpt-4", "cl100k_base"),
        ("gpt-4o", "o200k_base"),
        ("openai/gpt-4o", "o200k_base"),
        ("openrouter/openai/gpt-4o", "o200k_base"),
        ("claude-3.5-sonnet", "cl100k_base"),
        ("openrouter/qwen/qwen3-coder-next", "cl100k_base"),
    ],
)
def test_model_encoding_and_literal_special_tokens(model, encoding):
    text = "Zażółć gęślą jaźń 日本語 <|endoftext|> <|fim_prefix|>"
    tokenizer = Tokenizer()
    assert tokenizer.count_tokens(text, model) == len(
        tiktoken.get_encoding(encoding).encode_ordinary(text)
    )
    assert tokenizer.count_tokens("", model) == 0
    assert tokenizer.describe(model)["tokenizer"] == encoding


def test_estimation_is_local_and_labels_approximations(monkeypatch):
    import anthropic

    def forbidden(*args, **kwargs):
        pytest.fail("Local estimation must not create provider clients or call APIs")

    monkeypatch.setattr(anthropic, "Anthropic", forbidden)
    monkeypatch.setattr(httpx, "post", forbidden)
    result = calculator.ai_cost("+hello", api_key="unused")
    assert result["estimation"] == {
        "tokenizer": "cl100k_base",
        "input_tokens": "approximate",
        "output_tokens": "heuristic",
    }
    assert result["mode"] == "byok"


def test_empty_and_small_costs_have_no_artificial_floor():
    result = calculator.ai_cost("")
    assert result["cost"] == result["roi"] == 0
    assert result["tokens"] == {"input": 0, "output": 0, "total": 0}
    assert (
        calculator.calculate_cost({"input": 1, "output": 0}, "claude-3.5-sonnet")
        == 0.000003
    )
    assert (
        calculator.calculate_cost({"input": 100, "output": 20}, "claude-3.5-sonnet")
        == 0.0006
    )


@pytest.mark.parametrize("invalid", [-1, 1.5, True, float("nan"), float("inf")])
def test_invalid_token_counts_are_rejected(invalid):
    with pytest.raises(ValueError):
        calculator.calculate_cost({"input": invalid, "output": 0}, "local")


@pytest.mark.parametrize("invalid", [-1, float("nan"), float("inf")])
def test_invalid_prices_are_rejected(monkeypatch, invalid):
    monkeypatch.setitem(PRICES, "custom", {"input": invalid, "output": 0})
    with pytest.raises(ValueError):
        calculator.calculate_cost({"input": 1, "output": 0}, "custom")


def test_known_routed_prices_and_custom_overrides(monkeypatch):
    for model in ("claude-3.5-sonnet", "anthropic/claude-3.5-sonnet", "openai/gpt-4o"):
        assert get_model_price("openrouter/" + model) == get_model_price(model)
    custom = {"input": 0.0, "output": 0.0}
    monkeypatch.setitem(PRICES, "openrouter/openai/gpt-4o", custom)
    assert get_model_price("openrouter/openai/gpt-4o") == custom


def test_batch_rounds_once_and_parses_each_diff_once(monkeypatch):
    commit = SimpleNamespace(
        hexsha="a" * 40,
        message="test",
        author=SimpleNamespace(name="Test"),
        committed_datetime=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    original = GitDiffParser.parse_diff_stats
    calls = []

    def record(diff):
        calls.append(diff)
        return original(diff)

    monkeypatch.setattr(GitDiffParser, "parse_diff_stats", record)
    result = calculator.batch_calculate_costs([(commit, "+line\n")] * 10)
    assert len(calls) == 1
    assert result["summary"]["cache_hits"] == 9
    assert result["summary"]["total_hours_saved"] == 0.08
    assert result["summary"]["total_value_generated"] == 8.0
    assert calculator.calculate_roi(0.001, 100)["roi_formatted"] == "80000x"


@pytest.mark.parametrize(
    "payload", [{}, {"cost": -1}, {"cost": "1"}, {"cost": True}, {"cost": float("nan")}]
)
def test_invalid_saas_response_warns_and_falls_back(monkeypatch, payload):
    response = SimpleNamespace(raise_for_status=lambda: None, json=lambda: payload)
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: response)
    with pytest.warns(RuntimeWarning, match="using local pricing"):
        result = calculator.ai_cost("+hello", saas_token="test")
    assert result["mode"] == "local"
    assert result["cost"] > 0


def test_custom_saas_url_and_zero_cost(monkeypatch):
    requests = []

    def post(url, **kwargs):
        requests.append(url)
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"cost": 0})

    monkeypatch.setattr(httpx, "post", post)
    commit = SimpleNamespace(
        hexsha="a" * 40,
        message="test",
        author=SimpleNamespace(name="Test"),
        committed_datetime=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    result = calculator.batch_calculate_costs(
        [(commit, "+hello")], saas_token="test", saas_url="https://example.invalid/cost"
    )
    assert requests == ["https://example.invalid/cost"]
    assert result["commits"][0]["mode"] == "saas"
    assert result["summary"]["total_cost"] == 0
