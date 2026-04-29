@echo off
echo.
echo ==========================================
echo  ED AI Agent - Mercy Regional Medical Center
echo  LangChain + MySQL MCP + Claude Sonnet
echo ==========================================
echo.

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [!] Created .env from template - please add your ANTHROPIC_API_KEY
    echo     Edit .env and set: ANTHROPIC_API_KEY=sk-ant-...
    echo.
    pause
)

echo [1/3] Installing dependencies...
pip install -r requirements.txt --quiet

echo [2/3] Starting server at http://localhost:8000
echo.
echo  Dashboard  : http://localhost:8000
echo  AI Chat    : http://localhost:8000/chat
echo  Intake Form: http://localhost:8000/intake
echo  API Docs   : http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop.
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
