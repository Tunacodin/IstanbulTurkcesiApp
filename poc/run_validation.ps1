# End-to-end POC dogrulama runner.
# 1. Edge TTS ile Turkce test ornekleri uretir
# 2. align_and_score pipeline'ini bunlar uzerinde calistirir
# 3. Skor istatistiklerini yazar
#
# Kullanim:  pwsh -File run_validation.ps1

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "venv bulunamadi: $python" -ForegroundColor Red
    Write-Host "Once: python -m venv .venv ve pip install -r poc/requirements.txt"
    exit 1
}

Push-Location $PSScriptRoot
try {
    Write-Host "`n[1/2] Edge TTS test ornekleri uretiliyor..." -ForegroundColor Cyan
    & $python make_tts_samples.py
    if ($LASTEXITCODE -ne 0) { throw "TTS uretimi basarisiz" }

    $manifest = Join-Path $repo "data\validation_set\tts\manifest.json"
    if (-not (Test-Path $manifest)) { throw "Manifest yok: $manifest" }

    Write-Host "`n[2/2] Pipeline calistiriliyor (ilk seferde wav2vec2 modeli inecek, ~1 GB)..." -ForegroundColor Cyan
    & $python validate.py --manifest $manifest
    if ($LASTEXITCODE -ne 0) { throw "Validation basarisiz" }
}
finally {
    Pop-Location
}
