param([Parameter(Mandatory=$true)][string]$EngineRoot)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
$projectFile=Join-Path $projectRoot 'MakmaWorld.uproject'
$buildScript=Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat'
$editor=Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor-Cmd.exe'
if (-not (Test-Path -LiteralPath $buildScript) -or -not (Test-Path -LiteralPath $editor)) {throw 'EngineRoot must point to a complete Unreal Engine 5 installation.'}
& $buildScript MakmaWorldEditor Win64 Development $projectFile -WaitMutex
if ($LASTEXITCODE -ne 0) {throw 'Unreal C++ compilation failed; inspect build log.'}
& $editor $projectFile ('-ExecutePythonScript='+(Join-Path $PSScriptRoot 'create_campus.py')) -unattended -nosplash -NullRHI -stdout -FullStdOutLogOutput
if ($LASTEXITCODE -ne 0) {throw 'Campus asset generation failed; inspect editor log.'}
Write-Host 'Compiled and generated campus. Launch UnrealEditor with MakmaWorld.uproject to playtest.'
