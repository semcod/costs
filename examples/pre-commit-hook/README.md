# Pre-commit Hook

Automatically update cost badge before each commit.

## What it shows

- Install a git pre-commit hook
- Auto-update badge using pyproject.toml config
- Stage updated README.md

## Files

- `install.sh` - Install the hook
- `pre-commit` - The hook script
- `run.sh` - Run the hook manually

## Installation

```bash
./install.sh
```

This copies the hook to `.git/hooks/pre-commit`.

## What it does

1. Checks if `costs` is installed
2. Runs `costs auto-badge --repo .`
3. Stages README.md if modified
4. Continues with the commit

## Requirements

- Git repository initialized
- `costs` installed (`pip install costs`)
- `[tool.costs]` section in `pyproject.toml`
