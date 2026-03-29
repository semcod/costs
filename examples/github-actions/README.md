# GitHub Actions

Automatically update AI cost badge on every push.

## What it shows

- GitHub Actions workflow for cost tracking
- Auto-update badge on push to main
- Uses secrets for API keys

## Files

- `workflow.yml` - The GitHub Actions workflow file

## Usage

Copy `workflow.yml` to your repository:

```bash
cp workflow.yml .github/workflows/ai-cost-badge.yml
git add .github/workflows/ai-cost-badge.yml
git commit -m "Add AI cost badge workflow"
```

## Setup

1. Add your OpenRouter API key as a GitHub secret:
   - Go to Settings → Secrets and variables → Actions
   - Add `OPENROUTER_API_KEY`

2. Ensure `[tool.costs]` is configured in `pyproject.toml`

## What it does

1. Runs on every push to main/master
2. Installs `costs` package
3. Updates badge using `costs auto-badge`
4. Commits and pushes updated README
