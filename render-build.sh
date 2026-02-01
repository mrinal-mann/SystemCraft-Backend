#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Set binary cache directory to project root
# This ensures binaries are included in the deployment and found at runtime
export PRISMA_PY_BINARY_CACHE_DIR=.

# Fetch Prisma binaries
python -m prisma py fetch

# Generate Prisma Client
python -m prisma generate

