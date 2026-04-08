# AI Productivity Platform - Start Script
Write-Host "🚀 Starting AI Productivity Platform..." -ForegroundColor Cyan

# Activate virtual environment
$venvPath = Join-Path $PSScriptRoot "genai_env\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
    Write-Host "✅ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "❌ Virtual environment not found at $venvPath" -ForegroundColor Red
    exit 1
}

# Run the app
Set-Location $PSScriptRoot
Write-Host "✅ Starting Uvicorn server on http://localhost:8000" -ForegroundColor Green
python run.py
