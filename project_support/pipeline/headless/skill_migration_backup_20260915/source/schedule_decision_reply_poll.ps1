param(
    [Parameter(Mandatory = $true)][string]$Project,
    [Parameter(Mandatory = $true)][string]$DecisionId
)

$ErrorActionPreference = "Stop"
$skillDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $skillDir "__pycache__\poll_decision_replies.cpython-313.pyc"
$python = "C:\song_data\app\miniconda\root\python.exe"

if (-not (Test-Path -LiteralPath $runner)) {
    throw "Decision-reply runner not found: $runner"
}
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python runtime not found: $python"
}

$safeId = $DecisionId -replace "[^A-Za-z0-9_-]", "_"
$taskName = "PipelineDecisionReply-$Project-$safeId"
$start = (Get-Date).AddMinutes(1).ToString("HH:mm")
$taskRun = "`"$python`" `"$runner`" `"$Project`" `"$DecisionId`""

schtasks.exe /create /tn $taskName /tr $taskRun /sc MINUTE /mo 5 /st $start /f | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to schedule $taskName"
}

Write-Output "$taskName scheduled every 5 minutes"
