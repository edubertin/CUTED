from __future__ import annotations

import os
import re
import shutil
import subprocess
import uuid
from collections.abc import Callable
from pathlib import Path

from cuted_bumpers import normalize_bumpers_from_row
from cuted_contracts import EFFECT_PRESETS, OVERLAY_PRESETS, PlatformPreset


RunFfmpegFn = Callable[[list[str], dict[str, object], str | None], None]
DurationFn = Callable[[dict[str, object]], float]
FormatTimeFn = Callable[[float], str]
OutputArgsFn = Callable[[dict[str, object]], list[str]]
ResolveMediaPathFn = Callable[[Path, str], Path]
CodecThreadArgsFn = Callable[[dict[str, object]], list[str]]
MediaHasAudioFn = Callable[[Path, str], bool]


def apply_bumpers_to_output(
    output_path: Path,
    row: dict[str, object],
    preset: PlatformPreset,
    base_dir: Path,
    out_dir: Path,
    ffmpeg: str,
    caption_duration: DurationFn,
    run_ffmpeg_command: RunFfmpegFn,
    fmt_time: FormatTimeFn,
    ffmpeg_codec_thread_args: CodecThreadArgsFn,
    media_has_audio_fn: MediaHasAudioFn,
    resolve_media_path: ResolveMediaPathFn,
    final_video_crf: str,
) -> dict[str, object]:
    bumpers = normalize_bumpers_from_row(row)
    if not bumpers:
        return {}
    base_duration = caption_duration(row)
    work_dir = out_dir / "bumper-work" / output_path.stem
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    core_source = work_dir / "core-source.mp4"
    shutil.copy2(output_path, core_source)
    segments: list[Path] = []
    intro_duration = 0.0
    outro_duration = 0.0
    if "intro" in bumpers:
        intro = resolve_bumper_asset_path(base_dir, bumpers["intro"], resolve_media_path)
        intro_duration = bumper_duration(bumpers["intro"], intro, ffmpeg)
        intro_segment = work_dir / "intro.mp4"
        normalize_bumper_segment(intro, intro_segment, intro_duration, preset, ffmpeg, row, fmt_time, ffmpeg_codec_thread_args, media_has_audio_fn, run_ffmpeg_command, final_video_crf)
        segments.append(intro_segment)
    core_segment = work_dir / "core.mp4"
    normalize_bumper_segment(core_source, core_segment, base_duration, preset, ffmpeg, row, fmt_time, ffmpeg_codec_thread_args, media_has_audio_fn, run_ffmpeg_command, final_video_crf)
    segments.append(core_segment)
    if "outro" in bumpers:
        outro = resolve_bumper_asset_path(base_dir, bumpers["outro"], resolve_media_path)
        outro_duration = bumper_duration(bumpers["outro"], outro, ffmpeg)
        outro_segment = work_dir / "outro.mp4"
        normalize_bumper_segment(outro, outro_segment, outro_duration, preset, ffmpeg, row, fmt_time, ffmpeg_codec_thread_args, media_has_audio_fn, run_ffmpeg_command, final_video_crf)
        segments.append(outro_segment)
    concat_path = work_dir / "concat.txt"
    concat_path.write_text("".join(concat_file_entry(path) for path in segments), encoding="utf-8")
    temp_output = work_dir / "final.mp4"
    command = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", "-movflags", "+faststart", str(temp_output)]
    run_ffmpeg_command(command, row, None)
    shutil.copy2(temp_output, output_path)
    shutil.rmtree(work_dir, ignore_errors=True)
    final_duration = base_duration + intro_duration + outro_duration
    return {
        "bumpers": bumpers,
        "base_duration": round(base_duration, 3),
        "intro_duration": round(intro_duration, 3),
        "outro_duration": round(outro_duration, 3),
        "final_duration": round(final_duration, 3),
    }


def normalize_bumper_segment(
    source: Path,
    output: Path,
    duration: float,
    preset: PlatformPreset,
    ffmpeg: str,
    row: dict[str, object],
    fmt_time: FormatTimeFn,
    ffmpeg_codec_thread_args: CodecThreadArgsFn,
    media_has_audio_fn: MediaHasAudioFn,
    run_ffmpeg_command: RunFfmpegFn,
    final_video_crf: str,
) -> None:
    safe_duration = max(float(duration or 0.0), 0.1)
    video_filter_arg = ",".join([
        f"scale={preset.width}:{preset.height}:force_original_aspect_ratio=increase",
        f"crop={preset.width}:{preset.height}",
        "setsar=1",
        "fps=30",
        "format=yuv420p",
    ])
    command = [ffmpeg, "-y", "-i", str(source)]
    if media_has_audio_fn(source, ffmpeg):
        command.extend(["-t", fmt_time(safe_duration), "-vf", video_filter_arg, "-map", "0:v:0", "-map", "0:a:0"])
    else:
        command.extend([
            "-f", "lavfi", "-t", fmt_time(safe_duration), "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", fmt_time(safe_duration), "-vf", video_filter_arg, "-map", "0:v:0", "-map", "1:a:0", "-shortest",
        ])
    command.extend([
        "-c:v", "libx264",
        "-preset", "medium",
        "-profile:v", "main",
        "-level", "4.1",
        *ffmpeg_codec_thread_args(row),
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-crf", final_video_crf,
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-movflags", "+faststart",
        str(output),
    ])
    run_ffmpeg_command(command, row, None)


def media_has_audio(path: Path, ffmpeg: str) -> bool:
    command = [ffmpeg, "-hide_banner", "-i", str(path)]
    result = subprocess.run(command, capture_output=True, text=True)
    return "Audio:" in f"{result.stdout}\n{result.stderr}"


def bumper_duration(bumper: dict[str, object], path: Path, ffmpeg: str) -> float:
    duration = float(bumper.get("duration") or 0.0)
    if duration > 0:
        return duration
    return max(ffmpeg_media_duration(path, ffmpeg), 0.1)


def ffmpeg_media_duration(path: Path, ffmpeg: str) -> float:
    command = [ffmpeg, "-hide_banner", "-i", str(path)]
    result = subprocess.run(command, capture_output=True, text=True)
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", f"{result.stdout}\n{result.stderr}")
    if not match:
        return 0.0
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def concat_file_entry(path: Path) -> str:
    normalized = path.resolve().as_posix().replace("'", r"'\''")
    return f"file '{normalized}'\n"


def resolve_bumper_asset_path(base_dir: Path, bumper: dict[str, object], resolve_media_path: ResolveMediaPathFn) -> Path:
    asset_file = str(bumper.get("asset_file") or "")
    if not asset_file:
        raise ValueError("Vinheta sem arquivo local.")
    candidate = resolve_media_path(base_dir, asset_file).resolve()
    try:
        candidate.relative_to(base_dir.resolve())
    except ValueError as error:
        raise ValueError("Caminho de vinheta invalido.") from error
    if not candidate.exists() or not candidate.is_file():
        raise FileNotFoundError(f"Vinheta nao encontrada: {candidate}")
    return candidate


def render_cover_frame_tail_video(
    video_path: Path,
    cover_path: Path | None,
    row: dict[str, object],
    preset: PlatformPreset,
    out_dir: Path,
    ffmpeg: str,
    cover_frame_tail_seconds: float,
    fmt_time: FormatTimeFn,
    mp4_output_args: OutputArgsFn,
    media_has_audio_fn: MediaHasAudioFn,
    run_ffmpeg_command: RunFfmpegFn,
) -> Path | None:
    if cover_path is None or not cover_path.exists() or not video_path.exists():
        return None
    output = out_dir / f"clip-{int(row.get('rank', 0)):03d}-{preset.key}-cover-frame.mp4"
    work_dir = out_dir / "cover-frame-work" / f"{output.stem}-{uuid.uuid4().hex[:8]}"
    work_dir.mkdir(parents=True, exist_ok=False)
    try:
        cover_segment = work_dir / "cover-frame.mp4"
        render_cover_frame_segment(cover_path, cover_segment, media_has_audio_fn(video_path, ffmpeg), preset, row, ffmpeg, cover_frame_tail_seconds, fmt_time, mp4_output_args, run_ffmpeg_command)
        concat_path = work_dir / "concat.txt"
        concat_path.write_text(concat_file_entry(video_path) + concat_file_entry(cover_segment), encoding="utf-8")
        temp_output = work_dir / "cover-frame-final.mp4"
        command = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", "-movflags", "+faststart", str(temp_output)]
        try:
            run_ffmpeg_command(command, row, str(out_dir))
        except subprocess.CalledProcessError:
            temp_output = work_dir / "cover-frame-final-reencoded.mp4"
            fallback = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), *mp4_output_args(row), str(temp_output)]
            run_ffmpeg_command(fallback, row, str(out_dir))
        shutil.copy2(temp_output, output)
        return output if output.exists() and output.stat().st_size > 0 else None
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def render_cover_frame_segment(
    cover_path: Path,
    output: Path,
    include_audio: bool,
    preset: PlatformPreset,
    row: dict[str, object],
    ffmpeg: str,
    cover_frame_tail_seconds: float,
    fmt_time: FormatTimeFn,
    mp4_output_args: OutputArgsFn,
    run_ffmpeg_command: RunFfmpegFn,
) -> None:
    duration = fmt_time(cover_frame_tail_seconds)
    video_filter_arg = ",".join([
        f"scale={preset.width}:{preset.height}:force_original_aspect_ratio=increase",
        f"crop={preset.width}:{preset.height}",
        "setsar=1",
        "fps=30",
        "format=yuv420p",
    ])
    command = [ffmpeg, "-y", "-loop", "1", "-t", duration, "-i", str(cover_path)]
    if include_audio:
        command.extend(["-f", "lavfi", "-t", duration, "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"])
        command.extend(["-t", duration, "-vf", video_filter_arg, "-map", "0:v:0", "-map", "1:a:0", "-shortest"])
    else:
        command.extend(["-t", duration, "-vf", video_filter_arg, "-map", "0:v:0"])
    command.extend(mp4_output_args(row))
    command.append(str(output))
    run_ffmpeg_command(command, row, None)


def effect_filter(row: dict[str, object]) -> str:
    effect = effect_from_row(row)
    key = effect["key"]
    intensity = visible_effect_intensity(float(effect["intensity"]))
    if key == "none" or intensity <= 0:
        return ""
    if key == "light-grain":
        grain = scaled_value(intensity, 10, 28)
        contrast = scaled_float(intensity, 1.04, 1.12)
        return f"eq=contrast={contrast}:saturation=0.96,noise=alls={grain}:allf=t+u,unsharp=3:3:0.22"
    if key == "old-film":
        grain = scaled_value(intensity, 11, 26)
        contrast = scaled_float(intensity, 1.18, 1.32)
        brightness = scaled_float(intensity, -0.04, -0.08)
        return f"curves=preset=vintage,eq=saturation=0.56:contrast={contrast}:brightness={brightness},noise=alls={grain}:allf=t+u,vignette=PI/3"
    if key == "vhs":
        grain = scaled_value(intensity, 14, 34)
        contrast = scaled_float(intensity, 1.2, 1.34)
        return f"eq=saturation=0.55:contrast={contrast}:brightness=-0.06,noise=alls={grain}:allf=t+u,drawgrid=w=iw:h=4:t=1:c=white@0.08"
    if key == "bw-old":
        grain = scaled_value(intensity, 12, 30)
        contrast = scaled_float(intensity, 1.18, 1.34)
        return f"hue=s=0,eq=contrast={contrast}:brightness=-0.04,noise=alls={grain}:allf=t+u,vignette=PI/3"
    return ""


def video_crf(row: dict[str, object], final_video_crf: str, final_effect_video_crf: str) -> str:
    return final_effect_video_crf if effect_from_row(row)["key"] != "none" else final_video_crf


def visible_effect_intensity(intensity: float) -> float:
    if intensity <= 0:
        return 0.0
    return max(clamp(intensity, 0.0, 100.0), 24.0)


def scaled_value(intensity: float, low: int, high: int) -> int:
    value = low + ((clamp(intensity, 0.0, 100.0) / 100.0) * (high - low))
    return int(round(value))


def scaled_float(intensity: float, low: float, high: float) -> str:
    value = low + ((clamp(intensity, 0.0, 100.0) / 100.0) * (high - low))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def effect_from_row(row: dict[str, object]) -> dict[str, object]:
    raw = row.get("effect")
    if not isinstance(raw, dict):
        return {"key": "none", "label": EFFECT_PRESETS["none"].label, "intensity": 0}
    key = str(raw.get("key") or "none")
    preset = EFFECT_PRESETS.get(key, EFFECT_PRESETS["none"])
    intensity = clamp(float(raw.get("intensity") or 0.0), 0.0, 100.0)
    return {"key": preset.key, "label": preset.label, "intensity": intensity}


def overlay_filter(row: dict[str, object], preset: PlatformPreset) -> str:
    filters = [overlay_layer_filter(layer, preset) for layer in overlay_layers_from_row(row) if layer.get("kind") != "image"]
    return ",".join(item for item in filters if item)


def overlay_layer_filter(overlay: dict[str, object], preset: PlatformPreset) -> str:
    if overlay["key"] == "none":
        return ""
    if overlay.get("kind") == "image":
        return image_overlay_filter(overlay, preset)
    if overlay.get("kind") == "speech":
        return speech_overlay_filter(overlay, preset)
    if overlay.get("kind") == "text":
        return text_overlay_filter(overlay, preset)
    card = OVERLAY_PRESETS[str(overlay["key"])]
    box_w = int(round(preset.width * float(overlay["width"])))
    box_h = max(int(round(box_w * 0.28)), int(round(preset.height * 0.052)))
    x = min(int(round(preset.width * float(overlay["x"]))), max(preset.width - box_w, 0))
    y = min(int(round(preset.height * float(overlay["y"]))), max(preset.height - box_h, 0))
    pad = max(18, int(round(box_h * 0.18)))
    bar_w = max(8, int(round(box_w * 0.035)))
    title_size = max(28, int(round(box_h * 0.34)))
    subtitle_size = max(18, int(round(box_h * 0.21)))
    text_x = x + pad + bar_w
    title_y = y + max(14, int(round(box_h * 0.18)))
    subtitle_y = title_y + title_size + max(4, int(round(box_h * 0.08)))
    opacity = clamp(float(overlay["opacity"]) / 100.0, 0.35, 1.0)
    font = ffmpeg_filter_path(find_overlay_font())
    title = ffmpeg_text_value(card.title)
    subtitle = ffmpeg_text_value(card.subtitle)
    return ",".join([
        f"drawbox=x={x}:y={y}:w={box_w}:h={box_h}:color=black@{opacity:.2f}:t=fill",
        f"drawbox=x={x}:y={y}:w={bar_w}:h={box_h}:color={card.accent}@1.0:t=fill",
        f"drawtext=fontfile='{font}':text='{title}':x={text_x}:y={title_y}:fontsize={title_size}:fontcolor=white",
        f"drawtext=fontfile='{font}':text='{subtitle}':x={text_x}:y={subtitle_y}:fontsize={subtitle_size}:fontcolor=white@0.78",
    ])


def text_overlay_filter(overlay: dict[str, object], preset: PlatformPreset) -> str:
    text = str(overlay.get("text") or overlay.get("label") or "").strip()
    if not text:
        return ""
    box_w = int(round(preset.width * float(overlay["width"])))
    font_size = max(18, int(round(float(overlay["font_size"]) * preset.width / 1080.0)))
    box_h = max(int(round(font_size * 1.65)), int(round(preset.height * 0.04)))
    x = min(int(round(preset.width * float(overlay["x"]))), max(preset.width - box_w, 0))
    y = min(int(round(preset.height * float(overlay["y"]))), max(preset.height - box_h, 0))
    pad = max(10, int(round(font_size * 0.35)))
    text_y = y + max(6, int(round((box_h - font_size) / 2)))
    opacity = clamp(float(overlay["opacity"]) / 100.0, 0.1, 1.0)
    font = ffmpeg_filter_path(find_overlay_font())
    color = ffmpeg_color(str(overlay.get("color") or "#ffffff"))
    escaped_text = ffmpeg_text_value(text)
    enable = timed_overlay_enable(overlay)
    filters = []
    if bool(overlay.get("background_enabled")):
        background = ffmpeg_color(str(overlay.get("background_color") or "#000000"))
        background_opacity = clamp(float(overlay.get("background_opacity") or 70.0) / 100.0, 0.0, 1.0)
        filters.append(f"drawbox=x={x}:y={y}:w={box_w}:h={box_h}:color={background}@{background_opacity:.2f}:t=fill{enable}")
    filters.append(
        f"drawtext=fontfile='{font}':text='{escaped_text}':x={x + pad}:y={text_y}:"
        f"fontsize={font_size}:fontcolor={color}@{opacity:.2f}{enable}"
    )
    return ",".join(filters)


def timed_overlay_enable(overlay: dict[str, object]) -> str:
    start = max(float(overlay.get("start_seconds") if overlay.get("start_seconds") is not None else 0.0), 0.0)
    duration = max(float(overlay.get("duration_seconds") if overlay.get("duration_seconds") is not None else 3.0), 0.0)
    if duration <= 0.0:
        return ""
    return f":enable='between(t,{start:.3f},{start + duration:.3f})'"


def speech_overlay_filter(overlay: dict[str, object], preset: PlatformPreset) -> str:
    text = str(overlay.get("text") or overlay.get("label") or "").strip()
    if not text:
        return ""
    box_w = int(round(preset.width * float(overlay["width"])))
    font_size = max(18, int(round(float(overlay["font_size"]) * preset.width / 1080.0)))
    box_h = max(int(round(font_size * 1.95)), int(round(preset.height * 0.054)))
    x = min(int(round(preset.width * float(overlay["x"]))), max(preset.width - box_w, 0))
    y = min(int(round(preset.height * float(overlay["y"]))), max(preset.height - box_h, 0))
    pad = max(12, int(round(font_size * 0.44)))
    tail_w = max(18, int(round(font_size * 0.5)))
    tail_h = max(16, int(round(font_size * 0.44)))
    tail_x = min(x + max(pad, int(round(box_w * 0.2))), max(preset.width - tail_w, 0))
    tail_y = min(y + box_h - max(2, int(round(tail_h * 0.2))), preset.height)
    text_y = y + max(8, int(round((box_h - font_size) / 2)))
    opacity = clamp(float(overlay["opacity"]) / 100.0, 0.1, 1.0)
    font = ffmpeg_filter_path(find_overlay_font())
    color = ffmpeg_color(str(overlay.get("color") or "#050505"))
    background = ffmpeg_color(str(overlay.get("background_color") or "#ffffff"))
    escaped_text = ffmpeg_text_value(text)
    enable = timed_overlay_enable(overlay)
    return ",".join([
        f"drawbox=x={tail_x}:y={tail_y}:w={tail_w}:h={tail_h}:color={background}@{opacity:.2f}:t=fill{enable}",
        f"drawbox=x={x}:y={y}:w={box_w}:h={box_h}:color={background}@{opacity:.2f}:t=fill{enable}",
        f"drawtext=fontfile='{font}':text='{escaped_text}':x={x + pad}:y={text_y}:"
        f"fontsize={font_size}:fontcolor={color}@1.0{enable}",
    ])


def image_overlay_filter(overlay: dict[str, object], preset: PlatformPreset) -> str:
    image_file = str(overlay.get("image_file") or "")
    if not image_file:
        return ""
    width = int(round(preset.width * float(overlay["width"])))
    x = min(int(round(preset.width * float(overlay["x"]))), max(preset.width - width, 0))
    y = min(int(round(preset.height * float(overlay["y"]))), preset.height)
    opacity = clamp(float(overlay["opacity"]) / 100.0, 0.1, 1.0)
    path = ffmpeg_filter_path(Path(image_file))
    enable = timed_overlay_enable(overlay)
    return f"movie='{path}',scale={width}:-1,colorchannelmixer=aa={opacity:.2f}[img];[in][img]overlay={x}:{y}:format=auto{enable}[out]"


def overlay_from_row(row: dict[str, object]) -> dict[str, object]:
    layers = overlay_layers_from_row(row)
    for layer in layers:
        if layer.get("kind") != "image":
            return layer
    raw = row.get("overlay")
    if not isinstance(raw, dict):
        return default_overlay()
    return overlay_from_raw(raw)


def overlay_layers_from_row(row: dict[str, object]) -> list[dict[str, object]]:
    raw_layers = row.get("overlays")
    if isinstance(raw_layers, list):
        layers = [overlay_layer_from_raw(item) for item in raw_layers if isinstance(item, dict)]
        return [item for item in layers if item["key"] != "none"]
    legacy = overlay_from_raw(row.get("overlay") if isinstance(row.get("overlay"), dict) else {})
    return [] if legacy["key"] == "none" else [legacy]


def overlay_layer_from_raw(raw: dict[str, object]) -> dict[str, object]:
    if str(raw.get("kind") or raw.get("key") or "") == "image":
        return image_overlay_from_raw(raw)
    if str(raw.get("kind") or raw.get("key") or "") == "speech":
        return speech_overlay_from_raw(raw)
    if str(raw.get("kind") or raw.get("key") or "") == "text":
        return text_overlay_from_raw(raw)
    return overlay_from_raw(raw)


def overlay_from_raw(raw: dict[str, object]) -> dict[str, object]:
    key = str(raw.get("key") or "none")
    preset = OVERLAY_PRESETS.get(key, OVERLAY_PRESETS["none"])
    if preset.key == "none":
        return default_overlay()
    return {
        "id": str(raw.get("id") or ""),
        "kind": "cta",
        "key": preset.key,
        "label": preset.label,
        "x": clamp(float(raw.get("x") if raw.get("x") is not None else 0.62), 0.0, 1.0),
        "y": clamp(float(raw.get("y") if raw.get("y") is not None else 0.78), 0.0, 1.0),
        "width": clamp(float(raw.get("width") if raw.get("width") is not None else 0.34), 0.18, 0.72),
        "opacity": clamp(float(raw.get("opacity") if raw.get("opacity") is not None else 95.0), 35.0, 100.0),
    }


def image_overlay_from_raw(raw: dict[str, object]) -> dict[str, object]:
    image_file = str(raw.get("image_file") or "")
    image_data_url = str(raw.get("image_data_url") or "")
    if not image_file and not image_data_url:
        return default_overlay()
    return {
        "id": str(raw.get("id") or ""),
        "kind": "image",
        "key": "image",
        "label": str(raw.get("label") or "Imagem"),
        "x": clamp(float(raw.get("x") if raw.get("x") is not None else 0.58), 0.0, 1.0),
        "y": clamp(float(raw.get("y") if raw.get("y") is not None else 0.68), 0.0, 1.0),
        "width": clamp(float(raw.get("width") if raw.get("width") is not None else 0.28), 0.08, 0.9),
        "opacity": clamp(float(raw.get("opacity") if raw.get("opacity") is not None else 100.0), 10.0, 100.0),
        "image_file": image_file,
        "image_data_url": image_data_url,
        "start_seconds": clamp(float(raw.get("start_seconds") if raw.get("start_seconds") is not None else 0.0), 0.0, 9999.0),
        "duration_seconds": clamp(float(raw.get("duration_seconds") if raw.get("duration_seconds") is not None else 3.0), 0.3, 60.0),
    }


def text_overlay_from_raw(raw: dict[str, object]) -> dict[str, object]:
    text = str(raw.get("text") or raw.get("label") or "").strip()
    if not text:
        return default_overlay()
    return {
        "id": str(raw.get("id") or ""),
        "kind": "text",
        "key": "text",
        "label": text,
        "text": text,
        "x": clamp(float(raw.get("x") if raw.get("x") is not None else 0.36), 0.0, 1.0),
        "y": clamp(float(raw.get("y") if raw.get("y") is not None else 0.34), 0.0, 1.0),
        "width": clamp(float(raw.get("width") if raw.get("width") is not None else 0.42), 0.16, 0.9),
        "opacity": clamp(float(raw.get("opacity") if raw.get("opacity") is not None else 100.0), 10.0, 100.0),
        "font_size": clamp(float(raw.get("font_size") if raw.get("font_size") is not None else 44.0), 14.0, 96.0),
        "font_weight": str(raw.get("font_weight") or "700"),
        "color": safe_hex_color(str(raw.get("color") or "#ffffff"), "#ffffff"),
        "background_enabled": bool(raw.get("background_enabled", True)),
        "background_color": safe_hex_color(str(raw.get("background_color") or "#000000"), "#000000"),
        "background_opacity": clamp(float(raw.get("background_opacity") if raw.get("background_opacity") is not None else 70.0), 0.0, 100.0),
        "start_seconds": clamp(float(raw.get("start_seconds") if raw.get("start_seconds") is not None else 0.0), 0.0, 9999.0),
        "duration_seconds": clamp(float(raw.get("duration_seconds") if raw.get("duration_seconds") is not None else 3.0), 0.3, 60.0),
    }


def speech_overlay_from_raw(raw: dict[str, object]) -> dict[str, object]:
    layer = text_overlay_from_raw({
        **raw,
        "text": raw.get("text") or raw.get("label") or "Fala rapida",
        "background_enabled": True,
        "background_color": raw.get("background_color") or "#ffffff",
        "background_opacity": raw.get("background_opacity") if raw.get("background_opacity") is not None else 94,
        "color": raw.get("color") or "#050505",
        "font_size": raw.get("font_size") if raw.get("font_size") is not None else 34,
        "width": raw.get("width") if raw.get("width") is not None else 0.56,
    })
    if layer["key"] == "none":
        return layer
    layer["kind"] = "speech"
    layer["key"] = "speech"
    layer["label"] = str(layer["text"])
    layer["tail"] = str(raw.get("tail") or "bottom-left")
    layer["start_seconds"] = clamp(float(raw.get("start_seconds") if raw.get("start_seconds") is not None else 0.0), 0.0, 9999.0)
    layer["duration_seconds"] = clamp(float(raw.get("duration_seconds") if raw.get("duration_seconds") is not None else 3.0), 0.3, 60.0)
    return layer


def default_overlay() -> dict[str, object]:
    return {"id": "", "kind": "cta", "key": "none", "label": OVERLAY_PRESETS["none"].label, "x": 0.62, "y": 0.78, "width": 0.34, "opacity": 95}


def find_overlay_font() -> Path:
    candidates = [
        Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "arialbd.ttf",
        Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "arial.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError("No usable font found for video overlays.")


def ffmpeg_filter_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace(":", r"\:")


def ffmpeg_text_value(value: str) -> str:
    return value.replace("\\", r"\\").replace(":", r"\:").replace("'", r"\'")


def safe_hex_color(value: str, fallback: str) -> str:
    color = value.strip()
    if len(color) == 7 and color.startswith("#"):
        digits = color[1:]
    elif len(color) == 6:
        digits = color
    else:
        return fallback
    if all(char in "0123456789abcdefABCDEF" for char in digits):
        return f"#{digits.lower()}"
    return fallback


def ffmpeg_color(value: str) -> str:
    return "0x" + safe_hex_color(value, "#ffffff").removeprefix("#")


def clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)
