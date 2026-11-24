#!/usr/bin/env sh
set -eu
exec uvicorn assignment3.web:app --host 0.0.0.0 --port "${PORT:-8000}"
