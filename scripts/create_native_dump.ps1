$ErrorActionPreference = 'Stop'
if (-not $env:PGDATABASE) { $env:PGDATABASE = 'csci341_a3' }
if (-not $env:PGUSER) { $env:PGUSER = 'postgres' }
pg_dump -U $env:PGUSER -d $env:PGDATABASE --no-owner --no-privileges --inserts --clean --if-exists --file sql/postgres_dump.sql
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host 'Created sql/postgres_dump.sql (actual pg_dump export).'
