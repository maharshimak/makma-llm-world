$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$scripts=@(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1')
foreach($script in $scripts){
    [Management.Automation.Language.Parser]::ParseFile($script.FullName,[ref]$tokens,[ref]$errors)|Out-Null
    if($errors.Count){throw "PowerShell syntax errors: $($script.Name)"}
}
$script:externalCalls=0
function Get-Command {$script:externalCalls++;throw 'MOCK_EXTERNAL_OPERATION_FORBIDDEN'}
function Invoke-RestMethod {$script:externalCalls++;throw 'MOCK_EXTERNAL_OPERATION_FORBIDDEN'}
function Start-Process {$script:externalCalls++;throw 'MOCK_EXTERNAL_OPERATION_FORBIDDEN'}
function Start-Sleep {$script:externalCalls++;throw 'MOCK_EXTERNAL_OPERATION_FORBIDDEN'}
function ollama {$script:externalCalls++;throw 'MOCK_EXTERNAL_OPERATION_FORBIDDEN'}
function winget {$script:externalCalls++;throw 'MOCK_EXTERNAL_OPERATION_FORBIDDEN'}
function nvidia-smi {$script:externalCalls++;throw 'MOCK_EXTERNAL_OPERATION_FORBIDDEN'}
$checks=0
foreach($name in @('setup-llm.ps1','install-ministral-8b.ps1','test-qwen.ps1')){
    $refused=$false
    try {& (Join-Path $PSScriptRoot $name)} catch {if($_.Exception.Message -match '^OPT_IN_REQUIRED:'){$refused=$true}else{throw}}
    if(-not $refused){throw "Default operation did not refuse: $name"}
    $checks++
}
$cases=@(
    @{Name='setup-llm.ps1';Arguments=@{AllowSetup=$true;AllowDownload=$true}},
    @{Name='setup-llm.ps1';Arguments=@{AllowSetup=$true;AllowInference=$true}},
    @{Name='install-ministral-8b.ps1';Arguments=@{AllowDownload=$true}},
    @{Name='test-qwen.ps1';Arguments=@{AllowInference=$true}}
)
foreach($case in $cases){
    $refused=$false;$arguments=$case.Arguments
    try {& (Join-Path $PSScriptRoot $case.Name) @arguments} catch {if($_.Exception.Message -match '^MODEL_TERMS_REQUIRED:'){$refused=$true}else{throw}}
    if(-not $refused){throw 'Terms opt-in did not refuse an unreviewed operation'}
    $checks++
}
if($script:externalCalls -ne 0){throw 'An external operation was attempted during refusal tests'}
[pscustomobject]@{PowerShellFilesParsed=$scripts.Count;RefusalChecksPassed=$checks;ExternalCalls=$script:externalCalls;ActualInstallDownloadInference=$false}|ConvertTo-Json
