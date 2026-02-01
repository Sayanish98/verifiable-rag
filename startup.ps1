# Verifiable RAG - Startup Script
# This script installs dependencies and starts both backend and frontend

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Verifiable RAG - Startup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the root directory
$ROOT_DIR = $PSScriptRoot
$BACKEND_DIR = Join-Path $ROOT_DIR "backend"
$FRONTEND_DIR = Join-Path $ROOT_DIR "frontend"

# Step 1: Install Backend Dependencies
Write-Host "[1/5] Installing Backend Dependencies..." -ForegroundColor Yellow
Set-Location $BACKEND_DIR

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# Install requirements
Write-Host "Installing Python packages..." -ForegroundColor Cyan
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install backend dependencies!" -ForegroundColor Red
    exit 1
}

Write-Host "Backend dependencies installed successfully!" -ForegroundColor Green
Write-Host ""

# Step 2: Install Frontend Dependencies
Write-Host "[2/5] Installing Frontend Dependencies..." -ForegroundColor Yellow
Set-Location $FRONTEND_DIR

Write-Host "Installing Node packages..." -ForegroundColor Cyan
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install frontend dependencies!" -ForegroundColor Red
    exit 1
}

Write-Host "Frontend dependencies installed successfully!" -ForegroundColor Green
Write-Host ""

# Step 3: Start Backend Server
Write-Host "[3/5] Starting Backend Server..." -ForegroundColor Yellow
Set-Location $BACKEND_DIR

# Start backend in a new terminal window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$BACKEND_DIR'; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload"

Write-Host "Backend server starting at http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Waiting 5 seconds for backend to initialize..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
Write-Host ""

# Step 4: Start Frontend Server
Write-Host "[4/5] Starting Frontend Server..." -ForegroundColor Yellow
Set-Location $FRONTEND_DIR

# Start frontend in a new terminal window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FRONTEND_DIR'; npm start"

Write-Host "Frontend server starting at http://localhost:3000" -ForegroundColor Green
Write-Host ""

# Step 5: Complete
Write-Host "[5/5] Startup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Both servers are now running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
