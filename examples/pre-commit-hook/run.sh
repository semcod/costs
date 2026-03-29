#!/bin/bash
# Run pre-commit hook manually for testing

cd "$(dirname "$0")"
echo "Running pre-commit hook manually..."
bash pre-commit
