# Start the Trivia backend server
# Usage: .\start_server.ps1

$env:PYTHONUTF8 = "1"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Starting Trivia server..." -ForegroundColor Green
& "$scriptDir\.venv\Scripts\python.exe" "$scriptDir\backend\server.py"
