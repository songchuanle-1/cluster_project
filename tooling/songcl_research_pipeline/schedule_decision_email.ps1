param(
    [Parameter(Mandatory = $true)][string]$Project,
    [Parameter(Mandatory = $true)][string]$DecisionId
)

$ErrorActionPreference = "Stop"
$skillDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $skillDir "__pycache__\pending_decision_email.cpython-313.pyc"
$python = "C:\song_data\app\miniconda\root\python.exe"

if (-not (Test-Path -LiteralPath $runner)) {
    throw "Pending-decision email runner not found: $runner"
}
if (-not (Test-Path -LiteralPath $python)) {
    throw "Python runtime not found: $python"
}

$safeId = $DecisionId -replace "[^A-Za-z0-9_-]", "_"
$taskName = "PipelineDecisionMail-$Project-$safeId"
$runAt = (Get-Date).AddMinutes(30)
$date = $runAt.ToString("yyyy/MM/dd")
$time = $runAt.ToString("HH:mm")
$taskRun = "`"$python`" `"$runner`" `"$Project`" `"$DecisionId`""

schtasks.exe /create /tn $taskName /tr $taskRun /sc ONCE /sd $date /st $time /f | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to schedule $taskName"
}

Write-Output "$taskName scheduled for $($runAt.ToString('s'))"
