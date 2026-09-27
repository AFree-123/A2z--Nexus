# Start A2Z Nexus — Backend + Frontend

# ---- Backend ----
Write-Host "Starting A2Z Nexus backend..." -ForegroundColor Cyan
Set-Location backend
if (-not (Test-Path .venv)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    py -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
}
if (-not (Test-Path ..\.env)) {
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ..\.env.example ..\.env
}
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 4000"
Set-Location ..

# ---- Frontend ----
Write-Host "Starting A2Z Nexus frontend..." -ForegroundColor Cyan
Set-Location frontend
if (-not (Test-Path node_modules)) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm run dev"
Set-Location ..

Write-Host ""
Write-Host "A2Z Nexus is starting!" -ForegroundColor Green
Write-Host "  Backend API: http://localhost:4000" -ForegroundColor White
Write-Host "  API Docs:    http://localhost:4000/docs" -ForegroundColor White
Write-Host "  Frontend:    http://localhost:5173" -ForegroundColor White
