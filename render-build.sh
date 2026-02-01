#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# 1) Generate client
python -m prisma generate

# 2) Fetch the engine for Render (REQUIRED)
python -m prisma py fetch

# 3) Copy engine to where Prisma FIRST looks
ENGINE=$(find /opt/render/.cache/prisma-python/binaries -name "prisma-query-engine-debian-openssl-3.0.x" | head -n 1)
cp "$ENGINE" /opt/render/project/src/prisma-query-engine-debian-openssl-3.0.x
chmod +x /opt/render/project/src/prisma-query-engine-debian-openssl-3.0.x
