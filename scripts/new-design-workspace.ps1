<#!
.SYNOPSIS
    Creates a design-project workspace that inherits this repository's bridge setup.

.EXAMPLE
    .\scripts\new-design-workspace.ps1 -Name my_adc
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory, Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string]$Name
)

$ErrorActionPreference = "Stop"

$projectName = $Name.Trim()
$invalidName = (
    $projectName -in @(".", "..") -or
    [System.IO.Path]::GetFileName($projectName) -ne $projectName -or
    $projectName.IndexOfAny([System.IO.Path]::GetInvalidFileNameChars()) -ge 0
)
if ($invalidName) {
    throw "Name must be a single valid directory name, not a path: $Name"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Join-Path $repoRoot "workspace"
$projectRoot = Join-Path $workspaceRoot $projectName

if (Test-Path -LiteralPath $projectRoot) {
    throw "Project directory already exists: $projectRoot"
}

if ($PSCmdlet.ShouldProcess($projectRoot, "Create design workspace")) {
    New-Item -ItemType Directory -Path $projectRoot | Out-Null
    foreach ($directory in @("scripts", "results", "notes")) {
        New-Item -ItemType Directory -Path (Join-Path $projectRoot $directory) | Out-Null
    }

    $readmePath = Join-Path $projectRoot "README.md"
    @(
        "# $projectName",
        "",
        "This design project lives under the virtuoso-bridge-lite workspace. Work",
        "from the bridge repository root so this project inherits its AGENTS.md,",
        ".env, virtual environment, prompt templates, and remote Virtuoso connection.",
        "",
        "## New conversation prompt",
        "",
        "Work in $repoRoot.",
        "Current design project: workspace/$projectName.",
        "Read AGENTS.md, then run the non-mutating Virtuoso bridge probe",
        'VirtuosoClient.from_env().execute_skill("1+1") before making changes.',
        "Task: <describe the desired result>."
    ) | Set-Content -LiteralPath $readmePath -Encoding utf8
}

@(
    "Created design project: $projectRoot",
    "",
    "Start a new conversation with:",
    "",
    "Work in $repoRoot.",
    "Current design project: workspace/$projectName.",
    "Read AGENTS.md, then run the non-mutating Virtuoso bridge probe",
    'VirtuosoClient.from_env().execute_skill("1+1") before making changes.',
    "Task: <describe the desired result>."
) | Write-Output
