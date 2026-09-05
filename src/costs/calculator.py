"""Core cost calculation logic."""

from typing import Dict, Optional, Any, List, Tuple
import httpx
from .models import get_model_price, get_model_price_info
from .cache import EstimateCache, estimate_key
from .tokenizers import get_tokenizer, GitDiffParser
from decimal import Decimal
from math import fsum, isfinite
import warnings

OUTPUT_TOKENS_PER_ADDED_LINE = 30
OUTPUT_INPUT_RATIO = 0.25

# Share the public tokenizer; it caches encoding metadata, not commit content.
_tokenizer = get_tokenizer()


# Advanced metrics configuration
DEFAULT_HOURLY_RATE = 100.0  # USD/h
HUMAN_REVIEW_OVERHEAD = 0.2  # 20% of AI-saved time is spent on review
LOC_PER_HOUR = 100  # Human productivity baseline

# File type impact multipliers for token estimation
# Logic-heavy languages have a higher weight than boilerplate/docs
FILE_TYPE_MULTIPLIERS = {
    ".py": 1.8,
    ".js": 1.8,
    ".ts": 1.8,
    ".cpp": 1.8,
    ".go": 1.8,
    ".rs": 1.8,
    ".php": 1.8,
    ".md": 0.5,
    ".json": 0.4,
    ".yaml": 0.6,
    ".html": 0.8,
    ".css": 0.9,
}


def get_file_type_multiplier(filename: str) -> float:
    """Get multiplier based on file extension."""
    for ext, mult in FILE_TYPE_MULTIPLIERS.items():
        if filename.endswith(ext):
            return mult
    return 1.0


def estimate_tokens(diff: str, model: Optional[str] = None) -> Dict[str, int]:
    """
    Estimate tokens using proper tokenization.

    Args:
        diff: Git diff content
        model: Model name for accurate token counting

    Returns:
        Dict with input, output, and total token counts
    """
    return _estimate_tokens(diff, model, GitDiffParser.parse_diff_stats(diff))


def _estimate_tokens(
    diff: str, model: Optional[str], diff_stats: Dict[str, int]
) -> Dict[str, int]:
    """Estimate from already parsed statistics to avoid scanning each diff twice."""
    if not diff:
        return {"input": 0, "output": 0, "total": 0}

    # Create realistic prompt that would be sent to LLM
    prompt = f"Review this code change:\n```diff\n{diff}\n```"

    # Count input tokens accurately
    input_tokens = _tokenizer.count_tokens(prompt, model)

    # Estimate output tokens based on actual added lines
    # Configured heuristic: code review output ~30 tokens per added line
    # Minimum fallback: 25% of input for simple reviews
    added_lines = diff_stats["added_lines"]
    output_from_lines = added_lines * OUTPUT_TOKENS_PER_ADDED_LINE
    output_from_ratio = int(input_tokens * OUTPUT_INPUT_RATIO)

    output_tokens = max(output_from_lines, output_from_ratio, 1)

    return {
        "input": input_tokens,
        "output": output_tokens,
        "total": input_tokens + output_tokens,
    }


# Legacy function for backward compatibility
def _estimate_single_file_tokens(
    diff: str, filename: Optional[str] = None
) -> Dict[str, int]:
    """Legacy heuristic - kept for backward compatibility."""
    return estimate_tokens(diff)


def calculate_cost(tokens: Dict[str, int], model: str) -> float:
    """Calculate cost from tokens using model prices."""
    for key in ("input", "output"):
        if type(tokens[key]) is not int or tokens[key] < 0:
            raise ValueError(f"{key} tokens must be a non-negative integer")
    price = get_model_price(model, tokens["input"])
    if any(not isfinite(price[k]) or price[k] < 0 for k in ("input", "output")):
        raise ValueError("Token prices must be finite and non-negative")
    return float(
        sum(Decimal(tokens[k]) * Decimal(str(price[k])) for k in ("input", "output"))
    )


def calculate_roi(
    cost: float,
    lines_changed: int,
    hourly_rate: float = DEFAULT_HOURLY_RATE,
    review_factor: float = HUMAN_REVIEW_OVERHEAD,
) -> Dict[str, Any]:
    """Calculate ROI metrics with human review overhead."""
    # Gross time saved by AI
    hours_saved_gross = lines_changed / LOC_PER_HOUR

    # Net time saved (Subtract review overhead)
    review_time = hours_saved_gross * review_factor
    hours_saved_net = max(hours_saved_gross - review_time, 0.0)

    # Financial metrics
    value_generated = hours_saved_net * hourly_rate
    roi = (
        value_generated / cost
        if cost > 0
        else (float("inf") if value_generated else 0.0)
    )

    return {
        "hours_saved": round(hours_saved_net, 2),
        "review_time": round(review_time, 2),
        "value_generated": round(value_generated, 2),
        "roi": round(roi, 1),
        "roi_formatted": f"{roi:.0f}x" if isfinite(roi) else "∞",
    }


def ai_cost(
    commit_diff: str,
    model: str = "claude-3.5-sonnet",
    api_key: Optional[str] = None,
    saas_token: Optional[str] = None,
    saas_url: str = "https://your-saas.com/api/cost",
    *,
    cache: Optional[EstimateCache] = None,
) -> Dict[str, Any]:
    """Calculate AI cost for a commit with proper tokenization."""
    estimation = _tokenizer.describe(model)
    key = (
        estimate_key(commit_diff, model, estimation["tokenizer"])
        if cache is not None and cache.connection is not None
        else None
    )
    cached = cache.get(key) if cache is not None else None
    if cached is None:
        diff_stats = GitDiffParser.parse_diff_stats(commit_diff)
        tokens = _estimate_tokens(commit_diff, model, diff_stats)
        if cache is not None:
            cache.put(key, {"tokens": tokens, "diff_stats": diff_stats})
    else:
        diff_stats, tokens = cached["diff_stats"], cached["tokens"]
    lines_changed = diff_stats["total_changed"]

    # SaaS Mode
    if saas_token:
        try:
            resp = httpx.post(
                saas_url,
                json={"tokens": tokens, "model": model},
                headers={"Authorization": f"Bearer {saas_token}"},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            cost = data["cost"]
            if (
                isinstance(cost, bool)
                or not isinstance(cost, (int, float))
                or not isfinite(cost)
                or cost < 0
            ):
                raise ValueError("SaaS cost must be a finite non-negative number")
            return {
                "cost": cost,
                "cost_formatted": f"${cost:.4f}",
                "model": model,
                "mode": "saas",
                "tokens": tokens,
                "diff_stats": diff_stats,
                "estimation": estimation,
                **calculate_roi(cost, lines_changed),
            }
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            warnings.warn(
                "SaaS calculation failed; using local pricing estimate",
                RuntimeWarning,
                stacklevel=2,
            )

    # Local/BYOK Mode
    cost = calculate_cost(tokens, model)
    mode = "byok" if api_key else "local"

    return {
        "cost": cost,
        "cost_formatted": f"${cost:.4f}",
        "model": model,
        "mode": mode,
        "pricing": get_model_price_info(model, tokens["input"]),
        "tokens": tokens,
        "diff_stats": diff_stats,
        "estimation": estimation,
        **calculate_roi(cost, lines_changed),
    }


def batch_calculate_costs(
    commits_data: List[Tuple[Any, str]],
    model: str = "claude-3.5-sonnet",
    api_key: Optional[str] = None,
    saas_token: Optional[str] = None,
    saas_url: str = "https://your-saas.com/api/cost",
) -> Dict[str, Any]:
    """Calculate costs for multiple commits."""
    results = []

    cache = EstimateCache()
    try:
        for commit, diff in commits_data:
            cost_info = ai_cost(
                diff,
                model,
                api_key=api_key,
                saas_token=saas_token,
                saas_url=saas_url,
                cache=cache,
            )
            cost_info["commit_hash"] = commit.hexsha[:8]
            cost_info["commit_message"] = commit.message.strip()
            cost_info["author"] = commit.author.name
            cost_info["date"] = commit.committed_datetime.isoformat()
            results.append(cost_info)
    finally:
        cache.close()

    total_cost = fsum(result["cost"] for result in results)
    total_hours_saved = fsum(
        result["diff_stats"]["total_changed"]
        / LOC_PER_HOUR
        * (1 - HUMAN_REVIEW_OVERHEAD)
        for result in results
    )
    total_value = total_hours_saved * DEFAULT_HOURLY_RATE
    avg_roi = (
        total_value / total_cost
        if total_cost > 0
        else (float("inf") if total_value else 0.0)
    )

    return {
        "commits": results,
        "summary": {
            "total_commits": len(results),
            "cache_hits": cache.hits,
            "cache_misses": cache.misses,
            "total_cost": round(total_cost, 4),
            "total_cost_formatted": f"${total_cost:.4f}",
            "total_hours_saved": round(total_hours_saved, 2),
            "total_value_generated": round(total_value, 2),
            "average_roi": f"{avg_roi:.0f}x" if isfinite(avg_roi) else "∞",
            "model": model,
            "mode": results[0]["mode"] if results else "unknown",
        },
    }
