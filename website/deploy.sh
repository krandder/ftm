#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python build.py

npx --yes wrangler@latest deploy "$@"
