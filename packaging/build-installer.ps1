# Compila o instalador Inno Setup do CUTED sem gravar artefatos no repositorio.
# Uso:
#   powershell -ExecutionPolicy Bypass -File packaging\build-installer.ps1
#   powershell -ExecutionPolicy Bypass -File packaging\build-installer.ps1 -IsccPath "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

param(
    [string]$AppDir,
    [string]$OutputDir,
    [string]$AppVersion,
    [string]$IsccPath
)

$ErrorActionPreference = "Stop"

$buildRoot = Join-Path $env:LOCALAPPDATA "cuted-build"
if (-not $AppDir) {
    $AppDir = Join-Path $buildRoot "dist\CUTED"
}
if (-not $OutputDir) {
    $OutputDir = Join-Path $buildRoot "installer"
}
if (-not $AppVersion) {
    $versionFile = Join-Path $AppDir "VERSION"
    if (Test-Path $versionFile) {
        $AppVersion = (Get-Content $versionFile -Raw).Trim()
    } else {
        $AppVersion = Get-Date -Format "yyyy.MM.dd"
    }
}

function Find-Iscc {
    param([string]$ExplicitPath)
    if ($ExplicitPath) {
        if (Test-Path $ExplicitPath) { return (Resolve-Path $ExplicitPath).Path }
        throw "ISCC.exe nao encontrado em $ExplicitPath"
    }
    $command = Get-Command "iscc.exe" -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) { return $candidate }
    }
    throw "Inno Setup nao encontrado. Instale o Inno Setup 6 ou passe -IsccPath para ISCC.exe."
}

if (-not (Test-Path (Join-Path $AppDir "cuted.exe"))) {
    throw "Build portatil nao encontrado em $AppDir. Rode packaging\build.ps1 primeiro."
}

$iscc = Find-Iscc $IsccPath
New-Item -ItemType Directory -Force $OutputDir | Out-Null

$installerScript = Join-Path $PSScriptRoot "installer.iss"
Write-Host "Compilando instalador CUTED $AppVersion"
Write-Host "AppDir: $AppDir"
Write-Host "OutputDir: $OutputDir"
& $iscc $installerScript "/DAppDir=$AppDir" "/DAppVersion=$AppVersion" "/O$OutputDir"

$expected = Join-Path $OutputDir "CUTED-Setup-$AppVersion.exe"
if (-not (Test-Path $expected)) {
    throw "ISCC terminou, mas nao encontrei $expected"
}
$checksum = (Get-FileHash -LiteralPath $expected -Algorithm SHA256).Hash
$checksumFile = "$expected.sha256"
[IO.File]::WriteAllText(
    $checksumFile,
    "$checksum  $([IO.Path]::GetFileName($expected))`n",
    (New-Object System.Text.UTF8Encoding($false))
)
Write-Host "Instalador pronto: $expected"
Write-Host "SHA-256: $checksumFile"
