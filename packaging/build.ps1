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
$ffmpegVersion = "8.1.2"
$ffmpegUrl = "https://github.com/GyanD/codexffmpeg/releases/download/8.1.2/ffmpeg-8.1.2-essentials_build.zip"
$ffmpegExpectedSha256 = "DB580001CAA24AC104C8CB856CD113A87B0A443F7BDF47D8C12B1D740584A2EC"
$modelUrl = "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt"
$modelExpectedSha256 = "9B09CC8BF347F0FC8A5F7657480587F25DB09B34BF33B0652110FB03A8AD4FEF"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

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
    Invoke-WebRequest $ffmpegUrl -OutFile $ffmpegZip -UseBasicParsing
}
$ffmpegSha256 = (Get-FileHash -LiteralPath $ffmpegZip -Algorithm SHA256).Hash
if ($ffmpegSha256 -ne $ffmpegExpectedSha256) {
    throw "FFmpeg archive hash changed. Expected $ffmpegExpectedSha256, got $ffmpegSha256."
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
$ffmpegReadme = Get-ChildItem $ffmpegExtract -Recurse -Filter "README.txt" | Select-Object -First 1
if ($ffmpegReadme) { Copy-Item $ffmpegReadme.FullName (Join-Path $ffmpegDir "README.txt") }
$ffmpegVersionLine = & (Join-Path $ffmpegDir "ffmpeg.exe") -version | Select-Object -First 1
if ($ffmpegVersionLine -notmatch [regex]::Escape($ffmpegVersion)) {
    throw "Unexpected FFmpeg version: $ffmpegVersionLine"
}
[IO.File]::WriteAllText((Join-Path $ffmpegDir "VERSION.txt"), "$ffmpegVersionLine`n", $utf8NoBom)
$ffmpegSource = @"
Binary archive: $ffmpegUrl
Binary SHA-256: $ffmpegSha256
FFmpeg source commit: https://github.com/FFmpeg/FFmpeg/commit/38b88335f9
Build release: https://github.com/GyanD/codexffmpeg/releases/tag/$ffmpegVersion
Build configuration and external-library versions: README.txt
Release requirement: provide corresponding sources for FFmpeg and enabled GPL libraries beside every public binary.
"@
[IO.File]::WriteAllText((Join-Path $ffmpegDir "SOURCE.txt"), "$ffmpegSource`n", $utf8NoBom)

Write-Host "[4/6] Modelo YOLO local"
$modelSource = Join-Path $env:USERPROFILE ".cuted\models\yolo26n.pt"
if (-not (Test-Path $modelSource)) {
    New-Item -ItemType Directory -Force (Split-Path $modelSource -Parent) | Out-Null
    Invoke-WebRequest $modelUrl -OutFile $modelSource -UseBasicParsing
}
$modelSha256 = (Get-FileHash -LiteralPath $modelSource -Algorithm SHA256).Hash
if ($modelSha256 -ne $modelExpectedSha256) {
    throw "YOLO model hash changed. Expected $modelExpectedSha256, got $modelSha256."
}
$modelsDir = Join-Path $appDir "models"
New-Item -ItemType Directory -Force $modelsDir | Out-Null
Copy-Item $modelSource $modelsDir
$modelSourceText = "Source: $modelUrl`nSHA-256: $modelSha256`nLicense: AGPL-3.0`n"
[IO.File]::WriteAllText((Join-Path $modelsDir "SOURCE.txt"), $modelSourceText, $utf8NoBom)

Write-Host "[5/6] Licencas de terceiros e VERSION"
$licensesTarget = Join-Path $appDir "licenses"
New-Item -ItemType Directory -Force $licensesTarget | Out-Null
Copy-Item (Join-Path $PSScriptRoot "third-party-licenses\*") $licensesTarget -Recurse -Force
Copy-Item (Join-Path $repoRoot "LICENSE") (Join-Path $licensesTarget "CUTED-AGPL-3.0.txt") -Force
Copy-Item (Join-Path $repoRoot "COPYRIGHT.md") $licensesTarget -Force
Copy-Item (Join-Path $repoRoot "THIRD_PARTY_NOTICES.md") $licensesTarget -Force
Copy-Item (Join-Path $repoRoot "LICENSES") $licensesTarget -Recurse -Force
$pythonLicenses = Join-Path $licensesTarget "python"
& $venvPython (Join-Path $PSScriptRoot "collect-third-party-licenses.py") --out $pythonLicenses
[IO.File]::WriteAllText((Join-Path $appDir "VERSION"), "$version`n", $utf8NoBom)

Write-Host "[6/6] Pronto: $appDir (versao $version)"
Write-Host "Smoke test: powershell -File packaging\smoke-test.ps1 -AppDir `"$appDir`""
