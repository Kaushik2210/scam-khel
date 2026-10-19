#!/bin/sh
set -e

# Run production database migrations
echo "Running alembic upgrade head..."
alembic upgrade head

# Start application server
exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
