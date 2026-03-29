#!/bin/bash
# CLI Diff Estimation Example

echo "========================================"
echo "CLI Example: Diff Estimation"
echo "========================================"
echo ""

# ============================================
# 1. Estimate from file
# ============================================
echo "1. Estimate from file"
echo "   costs estimate my_changes.patch"
echo "   costs estimate my_changes.patch --model gpt-4o"

# ============================================
# 2. Estimate from stdin (git)
# ============================================
echo ""
echo "2. Estimate from stdin"
echo "   Pipe git diff to estimator:"
echo ""
echo "   a) Last commit:"
echo "      git diff HEAD~1 | costs estimate -"

if [ -d ".git" ]; then
    echo ""
    echo "   Running on last commit:"
    git diff HEAD~1 | costs estimate - 2>/dev/null || echo "   (costs not installed or no commits)"
fi

echo ""
echo "   b) Uncommitted changes:"
echo "      git diff | costs estimate -"

echo ""
echo "   c) Staged changes:"
echo "      git diff --staged | costs estimate -"

# ============================================
# 3. Compare models for same diff
# ============================================
echo ""
echo "3. Compare models for same diff"
if [ -d ".git" ]; then
    echo "   Saving last commit diff..."
    git diff HEAD~1 > /tmp/last_commit.diff 2>/dev/null || true
    
    if [ -f "/tmp/last_commit.diff" ] && [ -s "/tmp/last_commit.diff" ]; then
        echo ""
        echo "   GPT-4o:"
        costs estimate /tmp/last_commit.diff --model openai/gpt-4o 2>/dev/null || echo "   (skipped)"
        
        echo ""
        echo "   Claude 3.5 Sonnet:"
        costs estimate /tmp/last_commit.diff --model anthropic/claude-3.5-sonnet 2>/dev/null || echo "   (skipped)"
        
        echo ""
        echo "   Qwen3 Coder:"
        costs estimate /tmp/last_commit.diff --model openrouter/qwen/qwen3-coder-next 2>/dev/null || echo "   (skipped)"
        
        rm -f /tmp/last_commit.diff
    fi
fi

echo ""
echo "========================================"
echo "Example complete!"
echo "========================================"
