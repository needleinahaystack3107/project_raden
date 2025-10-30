#!/usr/bin/env bash
# Rayden Rules - Reflex Frontend Launcher

cd "$(dirname "$0")"

echo "⚡ Starting Rayden Rules Reflex Application ⚡"
echo "=============================================="
echo ""

# Check if FastAPI backend is running
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "✅ FastAPI Data Backend detected on port 8001"
    echo "📊 Data Mode: LIVE API DATA"
else
    echo "⚠️  FastAPI Data Backend NOT detected on port 8001"
    echo "📊 Data Mode: MOCK DATA (fallback)"
    echo ""
    echo "   To use live data, start the API backend first:"
    echo "   bash src/raydenrules/api/start_api.sh"
fi

echo ""
echo "Frontend (UI):              http://localhost:3000"
echo "Reflex Backend (State):     http://localhost:8000"
echo "FastAPI Backend (Data):     http://localhost:8001"
echo "API Docs:                   http://localhost:8001/docs"
echo ""

reflex run
