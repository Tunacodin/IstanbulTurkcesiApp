# Projeyi localhost:8765'te ayağa kaldırır.
# Kullanim:  powershell -ExecutionPolicy Bypass -File run.ps1
# veya:      .\run.ps1   (PowerShell penceresinden)

$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "venv bulunamadi: $python" -ForegroundColor Red
    Write-Host "Once: python -m venv .venv ve pip install -r poc/requirements.txt"
    exit 1
}

# Eger 8765 portu doluysa kapat
$conn = Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    Write-Host "Port 8765 dolu, eski PID $($conn.OwningProcess) durduruluyor..."
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

$env:PYTHONIOENCODING = "utf-8"
Push-Location (Join-Path $repo "poc")
try {
    Write-Host ""
    Write-Host "Tarayicida ac: http://127.0.0.1:8765/static/" -ForegroundColor Cyan
    Write-Host "Durdurmak icin: Ctrl+C"
    Write-Host ""
    & $python -m uvicorn api:app --host 127.0.0.1 --port 8765
}
finally {
    Pop-Location
}
