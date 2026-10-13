$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
docker build --tag makma-sandbox:0.1 (Join-Path $projectRoot 'infrastructure\docker') -f (Join-Path $projectRoot 'infrastructure\docker\Dockerfile.sandbox')
if ($LASTEXITCODE -ne 0) { throw 'Sandbox image build failed. Ensure Docker Desktop is running Linux containers.' }

