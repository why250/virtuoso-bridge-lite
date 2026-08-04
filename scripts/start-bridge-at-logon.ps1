<#!
.SYNOPSIS
    Starts virtuoso-bridge after Windows sign-in, retrying while the network
    and SSH agent become available.
#>

[CmdletBinding()]
param(
    [int]$InitialDelaySeconds = 30,
    [int]$MaxAttempts = 6,
    [int]$RetryDelaySeconds = 15
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$bridgeExe = Join-Path $repoRoot ".venv\Scripts\virtuoso-bridge.exe"
$logDirectory = Join-Path $env:LOCALAPPDATA "virtuoso-bridge"
$logPath = Join-Path $logDirectory "autostart.log"

New-Item -ItemType Directory -Force -Path $logDirectory | Out-Null

function Write-BridgeLog([string]$Message) {
    "{0:u} {1}" -f (Get-Date), $Message |
        Tee-Object -FilePath $logPath -Append
}

if (-not (Test-Path -LiteralPath $bridgeExe)) {
    throw "Bridge executable not found: $bridgeExe"
}

Write-BridgeLog "Autostart invoked. Waiting $InitialDelaySeconds seconds."
Start-Sleep -Seconds $InitialDelaySeconds

for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    Write-BridgeLog "Attempt $attempt of ${MaxAttempts}: virtuoso-bridge start"
    & $bridgeExe start 2>&1 |
        Tee-Object -FilePath $logPath -Append

    if ($LASTEXITCODE -eq 0) {
        Write-BridgeLog "Bridge tunnel started successfully."
        exit 0
    }

    if ($attempt -lt $MaxAttempts) {
        Write-BridgeLog "Attempt failed; retrying in $RetryDelaySeconds seconds."
        Start-Sleep -Seconds $RetryDelaySeconds
    }
}

Write-BridgeLog "Bridge autostart failed after $MaxAttempts attempts."
exit 1
