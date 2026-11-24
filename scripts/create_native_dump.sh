#!/usr/bin/env bash
set -euo pipefail
PGDATABASE="${PGDATABASE:-csci341_a3}"
PGUSER="${PGUSER:-postgres}"
pg_dump -U "$PGUSER" -d "$PGDATABASE" \
  --no-owner --no-privileges --inserts --clean --if-exists \
  --file sql/postgres_dump.sql
echo 'Created sql/postgres_dump.sql (actual pg_dump export).'
