<#!
.SYNOPSIS
    Installs or removes the per-user Windows logon entry for virtuoso-bridge.

.DESCRIPTION
    Creates a shortcut in the current user's Startup folder.  The shortcut
    runs start-bridge-at-logon.ps1, which waits for networking and retries the
    bridge startup while the SSH agent becomes available.
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$startupScript = Join-Path $PSScriptRoot "start-bridge-at-logon.ps1"
$startupDirectory = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupDirectory "Virtuoso Bridge Autostart.lnk"
$powershellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"

if ($Uninstall) {
    if (Test-Path -LiteralPath $shortcutPath) {
        if ($PSCmdlet.ShouldProcess($shortcutPath, "Remove Startup shortcut")) {
            Remove-Item -LiteralPath $shortcutPath -Force
            Write-Output "Removed: $shortcutPath"
        }
    }
    else {
        Write-Output "No Startup shortcut exists: $shortcutPath"
    }
    exit 0
}

if (-not (Test-Path -LiteralPath $startupScript)) {
    throw "Autostart script not found: $startupScript"
}

if ($PSCmdlet.ShouldProcess($shortcutPath, "Create or update Startup shortcut")) {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $powershellExe
    $shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}" -InitialDelaySeconds 30' -f $startupScript
    $shortcut.WorkingDirectory = $repoRoot
    $shortcut.WindowStyle = 7
    $shortcut.Description = "Start virtuoso-bridge after Windows sign-in"
    $shortcut.Save()
    Write-Output "Installed: $shortcutPath"
}
