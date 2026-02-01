#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Create a specific folder for binaries
mkdir -p prisma_binaries
export PRISMA_PY_BINARY_CACHE_DIR=/opt/render/project/src/prisma_binaries

# Fetch and Generate
python -m prisma py fetch
python -m prisma generate