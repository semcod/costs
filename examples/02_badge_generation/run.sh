#!/bin/bash
# CLI Badge Generation Example

echo "========================================"
echo "CLI Example: Badge Generation"
echo "========================================"
echo ""

# ============================================
# 1. Manual badge generation
# ============================================
echo "1. Generate badge manually"
echo "   costs badge --repo ."
# costs badge --repo .

echo ""
echo "   With all commits:"
echo "   costs badge --repo . --all"
# costs badge --repo . --all

echo ""
echo "   With specific model:"
echo "   costs badge --repo . --model anthropic/claude-3.5-sonnet"

# ============================================
# 2. Auto-badge from pyproject.toml config
# ============================================
echo ""
echo "2. Auto-badge from pyproject.toml config"
echo "   costs auto-badge --repo ."
# costs auto-badge --repo .

echo ""
echo "   With all commits:"
echo "   costs auto-badge --repo . --all"
# costs auto-badge --repo . --all

# ============================================
# 3. Report generation
# ============================================
echo ""
echo "3. Report generation"
echo "   Markdown report:"
echo "   costs report --repo . --format markdown"
# costs report --repo . --format markdown

echo ""
echo "   HTML report:"
echo "   costs report --repo . --format html"
# costs report --repo . --format html

echo ""
echo "   Both formats + update README:"
echo "   costs report --repo . --format both --update-readme"
# costs report --repo . --format both --update-readme

echo ""
echo "========================================"
echo "Example complete!"
echo "========================================"
