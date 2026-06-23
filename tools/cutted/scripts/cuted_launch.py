from __future__ import annotations

import http.client
import os
import socket
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
from typing import Callable


def prepare_workspace_dir(value: Path | None, default_workspace: Path) -> Path:
    workspace = (value or default_workspace).expanduser().resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def default_workspace_dir() -> Path:
    return Path.home() / "Documents" / "CUTED Workspace"


def launch_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".cuted")
    return Path(base) / "CUTED"


def launch_lock_path(data_dir: Path) -> Path:
    return data_dir / "cuted-launch.lock"


def append_launch_log(data_dir: Path, message: str) -> None:
    logs_dir = data_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with (logs_dir / "cuted-launch.log").open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


def running_workspace_port(
    lock_path: Path,
    host: str,
    server_alive: Callable[[str, int], bool],
    log_message: Callable[[str], None],
) -> int | None:
    if not lock_path.exists():
        return None
    try:
        port = int(lock_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    if server_alive(host, port):
        return port
    try:
        lock_path.unlink()
    except OSError as error:
        log_message(f"stale lock cleanup failed: {error}")
    return None


def cuted_server_alive(host: str, port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/api/settings/openai", timeout=1.5) as response:
            return response.status == 200
    except (OSError, http.client.HTTPException):
        return False


def find_free_port(host: str, port_range: range) -> int:
    for port in port_range:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            if probe.connect_ex((host, port)) != 0:
                return port
    raise RuntimeError("Nenhuma porta livre encontrada para o CUTED (8779-8799).")


def open_browser_later(host: str, port: int, delay: float) -> None:
    url = f"http://{host}:{port}/index.html"
    if delay <= 0:
        webbrowser.open(url)
        return
    threading.Timer(delay, webbrowser.open, args=(url,)).start()


def workspace_index_is_empty_shell(index_path: Path) -> bool:
    try:
        html = index_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return ("data-import-form" in html and '"moments": []' in html) or "data-project-home" in html
