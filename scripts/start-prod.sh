#!/bin/bash
set -e

echo "Starting Vohrad Backend..."

export PYTHONPATH="/app:$PYTHONPATH"

# Create log files
echo "Creating log files..."
touch /app/logs/app.log /app/logs/audit.log /app/logs/error.log /app/logs/security.log

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! python -c "
import asyncio
import asyncpg
import os
import sys

async def check_db():
    try:
        db_user = os.getenv('DB_USER', 'postgres')
        db_pass = os.getenv('DB_PASS') or os.getenv('DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD', 'postgres')
        db_host = os.getenv('DB_HOST', 'db')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'vohrad')
        
        conn = await asyncpg.connect(
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port,
            database=db_name
        )
        await conn.close()
        print('Database is ready!')
    except Exception as e:
        print(f'Database not ready: {e}')
        sys.exit(1)

asyncio.run(check_db())
"; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start
echo "Starting FastAPI application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000