#!/bin/bash
# entrypoint.sh

set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding roles and admin user..."
python -m scripts.seed_data

echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"