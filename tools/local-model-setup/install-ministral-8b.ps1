param([switch]$AllowDownload,[switch]$AcceptModelTerms)
$ErrorActionPreference='Stop'
if(-not $AllowDownload){throw 'OPT_IN_REQUIRED: model download is disabled by default; supply -AllowDownload only after review.'}
if(-not $AcceptModelTerms){throw 'MODEL_TERMS_REQUIRED: review the exact Ministral model terms before downloading.'}
if(-not (Get-Command ollama -ErrorAction SilentlyContinue)){throw 'Install a reviewed Ollama version separately before downloading the optional model.'}
& ollama pull 'ministral-3:8b'
if($LASTEXITCODE -ne 0){throw "Model download failed with exit code $LASTEXITCODE; stopped."}
Write-Output 'Optional model download completed. No inference was performed.'
