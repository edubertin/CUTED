from __future__ import annotations

from typing import Callable


NormalizePlatforms = Callable[[object], list[str]]
ResolutionKeyForPlatform = Callable[[str], str]


def caption_rows_from_data(data: object, selected_rows_to_caption_rows_fn: Callable[[object], list[dict[str, object]]]) -> list[dict[str, object]]:
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if not isinstance(data, dict):
        return []
    queue = data.get("caption_queue")
    if isinstance(queue, list):
        return [row for row in queue if isinstance(row, dict)]
    return selected_rows_to_caption_rows_fn(data.get("selected") or data.get("moments"))


def queue_rows_for_assets(data: object, selected_rows_to_caption_rows_fn: Callable[[object], list[dict[str, object]]]) -> list[dict[str, object]]:
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if not isinstance(data, dict):
        return []
    rows: list[dict[str, object]] = []
    for key in ("caption_queue", "selected", "moments"):
        value = data.get(key)
        if isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, dict))
            if key != "caption_queue":
                rows.extend(selected_rows_to_caption_rows_fn(value))
    return rows


def selected_rows_to_caption_rows(
    rows: object,
    normalize_platforms_fn: NormalizePlatforms,
    row_for_platform_fn: Callable[[dict[str, object], str], dict[str, object]],
) -> list[dict[str, object]]:
    if not isinstance(rows, list):
        return []
    queue: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for platform in normalize_platforms_fn(row.get("platforms")):
            queue.append(row_for_platform_fn(row, platform))
    return queue


def row_for_platform(
    row: dict[str, object],
    platform: str,
    platform_edit_from_row_fn: Callable[[dict[str, object], str], dict[str, object]],
) -> dict[str, object]:
    result = {**row, "platform": platform}
    edit = platform_edit_from_row_fn(row, platform)
    if edit:
        result.update(edit)
    return result


def platform_edit_from_row(
    row: dict[str, object],
    platform: str,
    resolution_key_for_platform_fn: ResolutionKeyForPlatform,
) -> dict[str, object]:
    edits = row.get("platform_edits")
    raw = edits.get(platform) if isinstance(edits, dict) else None
    if not isinstance(raw, dict):
        raw = resolution_edit_from_row(row, platform, resolution_key_for_platform_fn)
    if not isinstance(raw, dict):
        return {}
    result: dict[str, object] = {}
    for key in ("camera", "camera_path", "effect", "overlay", "overlays", "bumpers", "director_plan", "caption_language", "captionLanguage"):
        if key in raw:
            result[key] = raw[key]
    return result


def resolution_edit_from_row(
    row: dict[str, object],
    platform: str,
    resolution_key_for_platform_fn: ResolutionKeyForPlatform,
) -> dict[str, object]:
    edits = row.get("resolution_edits")
    if not isinstance(edits, dict):
        return {}
    raw = edits.get(resolution_key_for_platform_fn(platform))
    return raw if isinstance(raw, dict) else {}
