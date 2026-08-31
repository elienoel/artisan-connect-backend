#!/bin/sh
set -e

echo "Waiting for postgres..."
until python -c "
import sys, psycopg2, os
try:
    psycopg2.connect(os.environ['DATABASE_URL'].replace('+psycopg2', ''))
except Exception as e:
    sys.exit(1)
" 2>/dev/null; do
  sleep 1
done
echo "Postgres is up."

alembic upgrade head
python seed.py

exec "$@"
