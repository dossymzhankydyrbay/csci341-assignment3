$port = if ($env:PORT) { $env:PORT } else { "8000" }
python -m uvicorn assignment3.web:app --host 0.0.0.0 --port $port
