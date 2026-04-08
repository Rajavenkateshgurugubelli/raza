Write-Host "Starting R.A.Z.A Agent Application..."

# Start the Backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; pip install -r requirements.txt; uvicorn app.main:app --reload --port 8000"

# Start the Frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "Services are starting in separate windows."
