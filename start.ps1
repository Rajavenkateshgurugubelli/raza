Write-Host "Starting R.A.Z.A. Agent Application..." -ForegroundColor Cyan

# Ensure .env exists
if (-not (Test-Path "backend\.env")) {
    Write-Host "WARNING: backend\.env not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" "backend\.env"
}

$VenvPath = "backend\.venv"
$PythonPath = "C:\Users\rajag\AppData\Local\Programs\Python\Python312\python.exe"

# Recreate venv if missing
if (-not (Test-Path $VenvPath)) {
    Write-Host "Virtual environment not found. Re-initializing..." -ForegroundColor Yellow
    & $PythonPath -m venv $VenvPath
    & (Join-Path $VenvPath "Scripts\pip.exe") install -r backend\requirements.txt
}

# Start the Backend
$backendCmd = "cd backend; .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

Start-Sleep -Seconds 2

# Start the Frontend
$NpmPath = "C:\Program Files\nodejs\npm.cmd"
$frontendCmd = "cd frontend; & '$NpmPath' run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host ""
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "R.A.Z.A. is now initializing in separate windows." -ForegroundColor Yellow
Write-Host "Using Google Gemini Free Tier." -ForegroundColor Cyan

