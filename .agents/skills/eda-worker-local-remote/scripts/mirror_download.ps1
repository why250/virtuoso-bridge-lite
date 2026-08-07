#Requires -Version 5.1
<#
.SYNOPSIS
  Download a list of files from a remote eda-worker directory via ops.download.

.DESCRIPTION
  ops has no recursive directory download. List remote file names first
  (MCP file_list or shell find), then call this script.

  Prefer invoking with the call operator (keeps -Files arrays intact):

    & .\mirror_download.ps1 -RemoteDir "..." -LocalDir "..." -Files @("a", "b")

  Avoid nesting `powershell -File ... -Files @(...)` — PowerShell -File only
  binds the first array element. This script collects the rest via
  ValueFromRemainingArguments. Pass host only as -WorkerHost <ip>.

.PARAMETER RemoteDir
  Absolute remote directory (no trailing slash required).

.PARAMETER LocalDir
  Local destination directory (created if missing).

.PARAMETER Files
  File names only (not paths), relative to RemoteDir.

.PARAMETER WorkerHost
  Optional worker host for ops.download --host (when mcp.json has multiple workers).
  Named-only: -WorkerHost <ip>.

.EXAMPLE
  & .\mirror_download.ps1 `
    -RemoteDir "/home/eda_grp/weihaoyu/example/cell/output/runs/id/01_sim" `
    -LocalDir ".\example\cell\output\runs\id\01_sim" `
    -Files @("hpeesofsim_stdout.log", "cell.ds")
#>
[CmdletBinding()]
param(
    # Explicit Position on the three primary params makes later params named-only
    # (PS 5.1), so leftover -Files names are not stolen by -WorkerHost.
    [Parameter(Mandatory = $true, Position = 0)]
    [string] $RemoteDir,

    [Parameter(Mandatory = $true, Position = 1)]
    [string] $LocalDir,

    [Parameter(Mandatory = $true, Position = 2)]
    [string[]] $Files,

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $RemainingFiles = @(),

    [Parameter(Mandatory = $false)]
    [string] $WorkerHost = ""
)

$ErrorActionPreference = "Stop"

function Normalize-FileList {
    param([string[]] $Names)
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($n in $Names) {
        if ([string]::IsNullOrWhiteSpace($n)) { continue }
        if ($n -match ',') {
            foreach ($part in ($n -split '\s*,\s*')) {
                if (-not [string]::IsNullOrWhiteSpace($part)) {
                    $out.Add($part.Trim().Trim('"'))
                }
            }
        }
        else {
            $out.Add($n.Trim().Trim('"'))
        }
    }
    return , $out.ToArray()
}

$RemoteDir = $RemoteDir.TrimEnd("/", "\")
$Files = Normalize-FileList -Names (@($Files) + @($RemainingFiles))
if (-not $Files -or $Files.Count -eq 0) {
    throw "Files list is empty. Obtain names via MCP file_list or find first."
}

New-Item -ItemType Directory -Force -Path $LocalDir | Out-Null

$failed = @()
foreach ($name in $Files) {
    $base = [System.IO.Path]::GetFileName($name)
    if ([string]::IsNullOrWhiteSpace($base)) {
        Write-Warning "Skipping empty file name entry."
        continue
    }

    $remote = "$RemoteDir/$base"
    $local = Join-Path $LocalDir $base

    $pyArgs = @("-m", "ops.download")
    if (-not [string]::IsNullOrWhiteSpace($WorkerHost)) {
        $pyArgs += @("--host", $WorkerHost)
    }
    $pyArgs += @($remote, $local)

    Write-Host "ops.download $remote -> $local"
    & python @pyArgs
    if ($LASTEXITCODE -ne 0) {
        $failed += $base
        Write-Warning "Download failed (exit $LASTEXITCODE): $base"
    }
}

if ($failed.Count -gt 0) {
    throw ("Failed to download {0} file(s): {1}" -f $failed.Count, ($failed -join ", "))
}

Write-Host "OK: mirrored $($Files.Count) file(s) to $LocalDir"
