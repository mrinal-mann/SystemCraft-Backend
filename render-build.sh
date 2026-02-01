#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python -m prisma generate
python -m prisma py fetch

# 🔥 THE MISSING STEP — copy engine to project root
ENGINE=$(find /opt/render/.cache/prisma-python/binaries -name "prisma-query-engine-debian-openssl-3.0.x" | head -n 1)
cp "$ENGINE" /opt/render/project/src/prisma-query-engine-debian-openssl-3.0.x
chmod +x /opt/render/project/src/prisma-query-engine-debian-openssl-3.0.x
