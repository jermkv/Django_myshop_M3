#!/usr/bin/env bash
set -euo pipefail

echo "Running pytest..."
python -m pytest -q

echo "Running mypy..."
python -m mypy .

if command -v flake8 >/dev/null 2>&1; then
  echo "Running flake8..."
  flake8 .
else
  echo "flake8 not installed; skipping flake8."
fi

echo "All checks finished." 
