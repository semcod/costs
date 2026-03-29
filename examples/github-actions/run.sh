#!/bin/bash
# Run GitHub Actions workflow locally with act (if installed)

cd "$(dirname "$0")"

if command -v act &> /dev/null; then
    echo "Running workflow locally with act..."
    act push
else
    echo "To run locally, install 'act': https://github.com/nektos/act"
    echo ""
    echo "Or copy workflow.yml to your repo:"
    echo "  cp workflow.yml .github/workflows/ai-cost-badge.yml"
fi
