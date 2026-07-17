# PyInstaller spec do CUTED (Opcao A: pacote completo com YOLO/torch CPU).
# Build: pyinstaller packaging/cuted.spec --distpath <fora-do-OneDrive> --workpath <fora-do-OneDrive>
#
# Decisoes:
# - onedir, sem UPX: menos falso positivo de antivirus e start mais rapido.
# - cutted.py entra como DATA (arquivo real em _internal/tools/...), carregado
#   pelo cuted_launcher via importlib. Isso preserva __file__ real, faz
#   assets/brand resolver pelo layout do repositorio e permite hotfix trocando
#   um unico arquivo.
# - Como cutted.py e carregado dinamicamente, TODAS as dependencias dele
#   precisam ser declaradas aqui (collect_all/hiddenimports).

from PyInstaller.utils.hooks import collect_all
from pathlib import Path

SPEC_DIR = Path(SPECPATH).resolve()
REPO_ROOT = SPEC_DIR.parent
SCRIPT_DIR = REPO_ROOT / "tools" / "cutted" / "scripts"

datas = [
    (str(REPO_ROOT / "tools" / "cutted" / "scripts" / "cutted.py"), "tools/cutted/scripts"),
    *[(str(path), "tools/cutted/scripts") for path in sorted(SCRIPT_DIR.glob("cuted_*.py"))],
    (str(REPO_ROOT / "assets" / "brand" / "cuted-logo-transparent.png"), "assets/brand"),
    (str(REPO_ROOT / "assets" / "brand" / "cuted-logo-official.png"), "assets/brand"),
    (str(REPO_ROOT / "assets" / "brand" / "cuted-app-icon.png"), "assets/brand"),
    (str(REPO_ROOT / "assets" / "brand" / "cuted-app-icon.ico"), "assets/brand"),
]
binaries = []
# cutted.py e carregado em runtime via importlib, entao o PyInstaller nao
# enxerga os imports dele; stdlib usada so pelo cutted.py entra manualmente.
hiddenimports = [
    "tkinter",
    "tkinter.filedialog",
    "http.server",
    "http.client",
    "socketserver",
    "webbrowser",
]

for package in ("ultralytics", "torch", "cv2", "faster_whisper", "yt_dlp", "imageio_ffmpeg", "webview"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

a = Analysis(
    [str(SPEC_DIR / "cuted_launcher.py")],
    pathex=[str(SPEC_DIR), str(REPO_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "pandas",
        "scipy",
        "IPython",
        "notebook",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "tensorboard",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="cuted",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    icon=str(REPO_ROOT / "assets" / "brand" / "cuted-app-icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="CUTED",
)
