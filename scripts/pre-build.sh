#!/usr/bin/env bash

set -eo pipefail

if [ ! "$TESTENV" = "lint" ] && [ ! "$TESTENV" = "examples" ]
then
    curl -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 > ./cc-test-reporter
    chmod +x ./cc-test-reporter
    ./cc-test-reporter before-build
fi
