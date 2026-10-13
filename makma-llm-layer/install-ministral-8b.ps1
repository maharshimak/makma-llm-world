$ErrorActionPreference = "Stop"

$model = "ministral-3:8b"

Write-Host ""
Write-Host "Installing optional stronger Mak'ma brain: $model"
Write-Host "This Ollama package is roughly 6 GB and is heavier than Qwen3 4B."
Write-Host ""

ollama pull $model

Write-Host ""
Write-Host "Installed models:"
ollama list

Write-Host ""
Write-Host "Test it with:"
Write-Host "  ollama run ministral-3:8b"
