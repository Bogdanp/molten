#!/usr/bin/env bash

set -euo pipefail

flake8 molten tests examples
mypy --disallow-any-unimported \
     --disallow-any-generics \
     --disallow-untyped-calls \
     --disallow-untyped-defs \
     --disallow-incomplete-defs \
     --disallow-subclassing-any \
     --no-implicit-optional \
     molten
