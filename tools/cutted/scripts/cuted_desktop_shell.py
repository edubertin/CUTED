from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType
from typing import Callable


def desktop_shell_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/index.html"


def desktop_storage_path(data_dir: Path) -> str:
    storage = data_dir / "webview"
    storage.mkdir(parents=True, exist_ok=True)
    return str(storage)


def load_webview() -> ModuleType | None:
    try:
        return importlib.import_module("webview")
    except ImportError:
        return None


def open_desktop_shell(
    host: str,
    port: int,
    data_dir: Path,
    log_message: Callable[[str], None] | None = None,
) -> bool:
    webview = load_webview()
    if webview is None:
        if log_message is not None:
            log_message("desktop shell unavailable: pywebview is not installed")
        return False
    try:
        webview.create_window(
            "CUTED",
            desktop_shell_url(host, port),
            width=1280,
            height=820,
            min_size=(1024, 700),
            background_color="#050807",
            text_select=True,
        )
        webview.start(gui="edgechromium", private_mode=False, storage_path=desktop_storage_path(data_dir))
    except Exception as error:
        if log_message is not None:
            log_message(f"desktop shell failed: {error}")
        return False
    return True
