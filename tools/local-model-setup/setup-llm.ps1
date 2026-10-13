param(
    [switch]$AllowSetup,
    [switch]$AllowInstall,
    [switch]$AllowStartServer,
    [switch]$AllowDownload,
    [switch]$AllowInference,
    [switch]$AcceptModelTerms,
    [switch]$CheckGpu,
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9:_.-]{0,99}$')][string]$Model='qwen3:4b-q4_K_M'
)
$ErrorActionPreference='Stop'
if(-not $AllowSetup){throw 'OPT_IN_REQUIRED: setup is disabled by default. Review README.md and supply -AllowSetup plus individual operation switches.'}
if(($AllowDownload -or $AllowInference) -and -not $AcceptModelTerms){throw 'MODEL_TERMS_REQUIRED: review the exact model terms before download or inference.'}

function Invoke-CheckedNative([string]$Command,[string[]]$Arguments){
    & $Command @Arguments
    if($LASTEXITCODE -ne 0){throw "$Command failed with exit code $LASTEXITCODE; stopped."}
}
if($CheckGpu){
    if(Get-Command nvidia-smi -ErrorAction SilentlyContinue){Invoke-CheckedNative 'nvidia-smi' @('--query-gpu=name,memory.total,driver_version','--format=csv,noheader')}
}
if(-not (Get-Command ollama -ErrorAction SilentlyContinue)){
    if(-not $AllowInstall){throw 'INSTALL_OPT_IN_REQUIRED: Ollama is absent; installation requires -AllowInstall.'}
    if(-not (Get-Command winget -ErrorAction SilentlyContinue)){throw 'WinGet is unavailable. Review the official Ollama Windows installation instructions.'}
    # Agreement prompts remain interactive; this script does not accept them silently.
    Invoke-CheckedNative 'winget' @('install','--id','Ollama.Ollama','--exact','--source','winget')
    if(-not (Get-Command ollama -ErrorAction SilentlyContinue)){throw 'Reopen PowerShell after installation so the reviewed Ollama executable is on PATH.'}
}
$endpoint='http://127.0.0.1:11434'
try {Invoke-RestMethod -Uri "$endpoint/api/tags" -Method Get -TimeoutSec 3 | Out-Null}
catch {
    if(-not $AllowStartServer){throw 'SERVER_OPT_IN_REQUIRED: local Ollama is unreachable; starting a server requires -AllowStartServer.'}
    $previousHost=$env:OLLAMA_HOST
    try {
        $env:OLLAMA_HOST='127.0.0.1:11434'
        Start-Process -FilePath 'ollama' -ArgumentList 'serve' -WindowStyle Hidden | Out-Null
    } finally {$env:OLLAMA_HOST=$previousHost}
    Start-Sleep -Seconds 3
    Invoke-RestMethod -Uri "$endpoint/api/tags" -Method Get -TimeoutSec 5 | Out-Null
}
if($AllowDownload){Invoke-CheckedNative 'ollama' @('pull',$Model)}
if($AllowInference){
    $body=@{model=$Model;stream=$false;keep_alive=0;messages=@(@{role='user';content='Reply with exactly MAKMA_LOCAL_LLM_READY'});options=@{temperature=0;num_ctx=4096;num_predict=32}}|ConvertTo-Json -Depth 6
    $response=Invoke-RestMethod -Uri "$endpoint/api/chat" -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 60
    Write-Output $response.message.content
}
Write-Output 'Selected setup operations completed. No skipped download or inference was performed.'
