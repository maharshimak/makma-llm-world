$ErrorActionPreference = "Stop"
$model = "qwen3:4b-q4_K_M"

Write-Host "Testing $model..."
Write-Host ""

ollama run $model "You are Mak'ma's research brain. Give exactly three short bullet points explaining how multiple autonomous research agents can share one LLM while retaining separate memories."
