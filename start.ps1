Write-Host "Starting R.A.Z.A. Agent Application..." -ForegroundColor Cyan

# Ensure .env exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "WARNING: backend\.env not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" "backend\.env"
}

# Start the Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$PWD\backend'; " + `
    "pip install -r requirements.txt -q; " + `
    "uvicorn app.main:app --reload --port 8000"

Start-Sleep -Seconds 2

# Start the Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$PWD\frontend'; " + `
    "npm install; " + `
    "npm run dev"

Write-Host ""
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Remember to add your ANTHROPIC_API_KEY to backend\.env" -ForegroundColor Yellow
