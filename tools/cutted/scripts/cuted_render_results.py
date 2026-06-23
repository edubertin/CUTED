from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

from cuted_contracts import PLATFORM_PRESETS


FinalizedFileUrls = Callable[[list[dict[str, object]], Path], list[dict[str, object]]]
CaptionRowsFromData = Callable[[object], list[dict[str, object]]]


def finalized_results_from_gallery(
    gallery_dir: Path,
    finalized_file_urls: FinalizedFileUrls,
    caption_rows_from_data: CaptionRowsFromData,
) -> dict[str, object]:
    manifest_path = gallery_dir / "captioned-clips" / "captioned-clips.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            manifest = {}
        rows = manifest.get("captioned") if isinstance(manifest, dict) else None
        if isinstance(rows, list):
            captioned = [row for row in rows if isinstance(row, dict)]
            export_dir = str(manifest.get("export_dir") or "") if isinstance(manifest, dict) else ""
            return {
                "ok": True,
                "ready": True,
                "partial": False,
                "count": len(captioned),
                "files": finalized_file_urls(captioned, gallery_dir),
                "export_dir": export_dir,
            }
    recovered = recovered_captioned_files(gallery_dir, caption_rows_from_data)
    return {
        "ok": True,
        "ready": False,
        "partial": bool(recovered),
        "count": len(recovered),
        "files": finalized_file_urls(recovered, gallery_dir) if recovered else [],
        "export_dir": "",
    }


def recovered_captioned_files(gallery_dir: Path, caption_rows_from_data: CaptionRowsFromData) -> list[dict[str, object]]:
    out_dir = gallery_dir / "captioned-clips"
    if not out_dir.exists():
        return []
    queue_rows = caption_queue_rows_by_output(gallery_dir, caption_rows_from_data)
    recovered: list[dict[str, object]] = []
    for file_path in sorted(out_dir.glob("clip-*-*-captioned.mp4")):
        if not file_path.is_file() or file_path.stat().st_size <= 0:
            continue
        match = re.fullmatch(r"clip-(\d+)-([a-z0-9_-]+)-captioned\.mp4", file_path.name)
        if not match:
            continue
        rank = int(match.group(1))
        platform = match.group(2)
        row = dict(queue_rows.get((rank, platform)) or queue_rows.get((rank, representative_platform(platform))) or {})
        preset = PLATFORM_PRESETS.get(platform, PLATFORM_PRESETS["tiktok"])
        row.update({
            "rank": rank,
            "platform": platform,
            "label": row.get("platform_label") or preset.label,
            "width": row.get("width") or preset.width,
            "height": row.get("height") or preset.height,
            "file": str(file_path),
        })
        cover_path = out_dir / f"clip-{rank:03d}-{platform}-cover.jpg"
        if cover_path.exists() and cover_path.is_file():
            row["cover_file"] = str(cover_path)
        cover_frame_path = out_dir / f"clip-{rank:03d}-{platform}-cover-frame.mp4"
        legacy_cover_frame_path = out_dir / f"clip-{rank:03d}-{platform}-captioned-cover-frame.mp4"
        if cover_frame_path.exists() and cover_frame_path.is_file():
            row["cover_frame_file"] = str(cover_frame_path)
        elif legacy_cover_frame_path.exists() and legacy_cover_frame_path.is_file():
            row["cover_frame_file"] = str(legacy_cover_frame_path)
        recovered.append(row)
    return recovered


def caption_queue_rows_by_output(
    gallery_dir: Path,
    caption_rows_from_data: CaptionRowsFromData,
) -> dict[tuple[int, str], dict[str, object]]:
    path = gallery_dir / "caption-queue.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    rows: dict[tuple[int, str], dict[str, object]] = {}
    for row in caption_rows_from_data(data):
        try:
            rank = int(row.get("rank") or 0)
        except (TypeError, ValueError):
            continue
        platform = representative_platform(str(row.get("platform") or "tiktok"))
        if rank > 0:
            rows[(rank, platform)] = row
    return rows


def representative_platform(platform: str) -> str:
    return platform if platform in PLATFORM_PRESETS else "tiktok"
