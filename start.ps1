Write-Host "Starting R.A.Z.A. Agent Application..." -ForegroundColor Cyan

# Ensure .env exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "WARNING: backend\.env not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" "backend\.env"
}

# Start the Backend
$backendCmd = "cd backend; pip install -r requirements.txt -q; uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Start-Sleep -Seconds 2

# Start the Frontend
$frontendCmd = "cd frontend; npm install; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host ""
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "R.A.Z.A. is now initializing in separate windows." -ForegroundColor Yellow
Write-Host "Using Google Gemini Free Tier." -ForegroundColor Cyan
