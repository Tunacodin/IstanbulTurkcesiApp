# HTTPS modu: telefon + bilgisayardan PWA olarak kullanim icin.
# Kullanim:  .\run-https.ps1
# Sertifika yoksa otomatik uretir.

$ErrorActionPreference = "Stop"
$repo = $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"
$certDir = Join-Path $repo "poc\certs"
$keyPath = Join-Path $certDir "server.key"
$crtPath = Join-Path $certDir "server.crt"

if (-not (Test-Path $python)) {
    Write-Host "venv bulunamadi: $python" -ForegroundColor Red
    exit 1
}

# Sertifika yoksa olustur
if (-not (Test-Path $keyPath) -or -not (Test-Path $crtPath)) {
    Write-Host "TLS sertifikasi olusturuluyor..." -ForegroundColor Cyan
    Push-Location (Join-Path $repo "poc")
    try {
        & $python generate_cert.py
        if ($LASTEXITCODE -ne 0) { throw "Sertifika uretimi basarisiz" }
    } finally {
        Pop-Location
    }
}

# 8765 portunu temizle
$conn = Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($conn) {
    Write-Host "Port 8765 dolu, eski PID $($conn.OwningProcess) durduruluyor..."
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# LAN IP tespit
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.IPAddress -notmatch '^(127|169)' -and $_.PrefixOrigin -eq 'Dhcp' } |
    Select-Object -First 1).IPAddress
if (-not $lanIp) { $lanIp = "<LAN-IP>" }

$env:PYTHONIOENCODING = "utf-8"
Push-Location (Join-Path $repo "poc")
try {
    Write-Host ""
    Write-Host "--- HTTPS modu ayakta ---" -ForegroundColor Green
    Write-Host "Bilgisayar:  https://localhost:8765/static/"
    Write-Host "Telefon  :  https://$lanIp:8765/static/" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Telefonun ayni Wi-Fi'da olmali."
    Write-Host "Self-signed sertifika oldugu icin tarayici 'guvensiz' uyarir; 'Devam et' de."
    Write-Host "Mikrofon izni isteyince 'Izin ver'."
    Write-Host ""
    Write-Host "Durdurmak icin: Ctrl+C"
    Write-Host ""
    & $python -m uvicorn api:app `
        --host 0.0.0.0 --port 8765 `
        --ssl-keyfile certs/server.key `
        --ssl-certfile certs/server.crt
}
finally {
    Pop-Location
}
