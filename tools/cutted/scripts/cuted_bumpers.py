from __future__ import annotations

import base64
from pathlib import Path


BUMPER_VIDEO_MIME_EXTENSIONS = {
    "video/mp4": "mp4",
    "video/quicktime": "mov",
    "video/webm": "webm",
    "video/x-m4v": "m4v",
}
BUMPER_MAX_SOURCE_BYTES = 48_000_000
BUMPER_SLOTS = {"intro", "outro"}


def normalize_bumper_slot(value: object) -> str:
    slot = str(value or "").strip().lower()
    if slot not in BUMPER_SLOTS:
        raise ValueError("Slot de vinheta invalido.")
    return slot


def clean_bumper_label(value: object) -> str:
    label = str(value or "").strip()[:180]
    return Path(label).name if label else "vinheta.mp4"


def decode_data_url_video(value: str) -> tuple[bytes, str]:
    if not value.startswith("data:") or ";base64," not in value:
        raise ValueError("Envie uma vinheta em video.")
    header, encoded = value.split(";base64,", 1)
    mime = header.removeprefix("data:").lower()
    extension = BUMPER_VIDEO_MIME_EXTENSIONS.get(mime)
    if extension is None:
        raise ValueError("Use MP4, MOV, M4V ou WebM para a vinheta.")
    try:
        video_bytes = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise ValueError("Vinheta invalida ou corrompida.") from exc
    return video_bytes, extension


def normalize_bumpers_from_row(row: dict[str, object]) -> dict[str, dict[str, object]]:
    raw = row.get("bumpers")
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, object]] = {}
    for slot in ("intro", "outro"):
        value = raw.get(slot)
        if not isinstance(value, dict):
            continue
        asset_file = str(value.get("asset_file") or "")
        data_url = str(value.get("video_data_url") or "")
        if not asset_file and not data_url:
            continue
        result[slot] = {
            "id": str(value.get("id") or f"bumper-{slot}"),
            "slot": slot,
            "label": clean_bumper_label(value.get("label")),
            "asset_file": asset_file,
            "video_data_url": data_url,
            "width": int(float(value.get("width") or 0)),
            "height": int(float(value.get("height") or 0)),
            "duration": round(max(float(value.get("duration") or 0.0), 0.0), 3),
        }
    return result
