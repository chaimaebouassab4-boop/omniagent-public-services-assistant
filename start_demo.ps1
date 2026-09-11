$Root = $PSScriptRoot
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   DEMARRAGE DE LA DEMONSTRATION POC - OMNIAGENT MAROC GOV" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[1/2] Lancement du Backend FastAPI (Port 8000)..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$Root\backend`" && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload" -WindowStyle Normal

Start-Sleep -Seconds 2

Write-Host "[2/2] Lancement du Frontend React (Port 5173)..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d `"$Root\omniagent`" && npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "   POC DEMONSTRATEUR PRET !" -ForegroundColor Green
Write-Host "   - URL Citoyen : http://localhost:5173" -ForegroundColor Green
Write-Host "   - API & Docs  : http://localhost:8000/docs" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green

