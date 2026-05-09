# Windows SAPI TTS ile test wav uretir.
# Kullanim:  pwsh -File make_test_wav.ps1 -Text "merhaba dunya" -OutPath ../data/validation_set/sapi/test_001.wav

param(
    [Parameter(Mandatory = $true)] [string]$Text,
    [Parameter(Mandatory = $true)] [string]$OutPath,
    [string]$VoicePreference = "Tolga"
)

Add-Type -AssemblyName System.Speech

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voices = $synth.GetInstalledVoices() | Where-Object { $_.Enabled }

# Turkce ses bul (Tolga, Filiz, ya da TR-TR ile baslayan); yoksa varsayilan
$tr = $voices | Where-Object {
    $_.VoiceInfo.Culture.Name -like 'tr-*' -or $_.VoiceInfo.Name -like "*$VoicePreference*"
} | Select-Object -First 1
if ($tr) {
    $synth.SelectVoice($tr.VoiceInfo.Name)
    Write-Host "Voice: $($tr.VoiceInfo.Name) ($($tr.VoiceInfo.Culture.Name))"
} else {
    Write-Host "UYARI: Turkce ses yok. Varsayilan ses kullaniliyor: $($synth.Voice.Name)"
}

# Cikti klasorunu olustur
$dir = Split-Path -Parent $OutPath
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

# 16 kHz mono 16-bit WAV
$format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen, [System.Speech.AudioFormat.AudioChannel]::Mono)
$synth.SetOutputToWaveFile($OutPath, $format)
$synth.Speak($Text)
$synth.Dispose()

Write-Host "Yazildi: $OutPath"
