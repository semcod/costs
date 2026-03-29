# CLI Diff Estimation

Estimate cost for single diff or patch file.

## What it shows

- Estimate cost from a patch file
- Estimate cost from stdin (git diff)
- Compare costs across models for the same diff

## Files

- `run.sh` - Demonstrates diff estimation commands

## Usage

```bash
# View the commands
./run.sh --help

# Or run individual commands
costs estimate my_changes.patch
git diff HEAD~1 | costs estimate -
```

## Commands Demonstrated

### 1. From file
```bash
costs estimate my_changes.patch
costs estimate my_changes.patch --model gpt-4o
```

### 2. From stdin (git)
```bash
git diff HEAD~1 | costs estimate -
git diff | costs estimate -
git diff --staged | costs estimate -
```

### 3. Compare models
```bash
# Save diff and compare

```

## Commands Demonstrated

### 1. From file
```bash
costs estimate my_changes.patch
costs estimate my_changes.patch --model gpt-4o
```

### 2. From stdin (git)
```bash
git diff HEAD~1 | costs estimate -
git diff | costs estimate -
git diff --staged | costs estimate -
```

### 3. Compare models
```bash
# Save diff and compare
git diff HEAD~1 > /tmp/last_commit.diff
costs estimate /tmp/last_commit.diff --model openai/gpt-4o
costs estimate /tmp/last_commit.diff --model anthropic/claude-3.5-sonnet
```
