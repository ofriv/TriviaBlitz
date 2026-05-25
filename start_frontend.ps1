# Start the Trivia React frontend (dev server)
# Usage: .\start_frontend.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Starting Trivia frontend..." -ForegroundColor Cyan
Set-Location "$scriptDir\frontend"
npm run dev
