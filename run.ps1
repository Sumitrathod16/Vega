$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    throw "Vega is not installed. Run .\install.ps1 first."
}

& $venvPython (Join-Path $projectRoot "listener.py")
