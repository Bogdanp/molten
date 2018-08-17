#!/usr/bin/env bash

set -euo pipefail

echo "Running flake8..."
flake8 molten tests examples

echo "Running mypy..."
mypy --ignore-missing-imports \
     --disallow-any-unimported \
     --disallow-any-generics \
     --disallow-untyped-calls \
     --disallow-untyped-defs \
     --disallow-incomplete-defs \
     --disallow-subclassing-any \
     --no-implicit-optional \
     molten
