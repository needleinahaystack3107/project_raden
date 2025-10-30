#!/usr/bin/env bash
# Rayden Rules - FastAPI Backend Launcher

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Navigate to project root
cd "$SCRIPT_DIR/../../.."

# Set PYTHONPATH to include src directory (as fallback if package not installed)
export PYTHONPATH="$PWD/src:$PYTHONPATH"

echo "Starting Rayden Rules FastAPI Backend..."
echo "========================================="
echo ""
echo "API:       http://localhost:8001"
echo "API Docs:  http://localhost:8001/docs"
echo ""
echo "Project Root: $PWD"
echo "PYTHONPATH: $PYTHONPATH"
echo ""

uvicorn raydenrules.api.api:app --reload --host 0.0.0.0 --port 8001
