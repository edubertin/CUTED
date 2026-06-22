from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from cuted_contracts import PlatformPreset


DurationFn = Callable[[dict[str, object]], float]
FilterFn = Callable[[dict[str, object]], str]
RenderCommandFn = Callable[[list[str], Path, dict[str, object], PlatformPreset, list[str], float], list[str]]
RunCommandFn = Callable[[list[str], dict[str, object]], None]
BumperApplyFn = Callable[[Path, dict[str, object], PlatformPreset, Path, Path, str], dict[str, object]]
FormatTimeFn = Callable[[float], str]


def render_captioned_clip(
    input_path: Path,
    output_path: Path,
    subtitle_path: Path | None,
    row: dict[str, object],
    preset: PlatformPreset,
    base_dir: Path,
    out_dir: Path,
    ffmpeg: str,
    caption_duration: DurationFn,
    effect_filter: FilterFn,
    overlay_filter: Callable[[dict[str, object], PlatformPreset], str],
    render_command: RenderCommandFn,
    run_ffmpeg_command: Callable[[list[str], dict[str, object], str], None],
    apply_bumpers_to_output: BumperApplyFn,
    fmt_time: FormatTimeFn,
) -> dict[str, object]:
    filters = [f"ass={subtitle_filter_path(subtitle_path, out_dir)}"] if subtitle_path else []
    effect = effect_filter(row)
    if effect:
        filters.append(effect)
    overlay = overlay_filter(row, preset)
    if overlay:
        filters.append(overlay)
    command = captioned_ffmpeg_command(input_path, output_path, row, preset, ffmpeg, filters, caption_duration, render_command, fmt_time)
    run_ffmpeg_command(command, row, str(out_dir))
    return apply_bumpers_to_output(output_path, row, preset, base_dir, out_dir, ffmpeg)


def captioned_ffmpeg_command(
    input_path: Path,
    output_path: Path,
    row: dict[str, object],
    preset: PlatformPreset,
    ffmpeg: str,
    filters: list[str],
    caption_duration: DurationFn,
    render_command: RenderCommandFn,
    fmt_time: FormatTimeFn,
) -> list[str]:
    duration = caption_duration(row)
    base = [
        ffmpeg, "-y", "-ss", fmt_time(caption_trim_start(row)), "-i", str(input_path),
        "-t", fmt_time(duration),
    ]
    return render_command(base, output_path, row, preset, filters, duration)


def caption_trim_start(row: dict[str, object]) -> float:
    if isinstance(row.get("file"), str) and row.get("file"):
        return 0.0
    return float(row.get("trim_start_seconds") or 0.0)


def subtitle_filter_path(subtitle_path: Path, out_dir: Path) -> str:
    return subtitle_path.relative_to(out_dir).as_posix()


def captioned_row(
    row: dict[str, object],
    preset: PlatformPreset,
    output_path: Path,
    subtitle_path: Path | None,
    cover_path: Path | None,
    cover_frame_path: Path | None,
    base_duration: float,
    cover_frame_tail_seconds: float,
    caption_style: dict[str, object],
    camera: dict[str, object],
    camera_path: list[dict[str, object]],
    effect: dict[str, object],
    overlay: dict[str, object],
    overlays: list[dict[str, object]],
    bumpers: dict[str, dict[str, object]],
) -> dict[str, object]:
    return {
        "rank": row.get("rank"),
        "platform": preset.key,
        "label": preset.label,
        "width": preset.width,
        "height": preset.height,
        "file": str(output_path),
        "subtitle_file": str(subtitle_path) if subtitle_path else "",
        "captions_enabled": bool(subtitle_path),
        "caption_style": caption_style,
        "adjusted_start": row.get("adjusted_start"),
        "adjusted_end": row.get("adjusted_end"),
        "adjusted_duration": base_duration,
        "base_duration": base_duration,
        "final_duration": base_duration,
        "cover_file": str(cover_path) if cover_path else "",
        "cover_frame_file": str(cover_frame_path) if cover_frame_path else "",
        "cover_frame_duration": round(base_duration + cover_frame_tail_seconds, 3) if cover_frame_path else 0.0,
        "publish_metadata": row.get("publish_metadata") if isinstance(row.get("publish_metadata"), dict) else {},
        "camera": camera,
        "camera_path": camera_path,
        "effect": effect,
        "overlay": overlay,
        "overlays": overlays,
        "bumpers": bumpers,
    }
