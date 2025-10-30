#!/usr/bin/env bash
# Rayden Rules - FastAPI Backend Launcher

cd "$(dirname "$0")/../../.."

echo "Starting Rayden Rules FastAPI Backend..."
echo "========================================="
echo ""
echo "API:       http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""

uvicorn raydenrules.api.api:app --reload --host 0.0.0.0 --port 8000
