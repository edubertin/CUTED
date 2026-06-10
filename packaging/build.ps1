# Build do CUTED portatil (Opcao A: pacote completo).
# Uso: powershell -ExecutionPolicy Bypass -File packaging\build.ps1
# Requisitos: Python 3.12 x64 no PATH (ou definir $env:CUTED_BUILD_PYTHON).
#
# O build roda fora do OneDrive (%LOCALAPPDATA%\cuted-build) porque o sync
# atrapalha builds com milhares de arquivos. O resultado fica em
# %LOCALAPPDATA%\cuted-build\dist\CUTED.

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$repoRoot = Split-Path -Parent $PSScriptRoot
$buildRoot = Join-Path $env:LOCALAPPDATA "cuted-build"
$venvDir = Join-Path $buildRoot "venv"
$distDir = Join-Path $buildRoot "dist"
$workDir = Join-Path $buildRoot "work"
$appDir = Join-Path $distDir "CUTED"
$version = Get-Date -Format "yyyy.MM.dd"

$python = $env:CUTED_BUILD_PYTHON
if (-not $python) { $python = "python" }

Write-Host "[1/6] Preparando venv de build em $venvDir"
New-Item -ItemType Directory -Force $buildRoot | Out-Null
if (-not (Test-Path (Join-Path $venvDir "Scripts\python.exe"))) {
    & $python -m venv $venvDir
}
$venvPython = Join-Path $venvDir "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements-build.txt")

Write-Host "[2/6] Rodando PyInstaller (onedir, sem UPX)"
if (Test-Path $appDir) { Remove-Item $appDir -Recurse -Force }
& $venvPython -m PyInstaller (Join-Path $PSScriptRoot "cuted.spec") `
    --distpath $distDir --workpath $workDir --noconfirm
if (-not (Test-Path (Join-Path $appDir "cuted.exe"))) {
    throw "PyInstaller nao produziu cuted.exe em $appDir"
}

Write-Host "[3/6] FFmpeg (gyan.dev release-essentials, GPLv3)"
$ffmpegDir = Join-Path $appDir "ffmpeg"
$ffmpegZip = Join-Path $buildRoot "ffmpeg-release-essentials.zip"
if (-not (Test-Path $ffmpegZip)) {
    Invoke-WebRequest "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $ffmpegZip -UseBasicParsing
}
$ffmpegExtract = Join-Path $buildRoot "ffmpeg-extract"
if (Test-Path $ffmpegExtract) { Remove-Item $ffmpegExtract -Recurse -Force }
Expand-Archive $ffmpegZip -DestinationPath $ffmpegExtract
$ffmpegBin = Get-ChildItem $ffmpegExtract -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
New-Item -ItemType Directory -Force $ffmpegDir | Out-Null
Copy-Item $ffmpegBin.FullName $ffmpegDir
Copy-Item (Join-Path $ffmpegBin.Directory.FullName "ffprobe.exe") $ffmpegDir
$ffmpegLicense = Get-ChildItem $ffmpegExtract -Recurse -Filter "LICENSE*" | Select-Object -First 1
if ($ffmpegLicense) { Copy-Item $ffmpegLicense.FullName (Join-Path $ffmpegDir "LICENSE.txt") }
& (Join-Path $ffmpegDir "ffmpeg.exe") -version |
    Select-Object -First 1 | Out-File (Join-Path $ffmpegDir "VERSION.txt") -Encoding utf8

Write-Host "[4/6] Modelo YOLO local"
$modelSource = Join-Path $env:USERPROFILE ".cuted\models\yolo26n.pt"
if (Test-Path $modelSource) {
    $modelsDir = Join-Path $appDir "models"
    New-Item -ItemType Directory -Force $modelsDir | Out-Null
    Copy-Item $modelSource $modelsDir
} else {
    Write-Warning "yolo26n.pt nao encontrado em ~\.cuted\models. O app baixa na primeira analise."
}

Write-Host "[5/6] Licencas de terceiros e VERSION"
$licensesTarget = Join-Path $appDir "licenses"
New-Item -ItemType Directory -Force $licensesTarget | Out-Null
Copy-Item (Join-Path $PSScriptRoot "third-party-licenses\*") $licensesTarget -Recurse -Force
Set-Content (Join-Path $appDir "VERSION") $version -Encoding utf8

Write-Host "[6/6] Pronto: $appDir (versao $version)"
Write-Host "Smoke test: powershell -File packaging\smoke-test.ps1 -AppDir `"$appDir`""
