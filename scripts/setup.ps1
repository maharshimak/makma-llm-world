param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
& $Python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ is required.' }
& .\.venv\Scripts\python.exe -m pip install -e '.[test]'
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
New-Item -ItemType Directory -Path data -Force | Out-Null
Push-Location apps/web
try { npm.cmd ci; if ($LASTEXITCODE -ne 0) { throw 'Dashboard dependency installation failed.' } } finally { Pop-Location }
Write-Host 'Application installed. Run scripts/start.ps1. Model setup remains in makma-llm-layer/setup-llm.ps1.'

