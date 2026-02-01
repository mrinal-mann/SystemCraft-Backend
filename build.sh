#!/bin/bash
# Install dependencies
pip install -r requirements.txt

# Generate Prisma client
echo "Generating Prisma Client..."
python -m prisma generate

echo "Build completed"
