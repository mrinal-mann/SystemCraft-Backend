#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Fetch Prisma binaries
# This ensures the query engine and other binaries are available in the production environment
python -m prisma py fetch

# Generate Prisma Client
# This is required for the application to interact with the database
python -m prisma generate
