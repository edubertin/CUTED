from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
import uuid
from pathlib import Path


def render_job_fingerprint(payload: dict[str, object], profile: str, renderer_version: str) -> str:
    relevant = {
        "queue": payload.get("queue"),
        "chars_per_line": payload.get("chars_per_line"),
        "max_lines": payload.get("max_lines"),
        "captions_enabled": payload.get("captions_enabled"),
        "cover_frame_enabled": bool(payload.get("cover_frame_enabled", False)),
        "resource_profile": profile,
        "renderer": renderer_version,
    }
    raw = json.dumps(relevant, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def render_job_summary(payload: dict[str, object]) -> dict[str, object]:
    queue = payload.get("queue") if isinstance(payload, dict) else None
    rows = queue.get("caption_queue") if isinstance(queue, dict) else []
    first = rows[0] if isinstance(rows, list) and rows and isinstance(rows[0], dict) else {}
    return {
        "count": len(rows) if isinstance(rows, list) else 0,
        "rank": first.get("rank", ""),
        "title": first.get("title") or first.get("peak_text") or "Render CUTED",
        "platform": first.get("platform_label") or first.get("platform") or "",
        "duration": first.get("adjusted_duration") or "",
        "cover_frame_enabled": bool(payload.get("cover_frame_enabled", False)),
    }


def render_queue_manifest_path(gallery_dir: Path, renders_dir_name: str) -> Path:
    return gallery_dir / renders_dir_name / "render-queue.json"


def render_job_output_dir(gallery_dir: Path, renders_dir_name: str, job_id: str) -> Path:
    return gallery_dir / renders_dir_name / "jobs" / job_id


def read_render_queue_manifest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"version": 1, "jobs": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "jobs": []}
    return data if isinstance(data, dict) else {"version": 1, "jobs": []}


def write_render_queue_manifest(path: Path, jobs: list[dict[str, object]], attempts: int, retry_seconds: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps({"version": 1, "jobs": jobs}, ensure_ascii=False, indent=2)
    for attempt in range(attempts):
        temp_path = render_queue_temp_manifest_path(path)
        try:
            temp_path.write_text(payload, encoding="utf-8")
            temp_path.replace(path)
            return
        except OSError as error:
            if not render_queue_write_error_is_retryable(error) or attempt + 1 >= attempts:
                raise
            render_queue_cleanup_temp_manifest(temp_path)
            time.sleep(retry_seconds * (attempt + 1))


def render_queue_temp_manifest_path(path: Path) -> Path:
    suffix = f"{os.getpid()}-{threading.get_ident()}-{uuid.uuid4().hex[:8]}"
    return path.with_name(f"{path.stem}.{suffix}.tmp")


def render_queue_write_error_is_retryable(error: OSError) -> bool:
    return isinstance(error, PermissionError) or getattr(error, "winerror", None) == 5


def render_queue_cleanup_temp_manifest(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError as error:
        print(f"[cutted] render queue temp cleanup failed: {error}", file=sys.stderr)


def clean_render_resource_profile(value: object) -> str:
    profile = str(value or "medium").strip().lower()
    aliases = {"medio": "medium", "mÃ©dio": "medium", "alto": "high", "eco": "eco"}
    profile = aliases.get(profile, profile)
    return profile if profile in {"eco", "medium", "high"} else "medium"


def render_profile_label(profile: str) -> str:
    return {"eco": "Eco", "medium": "Medio", "high": "Alto"}.get(profile, "Medio")
