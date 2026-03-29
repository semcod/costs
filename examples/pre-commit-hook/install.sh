#!/bin/bash
# Install pre-commit hook

cd "$(dirname "$0")"

SCRIPT_DIR="$(pwd)"
GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo '')"

if [ -z "$GIT_ROOT" ]; then
    echo "Error: Not in a git repository"
    exit 1
fi

HOOKS_DIR="$GIT_ROOT/.git/hooks"

# Create hooks dir if needed
mkdir -p "$HOOKS_DIR"

# Copy hook
cp "$SCRIPT_DIR/pre-commit" "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/pre-commit"

echo "Pre-commit hook installed to $HOOKS_DIR/pre-commit"
echo ""
echo "The hook will:"
echo "  - Update AI cost badge on every commit"
echo "  - Stage README.md if modified"
