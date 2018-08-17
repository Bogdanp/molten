#!/usr/bin/env bash

set -eo pipefail

case "$TESTENV" in
    lint)     ./scripts/lint.sh;;
    examples) ./scripts/test-examples.sh;;
    *)        ./scripts/test.sh;;
esac
