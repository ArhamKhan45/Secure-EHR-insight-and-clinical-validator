#!/bin/sh
set -e

echo "Starting FastAPI..."

uvicorn src.api.main:app \
    --host 127.0.0.1 \
    --port 8000 &

API_PID=$!

echo "Waiting for FastAPI..."

until curl -fsS http://127.0.0.1:8000/openapi.json >/dev/null 2>&1; do
    if ! kill -0 "$API_PID" 2>/dev/null; then
        echo "FastAPI failed to start."
        wait "$API_PID"
        exit 1
    fi

    sleep 2
done

echo "FastAPI is ready."

echo "Starting Streamlit on port ${PORT:-10000}..."

exec streamlit run src/ui/app.py \
    --server.address=0.0.0.0 \
    --server.port="${PORT:-10000}" \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false