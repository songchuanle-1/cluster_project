param([switch]$ExecuteRoot, [string]$Admission, [string]$AdmissionSha256, [string]$Review, [string]$ReviewSha256)
$ErrorActionPreference = 'Stop'
if (-not $ExecuteRoot) {
    Write-Output '{"status":"DEFAULT_NOP_NO_SSH_OR_MUTATION"}'
    return
}
if (-not $Admission -or -not $AdmissionSha256 -or -not $Review -or -not $ReviewSha256) {
    throw 'Real current admission and independent sync review paths and SHA256 values are required'
}
$syncHelper = Join-Path $PSScriptRoot 'deploy_cso_once.py'
$previousGitOptionalLocks = $env:GIT_OPTIONAL_LOCKS
$previousDontWriteBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    $env:GIT_OPTIONAL_LOCKS = '0'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    & python -X utf8 -B $syncHelper --execute-root --phase sync --admission $Admission --admission-sha256 $AdmissionSha256 --review $Review --review-sha256 $ReviewSha256
    if ($LASTEXITCODE -ne 0) { throw "Sync helper failed with exit code $LASTEXITCODE; preserve intent and actual, no replay" }
} finally {
    $env:GIT_OPTIONAL_LOCKS = $previousGitOptionalLocks
    $env:PYTHONDONTWRITEBYTECODE = $previousDontWriteBytecode
}
