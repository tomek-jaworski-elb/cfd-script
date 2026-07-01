param([int]$Port = 8501)

$root = $PSScriptRoot
$pidFile = Join-Path $root "streamlit.pid"
$logFile = Join-Path $root "streamlit.log"
$errFile = Join-Path $root "streamlit.err.log"

if (Test-Path $pidFile) {
    $existingPid = Get-Content $pidFile
    if ($existingPid -and (Get-Process -Id $existingPid -ErrorAction SilentlyContinue)) {
        Write-Host "Already running (PID $existingPid) at http://localhost:$Port"
        exit 0
    }
}

$streamlitExe = Join-Path $root "venv\Scripts\streamlit.exe"
if (-not (Test-Path $streamlitExe)) {
    Write-Host "venv not found at $streamlitExe - run: python -m venv venv; .\venv\Scripts\pip.exe install -r requirements.txt"
    exit 1
}

$proc = Start-Process -FilePath $streamlitExe `
    -ArgumentList @("run", "app.py", "--server.headless", "true", "--server.port", $Port) `
    -WorkingDirectory $root `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError $errFile `
    -WindowStyle Hidden `
    -PassThru

$proc.Id | Out-File -FilePath $pidFile -Encoding ascii -NoNewline

$deadline = (Get-Date).AddSeconds(120)
while ((Get-Date) -lt $deadline) {
    try {
        Invoke-WebRequest -Uri "http://localhost:$Port" -UseBasicParsing -TimeoutSec 5 | Out-Null
        Write-Host "App running at http://localhost:$Port (PID $($proc.Id))"
        exit 0
    } catch {
        Start-Sleep -Seconds 1
    }
}

Write-Host "Timed out waiting for app to respond. Check $logFile / $errFile"
exit 1
