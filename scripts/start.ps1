param([switch]$ApiOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run scripts/setup.ps1 first.' }
New-Item -ItemType Directory -Path (Join-Path $projectRoot 'data') -Force | Out-Null
if (-not $ApiOnly) {
    Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','makma.api:create_app','--factory','--host','127.0.0.1','--port','8765' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot 'data/api.log') -RedirectStandardError (Join-Path $projectRoot 'data/api-error.log')
    Set-Location -LiteralPath (Join-Path $projectRoot 'apps\web')
    npm.cmd run dev -- --hostname 127.0.0.1 --port 3010
} else {
    & $pythonPath -m uvicorn makma.api:create_app --factory --host 127.0.0.1 --port 8765
}

