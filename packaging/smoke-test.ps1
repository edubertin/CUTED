# Smoke test do build portatil do CUTED.
# Uso: powershell -ExecutionPolicy Bypass -File packaging\smoke-test.ps1 -AppDir "<dist>\CUTED"
#
# Valida o criterio de paridade da Opcao A: o pacote precisa subir o workspace,
# responder a API local e ter FFmpeg + YOLO disponiveis. A parte de render/
# Smart Camera com video real continua manual (checklist no final).

param(
    [Parameter(Mandatory = $true)][string]$AppDir
)

$ErrorActionPreference = "Stop"
$failures = @()

function Check([string]$name, [bool]$ok) {
    if ($ok) { Write-Host "[PASS] $name" } else { Write-Host "[FAIL] $name"; $script:failures += $name }
}

$exe = Join-Path $AppDir "cuted.exe"
Check "cuted.exe existe" (Test-Path $exe)
Check "ffmpeg.exe embarcado" (Test-Path (Join-Path $AppDir "ffmpeg\ffmpeg.exe"))
Check "ffprobe.exe embarcado" (Test-Path (Join-Path $AppDir "ffmpeg\ffprobe.exe"))
Check "modelo YOLO embarcado" (Test-Path (Join-Path $AppDir "models\yolo26n.pt"))
Check "cutted.py como data file" (Test-Path (Join-Path $AppDir "_internal\tools\cutted\scripts\cutted.py"))
Check "logo da marca embarcado" (Test-Path (Join-Path $AppDir "_internal\assets\brand\cuted-logo-transparent.png"))
Check "licencas presentes" (Test-Path (Join-Path $AppDir "licenses"))

Write-Host "Verificando o shim de re-execucao (-m) usado por imports e yt-dlp..."
$shimOutput = & $exe -m platform 2>&1 | Out-String
Check "shim -m executa modulos python" ($shimOutput -match "Windows")

Write-Host "Verificando dependencia da shell desktop..."
$shellOutput = & $exe desktop-shell-check --json 2>&1 | Out-String
$shellExit = $LASTEXITCODE
Check "desktop shell pywebview disponivel" ($shellExit -eq 0 -and $shellOutput -match '"ok": true' -and $shellOutput -match '"renderer": "edgechromium"')

$workspace = Join-Path $env:TEMP "cuted-smoke-workspace"
if (Test-Path $workspace) { Remove-Item $workspace -Recurse -Force }
$lock = Join-Path $env:LOCALAPPDATA "CUTED\cuted-launch.lock"
if (Test-Path $lock) { Remove-Item $lock -Force }

Write-Host "Iniciando cuted.exe launch --no-browser (aguardando ate 90s pelo cold start)..."
$proc = Start-Process -FilePath $exe -ArgumentList "launch", "--no-browser", "--workspace", $workspace -PassThru -WindowStyle Hidden
$deadline = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $deadline) {
    if ($proc.HasExited) { break }
    if ((Test-Path $lock) -and (Get-Content $lock -ErrorAction SilentlyContinue)) { break }
    Start-Sleep -Seconds 2
}

try {
    Check "processo segue vivo" (-not $proc.HasExited)
    Check "lock file criado" (Test-Path $lock)
    $port = (Get-Content $lock -ErrorAction Stop).Trim()
    $index = Invoke-WebRequest "http://127.0.0.1:$port/index.html" -UseBasicParsing -TimeoutSec 10
    Check "galeria responde (HTTP 200)" ($index.StatusCode -eq 200)
    $api = Invoke-WebRequest "http://127.0.0.1:$port/api/settings/openai" -UseBasicParsing -TimeoutSec 10
    Check "API local responde" ($api.StatusCode -eq 200)
    Check "workspace index.html criado" (Test-Path (Join-Path $workspace "index.html"))
} catch {
    Check "servidor local subiu" $false
    Write-Host $_
} finally {
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
    if (Test-Path $lock) { Remove-Item $lock -Force }
    if (Test-Path $workspace) { Remove-Item $workspace -Recurse -Force }
}

Write-Host ""
if ($failures.Count -gt 0) {
    Write-Host "SMOKE TEST FALHOU: $($failures -join '; ')" -ForegroundColor Red
    exit 1
}
Write-Host "SMOKE TEST AUTOMATICO OK." -ForegroundColor Green
Write-Host ""
Write-Host "Checklist manual obrigatorio antes de distribuir (maquina limpa, sem Python):"
Write-Host " 1. Duplo clique em cuted.exe abre a janela desktop do CUTED."
Write-Host " 2. Importar um MP4 local com pasta de destino escolhida."
Write-Host " 3. Rodar Smart Camera e conferir diagnostics.vision_engine == hybrid-yolo."
Write-Host " 4. Renderizar um TikTok final com legenda e conferir o MP4 no destino."
Write-Host " 5. Fechar e reabrir: o projeto continua acessivel."
exit 0
