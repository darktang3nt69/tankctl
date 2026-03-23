#!/bin/bash
set -e

# Wait for Postgres to be ready
echo "Waiting for Postgres to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0
until pg_isready -h postgres -U tankctl -d tankctl > /dev/null 2>&1; do
  ATTEMPT=$((ATTEMPT + 1))
  if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
    echo "Failed to connect to Postgres after $MAX_ATTEMPTS attempts"
    exit 1
  fi
  echo "Postgres is unavailable - attempt $ATTEMPT/$MAX_ATTEMPTS, sleeping..."
  sleep 1
done
echo "✓ Postgres is ready!"

# Run migrations
echo "Running database migrations..."
export PGPASSWORD="password"

# Run each migration file
for migration_file in /app/migrations/*.sql; do
  if [ -f "$migration_file" ]; then
    echo "  → Applying $(basename $migration_file)..."
    psql -h postgres -U tankctl -d tankctl -q -f "$migration_file" || {
      echo "ERROR: Failed to apply migration $(basename $migration_file)"
      exit 1
    }
  fi
done
echo "✓ All migrations applied successfully!"

# Start the application
echo "Starting backend application..."
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000
