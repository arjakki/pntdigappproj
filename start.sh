#!/bin/bash
echo ""
echo "=========================================="
echo " ED AI Agent - Mercy Regional Medical Center"
echo " LangChain + MySQL MCP + Claude Sonnet"
echo "=========================================="
echo ""

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[!] Created .env — add your ANTHROPIC_API_KEY and rerun"
    exit 1
fi

echo "[1/2] Installing dependencies..."
pip install -r requirements.txt --quiet

echo "[2/2] Starting server..."
echo ""
echo "  Dashboard  : http://localhost:8000"
echo "  AI Chat    : http://localhost:8000/chat"
echo "  Intake Form: http://localhost:8000/intake"
echo "  API Docs   : http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop."
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
