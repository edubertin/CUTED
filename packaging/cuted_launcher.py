from __future__ import annotations

import importlib.util
import multiprocessing
import os
import runpy
import sys
from pathlib import Path


def bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", str(Path(sys.executable).resolve().parent)))
    return Path(__file__).resolve().parents[1]


def install_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def prepare_runtime_environment() -> None:
    ffmpeg_dir = install_dir() / "ffmpeg"
    if ffmpeg_dir.exists():
        os.environ["PATH"] = f"{ffmpeg_dir}{os.pathsep}{os.environ.get('PATH', '')}"
    models_dir = install_dir() / "models"
    if models_dir.exists():
        os.environ.setdefault("CUTED_YOLO_MODEL_DIR", str(models_dir))


def normalized_argv(argv: list[str]) -> list[str]:
    result = argv[:]
    if len(result) > 1 and result[1].lower().endswith("cutted.py"):
        result.pop(1)
    if len(result) == 1:
        result.append("launch")
    return result


def run_python_module(argv: list[str]) -> int:
    sys.argv = argv[:]
    try:
        runpy.run_module(argv[0], run_name="__main__", alter_sys=True)
    except SystemExit as exit_info:
        if exit_info.code is None:
            return 0
        return exit_info.code if isinstance(exit_info.code, int) else 1
    return 0


def load_cutted():
    script = bundle_dir() / "tools" / "cutted" / "scripts" / "cutted.py"
    spec = importlib.util.spec_from_file_location("cutted", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Nao encontrei o CUTED em {script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["cutted"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    prepare_runtime_environment()
    # No pacote congelado, cutted.py se re-executa como `cuted.exe <cutted.py> analyze ...`
    # e o yt-dlp como `cuted.exe -m yt_dlp ...`; os dois caminhos passam por aqui.
    if len(sys.argv) > 2 and sys.argv[1] == "-m":
        return run_python_module(sys.argv[2:])
    sys.argv = normalized_argv(sys.argv)
    return load_cutted().main()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
