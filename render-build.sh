#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Generate Prisma Client
# This is required for the application to interact with the database
python -m prisma generate
