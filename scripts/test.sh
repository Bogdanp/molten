#!/usr/bin/env bash

set -euo pipefail

py.test --cov-report xml
