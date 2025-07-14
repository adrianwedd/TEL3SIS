#!/bin/bash
# Install git-secrets if not already installed

set -euo pipefail

if command -v git-secrets >/dev/null 2>&1; then
  exit 0
fi

echo "git-secrets not found. Attempting to install..."

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y git-secrets
else
  echo "Please install git-secrets manually" >&2
  exit 1
fi

# Install git-secrets hooks for this repo
if ! git secrets --install -f >/dev/null 2>&1; then
  echo "Failed to install git-secrets hooks" >&2
  exit 1
fi
