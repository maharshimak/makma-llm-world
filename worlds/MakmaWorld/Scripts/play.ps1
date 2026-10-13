param([Parameter(Mandatory=$true)][string]$EngineRoot)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
$editor=Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe'
if (-not (Test-Path -LiteralPath $editor)) {throw 'UnrealEditor.exe not found.'}
& $editor (Join-Path $projectRoot 'MakmaWorld.uproject') /Game/Maps/Campus -game -windowed -ResX=1280 -ResY=720 -log
