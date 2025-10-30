#!/usr/bin/env bash
# Rayden Rules - Reflex Frontend Launcher

cd "$(dirname "$0")"

echo "Starting Rayden Rules Reflex Application..."
echo "==========================================="
echo ""
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:8001"
echo ""

reflex run
