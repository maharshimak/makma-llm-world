# Optional Windows local-model setup

These scripts were derived from audit component 121, a separate local-model setup archive. They are optional operator tools; they do not wire an Ollama provider into the research-world application and do not replace its mock-mode setup.

Every script refuses its default invocation before external commands, HTTP requests or server startup. No installers, model weights or binaries are included. The user confirmed ownership of the source; rights remain reserved, without assigning a permissive license.

Use Windows PowerShell 5.1+ or PowerShell 7 in a session whose execution policy already permits reviewed scripts. This package never bypasses or changes policy. Review MODEL_TERMS.md, executable resolution on PATH, available disk/RAM, and the exact current upstream model tags before opting in.

Examples of deliberately selected operations:

```powershell
# Existing Ollama and server only: no download or inference.
& .\setup-llm.ps1 -AllowSetup
# Download is a separate operation requiring terms review.
& .\setup-llm.ps1 -AllowSetup -AllowDownload -AcceptModelTerms
# Optional model download only, without inference.
& .\install-ministral-8b.ps1 -AllowDownload -AcceptModelTerms
# A bounded local text request, with no download by this script.
& .\test-qwen.ps1 -AllowInference -AcceptModelTerms
```

`setup-llm.ps1` additionally accepts `-AllowInstall` for WinGet installation, `-AllowStartServer` for a loopback-bound background server, `-CheckGpu` for a native NVIDIA diagnostic, and `-AllowInference` for a bounded test. These operations are independent and opt-in. Installer agreement prompts are not silently accepted. Installation can require reopening PowerShell to refresh PATH. A started server remains running; this package does not terminate unrelated processes. Local Ollama endpoints provide no application authentication and must remain on loopback.

Inference requests use at most 32 predicted tokens, a 4096 request context, and a 60-second HTTP timeout. A timeout does not guarantee immediate cancellation of server-side work. A missing local model may cause Ollama to report an error; these test scripts do not download it automatically.

Validation: `& .\Test-Safety.ps1` parses all PowerShell files and executes only default-refusal/terms-refusal paths with external operations replaced by failing mocks. No real installer, download, server, hardware query or inference is run. Actual model compatibility and hardware performance remain unverified.
