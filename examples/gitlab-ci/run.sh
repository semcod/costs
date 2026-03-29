#!/bin/bash
# Validate GitLab CI configuration

cd "$(dirname "$0")"

if command -v glab &> /dev/null; then
    echo "Validating with glab..."
    glab ci lint .gitlab-ci.yml
else
    echo "To validate, install 'glab' CLI: https://gitlab.com/gitlab-org/cli"
    echo ""
    echo "Or copy .gitlab-ci.yml to your repo:"
    echo "  cp .gitlab-ci.yml /path/to/your/repo/"
fi
