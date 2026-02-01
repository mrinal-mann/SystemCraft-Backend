#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# VERY IMPORTANT: use Prisma's real cache dir (what runtime expects)
export PRISMA_PY_BINARY_CACHE_DIR=/opt/render/.cache/prisma-python/binaries

python -m prisma py fetch
python -m prisma generate
