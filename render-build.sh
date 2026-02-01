#!/usr/bin/env bash
# Render Build Script for FastAPI + SQLAlchemy + Alembic
set -o errexit

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Running database migrations..."
# Run Alembic migrations to bring database to latest version
alembic upgrade head

echo "Build complete!"
