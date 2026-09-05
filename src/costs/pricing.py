"""Versioned, locally readable reference prices from OpenRouter's public catalog."""

import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

CATALOG_URL = "https://openrouter.ai/api/v1/models"
BUNDLED_CATALOG = Path(__file__).with_name("data") / "prices.json"


class UnknownModelPrice(ValueError):
    """A model has no explicit price; estimating it would invent a rate."""


def catalog_path():
    override = os.getenv("COSTS_PRICES_FILE")
    if override:
        return Path(override)
    cached = (
        Path(os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache")))
        / "costs"
        / "prices.json"
    )
    return cached if cached.is_file() else BUNDLED_CATALOG


def validate_catalog(data):
    if data.get("schema") != "costs.prices/v1" or data.get("currency") != "USD":
        raise ValueError("Unsupported price catalog schema or currency")
    datetime.fromisoformat(data["retrieved_at"])
    if not isinstance(data.get("source"), str) or not data["source"]:
        raise ValueError("A price catalog must identify its source")
    if not isinstance(data.get("models"), dict) or not data["models"]:
        raise ValueError("Price catalog has no models")
    for name, entry in data["models"].items():
        if not isinstance(name, str) or not name:
            raise ValueError("Invalid model identifier")
        for rate in [entry, *entry.get("tiers", [])]:
            for key in ("input", "output"):
                value = rate[key]
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or value < 0
                ):
                    raise ValueError("Prices must be finite non-negative numbers")
            if "min_prompt_tokens" in rate and (
                type(rate["min_prompt_tokens"]) is not int
                or rate["min_prompt_tokens"] < 0
            ):
                raise ValueError("Invalid pricing tier threshold")
    return data


def load_catalog(path=None):
    path = Path(path) if path else catalog_path()
    if path.stat().st_size > 4_000_000:
        raise ValueError("Price catalog exceeds 4 MB")
    return validate_catalog(json.loads(path.read_text(encoding="utf-8")))


def refresh_catalog(destination=None):
    """Explicit network refresh, atomically published only after validation."""
    with httpx.stream("GET", CATALOG_URL, timeout=20.0) as response:
        response.raise_for_status()
        chunks = []
        size = 0
        for chunk in response.iter_bytes():
            size += len(chunk)
            if size > 4_000_000:
                raise ValueError("Provider catalog exceeds 4 MB")
            chunks.append(chunk)
    models = {}
    for item in json.loads(b"".join(chunks))["data"]:
        if "text" not in item.get("architecture", {}).get("output_modalities", []):
            continue
        price = item["pricing"]
        if "prompt" not in price or "completion" not in price:
            continue
        entry = {"input": float(price["prompt"]), "output": float(price["completion"])}
        # Routing endpoints use -1 to indicate that no fixed token price exists.
        if entry["input"] == -1 or entry["output"] == -1:
            continue
        tiers = [
            {
                "min_prompt_tokens": t["min_prompt_tokens"],
                "input": float(t["prompt"]),
                "output": float(t["completion"]),
            }
            for t in price.get("overrides", [])
            if all(k in t for k in ("min_prompt_tokens", "prompt", "completion"))
        ]
        if tiers:
            entry["tiers"] = tiers
        models[item["id"]] = entry
    data = validate_catalog(
        {
            "schema": "costs.prices/v1",
            "currency": "USD",
            "source": CATALOG_URL,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "models": models,
        }
    )
    path = (
        Path(destination)
        if destination
        else Path(os.getenv("XDG_CACHE_HOME", str(Path.home() / ".cache")))
        / "costs"
        / "prices.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", dir=path.parent, delete=False, encoding="utf-8"
        ) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, indent=2, allow_nan=False, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path, data
