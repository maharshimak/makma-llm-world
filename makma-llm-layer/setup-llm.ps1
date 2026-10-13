$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================================"
Write-Host "            MAK'MA LOCAL LLM LAYER SETUP"
Write-Host "========================================================"
Write-Host ""

# 1. Show NVIDIA GPU if present
Write-Host "[1/6] Checking GPU..."
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
} else {
    Write-Host "nvidia-smi not found. Ollama can still run with CPU/system RAM."
}

# 2. Install Ollama if missing
Write-Host ""
Write-Host "[2/6] Checking Ollama..."
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "WinGet is not available. Install Ollama from https://ollama.com/download/windows and rerun this script."
    }

    Write-Host "Installing Ollama..."
    winget install --id Ollama.Ollama --exact --accept-package-agreements --accept-source-agreements

    # Refresh PATH for common Ollama location in the current shell.
    $ollamaPath = Join-Path $env:LOCALAPPDATA "Programs\Ollama"
    if (Test-Path $ollamaPath) {
        $env:Path = "$ollamaPath;$env:Path"
    }
} else {
    Write-Host "Ollama is already installed."
}

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "Ollama was installed but is not yet visible in this PowerShell session. Close PowerShell, reopen it, and run setup-llm.ps1 again."
}

# 3. Ensure local Ollama server is reachable
Write-Host ""
Write-Host "[3/6] Checking Ollama local API..."
$serverReady = $false
try {
    Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3 | Out-Null
    $serverReady = $true
} catch {
    Write-Host "Starting Ollama server..."
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 4

    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 5 | Out-Null
        $serverReady = $true
    } catch {
        throw "Could not start or reach Ollama at http://127.0.0.1:11434"
    }
}

if ($serverReady) {
    Write-Host "Ollama API is running locally."
}

# 4. Pull the default model
$model = "qwen3:4b-q4_K_M"

Write-Host ""
Write-Host "[4/6] Downloading Mak'ma default brain: $model"
ollama pull $model

# 5. Verify installation
Write-Host ""
Write-Host "[5/6] Verifying installed models..."
ollama list

# 6. Run a short test through the local HTTP API
Write-Host ""
Write-Host "[6/6] Testing local inference..."

$body = @{
    model = $model
    stream = $false
    messages = @(
        @{
            role = "system"
            content = "You are the local reasoning core for Mak'ma, a multi-agent research system. Be concise."
        },
        @{
            role = "user"
            content = "Reply with exactly: MAKMA_LOCAL_LLM_READY"
        }
    )
    options = @{
        temperature = 0
        num_ctx = 4096
    }
} | ConvertTo-Json -Depth 8

$response = Invoke-RestMethod `
    -Uri "http://127.0.0.1:11434/api/chat" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body `
    -TimeoutSec 300

Write-Host ""
Write-Host "Model response:"
Write-Host $response.message.content

Write-Host ""
Write-Host "========================================================"
Write-Host " MAK'MA LLM LAYER IS INSTALLED"
Write-Host "========================================================"
Write-Host ""
Write-Host "Default model: $model"
Write-Host "Local endpoint: http://127.0.0.1:11434"
Write-Host ""
Write-Host "Start interactive chat:"
Write-Host "  ollama run $model"
Write-Host ""
Write-Host "Next Mak'ma layer:"
Write-Host "  Agent Kernel -> private memory -> research tools -> evaluator"
Write-Host ""
