@echo off
TITLE OmniAgent Morocco Gov MVP - Demo Launcher
echo ======================================================================
echo    DEMARRAGE DE LA DEMONSTRATION POC - OMNIAGENT MAROC GOV
echo ======================================================================
echo.
echo [1/2] Lancement du Backend FastAPI (Port 8000)...
start "OmniAgent Backend (FastAPI)" cmd /k "cd /d %~dp0backend && set DEBUG_LOGGING=true&& .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak > nul

echo [2/2] Lancement du Frontend React (Port 5173)...
start "OmniAgent Frontend (React)" cmd /k "cd /d %~dp0omniagent && npm run dev"

echo.
echo ======================================================================
echo    POC DEMONSTRATEUR PRET !
echo    - URL Citoyen : http://localhost:5173
echo    - API & Docs  : http://localhost:8000/docs
echo ======================================================================
echo.
pause
