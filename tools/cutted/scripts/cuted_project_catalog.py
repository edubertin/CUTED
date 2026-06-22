from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
import urllib.parse
from pathlib import Path


def clean_project_id(value: object) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", str(value or "")).strip("-")[:80]


def empty_project_catalog(version: int) -> dict[str, object]:
    return {"version": version, "projects": []}


def read_gallery_moments(gallery_dir: Path) -> list[object]:
    path = gallery_dir / "moments.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return []
    moments = data.get("moments") if isinstance(data, dict) else data
    return moments if isinstance(moments, list) else []


def valid_recent_project_dir(project_dir: Path, workspace: Path) -> bool:
    try:
        resolved = project_dir.expanduser().resolve()
        root = workspace.resolve()
        resolved.relative_to(root)
    except (OSError, ValueError):
        return False
    return resolved != root and (resolved / "index.html").is_file()


def safe_project_delete_dir(project_dir: Path, workspace: Path) -> Path:
    resolved = project_dir.expanduser().resolve()
    root = workspace.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("So posso apagar projetos dentro do workspace atual.") from error
    if resolved == root or not (resolved / "index.html").exists():
        raise ValueError("Diretorio de projeto invalido para apagar.")
    return resolved


def delete_project_dir(project_dir: Path) -> str:
    if move_project_dir_to_recycle_bin(project_dir):
        return "recycle-bin"
    shutil.rmtree(project_dir)
    return "permanent-delete"


def move_project_dir_to_recycle_bin(project_dir: Path) -> bool:
    if os.name != "nt":
        return False
    try:
        import ctypes
    except ImportError:
        return False

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", ctypes.c_void_p),
            ("wFunc", ctypes.c_uint),
            ("pFrom", ctypes.c_wchar_p),
            ("pTo", ctypes.c_wchar_p),
            ("fFlags", ctypes.c_ushort),
            ("fAnyOperationsAborted", ctypes.c_bool),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", ctypes.c_wchar_p),
        ]

    operation = SHFILEOPSTRUCTW()
    operation.wFunc = 0x0003
    operation.pFrom = str(project_dir.resolve()) + "\0\0"
    operation.fFlags = 0x0040 | 0x0010 | 0x0400 | 0x0004
    result = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(operation))
    return result == 0 and not operation.fAnyOperationsAborted and not project_dir.exists()


def project_source_label(metadata: dict[str, object], gallery_dir: Path) -> str:
    source_path = str(metadata.get("source_path") or "").strip()
    source_url = str(metadata.get("source_url") or "").strip()
    if source_path:
        return Path(source_path).name or gallery_dir.name
    if source_url:
        parsed = urllib.parse.urlparse(source_url)
        return parsed.netloc or source_url[:80]
    return gallery_dir.name


def project_id_for_path(path: Path, slug: str) -> str:
    return f"{slug}-{hashlib.sha1(str(path.resolve()).encode('utf-8')).hexdigest()[:8]}"


def project_url_for_workspace(project_path: Path, workspace: Path) -> str:
    try:
        rel = project_path.resolve().relative_to(workspace.resolve())
    except (OSError, ValueError):
        return ""
    return f"/{urllib.parse.quote(rel.as_posix(), safe='/')}/index.html"


def directory_size(path: Path, file_limit: int) -> int:
    total = 0
    count = 0
    for item in path.rglob("*"):
        if count >= file_limit:
            break
        if item.is_file():
            count += 1
            try:
                total += item.stat().st_size
            except OSError:
                continue
    return total


def iso_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")
