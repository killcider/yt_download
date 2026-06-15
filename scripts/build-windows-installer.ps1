Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Require-Command {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name,
        [Parameter(Mandatory = $true)]
        [string] $InstallHint
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name was not found. $InstallHint"
    }
}

Require-Command "uv" "Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
Require-Command "iscc" "Install Inno Setup and make sure iscc.exe is available in PATH."

Write-Host "Installing locked dependencies..."
uv sync --all-groups

Write-Host "Building bundled Windows app..."
uv run pyinstaller packaging/social-video-download.spec --noconfirm --clean

Write-Host "Building one-click installer..."
iscc packaging/windows-installer.iss

$InstallerPath = Join-Path $ProjectRoot "dist\installer\Social-Video-Download-Setup.exe"
Write-Host ""
Write-Host "Done: $InstallerPath"
