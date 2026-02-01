#!/bin/bash

# Update pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Generate Prisma client
# Use 'python -m prisma' to ensure it's run using the current python environment
echo "Generating Prisma Client..."
python -m prisma generate --schema=prisma/schema.prisma

echo "Build process completed successfully"
