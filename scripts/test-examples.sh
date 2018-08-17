#!/usr/bin/env bash

set -euo pipefail

for folder in examples/*
do
    pushd "$folder"
    if [ -f test_app.py ]
    then
        py.test
    fi
    popd
done
