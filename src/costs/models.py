"""Model pricing definitions with liteLLM integration."""

import os
from typing import Dict
from dotenv import load_dotenv
from .pricing import load_catalog, UnknownModelPrice

# Load environment variables from .env file

if __name__ == "__main__":
    load_dotenv()

# Default configuration from .env
DEFAULT_OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "openrouter/qwen/qwen3-coder-next")

# Model pricing ($/token) - includes liteLLM supported providers
PRICES: Dict[str, Dict[str, float]] = {
    # Anthropic
    "claude-4-sonnet": {"input": 3e-6, "output": 15e-6},
    "anthropic/claude-4-sonnet": {"input": 3e-6, "output": 15e-6},
    "claude-3.5-sonnet": {"input": 3e-6, "output": 15e-6},
    "claude-3.5-haiku": {"input": 0.8e-6, "output": 4e-6},
    "claude-3-opus": {"input": 15e-6, "output": 75e-6},
    "anthropic/claude-3.5-sonnet": {"input": 3e-6, "output": 15e-6},
    "anthropic/claude-3.5-haiku": {"input": 0.8e-6, "output": 4e-6},
    # OpenAI
    "gpt-4o": {"input": 5e-6, "output": 15e-6},
    "gpt-5.4-mini": {"input": 0.15e-6, "output": 0.6e-6},
    "gpt-4": {"input": 30e-6, "output": 60e-6},
    "openai/gpt-4o": {"input": 5e-6, "output": 15e-6},
    "openai/gpt-5.4-mini": {"input": 0.15e-6, "output": 0.6e-6},
    # OpenRouter / Qwen
    "openrouter/qwen/qwen3-coder-next": {"input": 0.5e-6, "output": 1.5e-6},
    "openrouter/qwen/qwen3-coder": {"input": 0.5e-6, "output": 1.5e-6},
    "openrouter/qwen/qwen2.5-coder": {"input": 0.3e-6, "output": 1.0e-6},
    # Ollama / Local
    "ollama": {"input": 1e-7, "output": 1e-7},
    "local": {"input": 1e-7, "output": 1e-7},
    "ollama/*": {"input": 1e-7, "output": 1e-7},
}


# Keep explicitly registered legacy rates compatible, but identify them as
# unverified. Current catalog entries override them when the model still exists.
_PRICE_METADATA = {
    name: {
        "source": "legacy bundled estimate",
        "retrieved_at": None,
        "status": "unverified",
        "rates": dict(rates),
    }
    for name, rates in PRICES.items()
}
_catalog = load_catalog()
for _name, _entry in _catalog["models"].items():
    PRICES[_name] = {"input": _entry["input"], "output": _entry["output"]}
    _PRICE_METADATA[_name] = {
        "source": _catalog["source"],
        "retrieved_at": _catalog["retrieved_at"],
        "status": "catalog",
        "rates": dict(PRICES[_name]),
        "tiers": _entry.get("tiers", []),
    }
_ALIASES = {
    # Compatibility for the misspelling previously shipped in tool.costs config.
    "openrouter/deep/deep-v4-pro": "deepseek/deepseek-v4-pro",
    "claude-4-sonnet": "anthropic/claude-sonnet-4",
    "anthropic/claude-4-sonnet": "anthropic/claude-sonnet-4",
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
    "claude-3.5-haiku": "anthropic/claude-3.5-haiku",
    "claude-3-opus": "anthropic/claude-3-opus",
    "gpt-4o": "openai/gpt-4o",
    "gpt-4": "openai/gpt-4",
    "gpt-5.4-mini": "openai/gpt-5.4-mini",
}
_ALIASES.update({"openrouter/" + name: name for name in _catalog["models"]})
for _alias, _canonical in _ALIASES.items():
    if _canonical in PRICES:
        PRICES[_alias] = PRICES[_canonical]
        _PRICE_METADATA[_alias] = _PRICE_METADATA[_canonical]


def get_model_price_info(model: str, input_tokens: int = 0) -> dict:
    """Resolve explicit prices and their provenance, including context tiers."""
    name = model if model in PRICES else model.removeprefix("openrouter/")
    if name not in PRICES and name.startswith("ollama/"):
        name = "ollama/*"
    if name not in PRICES and "openai/" + name in PRICES:
        name = "openai/" + name
    if name not in PRICES:
        raise UnknownModelPrice(
            f"No price for model {model!r}. Run 'costs prices --refresh' or register explicit rates in costs.models.PRICES."
        )
    rates = dict(PRICES[name])
    metadata = _PRICE_METADATA.get(name, {})
    if rates != metadata.get("rates"):
        return {
            "rates": rates,
            "source": "custom registration",
            "retrieved_at": None,
            "status": "custom",
            "currency": "USD",
            "scope": "text_tokens",
        }
    for tier in sorted(
        metadata.get("tiers", []), key=lambda value: value["min_prompt_tokens"]
    ):
        if input_tokens >= tier["min_prompt_tokens"]:
            rates = {"input": tier["input"], "output": tier["output"]}
    return {
        "rates": rates,
        "source": metadata["source"],
        "retrieved_at": metadata["retrieved_at"],
        "status": metadata["status"],
        "currency": "USD",
        "scope": "text_tokens",
    }


def get_model_price(model: str, input_tokens: int = 0) -> Dict[str, float]:
    """Get USD-per-token prices. Unknown models never inherit a guessed rate."""
    return get_model_price_info(model, input_tokens)["rates"]


def get_openrouter_headers() -> Dict[str, str]:
    """Get headers for OpenRouter API calls."""
    return {
        "Authorization": f"Bearer {DEFAULT_OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://github.com/your-org/ai-cost-tracker",
        "X-OpenRouter-Title": os.getenv("OPENROUTER_APP_NAME", "AI Cost Tracker"),
    }


def get_litellm_model_name(model: str) -> str:
    """Convert model name to liteLLM format."""
    # If model is already in liteLLM format, return as-is
    if "/" in model:
        return model
    # Default to openrouter if no provider specified
    return f"openrouter/{model}"
