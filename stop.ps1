$root = $PSScriptRoot
$pidFile = Join-Path $root "streamlit.pid"

if (-not (Test-Path $pidFile)) {
    Write-Host "No PID file found - app not running (or not started via start.ps1)."
    exit 0
}

$procId = Get-Content $pidFile
if ($procId -and (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
    # streamlit.exe spawns a child python.exe; /T kills the whole tree, not just the launcher shim.
    taskkill /PID $procId /T /F | Out-Null
    Write-Host "Stopped process $procId (and children)"
} else {
    Write-Host "Process $procId not found (already stopped)."
}

Remove-Item $pidFile -Force
