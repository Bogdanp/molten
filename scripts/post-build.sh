#!/usr/bin/env bash

set -eo pipefail

if [ ! "$TESTENV" = "lint" ] && [ ! "$TESTENV" = "examples" ]
then
    ./cc-test-reporter after-build --exit-code "$TRAVIS_TEST_RESULT"
fi
