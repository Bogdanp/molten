#!/usr/bin/env bash

set -euo pipefail

echo "Running flake8..."
flake8 molten tests examples
