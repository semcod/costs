## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.2.0-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$2.51-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-19.4h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fdeepseek%2Fdeepseek--v4--pro-lightgrey)

- 🤖 **LLM usage:** $2.5070 (62 commits)
- 👤 **Human dev:** ~$1938 (19.4h @ $100/h, 30min dedup)

Generated on 2026-09-05 using [openrouter/deepseek/deepseek-v4-pro](https://openrouter.ai/deepseek/deepseek-v4-pro)

---

Track AI usage costs across your git commits with three flexible usage modes - no initial configuration required.

## Features

- **liteLLM Integration** - Support for 100+ AI providers via liteLLM
- **Default: Qwen3 Coder Next** - Pre-configured with openrouter/qwen/qwen3-coder-next
- **Zero Config** - Works out of the box, reads from `.env` file
- **Local Token Estimation** - Model-specific tiktoken encodings with explicit approximations for other providers
- **ROI Calculation** - Track value generated vs AI costs
- **Date Filtering** - Analyze specific days, date ranges, or full history
- **Auto Badges** - Automatically generate and update cost badges in README
- **Rich Reports** - Markdown and HTML reports with visualizations
- **All Commits Support** - Analyze all commits with `--all` flag (not just AI-tagged)

## Tokenization

The calculator estimates the cost of reviewing a Git diff. It does not reconstruct
actual API usage from commits. Input text uses the encoding selected by tiktoken
for supported models; other families use a local approximation.

| Model | Tokenizer | Interpretation |
|-------|-----------|----------------|
| Supported OpenAI models | Model-specific tiktoken encoding | Token count for the review prompt text |
| Anthropic Claude | cl100k_base fallback | Approximate; no Anthropic API call |
| Other / unknown models | cl100k_base fallback | Approximate |

Output tokens remain a heuristic: the greater of 30 tokens per added line,
25% of input tokens (rounded down), or one token. An empty diff has zero tokens
and zero cost. Prices come from a dated snapshot of OpenRouter's public catalog, bundled in
`src/costs/data/prices.json`. They are reference USD-per-token rates, not invoices.
Unknown models raise `UnknownModelPrice` instead of inheriting a guessed price.
Legacy rates for retired models are explicitly marked `unverified`. The `pricing`,
`estimation` and `diff_stats` fields expose the source, date and method used.
Known provider-prefixed aliases resolve to the same rate, including the old
`openrouter/deep/deep-v4-pro` spelling of `deepseek/deepseek-v4-pro`.

```bash
costs prices                 # Show source and retrieval date
costs prices --refresh       # Explicitly refresh the local catalog
```

New processes use the refreshed catalog. `COSTS_PRICES_FILE` selects a custom
catalog in the same validated format. The calculator includes published long
context input/output tiers. Tool calls, cached provider input, image/audio
charges and provider-specific routing fees are outside this text-token estimate.

Batch analysis caches token counts and diff statistics in a local SQLite database.
The cache key includes the diff content hash, model, encoding, tiktoken version
and estimator revision. Prices and ROI are recalculated on every run. Records
expire after 30 days and the cache holds at most 10,000 entries. No source code
or API keys are stored. Corrupt, locked or unavailable caches fall back to fresh
calculation. Set `COSTS_CACHE=0` to disable or `COSTS_CACHE_DIR` to change its location
(default: `$XDG_CACHE_HOME/costs`, otherwise `~/.cache/costs`). Summaries expose
`cache_hits` and `cache_misses`. Git patch extraction still runs to verify inputs.

History analysis reads patches in groups of at most 16 commits, compares merges
with their first parent, and includes initial commits. Token counts include file
headers. Tiny costs have no artificial minimum; batch time/value totals are
rounded only after aggregation. These corrections can change previous reports.

See [performance evidence and Wellmanifest adoption](docs/performance/README.md)
for the benchmark, compatibility notes, pinned standard and validation commands.

See the [documentation index](docs/README.md) and [dependency rollout reports](docs/dependencies/README.md) for published updates and consumer verification.

### Token Counting Examples

```python
from costs.tokenizers import count_tokens, Tokenizer

# Count tokens for any model
text = "def hello(): print('world')"
tokens = count_tokens(text, "claude-3.5-sonnet")  # local approximation
tokens = count_tokens(text, "gpt-4o")             # model-specific encoding

# Use tokenizer directly
tokenizer = Tokenizer()
input_tokens = tokenizer.count_tokens(prompt, model)
```

## Installation

```bash
pip install costs
```

# Edit .env file to add your OpenRouter API key
echo "OPENROUTER_API_KEY=YOUR_KEY" >> .env
```

# Uses defaults from .env (Qwen3 Coder Next)
costs analyze .

# Or specify directly
costs analyze . --model openrouter/qwen/qwen3-coder-next --api-key YOUR_KEY

# Analyze all commits (not just AI-tagged)
costs analyze . --all
```

## Configuration

Create a `.env` file in your project root:

```bash
# Required: OpenRouter API key (https://openrouter.ai/keys)
OPENROUTER_API_KEY=YOUR_KEY
LLM_MODEL=openrouter/qwen/qwen3-coder-next
```

Or use the built-in init command:

```bash
costs init
```

### Option 1: BYOK (Bring Your Own Key) - Free

The BYOK label records that an API key was supplied. This estimator calculates
costs locally from bundled rates; it does not send a completion request.

```bash
# With OpenRouter key (default from .env)
costs analyze .

# Explicit key
costs analyze . --api-key YOUR_KEY
```

**Supported models via liteLLM:**
- `openrouter/qwen/qwen3-coder-next` (default)
- `anthropic/claude-4-sonnet`
- `anthropic/claude-3.5-sonnet`
- `anthropic/claude-3.5-haiku`
- `openai/gpt-4o`
- `openai/gpt-5.4-mini`
- 100+ more via liteLLM

### Option 2: Local/Ollama - Local Estimates

No API key is needed. Estimates use tokenized diffs and bundled reference rates.

```bash
costs analyze . --mode local
```

**Cost formula:** `input_tokens * input_price + output_tokens * output_price`
(prices in USD per token). Local/Ollama reference rates are estimates, not API charges.

## Date Filtering

Analyze commits for specific time periods:

```bash
# Analyze specific day
costs analyze . --date 2024-03-15

# Analyze date range
costs analyze . --since 2024-01-01 --until 2024-03-31

# Analyze all commits since repository creation
costs analyze . --full-history

# Analyze only AI-tagged commits (default)
costs analyze . --ai-only

# Analyze all commits (not just AI-tagged)
costs analyze . --all
```

## Badge Generation

Generate and update cost badges in your README:

```bash
# Generate badge based on pyproject.toml configuration (AI commits only)
costs auto-badge --repo .

# Generate badge for all commits (not just AI-tagged)
costs auto-badge --repo . --all

# Manual badge generation
costs badge . --model openrouter/qwen/qwen3-coder-next

# Manual badge for all commits
costs badge . --all
```

This adds a badge section to README showing total cost, AI commits, and model used.

# Generate markdown report with charts
costs report . --format markdown

# Generate HTML report
costs report . --format html

# Generate both and update README
costs report . --format both --update-readme
```

## Python API

Use the calculator directly in your code:

```python
from costs.calculator import ai_cost, estimate_tokens, calculate_cost

# Calculate complete cost with ROI
result = ai_cost(commit_diff, model="claude-3.5-sonnet")
print(f"Cost: {result['cost_formatted']}")
print(f"Tokens: {result['tokens']['total']}")
print(f"ROI: {result['roi_formatted']}")

# Estimate tokens only
tokens = estimate_tokens(diff, model="gpt-4o")
print(f"Input: {tokens['input']}, Output: {tokens['output']}")

# Calculate cost from tokens
cost = calculate_cost(tokens, "openrouter/qwen/qwen3-coder-next")
```

See `examples/` directory for more usage patterns.

## How It Works

1. **Parse git history** - Analyzes commits with optional `[ai:model]` tags
2. **Estimate tokens** - Uses model-specific tiktoken encodings where supported and an explicit local approximation for Claude and other models
3. **Calculate cost** - Multiplies tokens × model price
4. **Generate ROI** - Estimates time saved (100 LOC/h × $100/h)

By default, only commits with `[ai:]` tags are analyzed. Use `--all` to analyze all commits.

## Why liteLLM?

- **Universal API** - Jedna składnia dla 100+ providerów
- **Automatic routing** - Fallback między providerami
- **Cost tracking** - Wbudowane liczenie tokenów
- **OpenRouter** - Dostęp do najnowszych modeli bez kont premium

### Option 3: SaaS Subscription - Managed

Enterprise managed solution with dashboard and invoicing.

```bash
costs --repo . --saas-token PLACEHOLDER
```

# Analyze last 50 commits (uses .env defaults)
costs analyze . -n 50

# Use specific model via liteLLM
costs analyze . --model anthropic/claude-3.5-sonnet

# Analyze all commits (not just AI-tagged)
costs analyze . --all

# Analyze with date filtering
costs analyze . --since 2024-01-01 --until 2024-03-31

# Export to custom file
costs analyze . --output my_costs.csv

# Show repository statistics
costs stats .

# Generate reports
costs report . --format both --update-readme

# Generate badge for all commits
costs badge . --all

# Auto-badge with pyproject.toml config
costs auto-badge --repo . --all

# Estimate single diff
costs estimate my_changes.patch

# Read diff from stdin
git diff HEAD~1 | costs estimate -
```

## Tagging AI Commits

Tag commits with `[ai:model]` for automatic tracking:

```bash
git commit -m "[ai:openrouter/qwen/qwen3-coder-next] Refactor authentication"
git commit -m "[ai:anthropic/claude-3.5-sonnet] Add payment integration"
```

## Sample Output

```
🔍 Analyzing 100 commits from my-project...
🤖 Model: openrouter/qwen/qwen3-coder-next | Mode: byok

==================================================
📊 AI COST ANALYSIS - openrouter/qwen/qwen3-coder-next
==================================================
   Commits analyzed: 42
   Total cost:       $12.34
   Hours saved:      15.3h
   Value generated:  $1530.00
   ROI:              124x
==================================================
📁 Results saved to: ai_costs.csv

💡 Recent AI commits:
   a1b2c3d4 | $0.32 | [ai:qwen3-coder-next] Refactor...
   e5f6g7h8 | $0.45 | [ai:qwen3-coder-next] Add feature...
```

## CSV Export Format

| Column | Description |
|--------|-------------|
| `commit_hash` | Short commit SHA |
| `commit_message` | Full commit message |
| `author` | Commit author name |
| `date` | ISO format datetime |
| `cost` | Calculated cost in USD |
| `cost_formatted` | Formatted cost string |
| `model` | AI model used |
| `mode` | Calculation mode (byok/local/saas) |
| `tokens_input` | Estimated input tokens |
| `tokens_output` | Estimated output tokens |
| `hours_saved` | Estimated hours saved |
| `roi` | ROI multiplier |

## Pricing Reference

Run `costs prices` to inspect the active catalog provenance. The bundled snapshot
was retrieved from [OpenRouter's public models API](https://openrouter.ai/api/v1/models)
on 2026-09-05. Refresh explicitly with `costs prices --refresh`; normal calculation
never fetches prices automatically. Applications can still register an explicit
custom rate in `costs.models.PRICES`.

## Business Model

| Tier | Price | Features |
|------|-------|----------|
| **BYOK** | Free | Use your own OpenRouter API key |
| **SaaS** | $9/month | Unlimited, managed keys, dashboard, EU invoicing |

# Run CLI
poetry run costs analyze ..

# Publish to PyPI
poetry publish --build
```

## PHP Badge Service

Standalone PHP service for generating badges:

```bash
cd services/badge-service
composer install
php -S localhost:8080
```

Generate badges via API:
```bash
curl "http://localhost:8080/badge.php?cost=12.34&model=claude-4&commits=42"
```

## Automatic Cost Calculation

The tool can automatically calculate costs and update badges on every commit and during test runs.

### Pre-commit Hook

Install the pre-commit hook to automatically update the badge before each commit:

```bash
# Copy hook to git hooks
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Or use project.sh (includes hook installation)
bash project.sh
```

The hook will:
1. Detect `costs` in global PATH or virtualenv
2. Run `costs auto-badge` if `[tool.costs]` is configured in `pyproject.toml`
3. Stage updated README.md (interactive prompt in terminal)

### Pytest Integration

Tests automatically validate the cost calculation pipeline:

```bash
# Run all tests including auto-badge test
pytest tests/test_cost.py -v

### GitHub Actions

The repository includes a workflow that runs on push/PR:

```yaml
## CLI Commands

| Command | Description | Key Options |
|---------|-------------|-------------|
| `costs init` | Initialize `.env` configuration | `--force` - overwrite existing |
| `costs analyze` | Analyze repository commits | `--repo`, `--model`, `--api-key`, `--all`, `--since`, `--until`, `--date`, `--full-history`, `--max-commits`, `--output` |
| `costs stats` | Show repository statistics | `--repo` |
| `costs report` | Generate markdown/HTML reports | `--repo`, `--model`, `--format`, `--output`, `--update-readme` |
| `costs badge` | Generate cost badge | `--repo`, `--model`, `--all` |
| `costs auto-badge` | Auto-generate badge from pyproject.toml | `--repo`, `--all` |
| `costs estimate` | Estimate cost for single diff | `--model` |

📖 **Automatic Badge Generation**: See [docs/AUTO_BADGE.md](docs/AUTO_BADGE.md) for GitHub Actions, pre-commit hooks, and CI/CD integration.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key | (required for BYOK) |
| `LLM_MODEL` | Default model for calculations | `openrouter/qwen/qwen3-coder-next` |

## License

Licensed under Apache-2.0.
## Status

_Last updated by [taskill](https://github.com/oqlos/taskill) at 2026-04-25 13:37 UTC_

| Metric | Value |
|---|---|
| HEAD | `ffe3cf2` |
| Coverage | — |
| Failing tests | — |
| Commits in last cycle | 50 |

> Large set of feature and documentation commits were made: configuration management, a deep code-analysis engine, CLI improvements, a commit-message generator, multi-language documentation, and new API capabilities, along with various refactors and formatting improvements.

<!-- taskill:status:end -->
