#!/bin/bash
# CLI Basic Usage Example
# This script demonstrates common costs CLI commands

set -e

echo "========================================"
echo "CLI Example: Basic Usage"
echo "========================================"
echo ""
echo "This example shows common CLI commands."
echo "Some commands are commented out for safety."
echo "Uncomment them to run on your repository."
echo ""

# ============================================
# 1. Initialize configuration
# ============================================
echo "1. Initialize configuration"
echo "   Command: costs init"
echo "   Creates .env file with default settings"
# costs init

echo ""

# ============================================
# 2. Analyze repository
# ============================================
echo "2. Analyze repository"
echo "   Current directory: $(pwd)"
echo ""
echo "   a) Analyze with defaults (uses .env):"
echo "      costs analyze --repo ."
# costs analyze --repo .

echo ""
echo "   b) Analyze with specific model:"
echo "      costs analyze --repo . --model openrouter/qwen/qwen3-coder-next"

echo ""
echo "   c) Analyze with explicit API key:"
echo "      costs analyze --repo . --api-key YOUR_OPENROUTER_KEY"

echo ""

# ============================================
# 3. Filter by date/time
# ============================================
echo "3. Date filtering"
echo "   a) Specific day:"
echo "      costs analyze --repo . --date 2024-03-15"

echo ""
echo "   b) Date range:"
echo "      costs analyze --repo . --since 2024-01-01 --until 2024-03-31"

echo ""
echo "   c) Full history:"
echo "      costs analyze --repo . --full-history"

echo ""
echo "   d) Limit commits:"
echo "      costs analyze --repo . -n 50"

echo ""

# ============================================
# 4. Statistics
# ============================================
echo "4. Repository statistics"
echo "   costs stats --repo ."
# costs stats --repo .

echo ""
echo "========================================"
echo "Example complete!"
echo "========================================"
