from __future__ import annotations

import argparse
import html
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace


TERMINAL_ENDINGS = (".", "!", "?", "…")
WEAK_ENDINGS = (
    "porque", "por que", "entao", "então", "mas", "aí", "ai", "só que", "so que",
    "ou seja", "tipo", "enfim", "daí", "dai", "logo", "portanto",
)
WEAK_STARTINGS = (
    "e ", "mas ", "aí ", "ai ", "então ", "entao ", "porque ", "por que ", "só que ", "so que ",
)


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class Moment:
    rank: int
    start: float
    end: float
    peak: float
    score: float
    title: str
    reason: str
    transcript: str
    peak_text: str
    clip_file: str | None
    frame_file: str | None
    caption_segments: tuple[Segment, ...] = ()


@dataclass(frozen=True)
class CuttedConfig:
    clips: int
    min_duration: float
    max_duration: float
    target_duration: float
    smart_boundaries: bool
    lead_in: float
    tail_out: float
    preset: str | None


@dataclass(frozen=True)
class SourceMedia:
    render_source: str
    transcribe_source: Path | str
    label: str
    cleanup_paths: tuple[Path, ...]


@dataclass(frozen=True)
class PlatformPreset:
    key: str
    label: str
    width: int
    height: int
    note: str


@dataclass(frozen=True)
class EffectPreset:
    key: str
    label: str
    note: str


@dataclass(frozen=True)
class CameraPreset:
    key: str
    label: str
    note: str


@dataclass(frozen=True)
class OverlayPreset:
    key: str
    label: str
    title: str
    subtitle: str
    accent: str


@dataclass(frozen=True)
class CaptionEvent:
    start: float
    end: float
    text: str


PLATFORM_PRESETS = {
    "tiktok": PlatformPreset("tiktok", "TikTok", 1080, 1920, "9:16 vertical"),
    "shorts": PlatformPreset("shorts", "Shorts", 1080, 1920, "9:16 vertical"),
    "instagram": PlatformPreset("instagram", "Instagram", 1080, 1920, "9:16 vertical"),
    "facebook": PlatformPreset("facebook", "Facebook", 1080, 1350, "4:5 feed"),
    "youtube": PlatformPreset("youtube", "YouTube", 1920, 1080, "16:9 landscape"),
}

EFFECT_PRESETS = {
    "none": EffectPreset("none", "Sem efeito", "Preview limpo"),
    "light-grain": EffectPreset("light-grain", "Chuvisco Leve", "Granulado sutil para tirar o aspecto cru"),
    "old-film": EffectPreset("old-film", "Filme Antigo", "Cor vintage, vinheta e textura de filme"),
    "vhs": EffectPreset("vhs", "VHS / TV Antiga", "Ruido mais forte e contraste analogico"),
    "bw-old": EffectPreset("bw-old", "Preto e Branco Antigo", "P&B com grao e vinheta"),
}

CAMERA_PRESETS = {
    "center": CameraPreset("center", "Centro seguro", "Crop limpo no centro do quadro"),
    "face-center": CameraPreset("face-center", "Rosto no centro", "Zoom leve para destacar uma pessoa central"),
    "face-left": CameraPreset("face-left", "Rosto a esquerda", "Prioriza quem esta do lado esquerdo"),
    "face-right": CameraPreset("face-right", "Rosto a direita", "Prioriza quem esta do lado direito"),
    "alternate": CameraPreset("alternate", "Alternar focos", "Movimento suave entre lados"),
    "soft-zoom": CameraPreset("soft-zoom", "Zoom sutil", "Aproxima o enquadramento sem mudar o lado"),
    "punch-in": CameraPreset("punch-in", "Punch-in", "Corte mais fechado para dar energia"),
}

OVERLAY_PRESETS = {
    "none": OverlayPreset("none", "Sem chamada", "", "", "0x000000"),
    "subscribe": OverlayPreset("subscribe", "Inscreva-se", "Inscreva-se", "Novos cortes toda semana", "0xff3b30"),
    "follow": OverlayPreset("follow", "Siga-nos", "Siga-nos", "Mais cortes no perfil", "0x24d17e"),
    "description": OverlayPreset("description", "Veja a descricao", "Veja a descricao", "Link e contexto completo", "0x4da3ff"),
    "like-share": OverlayPreset("like-share", "Curta e compartilhe", "Curta e compartilhe", "Mostre para alguem", "0xffd166"),
    "pinned-comment": OverlayPreset("pinned-comment", "Comentario fixado", "Comentario fixado", "Detalhes no primeiro comentario", "0xb388ff"),
    "watermark": OverlayPreset("watermark", "Marca d'agua", "CUTED", "clip selecionado", "0xf4f4f4"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate local video clip candidates and a review gallery.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze = subparsers.add_parser("analyze", help="Analyze one local video and generate an HTML gallery.")
    analyze.add_argument("video", nargs="?", type=Path)
    analyze.add_argument("--youtube-url", default=None)
    analyze.add_argument("--out", type=Path, required=True)
    analyze.add_argument("--clips", type=int, default=15)
    analyze.add_argument("--preset", choices=("tiktok", "shorts", "reels"), default=None)
    analyze.add_argument("--target-duration", type=float, default=None)
    analyze.add_argument("--min-duration", type=float, default=None)
    analyze.add_argument("--max-duration", type=float, default=None)
    analyze.add_argument("--smart-boundaries", action=argparse.BooleanOptionalAction, default=None)
    analyze.add_argument("--lead-in", type=float, default=1.0)
    analyze.add_argument("--tail-out", type=float, default=1.5)
    analyze.add_argument("--model", default="small")
    analyze.add_argument("--language", default=None)
    analyze.add_argument("--transcript-json", type=Path, default=None)
    analyze.add_argument("--youtube-captions", action=argparse.BooleanOptionalAction, default=True)
    analyze.add_argument("--skip-render", action="store_true")
    analyze.add_argument("--cleanup-source", action="store_true")
    render = subparsers.add_parser("render-selected", help="Render final clips from an exported selected-clips JSON.")
    render.add_argument("selection_json", type=Path)
    render.add_argument("--out", type=Path, required=True)
    render.add_argument("--base-dir", type=Path, default=None)
    caption = subparsers.add_parser("caption-selected", help="Burn styled subtitles from an exported caption queue JSON.")
    caption.add_argument("caption_json", type=Path)
    caption.add_argument("--out", type=Path, required=True)
    caption.add_argument("--base-dir", type=Path, default=None)
    caption.add_argument("--chars-per-line", type=int, default=28)
    caption.add_argument("--max-lines", type=int, default=2)
    serve = subparsers.add_parser("serve", help="Serve a generated gallery with local finalize API.")
    serve.add_argument("--dir", type=Path, required=True)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8777)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "analyze":
        analyze(args)
        return 0
    if args.command == "render-selected":
        render_selected(args)
        return 0
    if args.command == "caption-selected":
        caption_selected(args)
        return 0
    if args.command == "serve":
        serve_gallery(args)
        return 0
    raise RuntimeError(f"Unsupported command: {args.command}")


def analyze(args: argparse.Namespace) -> None:
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    config = build_config(args)
    ffmpeg = find_ffmpeg()
    ffprobe = find_ffprobe()
    source = prepare_source(args, out_dir, ffmpeg)
    duration = probe_duration(source.render_source, ffprobe)
    segments = load_segments(args, source.transcribe_source)
    moments = pick_moments(segments, config, duration)
    rendered = render_outputs(source.render_source, out_dir, moments, ffmpeg, args.skip_render)
    write_json(out_dir / "moments.json", rendered, source.label, duration, config)
    write_html(out_dir / "index.html", rendered, source.label)
    if args.cleanup_source:
        cleanup_sources(source.cleanup_paths)
    print(f"[cutted] Generated {len(rendered)} moments in {out_dir}")
    print(f"[cutted] Open: {out_dir / 'index.html'}")


def render_selected(args: argparse.Namespace) -> None:
    selection_path = args.selection_json.resolve()
    require_file(selection_path)
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base_dir = (args.base_dir or selection_path.parent).resolve()
    ffmpeg = find_ffmpeg()
    data = json.loads(selection_path.read_text(encoding="utf-8-sig"))
    rows = data.get("selected") or data.get("moments") or []
    rendered = render_selected_rows(rows, base_dir, out_dir, ffmpeg)
    manifest = {"source_selection": str(selection_path), "rendered": rendered}
    (out_dir / "rendered-clips.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[cutted] Rendered {len(rendered)} final clips in {out_dir}")


def caption_selected(args: argparse.Namespace) -> None:
    caption_path = args.caption_json.resolve()
    require_file(caption_path)
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base_dir = (args.base_dir or caption_path.parent).resolve()
    ffmpeg = find_ffmpeg()
    data = json.loads(caption_path.read_text(encoding="utf-8-sig"))
    rows = caption_rows_from_data(data)
    captioned = caption_selected_rows(rows, base_dir, out_dir, ffmpeg, args)
    manifest = {"source_caption_queue": str(caption_path), "captioned": captioned}
    (out_dir / "captioned-clips.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[cutted] Captioned {len(captioned)} final clips in {out_dir}")


def serve_gallery(args: argparse.Namespace) -> None:
    base_dir = args.dir.resolve()
    require_file(base_dir / "index.html")
    handler = gallery_handler(base_dir)
    server = http.server.ThreadingHTTPServer((args.host, args.port), handler)
    print(f"[cutted] Serving {base_dir}")
    print(f"[cutted] Open: http://{args.host}:{args.port}/index.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[cutted] Server stopped")
    finally:
        server.server_close()


def gallery_handler(base_dir: Path) -> type[http.server.SimpleHTTPRequestHandler]:
    class CuttedGalleryHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, directory=str(base_dir), **kwargs)

        def do_POST(self) -> None:
            if urllib.parse.urlparse(self.path).path != "/api/finalize":
                self.send_error(404, "Not found")
                return
            self.handle_finalize(base_dir)

        def handle_finalize(self, request_base_dir: Path) -> None:
            try:
                result = finalize_from_request(self, request_base_dir)
                send_json_response(self, 200, result)
            except Exception as error:
                send_json_response(self, 500, {"ok": False, "error": str(error)})

    return CuttedGalleryHandler


def finalize_from_request(handler: http.server.BaseHTTPRequestHandler, base_dir: Path) -> dict[str, object]:
    payload = read_json_body(handler)
    queue = payload.get("queue") if isinstance(payload, dict) else None
    if not isinstance(queue, dict):
        raise ValueError("Missing queue data.")
    caption_path = base_dir / "caption-queue.json"
    out_dir = base_dir / "captioned-clips"
    out_dir.mkdir(parents=True, exist_ok=True)
    caption_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = caption_rows_from_data(queue)
    options = SimpleNamespace(chars_per_line=int(payload.get("chars_per_line") or 28), max_lines=int(payload.get("max_lines") or 2))
    captioned = caption_selected_rows(rows, base_dir, out_dir, find_ffmpeg(), options)
    manifest = {"source_caption_queue": str(caption_path), "captioned": captioned}
    (out_dir / "captioned-clips.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "count": len(captioned), "files": finalized_file_urls(captioned, base_dir)}


def read_json_body(handler: http.server.BaseHTTPRequestHandler) -> dict[str, object]:
    length = int(handler.headers.get("Content-Length") or "0")
    if length <= 0 or length > 20_000_000:
        raise ValueError("Invalid request body.")
    raw = handler.rfile.read(length)
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    return data


def finalized_file_urls(rows: list[dict[str, object]], base_dir: Path) -> list[dict[str, object]]:
    files: list[dict[str, object]] = []
    for row in rows:
        file_path = Path(str(row.get("file") or ""))
        rel = file_path.resolve().relative_to(base_dir)
        files.append({**row, "url": rel.as_posix(), "download_name": file_path.name})
    return files


def send_json_response(handler: http.server.BaseHTTPRequestHandler, status: int, data: dict[str, object]) -> None:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def caption_rows_from_data(data: object) -> list[dict[str, object]]:
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if not isinstance(data, dict):
        return []
    queue = data.get("caption_queue")
    if isinstance(queue, list):
        return [row for row in queue if isinstance(row, dict)]
    return selected_rows_to_caption_rows(data.get("selected") or data.get("moments"))


def selected_rows_to_caption_rows(rows: object) -> list[dict[str, object]]:
    if not isinstance(rows, list):
        return []
    queue: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for platform in normalize_platforms(row.get("platforms")):
            queue.append({**row, "platform": platform})
    return queue


def render_selected_rows(rows: list[dict[str, object]], base_dir: Path, out_dir: Path, ffmpeg: str) -> list[dict[str, object]]:
    rendered: list[dict[str, object]] = []
    for row in rows:
        platforms = normalize_platforms(row.get("platforms"))
        if not platforms:
            continue
        clip_file = row.get("clip_file")
        if not isinstance(clip_file, str) or not clip_file:
            continue
        input_path = resolve_media_path(base_dir, clip_file)
        if not input_path.exists():
            continue
        for platform in platforms:
            preset = PLATFORM_PRESETS[platform]
            output_path = out_dir / f"clip-{int(row.get('rank', 0)):03d}-{preset.key}.mp4"
            trim_start = float(row.get("trim_start_seconds") or 0.0)
            adjusted_duration = float(row.get("adjusted_duration") or 0.0)
            if adjusted_duration <= 0:
                adjusted_duration = max(float(row.get("end", 0.0)) - float(row.get("start", 0.0)), 0.1)
            render_platform_clip(input_path, output_path, trim_start, adjusted_duration, preset, row, ffmpeg)
            rendered.append(rendered_row(row, preset, output_path))
    return rendered


def caption_selected_rows(
    rows: list[dict[str, object]], base_dir: Path, out_dir: Path, ffmpeg: str, args: argparse.Namespace
) -> list[dict[str, object]]:
    subtitles_dir = out_dir / "subtitles"
    subtitles_dir.mkdir(exist_ok=True)
    captioned: list[dict[str, object]] = []
    for row in rows:
        platform = str(row.get("platform") or "")
        if platform not in PLATFORM_PRESETS:
            continue
        input_path = caption_input_path(row, base_dir)
        if input_path is None:
            continue
        preset = PLATFORM_PRESETS[platform]
        stem = f"clip-{int(row.get('rank', 0)):03d}-{preset.key}"
        subtitle_path = subtitles_dir / f"{stem}.ass"
        output_path = out_dir / f"{stem}-captioned.mp4"
        write_ass_subtitles(subtitle_path, row, preset, args.chars_per_line, args.max_lines)
        render_captioned_clip(input_path, output_path, subtitle_path, row, preset, out_dir, ffmpeg)
        captioned.append(captioned_row(row, preset, output_path, subtitle_path))
    return captioned


def caption_input_path(row: dict[str, object], base_dir: Path) -> Path | None:
    rendered_file = row.get("file")
    clip_file = row.get("clip_file")
    candidate = rendered_file if isinstance(rendered_file, str) and rendered_file else clip_file
    if not isinstance(candidate, str) or not candidate:
        return None
    path = resolve_media_path(base_dir, candidate)
    return path if path.exists() else None


def write_ass_subtitles(path: Path, row: dict[str, object], preset: PlatformPreset, chars_per_line: int, max_lines: int) -> None:
    duration = caption_duration(row)
    events = caption_events(row, chars_per_line, max_lines, duration)
    path.write_text(ass_document(events, duration, preset, chars_per_line, max_lines), encoding="utf-8")


def caption_duration(row: dict[str, object]) -> float:
    duration = float(row.get("adjusted_duration") or 0.0)
    if duration > 0:
        return duration
    start = float(row.get("adjusted_start") or row.get("start") or 0.0)
    end = float(row.get("adjusted_end") or row.get("end") or 0.0)
    return max(end - start, 0.1)


def caption_source_text(row: dict[str, object]) -> str:
    transcript = str(row.get("transcript") or "").strip()
    if transcript:
        return clean_caption_text(transcript)
    fallback = str(row.get("peak_text") or row.get("title") or "Legenda do corte")
    return clean_caption_text(fallback)


def caption_events(row: dict[str, object], chars_per_line: int, max_lines: int, duration: float) -> list[CaptionEvent]:
    segment_events = caption_events_from_segments(row, chars_per_line, max_lines)
    if segment_events:
        return normalize_caption_events(segment_events, duration)
    text = caption_source_text(row)
    chunks = caption_chunks(text, chars_per_line, max_lines, duration)
    return normalize_caption_events(distributed_caption_events(chunks, duration), duration)


def caption_events_from_segments(row: dict[str, object], chars_per_line: int, max_lines: int) -> list[CaptionEvent]:
    segments = row.get("caption_segments")
    if not isinstance(segments, list):
        return []
    start = float(row.get("adjusted_start") or row.get("start") or 0.0)
    end = float(row.get("adjusted_end") or row.get("end") or 0.0)
    events = [event_from_segment(item, start, end, chars_per_line, max_lines) for item in segments]
    return [event for event in events if event is not None]


def event_from_segment(
    item: object, clip_start: float, clip_end: float, chars_per_line: int, max_lines: int
) -> CaptionEvent | None:
    if not isinstance(item, dict):
        return None
    start = max(float(item.get("start") or 0.0), clip_start) - clip_start
    end = min(float(item.get("end") or 0.0), clip_end) - clip_start
    text = clean_caption_text(str(item.get("text") or ""))
    if not text or end <= start:
        return None
    return CaptionEvent(round(start, 3), round(max(end, start + 0.35), 3), text)


def normalize_caption_events(events: list[CaptionEvent], duration: float) -> list[CaptionEvent]:
    sorted_events = sorted(events, key=lambda event: (event.start, event.end))
    normalized: list[CaptionEvent] = []
    for index, event in enumerate(sorted_events):
        start = clamp(event.start, 0.0, duration)
        end = clamp(event.end, start, duration)
        if index + 1 < len(sorted_events):
            next_start = clamp(sorted_events[index + 1].start, 0.0, duration)
            end = min(end, max(start, next_start - 0.04))
        if end - start >= 0.12:
            normalized.append(CaptionEvent(round(start, 3), round(end, 3), event.text))
    return normalized


def distributed_caption_events(chunks: list[str], duration: float) -> list[CaptionEvent]:
    slot = duration / max(len(chunks), 1)
    events: list[CaptionEvent] = []
    for index, chunk in enumerate(chunks):
        start = index * slot
        end = duration if index == len(chunks) - 1 else (index + 1) * slot
        events.append(CaptionEvent(round(start, 3), round(end, 3), chunk))
    return events


def clean_caption_text(text: str) -> str:
    clean = normalize_caption_symbols(text)
    clean = re.sub(r"(^|\s)(>{1,3}|-{1,2})\s*", " ", clean)
    clean = re.sub(r"\s+", " ", clean)
    clean = re.sub(r"\s+([,.;:!?])", r"\1", clean)
    clean = re.sub(r"([,.;:!?])([^\s,.;:!?])", r"\1 \2", clean)
    clean = re.sub(r"^(né\??|aham|uhum|hum|então|mas)\s+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\b(\w+)(\s+\1\b){2,}", r"\1", clean, flags=re.IGNORECASE)
    return clean.strip(" -")


def normalize_caption_symbols(text: str) -> str:
    return (
        text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        .replace("…", "...").replace("♪", " ").replace("\ufeff", " ")
    )


def caption_chunks(text: str, chars_per_line: int, max_lines: int, duration: float) -> list[str]:
    capacity = max(18, chars_per_line * max_lines)
    chunks = greedy_word_chunks(text.split(), capacity)
    limit = max(1, int(max(duration, 1.0) / 1.35))
    if len(chunks) > limit:
        chunks = chunks[:limit]
        chunks[-1] = ellipsize_caption(chunks[-1])
    return chunks or ["Legenda do corte"]


def greedy_word_chunks(words: list[str], capacity: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if current and len(candidate) > capacity:
            chunks.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        chunks.append(" ".join(current))
    return chunks


def ellipsize_caption(text: str) -> str:
    clean = text.rstrip(" .,;:")
    return f"{clean}..." if clean else "..."


def ass_document(events: list[CaptionEvent], duration: float, preset: PlatformPreset, chars_per_line: int, max_lines: int) -> str:
    return "\n".join([
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {preset.width}",
        f"PlayResY: {preset.height}",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
        "MarginR, MarginV, Encoding",
        ass_style_line(preset),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        *ass_dialogue_lines(events, duration, chars_per_line, max_lines),
        "",
    ])


def ass_style_line(preset: PlatformPreset) -> str:
    font_size = 72 if preset.height >= 1600 else 54
    margin_v = 250 if preset.height >= 1600 else 95
    outline = 7 if preset.height >= 1600 else 5
    return (
        "Style: Default,Arial,"
        f"{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H99000000,-1,0,0,0,100,100,0,0,1,"
        f"{outline},0,2,80,80,{margin_v},1"
    )


def ass_dialogue_lines(events: list[CaptionEvent], duration: float, chars_per_line: int, max_lines: int) -> list[str]:
    lines: list[str] = []
    for event in events:
        start = min(max(event.start, 0.0), duration)
        end = min(max(event.end, start + 0.15), duration)
        text = ass_escape_text(wrap_caption_text(event.text, chars_per_line, max_lines))
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{text}")
    return lines


def wrap_caption_text(text: str, chars_per_line: int, max_lines: int) -> str:
    lines = greedy_word_chunks(text.split(), max(chars_per_line, 12))
    if len(lines) > max_lines:
        lines = lines[:max_lines - 1] + [" ".join(lines[max_lines - 1:])]
    return r"\N".join(lines)


def ass_escape_text(text: str) -> str:
    return text.replace("{", "(").replace("}", ")")


def ass_time(value: float) -> str:
    centiseconds = int(round(max(value, 0.0) * 100))
    hours, rem = divmod(centiseconds, 360000)
    minutes, rem = divmod(rem, 6000)
    seconds, cs = divmod(rem, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{cs:02d}"


def render_captioned_clip(
    input_path: Path, output_path: Path, subtitle_path: Path, row: dict[str, object],
    preset: PlatformPreset, out_dir: Path, ffmpeg: str
) -> None:
    filters = [camera_filter(preset, row), f"ass={subtitle_filter_path(subtitle_path, out_dir)}"]
    effect = effect_filter(row)
    if effect:
        filters.append(effect)
    overlay = overlay_filter(row, preset)
    if overlay:
        filters.append(overlay)
    filter_arg = ",".join(filters)
    command = [
        ffmpeg, "-y", "-ss", fmt_time(caption_trim_start(row)), "-i", str(input_path),
        "-t", fmt_time(caption_duration(row)), "-vf", filter_arg,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", video_crf(row),
        "-c:a", "aac", "-movflags", "+faststart", str(output_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True, cwd=str(out_dir))


def caption_trim_start(row: dict[str, object]) -> float:
    if isinstance(row.get("file"), str) and row.get("file"):
        return 0.0
    return float(row.get("trim_start_seconds") or 0.0)


def subtitle_filter_path(subtitle_path: Path, out_dir: Path) -> str:
    return subtitle_path.relative_to(out_dir).as_posix()


def captioned_row(
    row: dict[str, object], preset: PlatformPreset, output_path: Path, subtitle_path: Path
) -> dict[str, object]:
    return {
        "rank": row.get("rank"),
        "platform": preset.key,
        "label": preset.label,
        "width": preset.width,
        "height": preset.height,
        "file": str(output_path),
        "subtitle_file": str(subtitle_path),
        "adjusted_start": row.get("adjusted_start"),
        "adjusted_end": row.get("adjusted_end"),
        "adjusted_duration": caption_duration(row),
        "publish_metadata": row.get("publish_metadata") if isinstance(row.get("publish_metadata"), dict) else {},
        "camera": camera_from_row(row),
        "effect": effect_from_row(row),
        "overlay": overlay_from_row(row),
    }


def normalize_platforms(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item) in PLATFORM_PRESETS]


def resolve_media_path(base_dir: Path, clip_file: str) -> Path:
    path = Path(clip_file)
    return path if path.is_absolute() else base_dir / path


def render_platform_clip(
    input_path: Path, output_path: Path, start: float, duration: float,
    preset: PlatformPreset, row: dict[str, object], ffmpeg: str
) -> None:
    filter_arg = video_filter(preset, row)
    command = [
        ffmpeg, "-y", "-ss", fmt_time(start), "-i", str(input_path), "-t", fmt_time(duration),
        "-vf", filter_arg, "-c:v", "libx264", "-preset", "veryfast", "-crf", video_crf(row),
        "-c:a", "aac", "-movflags", "+faststart", str(output_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)


def platform_filter(preset: PlatformPreset) -> str:
    return camera_filter(preset, {})


def video_filter(preset: PlatformPreset, row: dict[str, object]) -> str:
    filters = [camera_filter(preset, row)]
    effect = effect_filter(row)
    if effect:
        filters.append(effect)
    overlay = overlay_filter(row, preset)
    if overlay:
        filters.append(overlay)
    return ",".join(filters)


def camera_filter(preset: PlatformPreset, row: dict[str, object]) -> str:
    camera = camera_from_row(row)
    zoom = camera_zoom(camera)
    target_w = int(round(preset.width * zoom))
    target_h = int(round(preset.height * zoom))
    return ",".join([
        f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase",
        f"crop={preset.width}:{preset.height}:x='{camera_crop_x(camera)}':y='(ih-oh)/2'",
        "setsar=1",
    ])


def camera_crop_x(camera: dict[str, object]) -> str:
    key = str(camera["key"])
    strength = float(camera["strength"])
    if key == "face-left":
        return crop_ratio_expr(0.22 - strength * 0.0012)
    if key == "face-right":
        return crop_ratio_expr(0.78 + strength * 0.0012)
    if key == "alternate":
        amplitude = 0.12 + (strength / 100.0) * 0.22
        return f"(iw-ow)*(0.5+{amplitude:.3f}*sin(2*PI*t/6))"
    return crop_ratio_expr(0.5)


def crop_ratio_expr(ratio: float) -> str:
    return f"(iw-ow)*{clamp(ratio, 0.0, 1.0):.3f}"


def camera_zoom(camera: dict[str, object]) -> float:
    key = str(camera["key"])
    strength = float(camera["strength"])
    if key == "face-center":
        return 1.06 + (strength / 100.0) * 0.08
    if key == "soft-zoom":
        return 1.04 + (strength / 100.0) * 0.10
    if key == "punch-in":
        return 1.12 + (strength / 100.0) * 0.16
    return 1.0


def camera_from_row(row: dict[str, object]) -> dict[str, object]:
    raw = row.get("camera")
    if not isinstance(raw, dict):
        return default_camera()
    key = str(raw.get("key") or "center")
    preset = CAMERA_PRESETS.get(key, CAMERA_PRESETS["center"])
    strength = clamp(float(raw.get("strength") if raw.get("strength") is not None else 60.0), 0.0, 100.0)
    return {"key": preset.key, "label": preset.label, "strength": strength}


def default_camera() -> dict[str, object]:
    return {"key": "center", "label": CAMERA_PRESETS["center"].label, "strength": 60}


def effect_filter(row: dict[str, object]) -> str:
    effect = effect_from_row(row)
    key = effect["key"]
    intensity = float(effect["intensity"])
    if key == "none" or intensity <= 0:
        return ""
    if key == "light-grain":
        return f"noise=alls={scaled_value(intensity, 4, 14)}:allf=t+u"
    if key == "old-film":
        return f"curves=preset=vintage,eq=saturation=0.7:contrast=1.16:brightness=-0.04,noise=alls={scaled_value(intensity, 5, 16)}:allf=t+u,vignette=PI/4"
    if key == "vhs":
        return f"eq=saturation=0.62:contrast=1.2:brightness=-0.05,noise=alls={scaled_value(intensity, 7, 20)}:allf=t+u"
    if key == "bw-old":
        return f"hue=s=0,eq=contrast=1.18:brightness=-0.03,noise=alls={scaled_value(intensity, 6, 18)}:allf=t+u,vignette=PI/4"
    return ""


def video_crf(row: dict[str, object]) -> str:
    return "24" if effect_from_row(row)["key"] != "none" else "23"


def scaled_value(intensity: float, low: int, high: int) -> int:
    value = low + ((clamp(intensity, 0.0, 100.0) / 100.0) * (high - low))
    return int(round(value))


def effect_from_row(row: dict[str, object]) -> dict[str, object]:
    raw = row.get("effect")
    if not isinstance(raw, dict):
        return {"key": "none", "label": EFFECT_PRESETS["none"].label, "intensity": 0}
    key = str(raw.get("key") or "none")
    preset = EFFECT_PRESETS.get(key, EFFECT_PRESETS["none"])
    intensity = clamp(float(raw.get("intensity") or 0.0), 0.0, 100.0)
    return {"key": preset.key, "label": preset.label, "intensity": intensity}


def overlay_filter(row: dict[str, object], preset: PlatformPreset) -> str:
    overlay = overlay_from_row(row)
    if overlay["key"] == "none":
        return ""
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


def overlay_from_row(row: dict[str, object]) -> dict[str, object]:
    raw = row.get("overlay")
    if not isinstance(raw, dict):
        return default_overlay()
    key = str(raw.get("key") or "none")
    preset = OVERLAY_PRESETS.get(key, OVERLAY_PRESETS["none"])
    if preset.key == "none":
        return default_overlay()
    return {
        "key": preset.key,
        "label": preset.label,
        "x": clamp(float(raw.get("x") if raw.get("x") is not None else 0.62), 0.0, 1.0),
        "y": clamp(float(raw.get("y") if raw.get("y") is not None else 0.78), 0.0, 1.0),
        "width": clamp(float(raw.get("width") if raw.get("width") is not None else 0.34), 0.18, 0.72),
        "opacity": clamp(float(raw.get("opacity") if raw.get("opacity") is not None else 95.0), 35.0, 100.0),
    }


def default_overlay() -> dict[str, object]:
    return {"key": "none", "label": OVERLAY_PRESETS["none"].label, "x": 0.62, "y": 0.78, "width": 0.34, "opacity": 95}


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


def clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


def rendered_row(row: dict[str, object], preset: PlatformPreset, output_path: Path) -> dict[str, object]:
    return {
        "rank": row.get("rank"),
        "platform": preset.key,
        "label": preset.label,
        "width": preset.width,
        "height": preset.height,
        "file": str(output_path),
        "adjusted_start": row.get("adjusted_start"),
        "adjusted_end": row.get("adjusted_end"),
        "adjusted_duration": row.get("adjusted_duration"),
        "camera": camera_from_row(row),
        "effect": effect_from_row(row),
        "overlay": overlay_from_row(row),
    }


def build_config(args: argparse.Namespace) -> CuttedConfig:
    is_vertical_preset = args.preset in {"tiktok", "shorts", "reels"}
    return CuttedConfig(
        clips=args.clips,
        min_duration=args.min_duration if args.min_duration is not None else (30.0 if is_vertical_preset else 30.0),
        max_duration=args.max_duration if args.max_duration is not None else (70.0 if is_vertical_preset else 90.0),
        target_duration=args.target_duration if args.target_duration is not None else (42.0 if is_vertical_preset else 60.0),
        smart_boundaries=args.smart_boundaries if args.smart_boundaries is not None else is_vertical_preset,
        lead_in=args.lead_in,
        tail_out=args.tail_out,
        preset=args.preset,
    )


def prepare_source(args: argparse.Namespace, out_dir: Path, ffmpeg: str) -> SourceMedia:
    if args.youtube_url:
        return prepare_youtube_source(args, out_dir, ffmpeg)
    if not args.video:
        raise RuntimeError("Provide a local video path or --youtube-url.")
    video = args.video.resolve()
    require_file(video)
    return SourceMedia(str(video), video, video.name, ())


def prepare_youtube_source(args: argparse.Namespace, out_dir: Path, ffmpeg: str) -> SourceMedia:
    url = args.youtube_url
    temp_dir = out_dir / "_source"
    temp_dir.mkdir(exist_ok=True)
    label = youtube_title(url)
    transcript = try_youtube_transcript(url, temp_dir, args.language) if args.youtube_captions else None
    transcribe_source = transcript or download_youtube_audio(url, temp_dir / "audio.m4a", ffmpeg)
    render_source = youtube_render_url(url)
    cleanup = (transcribe_source,) if isinstance(transcribe_source, Path) else ()
    return SourceMedia(render_source, transcribe_source, label, cleanup)


def require_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Video file not found: {path}")


def find_ffmpeg() -> str:
    env_bin = os.environ.get("FFMPEG_BIN")
    if env_bin:
        return env_bin
    path_bin = shutil.which("ffmpeg")
    if path_bin:
        return path_bin
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError("FFmpeg not found. Install ffmpeg or `python -m pip install imageio-ffmpeg`.") from exc


def find_ffprobe() -> str | None:
    env_bin = os.environ.get("FFPROBE_BIN")
    if env_bin:
        return env_bin
    return shutil.which("ffprobe")


def probe_duration(video: Path | str, ffprobe: str | None) -> float:
    if not ffprobe:
        return 0.0
    command = [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def yt_dlp_command() -> list[str]:
    path_bin = shutil.which("yt-dlp")
    if path_bin:
        return [path_bin]
    return [sys.executable, "-m", "yt_dlp"]


def youtube_title(url: str) -> str:
    command = yt_dlp_command() + ["--no-playlist", "--print", "%(title)s", url]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return result.stdout.strip() or "YouTube video"


def youtube_render_url(url: str) -> str:
    command = yt_dlp_command() + ["-f", "18/b[height<=480]/best", "-g", "--no-playlist", url]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    urls = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith(("http://", "https://"))]
    if not urls:
        raise RuntimeError("Could not resolve a renderable YouTube media URL.")
    return urls[0]


def try_youtube_transcript(url: str, temp_dir: Path, language: str | None) -> Path | None:
    lang = youtube_caption_lang(language)
    command = yt_dlp_command() + [
        "--skip-download",
        "--write-auto-subs",
        "--sub-langs", lang,
        "--sub-format", "json3",
        "--no-playlist",
        "-o", str(temp_dir / "captions"),
        url,
    ]
    subprocess.run(command, check=False, capture_output=True, text=True)
    captions = sorted(temp_dir.glob("*.json3"))
    if not captions:
        return None
    transcript = temp_dir / "youtube-transcript.json"
    write_youtube_transcript(captions[0], transcript)
    return transcript


def youtube_caption_lang(language: str | None) -> str:
    if not language:
        return "pt-orig,pt"
    if language == "pt":
        return "pt-orig,pt"
    return f"{language}-orig,{language}"


def write_youtube_transcript(caption_path: Path, transcript_path: Path) -> None:
    data = json.loads(caption_path.read_text(encoding="utf-8-sig"))
    rows = [caption_event_to_segment(event) for event in data.get("events", [])]
    segments = [row for row in rows if row and row["text"]]
    transcript_path.write_text(json.dumps(segments, ensure_ascii=False, indent=2), encoding="utf-8")


def caption_event_to_segment(event: dict[str, object]) -> dict[str, object] | None:
    start_ms = event.get("tStartMs")
    if start_ms is None or "segs" not in event:
        return None
    duration_ms = float(event.get("dDurationMs") or 2500)
    text = "".join(str(seg.get("utf8", "")) for seg in event.get("segs", []) if isinstance(seg, dict))
    text = " ".join(text.replace("\n", " ").split())
    start = float(start_ms) / 1000.0
    return {"start": start, "end": start + (duration_ms / 1000.0), "text": text}


def download_youtube_audio(url: str, output: Path, ffmpeg: str) -> Path:
    command = yt_dlp_command() + [
        "--no-playlist",
        "--ffmpeg-location", ffmpeg,
        "-f", "139/bestaudio[ext=m4a]/bestaudio",
        "-o", str(output),
        url,
    ]
    subprocess.run(command, check=True)
    return output


def cleanup_sources(paths: tuple[Path, ...]) -> None:
    for path in paths:
        resolved = path.resolve()
        if resolved.exists() and "_source" in resolved.parts:
            resolved.unlink()
        parent = resolved.parent
        if parent.exists() and parent.name == "_source":
            for child in parent.iterdir():
                if child.is_file():
                    child.unlink()
            if not any(parent.iterdir()):
                parent.rmdir()


def load_segments(args: argparse.Namespace, video: Path | str) -> list[Segment]:
    if args.transcript_json:
        return read_transcript_json(args.transcript_json)
    if isinstance(video, Path) and video.suffix.lower() == ".json":
        return read_transcript_json(video)
    try:
        return transcribe_with_faster_whisper(video, args.model, args.language)
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install faster-whisper or pass --transcript-json with timestamped segments.") from exc


def read_transcript_json(path: Path) -> list[Segment]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = data["segments"] if isinstance(data, dict) and "segments" in data else data
    segments = [Segment(float(row["start"]), float(row["end"]), str(row["text"]).strip()) for row in rows]
    return [segment for segment in segments if segment.text and segment.end > segment.start]


def transcribe_with_faster_whisper(video: Path | str, model_name: str, language: str | None) -> list[Segment]:
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    rows, _info = model.transcribe(str(video), language=language, vad_filter=True)
    segments = [Segment(float(row.start), float(row.end), row.text.strip()) for row in rows]
    return [segment for segment in segments if segment.text]


def pick_moments(segments: list[Segment], config: CuttedConfig, video_duration: float) -> list[Moment]:
    if not segments:
        raise RuntimeError("No transcript segments found.")
    candidates = build_candidates(segments, config, video_duration)
    ranked = sorted(candidates, key=lambda item: item.score, reverse=True)
    selected = suppress_overlaps(ranked, config.clips)
    return [with_rank(moment, index + 1) for index, moment in enumerate(sorted(selected, key=lambda item: item.start))]


def build_candidates(segments: list[Segment], config: CuttedConfig, video_duration: float) -> list[Moment]:
    candidates: list[Moment] = []
    for index in range(len(segments)):
        group = collect_window(segments, index, config)
        if group:
            candidates.append(moment_from_segments(group, config, video_duration))
    return candidates


def collect_window(segments: list[Segment], index: int, config: CuttedConfig) -> list[Segment] | None:
    group: list[Segment] = []
    choices: list[list[Segment]] = []
    for segment in segments[index:]:
        if group and segment.end - group[0].start > config.max_duration:
            break
        group.append(segment)
        if segment.end - group[0].start >= config.min_duration:
            choices.append(group.copy())
    if not choices:
        return None
    return max(choices, key=lambda item: candidate_fit_score(item, config))


def candidate_fit_score(group: list[Segment], config: CuttedConfig) -> float:
    transcript = " ".join(segment.text for segment in group)
    duration = group[-1].end - group[0].start
    duration_penalty = abs(duration - config.target_duration) / max(config.target_duration, 1.0)
    return text_score(transcript) + boundary_score(group, config.smart_boundaries) - duration_penalty


def boundary_score(group: list[Segment], smart_boundaries: bool) -> float:
    if not smart_boundaries:
        return 0.0
    first = normalize_text(group[0].text)
    last = normalize_text(group[-1].text)
    score = 0.0
    score += 1.3 if ends_like_finished_thought(last) else -2.0
    score += -1.0 if starts_like_fragment(first) else 0.7
    score += -2.0 if ends_weakly(last) else 0.0
    return score


def moment_from_segments(group: list[Segment], config: CuttedConfig, video_duration: float) -> Moment:
    transcript = " ".join(segment.text for segment in group)
    peak_segment = max(group, key=lambda item: text_score(item.text))
    score = window_score(group, transcript, config)
    title = make_title(peak_segment.text)
    start = smart_start(group[0].start, config)
    end = smart_end(group[-1].end, video_duration, config)
    return Moment(0, start, end, midpoint(peak_segment), score, title, reason(score), transcript, peak_segment.text,
                  None, None, tuple(group))


def smart_start(start: float, config: CuttedConfig) -> float:
    if not config.smart_boundaries:
        return start
    return max(0.0, start - config.lead_in)


def smart_end(end: float, video_duration: float, config: CuttedConfig) -> float:
    if not config.smart_boundaries:
        return end
    adjusted = end + config.tail_out
    if video_duration > 0:
        return min(video_duration, adjusted)
    return adjusted


def text_score(text: str) -> float:
    lower = text.lower()
    keywords = ["porque", "entao", "verdade", "erro", "segredo", "absurdo", "importante", "aprendi", "dinheiro"]
    keyword_score = sum(1.2 for word in keywords if word in lower)
    punctuation = text.count("!") * 1.5 + text.count("?")
    density = min(len(text.split()) / 22.0, 2.0)
    return keyword_score + punctuation + density


def window_score(group: list[Segment], transcript: str, config: CuttedConfig) -> float:
    duration = group[-1].end - group[0].start
    pace = min(len(transcript.split()) / max(duration, 1.0), 4.0)
    peak = max(text_score(segment.text) for segment in group)
    duration_fit = max(0.0, 2.0 - abs(duration - config.target_duration) / max(config.target_duration, 1.0))
    boundaries = boundary_score(group, config.smart_boundaries)
    return round((peak * 2.0) + pace + duration_fit + boundaries, 2)


def normalize_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def ends_like_finished_thought(text: str) -> bool:
    clean = text.strip()
    if clean.endswith(TERMINAL_ENDINGS):
        return True
    return not ends_weakly(normalize_text(clean))


def ends_weakly(text: str) -> bool:
    clean = text.strip(" ,.;:!?")
    return any(clean.endswith(ending) for ending in WEAK_ENDINGS)


def starts_like_fragment(text: str) -> bool:
    clean = text.strip()
    return any(clean.startswith(starting) for starting in WEAK_STARTINGS)


def midpoint(segment: Segment) -> float:
    return round((segment.start + segment.end) / 2.0, 2)


def make_title(text: str) -> str:
    words = text.strip().split()
    title = " ".join(words[:10]).strip(" ,.;:!?")
    return title or "Suggested moment"


def reason(score: float) -> str:
    if score >= 9:
        return "Gancho forte, fala densa e bom contexto isolado."
    if score >= 6:
        return "Bom candidato, com pico de fala claro."
    return "Candidato utilizavel; revise o corte antes de exportar."


def suppress_overlaps(candidates: list[Moment], count: int) -> list[Moment]:
    selected: list[Moment] = []
    for candidate in candidates:
        if len(selected) >= count:
            break
        if all(overlap_ratio(candidate, item) < 0.35 for item in selected):
            selected.append(candidate)
    return selected


def overlap_ratio(left: Moment, right: Moment) -> float:
    overlap = max(0.0, min(left.end, right.end) - max(left.start, right.start))
    shortest = max(1.0, min(left.end - left.start, right.end - right.start))
    return overlap / shortest


def with_rank(moment: Moment, rank: int) -> Moment:
    return Moment(rank, moment.start, moment.end, moment.peak, moment.score, moment.title, moment.reason,
                  moment.transcript, moment.peak_text, moment.clip_file, moment.frame_file, moment.caption_segments)


def render_outputs(video: Path | str, out_dir: Path, moments: list[Moment], ffmpeg: str, skip_render: bool) -> list[Moment]:
    clips_dir = out_dir / "clips"
    frames_dir = out_dir / "frames"
    clips_dir.mkdir(exist_ok=True)
    frames_dir.mkdir(exist_ok=True)
    rendered = []
    for moment in moments:
        rendered.append(render_one(video, clips_dir, frames_dir, moment, ffmpeg, skip_render))
    return rendered


def render_one(video: Path | str, clips_dir: Path, frames_dir: Path, moment: Moment, ffmpeg: str, skip_render: bool) -> Moment:
    stem = f"clip-{moment.rank:03d}"
    clip_path = clips_dir / f"{stem}.mp4"
    frame_path = frames_dir / f"{stem}.jpg"
    if not skip_render:
        cut_clip(video, clip_path, moment.start, moment.end, ffmpeg)
        extract_frame(video, frame_path, moment.peak, ffmpeg)
    return Moment(moment.rank, moment.start, moment.end, moment.peak, moment.score, moment.title, moment.reason,
                  moment.transcript, moment.peak_text, rel(clip_path, clips_dir.parent), rel(frame_path, frames_dir.parent),
                  moment.caption_segments)


def cut_clip(video: Path | str, output: Path, start: float, end: float, ffmpeg: str) -> None:
    command = [ffmpeg, "-y", "-ss", fmt_time(start), "-i", str(video), "-t", fmt_time(end - start),
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-movflags", "+faststart", str(output)]
    subprocess.run(command, check=True, capture_output=True, text=True)


def extract_frame(video: Path | str, output: Path, timestamp: float, ffmpeg: str) -> None:
    command = [ffmpeg, "-y", "-ss", fmt_time(timestamp), "-i", str(video), "-frames:v", "1",
               "-q:v", "2", str(output)]
    subprocess.run(command, check=True, capture_output=True, text=True)


def fmt_time(value: float) -> str:
    return f"{max(value, 0.0):.3f}"


def rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def write_json(path: Path, moments: list[Moment], source: str, duration: float, config: CuttedConfig) -> None:
    payload = {
        "source": source,
        "duration": duration,
        "config": config_to_dict(config),
        "moments": [moment_to_dict(item) for item in moments],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def config_to_dict(config: CuttedConfig) -> dict[str, object]:
    return {
        "clips": config.clips,
        "min_duration": config.min_duration,
        "max_duration": config.max_duration,
        "target_duration": config.target_duration,
        "smart_boundaries": config.smart_boundaries,
        "lead_in": config.lead_in,
        "tail_out": config.tail_out,
        "preset": config.preset,
    }


def moment_to_dict(moment: Moment) -> dict[str, object]:
    return {
        "rank": moment.rank, "start": moment.start, "end": moment.end, "peak": moment.peak, "score": moment.score,
        "title": moment.title, "reason": moment.reason, "transcript": moment.transcript,
        "peak_text": moment.peak_text, "clip_file": moment.clip_file, "frame_file": moment.frame_file,
        "caption_segments": [segment_to_dict(item) for item in moment.caption_segments],
    }


def segment_to_dict(segment: Segment) -> dict[str, object]:
    return {"start": segment.start, "end": segment.end, "text": segment.text}


def write_html(path: Path, moments: list[Moment], source_label: str) -> None:
    cards = "\n".join(card_html(moment) for moment in moments)
    data = json.dumps({"moments": [moment_to_dict(item) for item in moments]}, ensure_ascii=False)
    path.write_text(page_html(source_label, cards, data), encoding="utf-8")


def card_html(moment: Moment) -> str:
    video_tag = media_html(moment)
    duration = max(0.0, moment.end - moment.start)
    return f"""
    <article class="card" data-rank="{moment.rank}" data-start="{moment.start:.3f}" data-end="{moment.end:.3f}" data-duration="{duration:.3f}">
      <div class="media">{video_tag}</div>
      <div class="timeline-editor">
        <div class="timeline-head">
          <span>Ajuste fino</span>
          <output data-trim-summary>Final: {moment.start:.1f}s - {moment.end:.1f}s ({duration:.1f}s)</output>
        </div>
        <div class="timeline" aria-label="Ajuste visual de corte">
          <div class="timeline-track">
            <div class="timeline-fill" data-trim-fill></div>
          </div>
          <input aria-label="Inicio do corte" data-trim="start" type="range" min="0" max="{duration:.1f}" step="0.1" value="0">
          <input aria-label="Fim do corte" data-trim="end" type="range" min="0" max="{duration:.1f}" step="0.1" value="{duration:.1f}">
        </div>
        <div class="timeline-values">
          <span>Inicio +<output data-output="start">0.0s</output></span>
          <span>Fim -<output data-output="end">0.0s</output></span>
        </div>
      </div>
      <div class="format-editor">
        <div class="format-head">
          <span>Destinos deste corte</span>
          <output data-platform-summary>Nenhum destino marcado</output>
        </div>
        <div class="platform-tags" role="group" aria-label="Destinos do clip">
          <button data-platform="tiktok">TikTok</button>
          <button data-platform="shorts">Shorts</button>
          <button data-platform="instagram">Instagram</button>
          <button data-platform="facebook">Facebook</button>
          <button data-platform="youtube">YouTube</button>
        </div>
      </div>
      <div class="body">
        <div class="top"><span>#{moment.rank:02d}</span><strong>{html.escape(moment.title)}</strong></div>
        <p class="peak">{html.escape(moment.peak_text)}</p>
        <p>{html.escape(moment.reason)}</p>
        <dl><dt>Score</dt><dd>{moment.score}</dd><dt>Inicio</dt><dd>{moment.start:.1f}s</dd><dt>Fim</dt><dd>{moment.end:.1f}s</dd></dl>
        <details><summary>Transcript</summary><p>{html.escape(moment.transcript)}</p></details>
        <div class="actions">
          <button data-action="like">Gostei</button>
          <button data-action="discard">Descartar</button>
          <button data-action="reset-trim">Resetar corte</button>
        </div>
      </div>
    </article>"""


def media_html(moment: Moment) -> str:
    token = preview_cache_token(moment)
    poster = html.escape(cache_busted_url(moment.frame_file, token))
    clip = html.escape(cache_busted_url(moment.clip_file, token))
    if clip:
        return f'<video controls preload="metadata" poster="{poster}" src="{clip}"></video>'
    if poster:
        return f'<img src="{poster}" alt="Peak frame for clip {moment.rank}">'
    return '<div class="placeholder">Preview pulado</div>'


def cache_busted_url(value: str | None, token: str) -> str:
    if not value:
        return ""
    separator = "&" if "?" in value else "?"
    return f"{value}{separator}v={token}"


def preview_cache_token(moment: Moment) -> str:
    return f"{moment.rank}-{int(moment.start * 1000)}-{int(moment.end * 1000)}"


def page_html(source_label: str, cards: str, data: str) -> str:
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CUTED Review</title>
  <style>{css()}</style>
</head>
<body data-format="tiktok" data-tab="edit">
  <header>
    <div><h1>CUTED</h1><p>{html.escape(source_label)}</p></div>
    <div class="header-actions">
      <button id="reset-ui">Zerar interface</button>
      <button id="export">Exportar selecionados</button>
    </div>
  </header>
  <nav class="tabs" aria-label="Fluxo">
    <button data-tab="edit" class="active">1. Cortes e formatos</button>
    <button data-tab="camera">2. Camera</button>
    <button data-tab="effects">3. Efeitos</button>
    <button data-tab="overlays">4. Chamadas</button>
    <button data-tab="final">5. Final</button>
  </nav>
  <section class="config" aria-label="Configuracao de formato">
    <div>
      <strong>Formato</strong>
      <span data-format-hint>TikTok/Reels/Shorts - 9:16</span>
    </div>
    <div class="segments" role="group" aria-label="Formato do preview">
      <button data-format="tiktok" class="active">TikTok</button>
      <button data-format="shorts">Shorts</button>
      <button data-format="youtube">YouTube</button>
      <button data-format="instagram">Instagram</button>
      <button data-format="facebook">Facebook</button>
    </div>
  </section>
  <section class="camera-stage">
    <div class="stage-head">
      <div>
        <strong>Camera</strong>
        <p>Escolha um enquadramento por corte antes dos efeitos.</p>
      </div>
      <button id="continue-effects">Continuar para efeitos</button>
    </div>
    <div class="camera-summary" data-camera-summary>Nenhum corte marcado ainda.</div>
    <div class="camera-preview" data-camera-preview></div>
  </section>
  <section class="effect-stage">
    <div class="stage-head">
      <div>
        <strong>Efeitos</strong>
        <p>Aplique um look por corte antes do render final.</p>
      </div>
      <button id="continue-overlays">Continuar para chamadas</button>
    </div>
    <div class="effect-summary" data-effect-summary>Nenhum corte marcado ainda.</div>
    <div class="effect-preview" data-effect-preview></div>
  </section>
  <section class="overlay-stage">
    <div class="stage-head">
      <div>
        <strong>Chamadas</strong>
        <p>Escolha um card por corte, ajuste legenda e fixe tudo no render final.</p>
      </div>
      <button id="continue-final">Continuar para final</button>
    </div>
    <div class="caption-settings" aria-label="Configuracao de legenda">
      <label>Linhas
        <select data-caption-lines>
          <option value="2" selected>2 linhas</option>
          <option value="1">1 linha</option>
          <option value="3">3 linhas</option>
        </select>
      </label>
      <label>Largura
        <input data-caption-width type="number" min="18" max="42" value="28">
      </label>
    </div>
    <div class="overlay-summary" data-overlay-summary>Nenhum corte marcado ainda.</div>
    <div class="overlay-preview" data-overlay-preview></div>
  </section>
  <section class="final-stage">
    <div class="stage-head">
      <div>
        <strong>Resultados</strong>
        <p data-final-summary>Continue da aba Chamadas para renderizar os videos.</p>
      </div>
      <div class="header-actions">
        <button id="finalize-videos">Renderizar novamente</button>
        <button id="export-final-queue">Exportar fila</button>
      </div>
    </div>
    <div class="render-status" data-render-status></div>
    <div class="render-results" data-render-results></div>
  </section>
  <main>{cards}</main>
  <script>window.CUTTED_DATA = {data}; window.CUTTED_SCRIPT = {json.dumps(str(Path(__file__).resolve()))};</script>
  <script>{js()}</script>
</body>
</html>"""


def css() -> str:
    return """
*{box-sizing:border-box}body{margin:0;background:#050505;color:#f4f4f4;font:14px/1.45 Arial,sans-serif}
header{position:sticky;top:0;z-index:2;display:flex;justify-content:space-between;gap:16px;align-items:center;padding:18px 22px;background:#050505;border-bottom:1px solid #202020}.header-actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
h1{margin:0;font-size:22px}header p{margin:3px 0 0;color:#9a9a9a}.tabs{position:sticky;top:75px;z-index:3;display:flex;gap:8px;padding:10px 22px;background:#060606;border-bottom:1px solid #1f1f1f}.tabs button{background:#191919;color:#ddd;border:1px solid #303030;padding:8px 12px}.tabs button.active{background:#f4f4f4;color:#050505;border-color:#f4f4f4}.config{position:sticky;top:126px;z-index:2;display:flex;justify-content:space-between;gap:14px;align-items:center;padding:12px 22px;background:#080808;border-bottom:1px solid #202020}.config strong{display:block;font-size:13px}.config span{color:#9a9a9a;font-size:12px}.segments{display:flex;gap:6px;flex-wrap:wrap}.segments button{background:#191919;color:#ddd;border:1px solid #303030;padding:8px 10px}.segments button.active{background:#f4f4f4;color:#050505;border-color:#f4f4f4}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;padding:18px;align-items:start}
.card{background:#111;border:1px solid #272727;border-radius:8px;overflow:hidden}.card.liked{border-color:#24d17e}.card.discarded{opacity:.42}
.media{position:relative;aspect-ratio:16/9;background:#000;max-height:58vh;transition:aspect-ratio .2s ease;overflow:hidden}.media video,.media img{width:100%;height:100%;object-fit:cover;display:block}.placeholder{display:grid;place-items:center;height:100%;color:#777}
body[data-format=tiktok] .media,body[data-format=shorts] .media,body[data-format=instagram] .media{aspect-ratio:9/16}body[data-format=facebook] .media{aspect-ratio:4/5}body[data-format=youtube] .media{aspect-ratio:16/9}
.caption-item[data-effect=light-grain] .caption-preview video,.caption-item[data-effect=light-grain] .caption-preview img{filter:contrast(1.08) brightness(1.02)}
.caption-item[data-effect=old-film] .caption-preview video,.caption-item[data-effect=old-film] .caption-preview img{filter:sepia(.48) contrast(1.2) saturate(.62) brightness(.92)}
.caption-item[data-effect=vhs] .caption-preview video,.caption-item[data-effect=vhs] .caption-preview img{filter:saturate(.62) contrast(1.22) brightness(.9) hue-rotate(-7deg)}
.caption-item[data-effect=bw-old] .caption-preview video,.caption-item[data-effect=bw-old] .caption-preview img{filter:grayscale(1) contrast(1.22) brightness(.9)}
.caption-item[data-effect=light-grain] .caption-preview:after,.caption-item[data-effect=old-film] .caption-preview:after,.caption-item[data-effect=vhs] .caption-preview:after,.caption-item[data-effect=bw-old] .caption-preview:after{content:"";position:absolute;inset:0;pointer-events:none;opacity:var(--effect-opacity,.24);background-image:radial-gradient(circle at 20% 30%,rgba(255,255,255,.95) 0 1px,transparent 1.6px),radial-gradient(circle at 70% 65%,rgba(0,0,0,.95) 0 1px,transparent 1.8px);background-size:4px 4px,6px 6px;mix-blend-mode:overlay}
.caption-item[data-effect=old-film] .caption-preview:before,.caption-item[data-effect=bw-old] .caption-preview:before{content:"";position:absolute;inset:0;pointer-events:none;z-index:1;background:radial-gradient(circle at center,transparent 44%,rgba(0,0,0,.46) 100%)}
.caption-item[data-effect=vhs] .caption-preview:before{content:"";position:absolute;inset:0;pointer-events:none;z-index:1;background:repeating-linear-gradient(0deg,rgba(255,255,255,.08) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
.body{padding:14px}.top{display:flex;gap:10px;align-items:center}.top span{color:#888}.top strong{font-size:15px}.peak{color:#fff;font-size:16px}
p{color:#bebebe}dl{display:grid;grid-template-columns:auto 1fr;gap:4px 10px;color:#aaa}dt{color:#707070}dd{margin:0}
.timeline-editor{padding:10px 14px 12px;background:#090909;border-top:1px solid #1e1e1e;border-bottom:1px solid #222}.timeline-head{display:flex;justify-content:space-between;gap:12px;color:#aaa;font-size:12px}.timeline-head output{color:#f4f4f4;text-align:right}.timeline{position:relative;height:34px;margin-top:8px}.timeline-track{position:absolute;left:0;right:0;top:14px;height:6px;background:#292929;border-radius:999px;overflow:hidden}.timeline-fill{position:absolute;top:0;bottom:0;background:#f4f4f4;border-radius:999px}.timeline input{position:absolute;inset:0;width:100%;height:34px;margin:0;background:transparent;pointer-events:none;-webkit-appearance:none;appearance:none}.timeline input::-webkit-slider-thumb{width:18px;height:18px;border-radius:50%;background:#f4f4f4;border:2px solid #050505;pointer-events:auto;-webkit-appearance:none;appearance:none}.timeline input::-webkit-slider-runnable-track{background:transparent}.timeline input::-moz-range-thumb{width:18px;height:18px;border-radius:50%;background:#f4f4f4;border:2px solid #050505;pointer-events:auto}.timeline input::-moz-range-track{background:transparent}.timeline-values{display:flex;justify-content:space-between;color:#aaa;font-size:12px}
.format-editor{display:block;padding:12px 14px;background:#090909;border-bottom:1px solid #222}.format-head{display:flex;justify-content:space-between;gap:12px;color:#aaa;font-size:12px}.format-head output{color:#f4f4f4;text-align:right}.platform-tags{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}.platform-tags button{background:#191919;color:#ddd;border:1px solid #333}.platform-tags button.active{background:#24d17e;color:#04130b;border-color:#24d17e}.camera-stage,.effect-stage,.overlay-stage{display:none;margin:18px;padding:18px;border:1px solid #272727;border-radius:8px;background:#111}.stage-head{display:flex;justify-content:space-between;gap:16px;align-items:center}.camera-stage p,.effect-stage p,.overlay-stage p{margin:4px 0 0}.caption-settings{display:grid;grid-template-columns:160px 180px;gap:12px;margin-top:16px;max-width:380px}.caption-settings label{display:grid;gap:6px;color:#aaa}.caption-settings select,.caption-settings input{width:100%;background:#050505;color:#f4f4f4;border:1px solid #333;border-radius:6px;padding:9px}.camera-summary,.effect-summary,.overlay-summary{margin-top:12px;color:#aaa}.caption-item{border:1px solid #2a2a2a;border-radius:8px;background:#0a0a0a;overflow:hidden}.caption-preview{position:relative;display:flex;justify-content:center;background:#000;overflow:hidden}.caption-preview video,.caption-preview img{width:100%;max-height:64vh;object-fit:cover;background:#000}.caption-item[data-platform=tiktok] video,.caption-item[data-platform=shorts] video,.caption-item[data-platform=instagram] video{aspect-ratio:9/16}.caption-item[data-platform=facebook] video{aspect-ratio:4/5}.caption-item[data-platform=youtube] video{aspect-ratio:16/9}.caption-item-body{padding:12px}.caption-item strong{display:block}.caption-item span{display:inline-flex;margin:8px 8px 0 0;padding:4px 8px;border-radius:999px;background:#242424;color:#ddd;font-size:12px}.caption-item dl{margin-top:10px}
.camera-preview,.effect-preview,.overlay-preview{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px;margin-top:16px;align-items:start}.camera-card-controls,.effect-card-controls,.overlay-card-controls{display:grid;gap:10px;margin-top:12px}.camera-card-buttons,.effect-card-buttons,.overlay-card-buttons{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.camera-card-buttons button,.effect-card-buttons button,.overlay-card-buttons button{background:#191919;color:#ddd;border:1px solid #333;text-align:left}.camera-card-buttons button.active,.effect-card-buttons button.active,.overlay-card-buttons button.active{background:#102018;border-color:#24d17e}.camera-card-controls label,.effect-card-controls label,.overlay-card-controls label{display:grid;gap:6px;color:#aaa;font-size:12px}.camera-card-controls input,.effect-card-controls input,.overlay-card-controls input{width:100%;accent-color:#24d17e}.camera-empty,.effect-empty,.overlay-empty{padding:18px;border:1px dashed #333;border-radius:8px;color:#aaa}.camera-surface video{object-position:var(--camera-x,50%) 50%;transform:scale(var(--camera-scale,1));transform-origin:var(--camera-x,50%) 50%}.camera-surface[data-camera-key=alternate] video{animation:camera-pan 6s ease-in-out infinite alternate}@keyframes camera-pan{0%{object-position:22% 50%}100%{object-position:78% 50%}}.camera-reticle{position:absolute;inset:14% 22%;border:1px solid rgba(36,209,126,.58);border-radius:8px;box-shadow:0 0 0 999px rgba(0,0,0,.1);pointer-events:none}.overlay-tools{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:end}.overlay-box{position:absolute;z-index:3;left:calc(var(--overlay-x)*100%);top:calc(var(--overlay-y)*100%);width:calc(var(--overlay-width)*100%);min-width:120px;padding:10px 14px 11px 18px;border-left:6px solid var(--overlay-accent,#24d17e);border-radius:8px;background:rgba(0,0,0,var(--overlay-opacity,.92));box-shadow:0 10px 30px rgba(0,0,0,.35);cursor:move;touch-action:none;user-select:none}.overlay-box[data-overlay-key=none]{display:none}.overlay-box strong{font-size:clamp(13px,4vw,20px);line-height:1.05}.overlay-box em{display:block;margin-top:3px;color:rgba(255,255,255,.75);font-style:normal;font-size:clamp(10px,2.4vw,13px);line-height:1.2}.overlay-resize{position:absolute;right:5px;bottom:5px;width:14px;height:14px;padding:0;border:1px solid rgba(255,255,255,.42);border-radius:3px;background:rgba(255,255,255,.18);cursor:nwse-resize}
body[data-tab=camera] main,body[data-tab=camera] .config,body[data-tab=camera] .effect-stage,body[data-tab=camera] .overlay-stage,body[data-tab=camera] .final-stage{display:none}body[data-tab=camera] .camera-stage{display:block}
body[data-tab=effects] main,body[data-tab=effects] .config,body[data-tab=effects] .camera-stage,body[data-tab=effects] .overlay-stage,body[data-tab=effects] .final-stage{display:none}body[data-tab=effects] .effect-stage{display:block}
body[data-tab=overlays] main,body[data-tab=overlays] .config,body[data-tab=overlays] .camera-stage,body[data-tab=overlays] .effect-stage,body[data-tab=overlays] .final-stage{display:none}body[data-tab=overlays] .overlay-stage{display:block}
body[data-tab=final] main,body[data-tab=final] .config,body[data-tab=final] .camera-stage,body[data-tab=final] .effect-stage,body[data-tab=final] .overlay-stage{display:none}body[data-tab=final] .final-stage{display:block}.final-stage{display:none;margin:18px;padding:18px;border:1px solid #272727;border-radius:8px;background:#111}.render-status{margin-top:12px;color:#aaa}.render-results{display:grid;gap:12px;margin-top:14px}.result-item{border:1px solid #303030;border-radius:8px;background:#090909;overflow:hidden}.result-item[open]{border-color:#3b3b3b}.result-item summary{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:12px 14px;border:0;color:#f4f4f4}.result-item summary strong{font-size:14px}.result-item summary span{color:#aaa;font-size:12px}.result-body{display:grid;grid-template-columns:minmax(260px,420px) minmax(240px,1fr);gap:14px;padding:0 14px 14px}.result-body video{width:100%;max-height:70vh;background:#000;border-radius:6px;object-fit:contain}.result-meta{display:grid;align-content:start;gap:10px}.result-meta dl{margin:0}.result-actions{display:flex;gap:8px;flex-wrap:wrap}.result-actions a{display:inline-flex;align-items:center;justify-content:center;min-height:38px;padding:9px 12px;border-radius:6px;background:#f4f4f4;color:#050505;text-decoration:none}.result-actions a.secondary{background:#242424;color:#ddd;border:1px solid #333}
details{border-top:1px solid #242424;margin-top:12px;padding-top:10px}summary{cursor:pointer;color:#ddd}.actions{display:flex;gap:8px;margin-top:12px}
button{background:#f4f4f4;color:#050505;border:0;border-radius:6px;padding:9px 12px;cursor:pointer}#reset-ui,button[data-action=discard]{background:#242424;color:#ddd}
button[data-action=reset-trim]{background:#191919;color:#ddd;border:1px solid #333}
@media(max-width:760px){.tabs{top:94px;overflow:auto}.config{top:144px;align-items:flex-start;flex-direction:column}.segments button{font-size:12px;padding:7px 9px}main{grid-template-columns:1fr;padding:12px}.camera-preview,.effect-preview,.overlay-preview,.caption-settings,.result-body{grid-template-columns:1fr}.stage-head{align-items:flex-start;flex-direction:column}.result-item summary{align-items:flex-start;flex-direction:column}}
"""


def js() -> str:
    return """
if (new URLSearchParams(location.search).has("reset")) {
  localStorage.removeItem("cutted-state");
  localStorage.removeItem("cutted-format");
  localStorage.removeItem("cutted-tab");
  history.replaceState(null, "", location.pathname);
}
const state = JSON.parse(localStorage.getItem("cutted-state") || "{}");
function save(){ localStorage.setItem("cutted-state", JSON.stringify(state)); }
function cardState(rank){
  const raw = state[rank];
  if (typeof raw === "string") return { status: raw, trimStart: 0, trimEnd: 0, platforms: [], camera: defaultCamera(), effect: defaultEffect(), overlay: defaultOverlay() };
  const next = Object.assign({ status: null, trimStart: 0, trimEnd: 0, platforms: [], camera: defaultCamera(), effect: defaultEffect(), overlay: defaultOverlay() }, raw || {});
  next.camera = normalizeCamera(next.camera);
  next.effect = normalizeEffect(next.effect);
  next.overlay = normalizeOverlay(next.overlay);
  return next;
}
function setCardState(rank, patch){ state[rank] = Object.assign(cardState(rank), patch); save(); }
function fixed(value){ return `${Number(value || 0).toFixed(1)}s`; }
const formatMeta = {
  tiktok: "TikTok - 9:16",
  shorts: "YouTube Shorts - 9:16",
  youtube: "YouTube - 16:9",
  instagram: "Instagram Reels - 9:16",
  facebook: "Facebook Feed - 4:5"
};
const platformMeta = {
  tiktok: { label: "TikTok", width: 1080, height: 1920 },
  shorts: { label: "Shorts", width: 1080, height: 1920 },
  instagram: { label: "Instagram", width: 1080, height: 1920 },
  facebook: { label: "Facebook", width: 1080, height: 1350 },
  youtube: { label: "YouTube", width: 1920, height: 1080 }
};
const effectMeta = {
  none: { label: "Sem efeito", note: "Preview limpo" },
  "light-grain": { label: "Chuvisco Leve", note: "Granulado sutil" },
  "old-film": { label: "Filme Antigo", note: "Vintage com vinheta" },
  vhs: { label: "VHS / TV Antiga", note: "Ruido analogico" },
  "bw-old": { label: "Preto e Branco Antigo", note: "P&B com grao" }
};
const cameraMeta = {
  center: { label: "Centro seguro", note: "Crop limpo no centro", x: 50, scale: 1 },
  "face-center": { label: "Rosto no centro", note: "Zoom leve no centro", x: 50, scale: 1.1 },
  "face-left": { label: "Rosto a esquerda", note: "Prioriza a pessoa da esquerda", x: 22, scale: 1 },
  "face-right": { label: "Rosto a direita", note: "Prioriza a pessoa da direita", x: 78, scale: 1 },
  alternate: { label: "Alternar focos", note: "Pan suave entre lados", x: 50, scale: 1 },
  "soft-zoom": { label: "Zoom sutil", note: "Aproxima sem trocar o foco", x: 50, scale: 1.12 },
  "punch-in": { label: "Punch-in", note: "Mais fechado e energetico", x: 50, scale: 1.22 }
};
const overlayMeta = {
  none: { label: "Sem chamada", title: "", subtitle: "", accent: "#000000" },
  subscribe: { label: "Inscreva-se", title: "Inscreva-se", subtitle: "Novos cortes toda semana", accent: "#ff3b30" },
  follow: { label: "Siga-nos", title: "Siga-nos", subtitle: "Mais cortes no perfil", accent: "#24d17e" },
  description: { label: "Veja a descricao", title: "Veja a descricao", subtitle: "Link e contexto completo", accent: "#4da3ff" },
  "like-share": { label: "Curta e compartilhe", title: "Curta e compartilhe", subtitle: "Mostre para alguem", accent: "#ffd166" },
  "pinned-comment": { label: "Comentario fixado", title: "Comentario fixado", subtitle: "Detalhes no primeiro comentario", accent: "#b388ff" },
  watermark: { label: "Marca d'agua", title: "CUTED", subtitle: "clip selecionado", accent: "#f4f4f4" }
};
function applyFormat(format){
  const next = formatMeta[format] ? format : "tiktok";
  document.body.dataset.format = next;
  localStorage.setItem("cutted-format", next);
  document.querySelector("[data-format-hint]").textContent = formatMeta[next];
  document.querySelectorAll(".segments [data-format]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.format === next);
  });
  document.querySelectorAll(".card").forEach(updatePlatformUi);
  renderCaptionQueue();
}
function applyTab(tab){
  const next = ["edit", "camera", "effects", "overlays", "final"].includes(tab) ? tab : "edit";
  document.body.dataset.tab = next;
  localStorage.setItem("cutted-tab", next);
  document.querySelectorAll(".tabs [data-tab]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === next);
  });
  renderCameraPreview();
  renderEffectPreview();
  renderOverlayPreview();
  renderFinalStage();
}
function platformLabel(key){
  return (platformMeta[key] || { label: key }).label;
}
function defaultCamera(){ return { key: "center", label: cameraMeta.center.label, strength: 60 }; }
function normalizeCamera(camera){
  const key = cameraMeta[camera?.key] ? camera.key : "center";
  const strength = Math.max(0, Math.min(Number(camera?.strength ?? 60), 100));
  return { key, label: cameraMeta[key].label, strength };
}
function cameraLabel(camera){
  const current = normalizeCamera(camera);
  return current.key === "center" ? current.label : `${current.label} - ${current.strength}%`;
}
function cameraForRank(rank){ return normalizeCamera(cardState(String(rank)).camera); }
function setCameraForRank(rank, patch){
  const current = cardState(String(rank));
  setCardState(String(rank), { camera: normalizeCamera(Object.assign({}, current.camera, patch)) });
  renderCameraPreview();
  renderFinalStage();
}
function cameraStyle(camera){
  const current = normalizeCamera(camera);
  const meta = cameraMeta[current.key] || cameraMeta.center;
  const strengthScale = current.key === "punch-in" ? current.strength / 500 : current.strength / 900;
  const scale = current.key === "center" || current.key === "face-left" || current.key === "face-right" || current.key === "alternate"
    ? meta.scale
    : meta.scale + strengthScale;
  return `--camera-x:${meta.x}%;--camera-scale:${scale}`;
}
function defaultEffect(){ return { key: "none", label: effectMeta.none.label, intensity: 0 }; }
function normalizeEffect(effect){
  const key = effectMeta[effect?.key] ? effect.key : "none";
  const intensity = key === "none" ? 0 : Math.max(0, Math.min(Number(effect?.intensity || 65), 100));
  return { key, label: effectMeta[key].label, intensity };
}
function effectLabel(effect){
  const current = normalizeEffect(effect);
  return current.key === "none" ? current.label : `${current.label} - ${current.intensity}%`;
}
function effectForRank(rank){ return normalizeEffect(cardState(String(rank)).effect); }
function setEffectForRank(rank, patch){
  const current = cardState(String(rank));
  setCardState(String(rank), { effect: normalizeEffect(Object.assign({}, current.effect, patch)) });
  renderEffectPreview();
  renderFinalStage();
}
function effectOpacity(effect){
  const current = normalizeEffect(effect);
  return current.key === "none" ? 0 : Math.max(.12, current.intensity / 185);
}
function defaultOverlay(){ return { key: "none", label: overlayMeta.none.label, x: .62, y: .78, width: .34, opacity: 95 }; }
function normalizeOverlay(overlay){
  const key = overlayMeta[overlay?.key] ? overlay.key : "none";
  if (key === "none") return defaultOverlay();
  return {
    key,
    label: overlayMeta[key].label,
    x: clampNumber(overlay?.x ?? .62, 0, 1),
    y: clampNumber(overlay?.y ?? .78, 0, 1),
    width: clampNumber(overlay?.width ?? .34, .18, .72),
    opacity: clampNumber(overlay?.opacity ?? 95, 35, 100)
  };
}
function overlayForRank(rank){ return normalizeOverlay(cardState(String(rank)).overlay); }
function setOverlayForRank(rank, patch, rerender = true){
  const current = cardState(String(rank));
  setCardState(String(rank), { overlay: normalizeOverlay(Object.assign({}, current.overlay, patch)) });
  if (rerender) renderOverlayPreview();
  renderFinalStage();
}
function overlayLabel(overlay){
  const current = normalizeOverlay(overlay);
  return current.key === "none" ? current.label : `${current.label} - ${Math.round(current.opacity)}%`;
}
function overlayStyle(overlay){
  const current = normalizeOverlay(overlay);
  const meta = overlayMeta[current.key] || overlayMeta.none;
  return `--overlay-x:${current.x};--overlay-y:${current.y};--overlay-width:${current.width};--overlay-opacity:${current.opacity / 100};--overlay-accent:${meta.accent}`;
}
function clampNumber(value, min, max){
  const next = Number(value);
  if (!Number.isFinite(next)) return min;
  return Math.min(Math.max(next, min), max);
}
function updatePlatformUi(card){
  const current = cardState(card.dataset.rank);
  const platforms = Array.isArray(current.platforms) ? current.platforms : [];
  card.querySelectorAll("[data-platform]").forEach(btn => {
    btn.classList.toggle("active", platforms.includes(btn.dataset.platform));
  });
  const fallback = document.body.dataset.format || "tiktok";
  const summary = platforms.length
    ? platforms.map(platformLabel).join(", ")
    : (current.status === "liked" ? `Formato atual: ${platformLabel(fallback)}` : "Nenhum destino marcado");
  card.querySelector("[data-platform-summary]").textContent = summary;
}
function paint(card){
  const current = cardState(card.dataset.rank);
  card.classList.toggle("liked",current.status==="liked");
  card.classList.toggle("discarded",current.status==="discarded");
}
function trimValues(card){
  const start = Number(card.dataset.start);
  const end = Number(card.dataset.end);
  const duration = Number(card.dataset.duration);
  const current = cardState(card.dataset.rank);
  const trimStart = Math.min(Number(current.trimStart || 0), Math.max(duration - 1, 0));
  const trimEnd = Math.min(Number(current.trimEnd || 0), Math.max(duration - trimStart - 1, 0));
  return { start, end, duration, trimStart, trimEnd, startPos: trimStart, endPos: duration - trimEnd, adjustedStart: start + trimStart, adjustedEnd: end - trimEnd };
}
function updateTrimUi(card){
  const values = trimValues(card);
  const startInput = card.querySelector("[data-trim=start]");
  const endInput = card.querySelector("[data-trim=end]");
  startInput.max = values.duration.toFixed(1);
  endInput.max = values.duration.toFixed(1);
  startInput.value = values.startPos;
  endInput.value = values.endPos;
  card.querySelector("[data-output=start]").textContent = fixed(values.trimStart);
  card.querySelector("[data-output=end]").textContent = fixed(values.trimEnd);
  card.querySelector("[data-trim-summary]").textContent = `Final: ${fixed(values.adjustedStart)} - ${fixed(values.adjustedEnd)} (${fixed(values.adjustedEnd - values.adjustedStart)})`;
  const fill = card.querySelector("[data-trim-fill]");
  fill.style.left = `${(values.startPos / values.duration) * 100}%`;
  fill.style.right = `${100 - ((values.endPos / values.duration) * 100)}%`;
}
function seekPreview(card){
  const video = card.querySelector("video");
  if (!video) return;
  const values = trimValues(card);
  video.currentTime = values.trimStart;
}
function adjustedMoment(moment){
  const current = cardState(String(moment.rank));
  const trimStart = Number(current.trimStart || 0);
  const trimEnd = Number(current.trimEnd || 0);
  const platforms = Array.isArray(current.platforms) ? current.platforms : [];
  return Object.assign({}, moment, {
    status: current.status || null,
    platforms,
    trim_start_seconds: trimStart,
    trim_end_seconds: trimEnd,
    adjusted_start: Number((moment.start + trimStart).toFixed(3)),
    adjusted_end: Number((moment.end - trimEnd).toFixed(3)),
    adjusted_duration: Number((moment.end - trimEnd - moment.start - trimStart).toFixed(3)),
    camera: cameraForRank(moment.rank),
    effect: effectForRank(moment.rank),
    overlay: overlayForRank(moment.rank)
  });
}
function buildExportData(){
  const data = Object.assign({}, window.CUTTED_DATA);
  data.export_format = document.body.dataset.format || "tiktok";
  const adjusted = data.moments.map(adjustedMoment);
  data.moments = adjusted;
  data.selected = adjusted.filter(m => m.status === "liked" || m.platforms.length > 0);
  data.caption_queue = data.selected.flatMap(moment => captionPlatforms(moment, data.export_format).map(platform => ({
    rank: moment.rank,
    platform,
    platform_label: platformLabel(platform),
    width: platformMeta[platform]?.width || null,
    height: platformMeta[platform]?.height || null,
    publish_metadata: publishMetadata(platform, moment),
    trim_start_seconds: moment.trim_start_seconds,
    trim_end_seconds: moment.trim_end_seconds,
    adjusted_start: moment.adjusted_start,
    adjusted_end: moment.adjusted_end,
    adjusted_duration: moment.adjusted_duration,
    camera: moment.camera,
    effect: moment.effect,
    overlay: moment.overlay,
    clip_file: moment.clip_file,
    title: moment.title,
    peak_text: moment.peak_text,
    transcript: moment.transcript,
    caption_segments: moment.caption_segments || []
  })));
  return data;
}
function captionPlatforms(moment, exportFormat){
  if (Array.isArray(moment.platforms) && moment.platforms.length) return moment.platforms;
  return moment.status === "liked" && platformMeta[exportFormat] ? [exportFormat] : [];
}
function publishMetadata(platform, moment){
  const hashtags = suggestHashtags(platform, `${moment.title} ${moment.peak_text} ${moment.transcript}`);
  return {
    hashtags,
    caption_hint: captionHint(platform, moment, hashtags),
    strategy: platformStrategy(platform)
  };
}
function suggestHashtags(platform, text){
  const topicTags = extractTopicTags(text);
  const topicalBoosts = inferTopicalBoosts(text);
  const defaults = {
    tiktok: ["IA", "InteligenciaArtificial", "Podcast"],
    shorts: ["IA", "InteligenciaArtificial", "Shorts"],
    youtube: ["IA", "InteligenciaArtificial", "Tecnologia"],
    instagram: ["IA", "InteligenciaArtificial", "Reels"],
    facebook: ["IA", "Tecnologia"]
  };
  const limits = { tiktok: 6, shorts: 4, youtube: 4, instagram: 5, facebook: 3 };
  const merged = [...topicalBoosts, ...(defaults[platform] || []), ...topicTags];
  return unique(merged).slice(0, limits[platform] || 4).map(tag => `#${tag}`);
}
function extractTopicTags(text){
  const extraStopWords = [
    "acho","ainda","agora","assim","cada","cara","certo","com","daqui","dele","dela","deles","dessa",
    "desse","disso","dizer","esta","estao","falar","mas","meio","nao","nem","nessa","nesse",
    "cortou","negocio","pela","pelo","qual","quando","que","quem","sabe","seguinte","tambem",
    "tem","tipo","uma","volta","vou"
  ];
  const stop = new Set(["para","como","porque","entao","então","sobre","isso","essa","esse","aqui","gente","voce","você","video","clip","coisa","forma","mais","menos","muito","fala","falando"]);
  extraStopWords.forEach(word => stop.add(word));
  const normalized = String(text).normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
  const words = normalized.match(/[a-zA-Z0-9]{3,}/g) || [];
  const counts = new Map();
  words.map(word => word.toLowerCase()).filter(word => !stop.has(word)).forEach(word => {
    counts.set(word, (counts.get(word) || 0) + 1);
  });
  return Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1] || b[0].length - a[0].length)
    .slice(0, 4)
    .map(([word]) => word.charAt(0).toUpperCase() + word.slice(1));
}
function inferTopicalBoosts(text){
  const normalized = String(text).normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toLowerCase();
  const boosts = [];
  if (/\\bia\\b|inteligencia artificial|artificial/.test(normalized)) boosts.push("IA", "InteligenciaArtificial");
  if (/podcast|episodio|entrevista|conversa/.test(normalized)) boosts.push("Podcast");
  if (/tecnologia|tech|futuro|ferramenta|automacao/.test(normalized)) boosts.push("Tecnologia");
  if (/criador|conteudo|youtube|tiktok|instagram|reels|shorts/.test(normalized)) boosts.push("Criadores");
  return boosts;
}
function unique(values){
  const seen = new Set();
  return values.filter(value => {
    const clean = String(value).replace(/^#/, "").replace(/[^a-zA-Z0-9]/g, "");
    const key = clean.toLowerCase();
    if (!clean || seen.has(key)) return false;
    seen.add(key);
    return true;
  }).map(value => String(value).replace(/^#/, "").replace(/[^a-zA-Z0-9]/g, ""));
}
function captionHint(platform, moment, hashtags){
  const lead = moment.peak_text || moment.title || "Corte selecionado";
  return `${lead}\\n\\n${hashtags.join(" ")}`;
}
function platformStrategy(platform){
  return {
    tiktok: "Usar poucos hashtags relevantes; validar tendencias no TikTok Creative Center antes de publicar.",
    shorts: "Priorizar 3-4 hashtags relevantes; no YouTube, os primeiros hashtags da descricao sao os mais visiveis.",
    youtube: "Usar hashtags como contexto, sem exagero; evitar excesso de hashtags.",
    instagram: "Usar 3-5 hashtags especificos e relevantes; evitar blocos longos genericos.",
    facebook: "Usar 1-3 hashtags pesquisaveis; legenda clara e nativa do feed importa mais que volume."
  }[platform] || "Usar hashtags relevantes e especificos.";
}
function downloadJson(data, filename){
  const blob = new Blob([JSON.stringify(data, null, 2)], {type:"application/json"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
}
function renderCaptionQueue(){
  renderCameraPreview();
  renderEffectPreview();
  renderOverlayPreview();
  renderFinalStage();
}
function renderCameraPreview(){
  const preview = document.querySelector("[data-camera-preview]");
  const summary = document.querySelector("[data-camera-summary]");
  if (!preview) return;
  const queue = buildExportData().caption_queue || [];
  if (!queue.length) {
    if (summary) summary.textContent = "Marque cortes como Gostei ou escolha destinos para liberar a camera.";
    preview.innerHTML = '<div class="camera-empty">Nenhum corte selecionado ainda.</div>';
    return;
  }
  if (summary) summary.textContent = `${queue.length} saidas selecionadas. Escolha um enquadramento em cada uma.`;
  preview.innerHTML = queue.map(cameraPreviewItemHtml).join("");
  bindCameraPreviewControls();
}
function cameraPreviewItemHtml(item){
  const camera = normalizeCamera(item.camera);
  const src = cacheBustedPreview(item.clip_file || "", `camera-${item.rank}-${item.adjusted_start}-${item.adjusted_end}`);
  return `<article class="caption-item" data-rank="${escapeAttr(item.rank)}" data-platform="${escapeAttr(item.platform)}">
    <div class="caption-preview camera-surface" data-camera-key="${escapeAttr(camera.key)}" style="${escapeAttr(cameraStyle(camera))}">
      <video controls preload="metadata" src="${escapeAttr(src)}"></video>
      <div class="camera-reticle"></div>
    </div>
    <div class="caption-item-body">
      <strong>Preview #${String(item.rank).padStart(2, "0")} ${escapeHtml(item.title || "")}</strong>
      <span>${escapeHtml(item.platform_label)}</span><span data-camera-current>${escapeHtml(cameraLabel(camera))}</span>
      <div class="camera-card-controls">
        <div class="camera-card-buttons" role="group" aria-label="Camera do corte ${escapeAttr(item.rank)}">
          ${cameraButtonsHtml(camera)}
        </div>
        <label>Forca do enquadramento
          <input data-preview-camera-strength type="range" min="0" max="100" step="5" value="${camera.strength}">
        </label>
      </div>
    </div>
  </article>`;
}
function cameraButtonsHtml(current){
  return Object.entries(cameraMeta).map(([key, meta]) => {
    const active = current.key === key ? " active" : "";
    return `<button data-preview-camera="${escapeAttr(key)}" class="${active}">${escapeHtml(meta.label)}</button>`;
  }).join("");
}
function bindCameraPreviewControls(){
  document.querySelectorAll("[data-camera-preview] .caption-item").forEach(item => {
    const rank = item.dataset.rank;
    item.querySelectorAll("[data-preview-camera]").forEach(button => {
      button.addEventListener("click", () => setCameraForRank(rank, { key: button.dataset.previewCamera }));
    });
    const strength = item.querySelector("[data-preview-camera-strength]");
    if (strength) {
      strength.addEventListener("input", () => setCameraForRank(rank, { strength: Number(strength.value) }));
      strength.addEventListener("change", () => setCameraForRank(rank, { strength: Number(strength.value) }));
    }
  });
}
function renderEffectPreview(){
  const preview = document.querySelector("[data-effect-preview]");
  const summary = document.querySelector("[data-effect-summary]");
  if (!preview) return;
  const queue = buildExportData().caption_queue || [];
  if (!queue.length) {
    if (summary) summary.textContent = "Marque cortes como Gostei ou escolha destinos para liberar os efeitos.";
    preview.innerHTML = '<div class="effect-empty">Nenhum corte selecionado ainda.</div>';
    return;
  }
  if (summary) summary.textContent = `${queue.length} saidas selecionadas. Escolha um efeito em cada uma.`;
  preview.innerHTML = queue.map(effectPreviewItemHtml).join("");
  bindEffectPreviewControls();
}
function effectPreviewItemHtml(item){
  const effect = normalizeEffect(item.effect);
  const src = cacheBustedPreview(item.clip_file || "", `effect-${item.rank}-${item.adjusted_start}-${item.adjusted_end}`);
  return `<article class="caption-item" data-rank="${escapeAttr(item.rank)}" data-platform="${escapeAttr(item.platform)}" data-effect="${escapeAttr(effect.key)}" style="--effect-opacity:${effectOpacity(effect)}">
    <div class="caption-preview"><video controls preload="metadata" src="${escapeAttr(src)}"></video></div>
    <div class="caption-item-body">
      <strong>Preview #${String(item.rank).padStart(2, "0")} ${escapeHtml(item.title || "")}</strong>
      <span>${escapeHtml(item.platform_label)}</span><span data-effect-current>${escapeHtml(effectLabel(effect))}</span>
      <div class="effect-card-controls">
        <div class="effect-card-buttons" role="group" aria-label="Efeito do corte ${escapeAttr(item.rank)}">
          ${effectButtonsHtml(effect)}
        </div>
        <label>Intensidade
          <input data-preview-effect-intensity type="range" min="0" max="100" step="5" value="${effect.intensity}">
        </label>
      </div>
    </div>
  </article>`;
}
function effectButtonsHtml(current){
  return Object.entries(effectMeta).map(([key, meta]) => {
    const active = current.key === key ? " active" : "";
    return `<button data-preview-effect="${escapeAttr(key)}" class="${active}">${escapeHtml(meta.label)}</button>`;
  }).join("");
}
function bindEffectPreviewControls(){
  document.querySelectorAll("[data-effect-preview] .caption-item").forEach(item => {
    const rank = item.dataset.rank;
    item.querySelectorAll("[data-preview-effect]").forEach(button => {
      button.addEventListener("click", () => setEffectForRank(rank, { key: button.dataset.previewEffect }));
    });
    const intensity = item.querySelector("[data-preview-effect-intensity]");
    if (intensity) {
      intensity.addEventListener("input", () => setEffectForRank(rank, { intensity: Number(intensity.value) }));
      intensity.addEventListener("change", () => setEffectForRank(rank, { intensity: Number(intensity.value) }));
    }
  });
}
function renderOverlayPreview(){
  const preview = document.querySelector("[data-overlay-preview]");
  const summary = document.querySelector("[data-overlay-summary]");
  if (!preview) return;
  const queue = buildExportData().caption_queue || [];
  if (!queue.length) {
    if (summary) summary.textContent = "Marque cortes como Gostei ou escolha destinos para liberar as chamadas.";
    preview.innerHTML = '<div class="overlay-empty">Nenhum corte selecionado ainda.</div>';
    return;
  }
  if (summary) summary.textContent = `${queue.length} saidas selecionadas. Escolha um card e arraste em cada preview.`;
  preview.innerHTML = queue.map(overlayPreviewItemHtml).join("");
  bindOverlayPreviewControls();
}
function overlayPreviewItemHtml(item){
  const overlay = normalizeOverlay(item.overlay);
  const meta = overlayMeta[overlay.key] || overlayMeta.none;
  const src = cacheBustedPreview(item.clip_file || "", `overlay-${item.rank}-${item.adjusted_start}-${item.adjusted_end}`);
  return `<article class="caption-item" data-rank="${escapeAttr(item.rank)}" data-platform="${escapeAttr(item.platform)}">
    <div class="caption-preview" data-overlay-surface>
      <video controls preload="metadata" src="${escapeAttr(src)}"></video>
      <div class="overlay-box" data-overlay-drag data-overlay-key="${escapeAttr(overlay.key)}" style="${escapeAttr(overlayStyle(overlay))}">
        <strong>${escapeHtml(meta.title)}</strong>
        <em>${escapeHtml(meta.subtitle)}</em>
        <button class="overlay-resize" data-overlay-resize title="Redimensionar"></button>
      </div>
    </div>
    <div class="caption-item-body">
      <strong>Preview #${String(item.rank).padStart(2, "0")} ${escapeHtml(item.title || "")}</strong>
      <span>${escapeHtml(item.platform_label)}</span><span data-overlay-current>${escapeHtml(overlayLabel(overlay))}</span>
      <div class="overlay-card-controls">
        <div class="overlay-card-buttons" role="group" aria-label="Chamada do corte ${escapeAttr(item.rank)}">
          ${overlayButtonsHtml(overlay)}
        </div>
        <div class="overlay-tools">
          <label>Opacidade
            <input data-preview-overlay-opacity type="range" min="35" max="100" step="5" value="${overlay.opacity}">
          </label>
          <button data-overlay-reset>Resetar posicao</button>
        </div>
      </div>
    </div>
  </article>`;
}
function overlayButtonsHtml(current){
  return Object.entries(overlayMeta).map(([key, meta]) => {
    const active = current.key === key ? " active" : "";
    return `<button data-preview-overlay="${escapeAttr(key)}" class="${active}">${escapeHtml(meta.label)}</button>`;
  }).join("");
}
function bindOverlayPreviewControls(){
  document.querySelectorAll("[data-overlay-preview] .caption-item").forEach(item => {
    const rank = item.dataset.rank;
    item.querySelectorAll("[data-preview-overlay]").forEach(button => {
      button.addEventListener("click", () => setOverlayForRank(rank, { key: button.dataset.previewOverlay }));
    });
    const opacity = item.querySelector("[data-preview-overlay-opacity]");
    if (opacity) {
      opacity.addEventListener("input", () => setOverlayForRank(rank, { opacity: Number(opacity.value) }));
      opacity.addEventListener("change", () => setOverlayForRank(rank, { opacity: Number(opacity.value) }));
    }
    const reset = item.querySelector("[data-overlay-reset]");
    if (reset) reset.addEventListener("click", () => setOverlayForRank(rank, { x: .62, y: .78, width: .34 }));
    bindOverlayDrag(item);
  });
}
function bindOverlayDrag(item){
  const surface = item.querySelector("[data-overlay-surface]");
  const box = item.querySelector("[data-overlay-drag]");
  if (!surface || !box || box.dataset.overlayKey === "none") return;
  let drag = null;
  const startDrag = event => {
    const resizing = event.target?.hasAttribute?.("data-overlay-resize");
    const surfaceRect = surface.getBoundingClientRect();
    const boxRect = box.getBoundingClientRect();
    drag = {
      type: resizing ? "resize" : "move",
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      startLeft: boxRect.left - surfaceRect.left,
      startTop: boxRect.top - surfaceRect.top,
      startWidth: boxRect.width,
      surfaceWidth: surfaceRect.width,
      surfaceHeight: surfaceRect.height
    };
    box.setPointerCapture(event.pointerId);
    event.preventDefault();
  };
  const moveDrag = event => {
    if (!drag || event.pointerId !== drag.pointerId) return;
    const dx = event.clientX - drag.startX;
    const dy = event.clientY - drag.startY;
    const next = overlayForRank(item.dataset.rank);
    if (drag.type === "resize") {
      const width = clampNumber((drag.startWidth + dx) / drag.surfaceWidth, .18, .72);
      box.style.setProperty("--overlay-width", width);
      next.width = width;
    } else {
      const boxRect = box.getBoundingClientRect();
      const maxLeft = Math.max(drag.surfaceWidth - boxRect.width, 0);
      const maxTop = Math.max(drag.surfaceHeight - boxRect.height, 0);
      const left = clampNumber(drag.startLeft + dx, 0, maxLeft);
      const top = clampNumber(drag.startTop + dy, 0, maxTop);
      next.x = drag.surfaceWidth ? left / drag.surfaceWidth : 0;
      next.y = drag.surfaceHeight ? top / drag.surfaceHeight : 0;
      box.style.setProperty("--overlay-x", next.x);
      box.style.setProperty("--overlay-y", next.y);
    }
    setOverlayForRank(item.dataset.rank, next, false);
  };
  const endDrag = event => {
    if (!drag || event.pointerId !== drag.pointerId) return;
    drag = null;
    renderOverlayPreview();
  };
  box.addEventListener("pointerdown", startDrag);
  box.addEventListener("pointermove", moveDrag);
  box.addEventListener("pointerup", endDrag);
  box.addEventListener("pointercancel", endDrag);
}
function renderFinalStage(){
  const queue = buildExportData().caption_queue || [];
  const summary = document.querySelector("[data-final-summary]");
  if (summary) {
    const cameraCount = queue.filter(item => normalizeCamera(item.camera).key !== "center").length;
    const effectCount = queue.filter(item => normalizeEffect(item.effect).key !== "none").length;
    const overlayCount = queue.filter(item => normalizeOverlay(item.overlay).key !== "none").length;
    summary.textContent = queue.length
      ? `${queue.length} video(s) na fila; ${cameraCount} com camera; ${effectCount} com efeito; ${overlayCount} com chamada.`
      : "Selecione cortes antes de renderizar.";
  }
}
function captionCommand(){
  const chars = Number(document.querySelector("[data-caption-width]")?.value || 28);
  const lines = Number(document.querySelector("[data-caption-lines]")?.value || 2);
  const script = window.CUTTED_SCRIPT || "cutted.py";
  return `python "${script}" caption-selected "caption-queue.json" --out "captioned-clips" --base-dir "." --chars-per-line ${chars} --max-lines ${lines}`;
}
async function finalizeVideos(){
  const button = document.getElementById("finalize-videos");
  const status = document.querySelector("[data-render-status]");
  const results = document.querySelector("[data-render-results]");
  const data = buildExportData();
  const queue = data.caption_queue || [];
  if (!queue.length) {
    if (status) status.textContent = "Selecione ao menos um corte antes de finalizar.";
    return;
  }
  button.disabled = true;
  if (status) status.textContent = `Renderizando ${queue.length} video(s)...`;
  if (results) results.innerHTML = "";
  try {
    const response = await fetch("/api/finalize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        queue: data,
        chars_per_line: Number(document.querySelector("[data-caption-width]")?.value || 28),
        max_lines: Number(document.querySelector("[data-caption-lines]")?.value || 2)
      })
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao renderizar.");
    renderFinalizeResults(payload.files || []);
    if (status) status.textContent = `${payload.count || 0} video(s) finalizado(s).`;
  } catch (error) {
    if (status) status.textContent = finalizeErrorMessage(error);
  } finally {
    button.disabled = false;
  }
}
function renderFinalizeResults(files){
  const results = document.querySelector("[data-render-results]");
  if (!results) return;
  if (!files.length) {
    results.innerHTML = '<div class="effect-empty">Nenhum video renderizado ainda.</div>';
    return;
  }
  results.innerHTML = files.map((file, index) => {
    const camera = normalizeCamera(file.camera);
    const effect = normalizeEffect(file.effect);
    const overlay = normalizeOverlay(file.overlay);
    const title = `#${String(file.rank || "").padStart(2, "0")} ${file.label || file.platform || "video"}`;
    const meta = [
      file.width && file.height ? `${file.width}x${file.height}` : "",
      file.adjusted_duration ? fixed(file.adjusted_duration) : "",
      camera.key !== "center" ? camera.label : "",
      effect.key !== "none" ? effect.label : "",
      overlay.key !== "none" ? overlay.label : ""
    ].filter(Boolean).join(" - ");
    const open = index === 0 ? " open" : "";
    const downloadName = file.download_name || file.url?.split("/").pop() || "cuted-video.mp4";
    return `<details class="result-item"${open}>
      <summary><strong>${escapeHtml(title)}</strong><span>${escapeHtml(meta || "Video finalizado")}</span></summary>
      <div class="result-body">
        <video controls preload="metadata" src="${escapeAttr(file.url)}"></video>
        <div class="result-meta">
          <dl>
            <dt>Formato</dt><dd>${escapeHtml(file.label || file.platform || "-")}</dd>
            <dt>Duracao</dt><dd>${escapeHtml(file.adjusted_duration ? fixed(file.adjusted_duration) : "-")}</dd>
            <dt>Camera</dt><dd>${escapeHtml(camera.label)}</dd>
            <dt>Efeito</dt><dd>${escapeHtml(effect.label)}</dd>
            <dt>Chamada</dt><dd>${escapeHtml(overlay.label)}</dd>
          </dl>
          <div class="result-actions">
            <a href="${escapeAttr(file.url)}" target="_blank" rel="noopener">Abrir</a>
            <a class="secondary" href="${escapeAttr(file.url)}" download="${escapeAttr(downloadName)}">Baixar MP4</a>
          </div>
        </div>
      </div>
    </details>`;
  }).join("");
}
function finalizeErrorMessage(error){
  const script = window.CUTTED_SCRIPT || "cutted.py";
  const serveCommand = `python "${script}" serve --dir "." --port 8778`;
  return `Nao consegui finalizar pelo navegador atual. Abra a galeria com: ${serveCommand}`;
}
function captionItemHtml(item){
  const previewSrc = cacheBustedPreview(item.clip_file || "", `${item.rank}-${item.adjusted_start}-${item.adjusted_end}`);
  return `
    <article class="caption-item" data-platform="${escapeAttr(item.platform)}">
      <div class="caption-preview"><video controls preload="metadata" src="${escapeAttr(previewSrc)}"></video></div>
      <div class="caption-item-body">
        <strong>#${String(item.rank).padStart(2, "0")} ${escapeHtml(item.title || "")}</strong>
        <span>${escapeHtml(item.platform_label)}</span><span>${item.width}x${item.height}</span><span>${fixed(item.adjusted_duration)}</span>
        <p>${escapeHtml((item.publish_metadata?.hashtags || []).join(" "))}</p>
        <dl><dt>Inicio</dt><dd>${fixed(item.adjusted_start)}</dd><dt>Fim</dt><dd>${fixed(item.adjusted_end)}</dd></dl>
      </div>
    </article>`;
}
function cacheBustedPreview(value, token){
  if (!value) return "";
  return `${value}${String(value).includes("?") ? "&" : "?"}v=${encodeURIComponent(token)}`;
}
function escapeHtml(value){
  return String(value).replace(/[&<>"']/g, char => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[char]));
}
function escapeAttr(value){ return escapeHtml(value); }
applyFormat(localStorage.getItem("cutted-format") || "tiktok");
applyTab(localStorage.getItem("cutted-tab") || "edit");
document.querySelectorAll(".segments [data-format]").forEach(btn => {
  btn.addEventListener("click", () => applyFormat(btn.dataset.format));
});
document.querySelectorAll(".tabs [data-tab]").forEach(btn => {
  btn.addEventListener("click", () => { applyTab(btn.dataset.tab); renderCaptionQueue(); });
});
document.querySelectorAll(".card").forEach(card => {
  paint(card);
  updateTrimUi(card);
  updatePlatformUi(card);
  const video = card.querySelector("video");
  if (video) {
    video.addEventListener("play", () => {
      const values = trimValues(card);
      if (video.currentTime < values.trimStart || video.currentTime >= values.duration - values.trimEnd) {
        video.currentTime = values.trimStart;
      }
    });
    video.addEventListener("timeupdate", () => {
      const values = trimValues(card);
      if (video.currentTime >= values.duration - values.trimEnd) {
        video.pause();
        video.currentTime = values.trimStart;
      }
    });
  }
  card.querySelectorAll("[data-trim]").forEach(input => input.addEventListener("input", () => {
    const current = cardState(card.dataset.rank);
    const duration = Number(card.dataset.duration);
    const startInput = card.querySelector("[data-trim=start]");
    const endInput = card.querySelector("[data-trim=end]");
    let startPos = Number(startInput.value);
    let endPos = Number(endInput.value);
    if (input.dataset.trim === "start") startPos = Math.min(startPos, endPos - 1);
    if (input.dataset.trim === "end") endPos = Math.max(endPos, startPos + 1);
    const patch = { trimStart: Math.max(startPos, 0), trimEnd: Math.max(duration - endPos, 0) };
    setCardState(card.dataset.rank, Object.assign(current, patch));
    updateTrimUi(card);
    seekPreview(card);
    renderCaptionQueue();
  }));
  card.querySelectorAll("[data-platform]").forEach(btn => btn.addEventListener("click", () => {
    const current = cardState(card.dataset.rank);
    const platforms = Array.isArray(current.platforms) ? current.platforms.slice() : [];
    const existing = platforms.indexOf(btn.dataset.platform);
    if (existing >= 0) platforms.splice(existing, 1);
    else platforms.push(btn.dataset.platform);
    setCardState(card.dataset.rank, { platforms });
    updatePlatformUi(card);
    renderCaptionQueue();
  }));
  card.querySelectorAll("button[data-action]").forEach(btn => btn.addEventListener("click", () => {
    if (btn.dataset.action === "reset-trim") {
      setCardState(card.dataset.rank, { trimStart: 0, trimEnd: 0 });
      updateTrimUi(card);
      seekPreview(card);
      renderCaptionQueue();
      return;
    }
    setCardState(card.dataset.rank, { status: btn.dataset.action === "like" ? "liked" : "discarded" });
    paint(card);
    updatePlatformUi(card);
    renderCaptionQueue();
  }));
});
document.getElementById("export").addEventListener("click", async () => {
  downloadJson(buildExportData(), "selected-clips.json");
});
document.getElementById("reset-ui").addEventListener("click", () => {
  if (!confirm("Zerar cortes, formatos e estado desta interface?")) return;
  localStorage.removeItem("cutted-state");
  localStorage.removeItem("cutted-format");
  localStorage.removeItem("cutted-tab");
  location.reload();
});
document.getElementById("continue-effects").addEventListener("click", async () => {
  applyTab("effects");
});
document.getElementById("continue-overlays").addEventListener("click", async () => {
  applyTab("overlays");
});
document.getElementById("continue-final").addEventListener("click", async () => {
  applyTab("final");
  await finalizeVideos();
});
document.getElementById("export-final-queue").addEventListener("click", async () => {
  downloadJson(buildExportData(), "caption-queue.json");
});
document.getElementById("finalize-videos").addEventListener("click", finalizeVideos);
document.querySelectorAll("[data-caption-lines],[data-caption-width]").forEach(input => {
  input.addEventListener("input", renderFinalStage);
  input.addEventListener("change", renderFinalStage);
});
function selectElementText(element){
  if (!element || !window.getSelection || !document.createRange) return;
  const range = document.createRange();
  range.selectNodeContents(element);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
}
renderCaptionQueue();
"""


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"[cutted] Error: {error}", file=sys.stderr)
        raise SystemExit(1)
