#!/bin/bash
# Set up a Python virtual environment with development dependencies
set -euo pipefail

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
pre-commit install
