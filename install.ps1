$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $projectRoot ".venv"
$python = Get-Command python -ErrorAction SilentlyContinue

if (-not $python) {
    throw "Python 3.11 or newer is required. Install Python from https://www.python.org/downloads/ and run this script again."
}

if (-not (Test-Path (Join-Path $venvPath "Scripts\python.exe"))) {
    & $python.Source -m venv $venvPath
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "Ollama is required for the AI brain. Install Ollama or enable winget, then run this script again."
    }

    & $winget.Source install --id Ollama.Ollama -e --accept-source-agreements --accept-package-agreements
    $ollama = Get-Command ollama -ErrorAction SilentlyContinue
}

if (-not $ollama) {
    throw "Ollama was installed, but its command is not available yet. Restart PowerShell and run install.ps1 again."
}

& $ollama.Source pull llama3.2:3b
& $ollama.Source pull moondream

Write-Host "Vega is installed. Start it with .\run.ps1" -ForegroundColor Green
