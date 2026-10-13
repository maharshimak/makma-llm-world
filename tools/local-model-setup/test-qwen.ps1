param([switch]$AllowInference,[switch]$AcceptModelTerms)
$ErrorActionPreference='Stop'
if(-not $AllowInference){throw 'OPT_IN_REQUIRED: inference is disabled by default; supply -AllowInference only after review.'}
if(-not $AcceptModelTerms){throw 'MODEL_TERMS_REQUIRED: review the exact Qwen model terms before inference.'}
$body=@{model='qwen3:4b-q4_K_M';stream=$false;keep_alive=0;messages=@(@{role='user';content='Reply with exactly MAKMA_LOCAL_LLM_READY'});options=@{temperature=0;num_ctx=4096;num_predict=32}}|ConvertTo-Json -Depth 6
$response=Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/chat' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 60
Write-Output $response.message.content
