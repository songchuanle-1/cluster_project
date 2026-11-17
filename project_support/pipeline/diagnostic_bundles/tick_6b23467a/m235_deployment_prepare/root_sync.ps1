param([switch]$ExecuteRoot, [string]$Review, [string]$ReviewSha256)
$ErrorActionPreference = 'Stop'
if (-not $ExecuteRoot) {
    Write-Output '{"status":"DEFAULT_NOP_NO_SSH_OR_MUTATION"}'
    return
}
if (-not $Review -or -not $ReviewSha256) { throw 'A genuine frozen-packet peer review path and SHA256 are required' }
$syncHelper = Join-Path $PSScriptRoot 'deploy_m235_once.py'
$previousGitOptionalLocks = $env:GIT_OPTIONAL_LOCKS
$previousDontWriteBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
    $env:GIT_OPTIONAL_LOCKS = '0'
    $env:PYTHONDONTWRITEBYTECODE = '1'
    & python -X utf8 -B $syncHelper --execute-root --phase sync --admission 'D:/project/cluster_project/pipeline/admissions/M235-SINC.json' --admission-sha256 'ab1bc5d187022e26dbcbc1063c24a886c7429350739039aff06f51c1bbcb5169' --review $Review --review-sha256 $ReviewSha256
    if ($LASTEXITCODE -ne 0) { throw "Sync helper failed with exit code $LASTEXITCODE; preserve intent and actual, no replay" }
} finally {
    $env:GIT_OPTIONAL_LOCKS = $previousGitOptionalLocks
    $env:PYTHONDONTWRITEBYTECODE = $previousDontWriteBytecode
}
