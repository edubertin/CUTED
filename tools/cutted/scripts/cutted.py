from __future__ import annotations

import argparse
import base64
import hashlib
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
    "jump-cut": CameraPreset("jump-cut", "Corte entre focos", "Troca seca entre lados, sem pan"),
    "soft-zoom": CameraPreset("soft-zoom", "Zoom sutil", "Aproxima o enquadramento sem mudar o lado"),
    "punch-in": CameraPreset("punch-in", "Punch-in", "Corte mais fechado para dar energia"),
}

CAMERA_SEGMENT_PARTS = ("start", "middle", "end")
CAMERA_SEGMENT_LABELS = {"start": "Inicio", "middle": "Meio", "end": "Fim"}

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
    materialize_queue_image_assets(data, out_dir / "overlay-assets")
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
    materialize_queue_image_assets(data, out_dir / "overlay-assets")
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
    materialize_queue_image_assets(queue, base_dir / "overlay-assets")
    caption_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = caption_rows_from_data(queue)
    options = SimpleNamespace(chars_per_line=int(payload.get("chars_per_line") or 28), max_lines=int(payload.get("max_lines") or 2))
    captioned = caption_selected_rows(rows, base_dir, out_dir, find_ffmpeg(), options)
    manifest = {"source_caption_queue": str(caption_path), "captioned": captioned}
    (out_dir / "captioned-clips.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "count": len(captioned), "files": finalized_file_urls(captioned, base_dir)}


def read_json_body(handler: http.server.BaseHTTPRequestHandler) -> dict[str, object]:
    length = int(handler.headers.get("Content-Length") or "0")
    if length <= 0 or length > 80_000_000:
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


def materialize_queue_image_assets(data: object, asset_dir: Path) -> None:
    rows = queue_rows_for_assets(data)
    for row in rows:
        overlays = row.get("overlays")
        if not isinstance(overlays, list):
            continue
        for layer in overlays:
            if not isinstance(layer, dict) or str(layer.get("kind") or layer.get("key") or "") != "image":
                continue
            materialize_image_layer(layer, asset_dir)


def queue_rows_for_assets(data: object) -> list[dict[str, object]]:
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if not isinstance(data, dict):
        return []
    rows: list[dict[str, object]] = []
    for key in ("caption_queue", "selected", "moments"):
        value = data.get(key)
        if isinstance(value, list):
            rows.extend(row for row in value if isinstance(row, dict))
    return rows


def materialize_image_layer(layer: dict[str, object], asset_dir: Path) -> None:
    if str(layer.get("image_file") or ""):
        return
    decoded = decode_data_url_image(str(layer.get("image_data_url") or ""))
    if decoded is None:
        return
    image_bytes, extension = decoded
    asset_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(image_bytes).hexdigest()[:16]
    path = asset_dir / f"overlay-{digest}.{extension}"
    if not path.exists():
        path.write_bytes(image_bytes)
    layer["image_file"] = str(path)
    layer["image_data_url"] = ""


def decode_data_url_image(value: str) -> tuple[bytes, str] | None:
    if not value.startswith("data:image/") or ";base64," not in value:
        return None
    header, encoded = value.split(";base64,", 1)
    mime = header.removeprefix("data:").lower()
    extensions = {"image/png": "png", "image/webp": "webp", "image/jpeg": "jpg", "image/jpg": "jpg"}
    extension = extensions.get(mime)
    if extension is None:
        return None
    try:
        return base64.b64decode(encoded, validate=True), extension
    except ValueError:
        return None


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
    filters = [f"ass={subtitle_filter_path(subtitle_path, out_dir)}"]
    effect = effect_filter(row)
    if effect:
        filters.append(effect)
    overlay = overlay_filter(row, preset)
    if overlay:
        filters.append(overlay)
    command = captioned_ffmpeg_command(input_path, output_path, row, preset, ffmpeg, filters)
    subprocess.run(command, check=True, capture_output=True, text=True, cwd=str(out_dir))


def captioned_ffmpeg_command(
    input_path: Path, output_path: Path, row: dict[str, object], preset: PlatformPreset,
    ffmpeg: str, filters: list[str]
) -> list[str]:
    base = [
        ffmpeg, "-y", "-ss", fmt_time(caption_trim_start(row)), "-i", str(input_path),
        "-t", fmt_time(caption_duration(row)),
    ]
    return render_command(base, output_path, row, preset, filters, caption_duration(row))


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
        "overlays": overlay_layers_from_row(row),
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
    filters = post_camera_filters(preset, row)
    base = [
        ffmpeg, "-y", "-ss", fmt_time(start), "-i", str(input_path), "-t", fmt_time(duration),
    ]
    command = render_command(base, output_path, row, preset, filters, duration)
    subprocess.run(command, check=True, capture_output=True, text=True)


def render_command(
    base: list[str], output_path: Path, row: dict[str, object], preset: PlatformPreset,
    filters: list[str], duration: float
) -> list[str]:
    if image_overlay_layers_from_row(row):
        filter_arg = image_overlay_complex_filter(preset, row, duration, filters)
        return [
            *base, "-filter_complex", filter_arg, "-map", "[vout]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", video_crf(row),
            "-c:a", "aac", "-movflags", "+faststart", str(output_path),
        ]
    if camera_is_sequence(row):
        filter_arg = camera_sequence_filter(preset, row, duration, filters)
        return [
            *base, "-filter_complex", filter_arg, "-map", "[vout]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", video_crf(row),
            "-c:a", "aac", "-movflags", "+faststart", str(output_path),
        ]
    filter_arg = ",".join([camera_filter(preset, row), *filters])
    return [
        *base, "-vf", filter_arg,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", video_crf(row),
        "-c:a", "aac", "-movflags", "+faststart", str(output_path),
    ]


def platform_filter(preset: PlatformPreset) -> str:
    return camera_filter(preset, {})


def video_filter(preset: PlatformPreset, row: dict[str, object]) -> str:
    filters = [camera_filter(preset, row)]
    filters.extend(post_camera_filters(preset, row))
    return ",".join(filters)


def post_camera_filters(preset: PlatformPreset, row: dict[str, object]) -> list[str]:
    filters = []
    effect = effect_filter(row)
    if effect:
        filters.append(effect)
    overlay = overlay_filter(row, preset)
    if overlay:
        filters.append(overlay)
    return filters


def image_overlay_complex_filter(
    preset: PlatformPreset, row: dict[str, object], duration: float, filters: list[str]
) -> str:
    parts: list[str] = []
    tail = ",".join(filters)
    if camera_is_sequence(row):
        parts.extend(camera_split_filters(preset, camera_from_row(row).get("segments"), duration))
        base = "".join(f"[cv{index}]" for index in range(3)) + "concat=n=3:v=1:a=0"
        if tail:
            base = f"{base},{tail}"
        parts.append(f"{base}[vbase]")
    else:
        base_filters = ",".join([camera_filter(preset, row), *filters])
        parts.append(f"[0:v]{base_filters}[vbase]")
    previous = "vbase"
    image_layers = image_overlay_layers_from_row(row)
    for index, layer in enumerate(image_layers):
        image_label = f"img{index}"
        output_label = "vout" if index == len(image_layers) - 1 else f"vimg{index}"
        parts.append(image_overlay_source_filter(layer, preset, image_label))
        parts.append(image_overlay_compose_filter(layer, preset, previous, image_label, output_label))
        previous = output_label
    return ";".join(parts)


def image_overlay_layers_from_row(row: dict[str, object]) -> list[dict[str, object]]:
    return [
        layer for layer in overlay_layers_from_row(row)
        if layer.get("kind") == "image" and str(layer.get("image_file") or "")
    ]


def image_overlay_source_filter(overlay: dict[str, object], preset: PlatformPreset, label: str) -> str:
    width = int(round(preset.width * float(overlay["width"])))
    opacity = clamp(float(overlay["opacity"]) / 100.0, 0.1, 1.0)
    path = ffmpeg_filter_path(Path(str(overlay["image_file"])))
    return f"movie='{path}',scale={width}:-1,format=rgba,colorchannelmixer=aa={opacity:.2f}[{label}]"


def image_overlay_compose_filter(
    overlay: dict[str, object], preset: PlatformPreset, input_label: str, image_label: str, output_label: str
) -> str:
    width = int(round(preset.width * float(overlay["width"])))
    x = min(int(round(preset.width * float(overlay["x"]))), max(preset.width - width, 0))
    y = min(int(round(preset.height * float(overlay["y"]))), preset.height)
    return f"[{input_label}][{image_label}]overlay={x}:{y}:format=auto:shortest=1[{output_label}]"


def camera_filter(preset: PlatformPreset, row: dict[str, object]) -> str:
    camera = camera_from_row(row)
    if camera["key"] == "sequence":
        camera = default_camera()
    return camera_filter_from_camera(preset, camera)


def camera_filter_from_camera(preset: PlatformPreset, camera: dict[str, object]) -> str:
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
    if key == "jump-cut":
        left = 0.22 - strength * 0.0012
        right = 0.78 + strength * 0.0012
        return f"if(lt(mod(t\\,6)\\,3)\\,(iw-ow)*{clamp(left, 0.0, 1.0):.3f}\\,(iw-ow)*{clamp(right, 0.0, 1.0):.3f})"
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
    if raw.get("key") == "sequence" or isinstance(raw.get("segments"), list):
        return sequence_camera_from_raw(raw)
    key = str(raw.get("key") or "center")
    preset = CAMERA_PRESETS.get(key, CAMERA_PRESETS["center"])
    strength = clamp(float(raw.get("strength") if raw.get("strength") is not None else 60.0), 0.0, 100.0)
    return {"key": preset.key, "label": preset.label, "strength": strength}


def default_camera() -> dict[str, object]:
    return {"key": "center", "label": CAMERA_PRESETS["center"].label, "strength": 60}


def sequence_camera_from_raw(raw: dict[str, object]) -> dict[str, object]:
    source = raw.get("segments") if isinstance(raw.get("segments"), list) else []
    segments = [camera_segment_from_source(source, part) for part in CAMERA_SEGMENT_PARTS]
    return {"key": "sequence", "label": "Linha de camera", "strength": 60, "segments": segments}


def camera_segment_from_source(source: object, part: str) -> dict[str, object]:
    raw = {}
    if isinstance(source, list):
        raw = next((item for item in source if isinstance(item, dict) and item.get("part") == part), {})
    key = str(raw.get("key") or "center")
    preset = CAMERA_PRESETS.get(key, CAMERA_PRESETS["center"])
    strength = clamp(float(raw.get("strength") if raw.get("strength") is not None else 60.0), 0.0, 100.0)
    return {"part": part, "part_label": CAMERA_SEGMENT_LABELS[part], "key": preset.key, "label": preset.label, "strength": strength}


def camera_is_sequence(row: dict[str, object]) -> bool:
    return camera_from_row(row).get("key") == "sequence"


def camera_sequence_filter(
    preset: PlatformPreset, row: dict[str, object], duration: float, filters: list[str]
) -> str:
    camera = camera_from_row(row)
    segments = camera.get("segments") if isinstance(camera.get("segments"), list) else []
    split_filters = camera_split_filters(preset, segments, duration)
    tail = ",".join(filters)
    concat = "".join(f"[cv{index}]" for index in range(3)) + "concat=n=3:v=1:a=0"
    if tail:
        concat = f"{concat},{tail}"
    return ";".join([*split_filters, f"{concat}[vout]"])


def camera_split_filters(preset: PlatformPreset, segments: object, duration: float) -> list[str]:
    filters = []
    bounds = camera_segment_bounds(duration)
    safe_segments = segments if isinstance(segments, list) else []
    for index, (start, end) in enumerate(bounds):
        segment = safe_segments[index] if index < len(safe_segments) and isinstance(safe_segments[index], dict) else default_camera()
        filters.append(
            f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS,"
            f"{camera_filter_from_camera(preset, segment)}[cv{index}]"
        )
    return filters


def camera_segment_bounds(duration: float) -> list[tuple[float, float]]:
    safe_duration = max(duration, 0.3)
    first = safe_duration / 3.0
    second = first * 2.0
    return [(0.0, first), (first, second), (second, safe_duration)]


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
    filters = [overlay_layer_filter(layer, preset) for layer in overlay_layers_from_row(row) if layer.get("kind") != "image"]
    return ",".join(item for item in filters if item)


def overlay_layer_filter(overlay: dict[str, object], preset: PlatformPreset) -> str:
    if overlay["key"] == "none":
        return ""
    if overlay.get("kind") == "image":
        return image_overlay_filter(overlay, preset)
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


def image_overlay_filter(overlay: dict[str, object], preset: PlatformPreset) -> str:
    image_file = str(overlay.get("image_file") or "")
    if not image_file:
        return ""
    width = int(round(preset.width * float(overlay["width"])))
    x = min(int(round(preset.width * float(overlay["x"]))), max(preset.width - width, 0))
    y = min(int(round(preset.height * float(overlay["y"]))), preset.height)
    opacity = clamp(float(overlay["opacity"]) / 100.0, 0.1, 1.0)
    path = ffmpeg_filter_path(Path(image_file))
    return f"movie='{path}',scale={width}:-1,colorchannelmixer=aa={opacity:.2f}[img];[in][img]overlay={x}:{y}:format=auto[out]"


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
    }


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
        "overlays": overlay_layers_from_row(row),
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
    open_attr = " open" if moment.rank == 1 else ""
    return f"""
    <details class="card" data-rank="{moment.rank}" data-start="{moment.start:.3f}" data-end="{moment.end:.3f}" data-duration="{duration:.3f}" data-preview-format="tiktok"{open_attr}>
      <summary class="clip-summary">
        <span class="clip-rank">#{moment.rank:02d}</span>
        <span class="clip-title">
          <strong>{html.escape(moment.title)}</strong>
          <small data-card-summary>Final: {moment.start:.1f}s - {moment.end:.1f}s ({duration:.1f}s)</small>
        </span>
        <span class="clip-status">
          <span data-platform-summary>Nenhum destino marcado</span>
          <span data-status-pill>Pendente</span>
        </span>
      </summary>
      <div class="editor-shell">
        <div class="editor-preview">
          <div class="preview-frame">
            <div class="media camera-surface" data-overlay-surface>
              {video_tag}
              <div class="camera-reticle"></div>
              <div data-overlay-layer-list></div>
              <div class="overlay-menu" data-overlay-menu hidden></div>
            </div>
            <div class="preview-bar">
              <div class="preview-controls" aria-label="Controles do preview">
                <button class="preview-icon preview-play" data-preview-play type="button" aria-label="Reproduzir" title="Reproduzir">Play</button>
                <div class="preview-volume-group" aria-label="Volume do preview">
                  <button class="preview-icon preview-volume" data-preview-volume type="button" aria-label="Alternar mudo" title="Alternar mudo">Vol</button>
                  <button class="preview-step" data-preview-volume-down type="button" aria-label="Diminuir volume" title="Diminuir volume">-</button>
                  <output data-preview-volume-value>20%</output>
                  <button class="preview-step" data-preview-volume-up type="button" aria-label="Aumentar volume" title="Aumentar volume">+</button>
                </div>
              </div>
              <div class="preview-strip" role="group" aria-label="Visualizacao do formato">
                <button data-card-format-preview="tiktok" class="active">TikTok</button>
                <button data-card-format-preview="shorts">Shorts</button>
                <button data-card-format-preview="instagram">Instagram</button>
                <button data-card-format-preview="facebook">Facebook</button>
                <button data-card-format-preview="youtube">YouTube</button>
              </div>
            </div>
          </div>
        </div>
        <div class="editor-tools">
          <nav class="card-tabs" aria-label="Ferramentas do corte">
            <button data-card-panel="cut" class="active">Corte</button>
            <button data-card-panel="camera">Camera</button>
            <button data-card-panel="effects">Efeitos</button>
            <button data-card-panel="overlays">Chamadas</button>
            <button data-card-panel="captions">Legenda</button>
            <button data-card-panel="transcript">Transcript</button>
          </nav>
          <section class="tool-panel active" data-panel="cut">
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
            <div class="actions">
              <button data-action="like">Gostei</button>
              <button data-action="discard">Descartar</button>
              <button data-action="reset-trim">Resetar corte</button>
              <button data-action="next-card">OK / Proximo</button>
            </div>
          </section>
          <section class="tool-panel" data-panel="camera">
            <div class="tool-summary" data-camera-current>Centro seguro</div>
            <div data-card-camera></div>
          </section>
          <section class="tool-panel" data-panel="effects">
            <div class="tool-summary" data-effect-current>Sem efeito</div>
            <div data-card-effect></div>
          </section>
          <section class="tool-panel" data-panel="overlays">
            <div class="tool-summary" data-overlay-current>Sem chamada</div>
            <div data-card-overlay></div>
          </section>
          <section class="tool-panel" data-panel="captions">
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
          </section>
          <section class="tool-panel transcript-panel" data-panel="transcript">
            <p class="peak">{html.escape(moment.peak_text)}</p>
            <dl><dt>Score</dt><dd>{moment.score}</dd><dt>Inicio</dt><dd>{moment.start:.1f}s</dd><dt>Fim</dt><dd>{moment.end:.1f}s</dd></dl>
            <details><summary>Transcript</summary><p>{html.escape(moment.transcript)}</p></details>
          </section>
          <footer class="export-dock" aria-label="Fila de exportacao do corte">
            <div>
              <strong>Export</strong>
              <span data-platform-summary>Nenhum destino marcado</span>
            </div>
            <div class="platform-tags" role="group" aria-label="Adicionar destino na fila final">
              <button data-platform="tiktok">TikTok</button>
              <button data-platform="shorts">Shorts</button>
              <button data-platform="instagram">Instagram</button>
              <button data-platform="facebook">Facebook</button>
              <button data-platform="youtube">YouTube</button>
            </div>
          </footer>
          </div>
        </div>
    </details>"""


def media_html(moment: Moment) -> str:
    token = preview_cache_token(moment)
    poster = html.escape(cache_busted_url(moment.frame_file, token))
    clip = html.escape(cache_busted_url(moment.clip_file, token))
    if clip:
        return f'<video playsinline preload="none" loading="lazy" poster="{poster}" data-src="{clip}"></video>'
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
    <button data-tab="edit" class="active">1. Editar cortes</button>
    <button data-tab="final">2. Final</button>
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
  <section class="final-stage">
    <div class="stage-head">
      <div>
        <strong>Resultados</strong>
        <p data-final-summary>Selecione cortes antes de renderizar.</p>
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
header{position:sticky;top:0;z-index:5;display:flex;justify-content:space-between;gap:16px;align-items:center;padding:16px 22px;background:#050505;border-bottom:1px solid #202020}.header-actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
h1{margin:0;font-size:22px;letter-spacing:0}header p{margin:3px 0 0;color:#9a9a9a}.tabs{position:sticky;top:70px;z-index:4;display:flex;gap:8px;padding:10px 22px;background:#060606;border-bottom:1px solid #1f1f1f}.tabs button{background:#191919;color:#ddd;border:1px solid #303030;padding:8px 12px}.tabs button.active{background:#f4f4f4;color:#050505;border-color:#f4f4f4}.config{position:sticky;top:119px;z-index:3;display:flex;justify-content:space-between;gap:14px;align-items:center;padding:12px 22px;background:#080808;border-bottom:1px solid #202020}.config strong{display:block;font-size:13px}.config span{color:#9a9a9a;font-size:12px}.segments{display:flex;gap:6px;flex-wrap:wrap}.segments button{background:#191919;color:#ddd;border:1px solid #303030;padding:8px 10px}.segments button.active{background:#f4f4f4;color:#050505;border-color:#f4f4f4}
main{display:grid;gap:12px;max-width:1440px;margin:0 auto;padding:16px 18px 28px}.card{border:1px solid #272727;border-radius:8px;background:#0d0d0d;overflow:hidden}.card[open]{border-color:#3b3b3b;background:#101010}.card.liked{border-color:#24d17e}.card.discarded{opacity:.46}.clip-summary{display:grid;grid-template-columns:auto minmax(0,1fr) auto;gap:12px;align-items:center;min-height:62px;padding:12px 14px;cursor:pointer;list-style:none}.clip-summary::-webkit-details-marker{display:none}.clip-rank{color:#8f8f8f;font-weight:700}.clip-title{display:grid;gap:2px;min-width:0}.clip-title strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:15px}.clip-title small{color:#9c9c9c}.clip-status{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}.clip-status span,.format-previews span{display:inline-flex;align-items:center;min-height:26px;padding:4px 8px;border-radius:999px;background:#242424;color:#ddd;font-size:12px}
.editor-shell{display:grid;grid-template-columns:minmax(280px,520px) minmax(360px,1fr);gap:14px;padding:0 14px 14px}.editor-preview{display:grid;align-content:start;justify-items:center;gap:10px}.preview-frame{display:grid;gap:10px;width:100%;max-width:520px}.media{position:relative;aspect-ratio:16/9;background:#000;max-height:72vh;overflow:hidden;border-radius:6px}.media video,.media img{width:100%;height:100%;object-fit:cover;display:block;background:#000;pointer-events:none}.placeholder{display:grid;place-items:center;height:100%;color:#777}.preview-bar{display:grid;grid-template-columns:1fr;gap:8px;justify-items:center;width:100%;padding:8px;border:1px solid #252525;border-radius:8px;background:#0a0a0a}.preview-controls,.preview-volume-group{display:flex;gap:6px;align-items:center}.preview-controls{justify-content:center;padding:4px;border:1px solid #202020;border-radius:999px;background:#111}.preview-volume-group{padding-left:4px;border-left:1px solid #2d2d2d}.preview-icon,.preview-step{display:inline-grid;place-items:center;width:32px;height:32px;min-width:32px;padding:0;border:1px solid #333;border-radius:999px;background:#191919;color:#ddd}.preview-play{background:#f4f4f4;color:#050505;border-color:#f4f4f4}.preview-icon svg{width:16px;height:16px;display:block;stroke:currentColor}.preview-step{width:26px;height:26px;min-width:26px;font-weight:700}.preview-volume-group output{min-width:32px;color:#d8d8d8;font-size:12px;text-align:center}.card[data-preview-format=tiktok] .preview-frame,.card[data-preview-format=shorts] .preview-frame,.card[data-preview-format=instagram] .preview-frame{max-width:min(100%,calc(72vh * 9 / 16))}.card[data-preview-format=facebook] .preview-frame{max-width:min(100%,calc(72vh * 4 / 5))}.card[data-preview-format=youtube] .preview-frame{max-width:min(100%,520px)}.card[data-preview-format=tiktok] .media,.card[data-preview-format=shorts] .media,.card[data-preview-format=instagram] .media{aspect-ratio:9/16}.card[data-preview-format=facebook] .media{aspect-ratio:4/5}.card[data-preview-format=youtube] .media{aspect-ratio:16/9}.preview-strip,.card-tabs{display:flex;gap:6px;flex-wrap:wrap}.preview-strip{justify-content:center;overflow:visible;padding-bottom:1px}.preview-strip button,.card-tabs button{background:#191919;color:#ddd;border:1px solid #303030;padding:8px 10px}.preview-strip button{min-height:34px;border-radius:999px;white-space:nowrap}.preview-strip button.active,.card-tabs button.active{background:#f4f4f4;color:#050505;border-color:#f4f4f4}
.editor-tools{display:grid;align-content:start;gap:12px}.tool-panel{display:none;border:1px solid #242424;border-radius:8px;background:#0a0a0a;padding:12px}.tool-panel.active{display:block}.tool-summary{margin-bottom:10px;color:#d8d8d8}.timeline-editor{padding:0}.timeline-head{display:flex;justify-content:space-between;gap:12px;color:#aaa;font-size:12px}.timeline-head output{color:#f4f4f4;text-align:right}.timeline{position:relative;height:34px;margin-top:8px}.timeline-track{position:absolute;left:0;right:0;top:14px;height:6px;background:#292929;border-radius:999px;overflow:hidden}.timeline-fill{position:absolute;top:0;bottom:0;background:#f4f4f4;border-radius:999px}.timeline input{position:absolute;inset:0;width:100%;height:34px;margin:0;background:transparent;pointer-events:none;-webkit-appearance:none;appearance:none}.timeline input::-webkit-slider-thumb{width:18px;height:18px;border-radius:50%;background:#f4f4f4;border:2px solid #050505;pointer-events:auto;-webkit-appearance:none;appearance:none}.timeline input::-webkit-slider-runnable-track{background:transparent}.timeline input::-moz-range-thumb{width:18px;height:18px;border-radius:50%;background:#f4f4f4;border:2px solid #050505;pointer-events:auto}.timeline input::-moz-range-track{background:transparent}.timeline-values{display:flex;justify-content:space-between;color:#aaa;font-size:12px}.actions,.platform-tags{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.export-dock{display:grid;gap:8px;margin-top:2px;padding:12px;border:1px solid #303030;border-radius:8px;background:#111}.export-dock strong{display:block;font-size:13px}.export-dock span{color:#a8a8a8;font-size:12px}
.platform-tags button,.camera-card-buttons button,.effect-card-buttons button,.overlay-card-buttons button{background:#191919;color:#ddd;border:1px solid #333;text-align:left}.platform-tags button.active,.camera-card-buttons button.active,.effect-card-buttons button.active,.overlay-card-buttons button.active{background:#102018;color:#f4f4f4;border-color:#24d17e}.camera-card-controls,.effect-card-controls,.overlay-card-controls{display:grid;gap:10px}.camera-card-buttons,.effect-card-buttons,.overlay-card-buttons{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.camera-card-controls label,.effect-card-controls label,.overlay-card-controls label,.caption-settings label{display:grid;gap:6px;color:#aaa;font-size:12px}.camera-card-controls input,.effect-card-controls input,.overlay-card-controls input{width:100%;accent-color:#24d17e}.camera-card-controls select,.caption-settings select,.caption-settings input{width:100%;background:#050505;color:#f4f4f4;border:1px solid #333;border-radius:6px;padding:8px}.camera-segments{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.camera-segment{display:grid;gap:8px;padding:10px;border:1px solid #2a2a2a;border-radius:8px;background:#101010}.camera-segment strong{font-size:12px}.caption-settings{display:grid;grid-template-columns:160px 180px;gap:12px;max-width:380px}
.camera-surface video{object-position:var(--camera-x,50%) 50%;transform:scale(var(--camera-scale,1));transform-origin:var(--camera-x,50%) 50%}.camera-surface[data-camera-key=alternate] video{animation:camera-pan 6s ease-in-out infinite alternate}.camera-surface[data-camera-key=jump-cut] video{animation:camera-jump 3s steps(1,end) infinite alternate}@keyframes camera-pan{0%{object-position:22% 50%}100%{object-position:78% 50%}}@keyframes camera-jump{0%{object-position:22% 50%}50%{object-position:78% 50%}100%{object-position:78% 50%}}.camera-reticle{position:absolute;inset:14% 22%;border:1px solid rgba(36,209,126,.58);border-radius:8px;box-shadow:0 0 0 999px rgba(0,0,0,.1);pointer-events:none}
.card[data-effect=light-grain] .media video,.card[data-effect=light-grain] .media img{filter:contrast(1.08) brightness(1.02)}.card[data-effect=old-film] .media video,.card[data-effect=old-film] .media img{filter:sepia(.48) contrast(1.2) saturate(.62) brightness(.92)}.card[data-effect=vhs] .media video,.card[data-effect=vhs] .media img{filter:saturate(.62) contrast(1.22) brightness(.9) hue-rotate(-7deg)}.card[data-effect=bw-old] .media video,.card[data-effect=bw-old] .media img{filter:grayscale(1) contrast(1.22) brightness(.9)}.card[data-effect=light-grain] .media:after,.card[data-effect=old-film] .media:after,.card[data-effect=vhs] .media:after,.card[data-effect=bw-old] .media:after{content:"";position:absolute;inset:0;pointer-events:none;opacity:var(--effect-opacity,.24);background-image:radial-gradient(circle at 20% 30%,rgba(255,255,255,.95) 0 1px,transparent 1.6px),radial-gradient(circle at 70% 65%,rgba(0,0,0,.95) 0 1px,transparent 1.8px);background-size:4px 4px,6px 6px;mix-blend-mode:overlay}.card[data-effect=old-film] .media:before,.card[data-effect=bw-old] .media:before{content:"";position:absolute;inset:0;pointer-events:none;z-index:1;background:radial-gradient(circle at center,transparent 44%,rgba(0,0,0,.46) 100%)}.card[data-effect=vhs] .media:before{content:"";position:absolute;inset:0;pointer-events:none;z-index:1;background:repeating-linear-gradient(0deg,rgba(255,255,255,.08) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
.overlay-tools{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:end}.overlay-box{position:absolute;z-index:3;left:calc(var(--overlay-x)*100%);top:calc(var(--overlay-y)*100%);width:calc(var(--overlay-width)*100%);min-width:120px;padding:10px 14px 11px 18px;border-left:6px solid var(--overlay-accent,#24d17e);border-radius:8px;background:rgba(0,0,0,var(--overlay-opacity,.92));box-shadow:0 10px 30px rgba(0,0,0,.35);cursor:move;touch-action:none;user-select:none;pointer-events:auto}.overlay-box[data-overlay-key=none]{display:none}.overlay-box strong{font-size:clamp(13px,4vw,20px);line-height:1.05}.overlay-box em{display:block;margin-top:3px;color:rgba(255,255,255,.75);font-style:normal;font-size:clamp(10px,2.4vw,13px);line-height:1.2}.overlay-image-box{display:grid;place-items:center;min-width:72px;min-height:72px;padding:6px;border:1px dashed rgba(255,255,255,.42);background:rgba(0,0,0,.12);box-shadow:0 8px 24px rgba(0,0,0,.22)}.overlay-image-box img{display:block;width:100%;height:auto;max-height:100%;object-fit:contain;opacity:var(--overlay-opacity,1);pointer-events:none;background:transparent}.overlay-resize{position:absolute;right:5px;bottom:5px;width:14px;height:14px;padding:0;border:1px solid rgba(255,255,255,.42);border-radius:3px;background:rgba(255,255,255,.18);cursor:nwse-resize}.overlay-menu{position:absolute;z-index:6;display:grid;gap:8px;width:min(360px,94%);padding:8px;border:1px solid #333;border-radius:8px;background:#101010;box-shadow:0 14px 42px rgba(0,0,0,.5);touch-action:none}.overlay-menu[hidden]{display:none}.overlay-menu-head{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:2px 2px 4px;cursor:move}.overlay-menu-head strong{font-size:13px}.overlay-menu-head button{padding:6px 9px}.overlay-menu-actions{display:grid;grid-template-columns:repeat(2,minmax(120px,1fr));gap:6px}.overlay-menu button{background:#242424;color:#ddd;border:1px solid #333}.image-upload{padding:10px;border:1px dashed #333;border-radius:8px;background:#0f0f0f}.overlay-layer-list{display:grid;gap:6px}.overlay-layer-row{display:flex;justify-content:space-between;gap:8px;align-items:center;padding:8px;border:1px solid #242424;border-radius:6px;background:#101010}.overlay-layer-row span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.overlay-layer-row button{padding:6px 9px;background:#242424;color:#ddd;border:1px solid #333}.overlay-empty{padding:10px;border:1px dashed #333;border-radius:8px;color:#aaa}
p{color:#bebebe}.peak{color:#fff;font-size:16px}dl{display:grid;grid-template-columns:auto 1fr;gap:4px 10px;color:#aaa}dt{color:#707070}dd{margin:0}.transcript-panel details{border-top:1px solid #242424;margin-top:12px;padding-top:10px}.transcript-panel summary{cursor:pointer;color:#ddd}
body[data-tab=final] main,body[data-tab=final] .config{display:none}body[data-tab=final] .final-stage{display:block}.final-stage{display:none;margin:18px auto;max-width:1240px;padding:18px;border:1px solid #272727;border-radius:8px;background:#111}.stage-head{display:flex;justify-content:space-between;gap:16px;align-items:center}.render-status{margin-top:12px;color:#aaa}.render-results{display:grid;gap:12px;margin-top:14px}.result-item{border:1px solid #303030;border-radius:8px;background:#090909;overflow:hidden}.result-item[open]{border-color:#3b3b3b}.result-item summary{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:12px 14px;border:0;color:#f4f4f4}.result-item summary strong{font-size:14px}.result-item summary span{color:#aaa;font-size:12px}.result-body{display:grid;grid-template-columns:minmax(260px,420px) minmax(240px,1fr);gap:14px;padding:0 14px 14px}.result-body video{width:100%;max-height:70vh;background:#000;border-radius:6px;object-fit:contain}.result-meta{display:grid;align-content:start;gap:10px}.result-meta dl{margin:0}.result-actions{display:flex;gap:8px;flex-wrap:wrap}.result-actions a{display:inline-flex;align-items:center;justify-content:center;min-height:38px;padding:9px 12px;border-radius:6px;background:#f4f4f4;color:#050505;text-decoration:none}.result-actions a.secondary{background:#242424;color:#ddd;border:1px solid #333}
button{background:#f4f4f4;color:#050505;border:0;border-radius:6px;padding:9px 12px;cursor:pointer}#reset-ui,button[data-action=discard]{background:#242424;color:#ddd}button[data-action=reset-trim],button[data-action=next-card]{background:#191919;color:#ddd;border:1px solid #333}
@media(max-width:860px){header{position:relative;align-items:flex-start;flex-direction:column}.tabs{top:0;overflow:auto}.config{top:49px;align-items:flex-start;flex-direction:column}.segments button,.preview-strip button,.card-tabs button{font-size:12px;padding:7px 9px}main{padding:12px}.clip-summary{grid-template-columns:auto minmax(0,1fr);align-items:start}.clip-status{grid-column:1/-1;justify-content:flex-start}.editor-shell,.result-body,.camera-segments,.caption-settings,.preview-bar{grid-template-columns:1fr}.preview-frame{max-width:100%}.preview-strip{justify-content:center}.preview-controls{width:max-content;max-width:100%;flex-wrap:wrap}.media{max-height:none}.stage-head{align-items:flex-start;flex-direction:column}.result-item summary{align-items:flex-start;flex-direction:column}.camera-card-buttons,.effect-card-buttons,.overlay-card-buttons,.overlay-menu{grid-template-columns:1fr}}
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
  if (typeof raw === "string") return { status: raw, trimStart: 0, trimEnd: 0, platforms: [], camera: defaultCamera(), effect: defaultEffect(), overlay: defaultOverlay(), overlays: [], platformEdits: {} };
  const next = Object.assign({ status: null, trimStart: 0, trimEnd: 0, platforms: [], camera: defaultCamera(), effect: defaultEffect(), overlay: defaultOverlay(), overlays: [], platformEdits: {} }, raw || {});
  next.camera = normalizeCamera(next.camera);
  next.effect = normalizeEffect(next.effect);
  next.overlay = normalizeOverlay(next.overlay);
  next.overlays = normalizeOverlayLayers(next.overlays, next.overlay);
  next.platformEdits = normalizePlatformEdits(next.platformEdits, next);
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
const defaultPreviewVolume = 0.2;
const previewVolumeStep = 0.1;
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
  "jump-cut": { label: "Corte entre focos", note: "Troca seca entre lados", x: 50, scale: 1 },
  "soft-zoom": { label: "Zoom sutil", note: "Aproxima sem trocar o foco", x: 50, scale: 1.12 },
  "punch-in": { label: "Punch-in", note: "Mais fechado e energetico", x: 50, scale: 1.22 }
};
const cameraParts = [
  { key: "start", label: "Inicio" },
  { key: "middle", label: "Meio" },
  { key: "end", label: "Fim" }
];
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
  document.querySelectorAll(".card").forEach(card => {
    if (!card.dataset.previewTouched) {
      setCardPreviewFormat(card, next);
      if (card.open) updateCardTools(card);
    }
    updatePlatformUi(card);
  });
  renderFinalStage();
}
function applyTab(tab){
  const next = ["edit", "final"].includes(tab) ? tab : "edit";
  document.body.dataset.tab = next;
  localStorage.setItem("cutted-tab", next);
  document.querySelectorAll(".tabs [data-tab]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === next);
  });
  renderFinalStage();
}
function platformLabel(key){
  return (platformMeta[key] || { label: key }).label;
}
function validPlatform(format){
  return platformMeta[format] ? format : "tiktok";
}
function activePlatformForRank(rank){
  const card = cardForRank(rank);
  return validPlatform(card?.dataset.previewFormat || document.body.dataset.format || "tiktok");
}
function normalizePlatformEdit(edit, fallback){
  const source = edit && typeof edit === "object" ? edit : {};
  const base = fallback && typeof fallback === "object" ? fallback : {};
  const overlayFallback = source.overlay || base.overlay || defaultOverlay();
  const overlays = normalizeOverlayLayers(source.overlays, overlayFallback);
  return {
    camera: normalizeCamera(source.camera || base.camera || defaultCamera()),
    effect: normalizeEffect(source.effect || base.effect || defaultEffect()),
    overlay: overlays.find(layer => layer.kind !== "image") || defaultOverlay(),
    overlays
  };
}
function normalizePlatformEdits(edits, fallback){
  if (!edits || typeof edits !== "object") return {};
  return Object.fromEntries(Object.entries(edits)
    .filter(([key]) => platformMeta[key])
    .map(([key, edit]) => [key, normalizePlatformEdit(edit, fallback)]));
}
function platformEditForRank(rank, platform = activePlatformForRank(rank)){
  const current = cardState(String(rank));
  return normalizePlatformEdit(current.platformEdits[validPlatform(platform)], current);
}
function setPlatformEditForRank(rank, platform, patch){
  const key = validPlatform(platform);
  const current = cardState(String(rank));
  const edit = normalizePlatformEdit(Object.assign({}, platformEditForRank(rank, key), patch), current);
  setCardState(String(rank), {
    platformEdits: Object.assign({}, current.platformEdits, { [key]: edit })
  });
}
function defaultCamera(){ return cameraSequence(cameraParts.map(part => defaultCameraSegment(part.key))); }
function defaultCameraSegment(part){ return { part, part_label: cameraPartLabel(part), key: "center", label: cameraMeta.center.label, strength: 60 }; }
function cameraPartLabel(part){ return (cameraParts.find(item => item.key === part) || { label: part }).label; }
function cameraSequence(segments){ return { key: "sequence", label: "Linha de camera", strength: 60, segments }; }
function normalizeCamera(camera){
  if (camera?.key === "sequence" || Array.isArray(camera?.segments)) {
    const source = Array.isArray(camera?.segments) ? camera.segments : [];
    return cameraSequence(cameraParts.map(part => normalizeCameraSegment(source.find(item => item?.part === part.key), part.key)));
  }
  const base = normalizeSingleCamera(camera);
  return cameraSequence(cameraParts.map(part => Object.assign({ part: part.key, part_label: part.label }, base)));
}
function cameraLabel(camera){
  const current = normalizeCamera(camera);
  const active = current.segments.filter(segment => segment.key !== "center");
  if (!active.length) return cameraMeta.center.label;
  return active.map(segment => `${segment.part_label}: ${segment.label}`).join(" | ");
}
function cameraForRank(rank, platform = activePlatformForRank(rank)){ return platformEditForRank(rank, platform).camera; }
function setCameraSegmentForRank(rank, part, patch){
  const platform = activePlatformForRank(rank);
  const camera = cameraForRank(rank, platform);
  const segments = camera.segments.map(segment => {
    if (segment.part !== part) return segment;
    return normalizeCameraSegment(Object.assign({}, segment, patch), part);
  });
  setPlatformEditForRank(rank, platform, { camera: cameraSequence(segments) });
  const card = cardForRank(rank);
  if (card) updateCameraUi(card);
  renderFinalStage();
}
function normalizeSingleCamera(camera){
  const key = cameraMeta[camera?.key] ? camera.key : "center";
  const strength = Math.max(0, Math.min(Number(camera?.strength ?? 60), 100));
  return { key, label: cameraMeta[key].label, strength };
}
function normalizeCameraSegment(segment, part){
  const current = normalizeSingleCamera(segment);
  return Object.assign({ part, part_label: cameraPartLabel(part) }, current);
}
function cameraHasMovement(camera){
  return normalizeCamera(camera).segments.some(segment => segment.key !== "center");
}
function cameraStyle(camera){
  const current = normalizeSingleCamera(camera);
  const meta = cameraMeta[current.key] || cameraMeta.center;
  const strengthScale = current.key === "punch-in" ? current.strength / 500 : current.strength / 900;
  const scale = current.key === "center" || current.key === "face-left" || current.key === "face-right" || current.key === "alternate" || current.key === "jump-cut"
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
function effectForRank(rank, platform = activePlatformForRank(rank)){ return platformEditForRank(rank, platform).effect; }
function setEffectForRank(rank, patch){
  const platform = activePlatformForRank(rank);
  const current = effectForRank(rank, platform);
  setPlatformEditForRank(rank, platform, { effect: normalizeEffect(Object.assign({}, current, patch)) });
  const card = cardForRank(rank);
  if (card) updateEffectUi(card);
  renderFinalStage();
}
function effectOpacity(effect){
  const current = normalizeEffect(effect);
  return current.key === "none" ? 0 : Math.max(.12, current.intensity / 185);
}
function defaultOverlay(){ return { key: "none", label: overlayMeta.none.label, x: .62, y: .78, width: .34, opacity: 95 }; }
function overlayId(){
  return `layer-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}
function normalizeOverlay(overlay){
  const key = overlayMeta[overlay?.key] ? overlay.key : "none";
  if (key === "none") return defaultOverlay();
  return {
    id: String(overlay?.id || overlayId()),
    kind: "cta",
    key,
    label: overlayMeta[key].label,
    x: clampNumber(overlay?.x ?? .62, 0, 1),
    y: clampNumber(overlay?.y ?? .78, 0, 1),
    width: clampNumber(overlay?.width ?? .34, .18, .72),
    opacity: clampNumber(overlay?.opacity ?? 95, 35, 100)
  };
}
function normalizeImageOverlay(layer){
  return {
    id: String(layer?.id || overlayId()),
    kind: "image",
    key: "image",
    label: String(layer?.label || "Imagem"),
    x: clampNumber(layer?.x ?? .58, 0, 1),
    y: clampNumber(layer?.y ?? .68, 0, 1),
    width: clampNumber(layer?.width ?? .28, .08, .9),
    opacity: clampNumber(layer?.opacity ?? 100, 10, 100),
    image_data_url: String(layer?.image_data_url || ""),
    image_file: String(layer?.image_file || "")
  };
}
function normalizeOverlayLayer(layer){
  if (layer?.kind === "image" || layer?.key === "image") return normalizeImageOverlay(layer);
  return normalizeOverlay(layer);
}
function normalizeOverlayLayers(layers, fallback){
  const source = Array.isArray(layers) ? layers : [];
  const normalized = source.map(normalizeOverlayLayer).filter(layer => layer.key !== "none");
  if (normalized.length) return normalized;
  const legacy = normalizeOverlay(fallback);
  return legacy.key === "none" ? [] : [legacy];
}
function overlayLayersForRank(rank, platform = activePlatformForRank(rank)){ return platformEditForRank(rank, platform).overlays; }
function primaryOverlayForRank(rank, platform = activePlatformForRank(rank)){
  const layers = overlayLayersForRank(rank, platform).filter(layer => layer.kind !== "image");
  return layers[0] || defaultOverlay();
}
function setOverlayLayersForRank(rank, layers, rerender = true){
  const platform = activePlatformForRank(rank);
  const normalized = normalizeOverlayLayers(layers, defaultOverlay());
  setPlatformEditForRank(rank, platform, { overlays: normalized, overlay: normalized.find(layer => layer.kind !== "image") || defaultOverlay() });
  const card = cardForRank(rank);
  if (card && rerender) updateOverlayUi(card);
  renderFinalStage();
}
function addOverlayLayerForRank(rank, layer){
  setOverlayLayersForRank(rank, [...overlayLayersForRank(rank), normalizeOverlayLayer(layer)]);
}
function patchOverlayLayerForRank(rank, id, patch, rerender = true){
  const layers = overlayLayersForRank(rank).map(layer => layer.id === id ? normalizeOverlayLayer(Object.assign({}, layer, patch)) : layer);
  setOverlayLayersForRank(rank, layers, rerender);
}
function removeOverlayLayerForRank(rank, id){
  setOverlayLayersForRank(rank, overlayLayersForRank(rank).filter(layer => layer.id !== id));
}
function setOverlayForRank(rank, patch, rerender = true){
  const layers = overlayLayersForRank(rank);
  const first = layers.find(layer => layer.kind !== "image");
  if (first) {
    patchOverlayLayerForRank(rank, first.id, patch, rerender);
    return;
  }
  setOverlayLayersForRank(rank, [normalizeOverlay(Object.assign({}, defaultOverlay(), patch))], rerender);
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
function cardForRank(rank){
  return document.querySelector(`.card[data-rank="${CSS.escape(String(rank))}"]`);
}
function statusLabel(status){
  if (status === "liked") return "Aprovado";
  if (status === "discarded") return "Descartado";
  return "Pendente";
}
function setCardPreviewFormat(card, format){
  const next = validPlatform(format);
  card.dataset.previewFormat = next;
  card.querySelectorAll("[data-card-format-preview]").forEach(button => {
    button.classList.toggle("active", button.dataset.cardFormatPreview === next);
  });
  const status = card.querySelector("[data-platform-preset-current]");
  if (status) status.textContent = `Editando preset: ${platformLabel(next)}`;
}
function updateCardTools(card){
  updateCameraUi(card);
  updateEffectUi(card);
  updateOverlayUi(card);
}
function updateCameraUi(card){
  const camera = cameraForRank(card.dataset.rank);
  const active = camera.segments.find(segment => segment.key !== "center") || camera.segments[0] || defaultCameraSegment("start");
  const surface = card.querySelector(".camera-surface");
  if (surface) {
    surface.dataset.cameraKey = active.key;
    surface.setAttribute("style", cameraStyle(active));
  }
  const summary = card.querySelector("[data-camera-current]");
  if (summary) summary.textContent = cameraLabel(camera);
  const container = card.querySelector("[data-card-camera]");
  if (!container) return;
  container.innerHTML = `<div class="camera-card-controls">${cameraSegmentsHtml(camera)}</div>`;
  bindCardCameraControls(card);
}
function bindCardCameraControls(card){
  const rank = card.dataset.rank;
  card.querySelectorAll("[data-preview-camera-segment]").forEach(select => {
    select.addEventListener("change", () => setCameraSegmentForRank(rank, select.dataset.previewCameraSegment, { key: select.value }));
  });
  card.querySelectorAll("[data-preview-camera-strength]").forEach(strength => {
    const update = () => setCameraSegmentForRank(rank, strength.dataset.previewCameraStrength, { strength: Number(strength.value) });
    strength.addEventListener("input", update);
    strength.addEventListener("change", update);
  });
}
function updateEffectUi(card){
  const effect = effectForRank(card.dataset.rank);
  card.dataset.effect = effect.key;
  card.style.setProperty("--effect-opacity", effectOpacity(effect));
  const summary = card.querySelector("[data-effect-current]");
  if (summary) summary.textContent = effectLabel(effect);
  const container = card.querySelector("[data-card-effect]");
  if (!container) return;
  container.innerHTML = `<div class="effect-card-controls">
    <div class="effect-card-buttons" role="group" aria-label="Efeito do corte ${escapeAttr(card.dataset.rank)}">${effectButtonsHtml(effect)}</div>
    <label>Intensidade
      <input data-preview-effect-intensity type="range" min="0" max="100" step="5" value="${effect.intensity}">
    </label>
  </div>`;
  bindCardEffectControls(card);
}
function bindCardEffectControls(card){
  const rank = card.dataset.rank;
  card.querySelectorAll("[data-preview-effect]").forEach(button => {
    button.addEventListener("click", () => setEffectForRank(rank, { key: button.dataset.previewEffect }));
  });
  const intensity = card.querySelector("[data-preview-effect-intensity]");
  if (!intensity) return;
  intensity.addEventListener("input", () => setEffectForRank(rank, { intensity: Number(intensity.value) }));
  intensity.addEventListener("change", () => setEffectForRank(rank, { intensity: Number(intensity.value) }));
}
function updateOverlayUi(card){
  const layers = overlayLayersForRank(card.dataset.rank);
  const summary = card.querySelector("[data-overlay-current]");
  if (summary) summary.textContent = layers.length ? `${layers.length} camada(s)` : "Sem chamada";
  renderOverlayLayerBoxes(card, layers);
  const container = card.querySelector("[data-card-overlay]");
  if (!container) return;
  const primary = primaryOverlayForRank(card.dataset.rank);
  container.innerHTML = `<div class="overlay-card-controls">
    <div class="overlay-card-buttons" role="group" aria-label="Adicionar chamada no corte ${escapeAttr(card.dataset.rank)}">${overlayButtonsHtml(primary)}</div>
    <label class="image-upload">Imagem transparente
      <input data-overlay-image type="file" accept="image/png,image/webp,image/jpeg">
    </label>
    <div class="overlay-layer-list" data-overlay-layer-controls>${overlayLayerControlsHtml(layers)}</div>
    <div class="overlay-tools">
      <label>Opacidade
        <input data-preview-overlay-opacity type="range" min="10" max="100" step="5" value="${(layers[0] || defaultOverlay()).opacity}">
      </label>
      <button data-overlay-reset>Resetar posicao</button>
    </div>
  </div>`;
  bindCardOverlayControls(card);
}
function renderOverlayLayerBoxes(card, layers){
  const list = card.querySelector("[data-overlay-layer-list]");
  if (!list) return;
  list.innerHTML = layers.map(overlayLayerBoxHtml).join("");
}
function overlayLayerBoxHtml(layer){
  if (layer.kind === "image") {
    const src = layer.image_data_url || layer.image_file || "";
    return `<div class="overlay-box overlay-image-box" data-overlay-drag data-overlay-layer="${escapeAttr(layer.id)}" data-overlay-key="image" style="${escapeAttr(overlayStyle(layer))}">
      <img src="${escapeAttr(src)}" alt="${escapeAttr(layer.label)}">
      <button class="overlay-resize" data-overlay-resize title="Redimensionar"></button>
    </div>`;
  }
  const meta = overlayMeta[layer.key] || overlayMeta.none;
  return `<div class="overlay-box" data-overlay-drag data-overlay-layer="${escapeAttr(layer.id)}" data-overlay-key="${escapeAttr(layer.key)}" style="${escapeAttr(overlayStyle(layer))}">
    <strong>${escapeHtml(meta.title)}</strong>
    <em>${escapeHtml(meta.subtitle)}</em>
    <button class="overlay-resize" data-overlay-resize title="Redimensionar"></button>
  </div>`;
}
function overlayLayerControlsHtml(layers){
  if (!layers.length) return '<div class="overlay-empty">Clique no preview ou envie uma imagem.</div>';
  return layers.map((layer, index) => {
    const label = layer.kind === "image" ? layer.label : (overlayMeta[layer.key]?.label || layer.label);
    return `<div class="overlay-layer-row" data-overlay-layer-row="${escapeAttr(layer.id)}">
      <span>${index + 1}. ${escapeHtml(label)}</span>
      <button data-overlay-remove="${escapeAttr(layer.id)}">Remover</button>
    </div>`;
  }).join("");
}
function overlayPlaceButtonsHtml(){
  const actions = Object.entries(overlayMeta).filter(([key]) => key !== "none").map(([key, meta]) => {
    return `<button data-overlay-place="${escapeAttr(key)}">${escapeHtml(meta.label)}</button>`;
  }).join("");
  return `<div class="overlay-menu-head" data-overlay-menu-drag><strong>Chamada</strong><button data-overlay-close>Fechar</button></div><div class="overlay-menu-actions">${actions}</div>`;
}
function bindCardOverlayControls(card){
  const rank = card.dataset.rank;
  card.querySelectorAll("[data-preview-overlay]").forEach(button => {
    button.addEventListener("click", () => addOverlayLayerForRank(rank, { key: button.dataset.previewOverlay, x: .62, y: .78 }));
  });
  const opacity = card.querySelector("[data-preview-overlay-opacity]");
  if (opacity) {
    const update = () => {
      const first = overlayLayersForRank(rank)[0];
      if (first) patchOverlayLayerForRank(rank, first.id, { opacity: Number(opacity.value) });
    };
    opacity.addEventListener("input", update);
    opacity.addEventListener("change", update);
  }
  const reset = card.querySelector("[data-overlay-reset]");
  if (reset) reset.addEventListener("click", () => {
    const layers = overlayLayersForRank(rank).map(layer => Object.assign({}, layer, { x: .62, y: .78, width: layer.kind === "image" ? .28 : .34 }));
    setOverlayLayersForRank(rank, layers);
  });
  card.querySelectorAll("[data-overlay-remove]").forEach(button => {
    button.addEventListener("click", () => removeOverlayLayerForRank(rank, button.dataset.overlayRemove));
  });
  const imageInput = card.querySelector("[data-overlay-image]");
  if (imageInput) imageInput.addEventListener("change", () => addImageOverlayFromInput(card, imageInput));
  bindOverlayDrag(card);
  bindOverlayPlacement(card);
}
function addImageOverlayFromInput(card, input){
  const file = input.files && input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    addOverlayLayerForRank(card.dataset.rank, {
      id: overlayId(),
      kind: "image",
      key: "image",
      label: file.name,
      image_data_url: String(reader.result || ""),
      x: .36,
      y: .34,
      width: .28,
      opacity: 100
    });
    input.value = "";
  };
  reader.readAsDataURL(file);
}
function bindOverlayPlacement(card){
  const surface = card.querySelector("[data-overlay-surface]");
  const menu = card.querySelector("[data-overlay-menu]");
  if (!surface || !menu) return;
  menu.innerHTML = overlayPlaceButtonsHtml();
  const closeMenu = () => { menu.hidden = true; };
  menu.querySelector("[data-overlay-close]")?.addEventListener("click", closeMenu);
  bindOverlayMenuDrag(surface, menu);
  surface.onclick = event => {
    if (event.target.closest("[data-overlay-drag]") || event.target.closest("[data-overlay-menu]") || event.target.closest(".preview-bar")) return;
    const rect = surface.getBoundingClientRect();
    const x = clampNumber((event.clientX - rect.left) / rect.width, 0, 1);
    const y = clampNumber((event.clientY - rect.top) / rect.height, 0, 1);
    menu.dataset.x = x;
    menu.dataset.y = y;
    positionOverlayMenu(surface, menu, event.clientX - rect.left, event.clientY - rect.top);
    menu.hidden = false;
  };
  menu.querySelectorAll("[data-overlay-place]").forEach(button => {
    button.addEventListener("click", () => {
      addOverlayLayerForRank(card.dataset.rank, { key: button.dataset.overlayPlace, x: Number(menu.dataset.x), y: Number(menu.dataset.y) });
      closeMenu();
    });
  });
  document.addEventListener("pointerdown", event => {
    if (menu.hidden || surface.contains(event.target)) return;
    closeMenu();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") closeMenu();
  });
}
function bindOverlayMenuDrag(surface, menu){
  const handle = menu.querySelector("[data-overlay-menu-drag]");
  if (!handle) return;
  let drag = null;
  const start = event => {
    if (event.type === "mousedown" && drag) return;
    if (event.target.closest("button")) return;
    const surfaceRect = surface.getBoundingClientRect();
    const menuRect = menu.getBoundingClientRect();
    drag = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      startLeft: menuRect.left - surfaceRect.left,
      startTop: menuRect.top - surfaceRect.top
    };
    if (event.pointerId !== undefined && handle.setPointerCapture) handle.setPointerCapture(event.pointerId);
    if (event.type === "mousedown") {
      document.addEventListener("mousemove", move);
      document.addEventListener("mouseup", end, { once: true });
    }
    event.preventDefault();
    event.stopPropagation();
  };
  const move = event => {
    if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
    positionOverlayMenu(surface, menu, drag.startLeft + event.clientX - drag.startX, drag.startTop + event.clientY - drag.startY);
    event.preventDefault();
    event.stopPropagation();
  };
  const end = event => {
    if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
    drag = null;
    document.removeEventListener("mousemove", move);
    event.stopPropagation();
  };
  handle.onpointerdown = start;
  handle.onpointermove = move;
  handle.onpointerup = end;
  handle.onpointercancel = end;
  handle.onmousedown = start;
}
function positionOverlayMenu(surface, menu, left, top){
  const rect = surface.getBoundingClientRect();
  const menuWidth = menu.offsetWidth || Math.min(360, rect.width * .94);
  const menuHeight = menu.offsetHeight || 150;
  menu.style.left = `${clampNumber(left, 8, Math.max(rect.width - menuWidth - 8, 8))}px`;
  menu.style.top = `${clampNumber(top, 8, Math.max(rect.height - menuHeight - 8, 8))}px`;
}
function updatePlatformUi(card){
  const current = cardState(card.dataset.rank);
  const platforms = Array.isArray(current.platforms) ? current.platforms : [];
  card.querySelectorAll("[data-platform]").forEach(btn => {
    btn.classList.toggle("active", platforms.includes(btn.dataset.platform));
  });
  const fallback = document.body.dataset.format || "tiktok";
  const summary = platforms.length
    ? `Na fila: ${platforms.map(platformLabel).join(", ")}`
    : (current.status === "liked" ? `Fila usa formato atual: ${platformLabel(fallback)}` : "Fora da fila final");
  card.querySelectorAll("[data-platform-summary]").forEach(item => { item.textContent = summary; });
  const status = card.querySelector("[data-status-pill]");
  if (status) status.textContent = statusLabel(current.status);
}
function paint(card){
  const current = cardState(card.dataset.rank);
  card.classList.toggle("liked",current.status==="liked");
  card.classList.toggle("discarded",current.status==="discarded");
  const status = card.querySelector("[data-status-pill]");
  if (status) status.textContent = statusLabel(current.status);
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
  const summary = `Final: ${fixed(values.adjustedStart)} - ${fixed(values.adjustedEnd)} (${fixed(values.adjustedEnd - values.adjustedStart)})`;
  card.querySelector("[data-trim-summary]").textContent = summary;
  const cardSummary = card.querySelector("[data-card-summary]");
  if (cardSummary) cardSummary.textContent = summary;
  const fill = card.querySelector("[data-trim-fill]");
  const duration = Math.max(values.duration, .1);
  fill.style.left = `${(values.startPos / duration) * 100}%`;
  fill.style.right = `${100 - ((values.endPos / duration) * 100)}%`;
}
function seekPreview(card){
  const video = card.querySelector("video");
  if (!video) return;
  loadCardVideo(card);
  const values = trimValues(card);
  video.currentTime = values.trimStart;
}
function togglePreviewPlayback(card){
  const video = card.querySelector("video");
  if (!video) return;
  loadCardVideo(card);
  applyPreviewVolume(video);
  if (video.paused) {
    const playback = video.play();
    if (playback && typeof playback.catch === "function") playback.catch(() => syncPreviewPlayButton(card));
    return;
  }
  video.pause();
}
function applyPreviewVolume(video){
  if (!video) return;
  if (!video.dataset.volumeReady) {
    video.volume = defaultPreviewVolume;
    video.dataset.volumeReady = "1";
  }
}
function setPreviewVolume(card, value){
  const video = card.querySelector("video");
  if (!video) return;
  video.dataset.volumeReady = "1";
  video.volume = clampNumber(value, 0, 1);
  video.muted = video.volume <= 0;
  syncPreviewVolumeButton(card);
}
function syncPreviewPlayButton(card){
  const button = card.querySelector("[data-preview-play]");
  const video = card.querySelector("video");
  if (!button) return;
  if (!video) {
    button.hidden = true;
    return;
  }
  button.hidden = false;
  button.innerHTML = previewIcon(video.paused ? "play" : "pause");
  button.setAttribute("aria-label", video.paused ? "Reproduzir" : "Pausar");
  button.title = video.paused ? "Reproduzir" : "Pausar";
}
function togglePreviewVolume(card){
  const video = card.querySelector("video");
  if (!video) return;
  applyPreviewVolume(video);
  video.muted = !video.muted;
  syncPreviewVolumeButton(card);
}
function stepPreviewVolume(card, direction){
  const video = card.querySelector("video");
  if (!video) return;
  applyPreviewVolume(video);
  setPreviewVolume(card, (video.muted ? 0 : video.volume) + (direction * previewVolumeStep));
}
function syncPreviewVolumeButton(card){
  const button = card.querySelector("[data-preview-volume]");
  const value = card.querySelector("[data-preview-volume-value]");
  const video = card.querySelector("video");
  if (!button) return;
  if (!video) {
    button.hidden = true;
    if (value) value.hidden = true;
    return;
  }
  applyPreviewVolume(video);
  button.hidden = false;
  if (value) value.hidden = false;
  const percent = Math.round((video.muted ? 0 : video.volume) * 100);
  button.innerHTML = previewIcon(video.muted || video.volume <= 0 ? "volume-off" : "volume");
  button.setAttribute("aria-label", video.muted ? "Ativar volume" : "Silenciar");
  button.title = video.muted ? "Ativar volume" : "Silenciar";
  if (value) value.textContent = `${percent}%`;
}
function previewIcon(name){
  const icons = {
    play: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z" fill="currentColor" stroke="none"></path></svg>',
    pause: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5h4v14H7zM13 5h4v14h-4z" fill="currentColor" stroke="none"></path></svg>',
    volume: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor" stroke="none"></path><path d="M16 9.5c1.2 1.4 1.2 3.6 0 5M18.5 7c2.4 2.8 2.4 7.2 0 10" fill="none" stroke-width="2" stroke-linecap="round"></path></svg>',
    "volume-off": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4z" fill="currentColor" stroke="none"></path><path d="M16 9l5 5M21 9l-5 5" fill="none" stroke-width="2" stroke-linecap="round"></path></svg>'
  };
  return icons[name] || "";
}
function loadCardVideo(card){
  const video = card.querySelector("video[data-src]");
  if (!video || video.getAttribute("src")) return;
  video.setAttribute("src", video.dataset.src);
  applyPreviewVolume(video);
  video.load();
  syncPreviewPlayButton(card);
  syncPreviewVolumeButton(card);
}
function unloadCardVideo(card){
  const video = card.querySelector("video[data-src]");
  if (!video || !video.getAttribute("src")) return;
  video.pause();
  video.removeAttribute("src");
  video.load();
  syncPreviewPlayButton(card);
  syncPreviewVolumeButton(card);
}
function activateCard(card){
  document.querySelectorAll(".card[open]").forEach(item => {
    if (item === card) return;
    item.open = false;
    unloadCardVideo(item);
  });
  if (card.open) {
    loadCardVideo(card);
    updateCardTools(card);
  } else {
    unloadCardVideo(card);
  }
}
function openNextCard(card){
  const cards = Array.from(document.querySelectorAll(".card"));
  const index = cards.indexOf(card);
  const next = cards[index + 1];
  if (next) {
    next.open = true;
    next.scrollIntoView({ behavior: "smooth", block: "start" });
    activateCard(next);
    return;
  }
  applyTab("final");
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
    overlay: primaryOverlayForRank(moment.rank),
    overlays: overlayLayersForRank(moment.rank),
    platform_edits: current.platformEdits
  });
}
function buildExportData(){
  const data = Object.assign({}, window.CUTTED_DATA);
  data.export_format = document.body.dataset.format || "tiktok";
  const adjusted = data.moments.map(adjustedMoment);
  data.moments = adjusted;
  data.selected = adjusted.filter(m => m.status === "liked" || m.platforms.length > 0);
  data.caption_queue = data.selected.flatMap(moment => captionPlatforms(moment, data.export_format).map(platform => {
    const edit = platformEditForRank(moment.rank, platform);
    const overlays = edit.overlays;
    return {
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
      camera: edit.camera,
      effect: edit.effect,
      overlay: overlays.find(layer => layer.kind !== "image") || defaultOverlay(),
      overlays,
      clip_file: moment.clip_file,
      title: moment.title,
      peak_text: moment.peak_text,
      transcript: moment.transcript,
      caption_segments: moment.caption_segments || []
    };
  }));
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
  const previewSegment = camera.segments.find(segment => segment.key !== "center") || camera.segments[0] || defaultCameraSegment("start");
  const src = cacheBustedPreview(item.clip_file || "", `camera-${item.rank}-${item.adjusted_start}-${item.adjusted_end}`);
  return `<article class="caption-item" data-rank="${escapeAttr(item.rank)}" data-platform="${escapeAttr(item.platform)}">
    <div class="caption-preview camera-surface" data-camera-key="${escapeAttr(previewSegment.key)}" style="${escapeAttr(cameraStyle(previewSegment))}">
      <video controls preload="metadata" src="${escapeAttr(src)}"></video>
      <div class="camera-reticle"></div>
    </div>
    <div class="caption-item-body">
      <strong>Preview #${String(item.rank).padStart(2, "0")} ${escapeHtml(item.title || "")}</strong>
      <span>${escapeHtml(item.platform_label)}</span><span data-camera-current>${escapeHtml(cameraLabel(camera))}</span>
      <div class="camera-card-controls">
        ${cameraSegmentsHtml(camera)}
      </div>
    </div>
  </article>`;
}
function cameraSegmentsHtml(camera){
  return `<div class="camera-segments">${cameraParts.map(part => {
    const segment = camera.segments.find(item => item.part === part.key) || defaultCameraSegment(part.key);
    return `<div class="camera-segment" data-camera-part="${escapeAttr(part.key)}">
      <strong>${escapeHtml(part.label)}</strong>
      <select data-preview-camera-segment="${escapeAttr(part.key)}">${cameraOptionsHtml(segment.key)}</select>
      <label>Forca
        <input data-preview-camera-strength="${escapeAttr(part.key)}" type="range" min="0" max="100" step="5" value="${segment.strength}">
      </label>
    </div>`;
  }).join("")}</div>`;
}
function cameraOptionsHtml(selectedKey){
  return Object.entries(cameraMeta).map(([key, meta]) => {
    const selected = selectedKey === key ? " selected" : "";
    return `<option value="${escapeAttr(key)}"${selected}>${escapeHtml(meta.label)}</option>`;
  }).join("");
}
function bindCameraPreviewControls(){
  document.querySelectorAll("[data-camera-preview] .caption-item").forEach(item => {
    const rank = item.dataset.rank;
    item.querySelectorAll("[data-preview-camera-segment]").forEach(select => {
      select.addEventListener("change", () => setCameraSegmentForRank(rank, select.dataset.previewCameraSegment, { key: select.value }));
    });
    item.querySelectorAll("[data-preview-camera-strength]").forEach(strength => {
      const update = () => setCameraSegmentForRank(rank, strength.dataset.previewCameraStrength, { strength: Number(strength.value) });
      strength.addEventListener("input", update);
      strength.addEventListener("change", update);
    });
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
  if (!surface) return;
  item.querySelectorAll("[data-overlay-drag]").forEach(box => {
    if (box.dataset.overlayKey === "none") return;
    let drag = null;
    const startDrag = event => {
      if (event.type === "mousedown" && drag) return;
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
      if (event.pointerId !== undefined && box.setPointerCapture) box.setPointerCapture(event.pointerId);
      if (event.type === "mousedown") {
        document.addEventListener("mousemove", moveDrag);
        document.addEventListener("mouseup", endDrag, { once: true });
      }
      event.preventDefault();
      event.stopPropagation();
    };
    const moveDrag = event => {
      if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
      const dx = event.clientX - drag.startX;
      const dy = event.clientY - drag.startY;
      const patch = {};
      if (drag.type === "resize") {
        const minWidth = box.dataset.overlayKey === "image" ? .08 : .18;
        const width = clampNumber((drag.startWidth + dx) / drag.surfaceWidth, minWidth, .9);
        box.style.setProperty("--overlay-width", width);
        patch.width = width;
      } else {
        const boxRect = box.getBoundingClientRect();
        const maxLeft = Math.max(drag.surfaceWidth - boxRect.width, 0);
        const maxTop = Math.max(drag.surfaceHeight - boxRect.height, 0);
        const left = clampNumber(drag.startLeft + dx, 0, maxLeft);
        const top = clampNumber(drag.startTop + dy, 0, maxTop);
        patch.x = drag.surfaceWidth ? left / drag.surfaceWidth : 0;
        patch.y = drag.surfaceHeight ? top / drag.surfaceHeight : 0;
        box.style.setProperty("--overlay-x", patch.x);
        box.style.setProperty("--overlay-y", patch.y);
      }
      patchOverlayLayerForRank(item.dataset.rank, box.dataset.overlayLayer, patch, false);
      event.preventDefault();
      event.stopPropagation();
    };
    const endDrag = event => {
      if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
      drag = null;
      document.removeEventListener("mousemove", moveDrag);
      updateOverlayUi(item);
      event.stopPropagation();
    };
    box.onpointerdown = startDrag;
    box.onpointermove = moveDrag;
    box.onpointerup = endDrag;
    box.onpointercancel = endDrag;
    box.onmousedown = startDrag;
  });
}
function renderFinalStage(){
  const queue = buildExportData().caption_queue || [];
  const summary = document.querySelector("[data-final-summary]");
  if (summary) {
    const cameraCount = queue.filter(item => cameraHasMovement(item.camera)).length;
    const effectCount = queue.filter(item => normalizeEffect(item.effect).key !== "none").length;
    const overlayCount = queue.reduce((count, item) => count + normalizeOverlayLayers(item.overlays, item.overlay).length, 0);
    summary.textContent = queue.length
      ? `${queue.length} video(s) na fila; ${cameraCount} com camera; ${effectCount} com efeito; ${overlayCount} com chamada.`
      : "Selecione cortes antes de renderizar.";
  }
}
function captionLines(){
  return Number(localStorage.getItem("cutted-caption-lines") || 2);
}
function captionWidth(){
  return Number(localStorage.getItem("cutted-caption-width") || 28);
}
function syncCaptionInputs(){
  document.querySelectorAll("[data-caption-lines]").forEach(input => { input.value = String(captionLines()); });
  document.querySelectorAll("[data-caption-width]").forEach(input => { input.value = String(captionWidth()); });
}
function captionCommand(){
  const chars = captionWidth();
  const lines = captionLines();
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
        chars_per_line: captionWidth(),
        max_lines: captionLines()
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
      cameraHasMovement(camera) ? cameraLabel(camera) : "",
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
            <dt>Camera</dt><dd>${escapeHtml(cameraLabel(camera))}</dd>
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
syncCaptionInputs();
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
  updateCardTools(card);
  const summary = card.querySelector(".clip-summary");
  if (summary) {
    const toggleCard = event => {
      event.preventDefault();
      card.open = !card.open;
      activateCard(card);
    };
    summary.addEventListener("click", toggleCard);
    summary.addEventListener("keydown", event => {
      if (event.key !== "Enter" && event.key !== " ") return;
      toggleCard(event);
    });
  }
  card.querySelectorAll("[data-card-panel]").forEach(button => {
    button.addEventListener("click", () => {
      card.querySelectorAll("[data-card-panel]").forEach(item => item.classList.toggle("active", item === button));
      card.querySelectorAll("[data-panel]").forEach(panel => panel.classList.toggle("active", panel.dataset.panel === button.dataset.cardPanel));
    });
  });
  card.querySelectorAll("[data-card-format-preview]").forEach(button => {
    button.addEventListener("click", () => {
      card.dataset.previewTouched = "1";
      setCardPreviewFormat(card, button.dataset.cardFormatPreview);
      updateCardTools(card);
      renderFinalStage();
    });
  });
  const playButton = card.querySelector("[data-preview-play]");
  if (playButton) {
    playButton.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      togglePreviewPlayback(card);
    });
  }
  const volumeButton = card.querySelector("[data-preview-volume]");
  if (volumeButton) {
    volumeButton.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      togglePreviewVolume(card);
    });
  }
  const volumeDown = card.querySelector("[data-preview-volume-down]");
  if (volumeDown) {
    volumeDown.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      stepPreviewVolume(card, -1);
    });
  }
  const volumeUp = card.querySelector("[data-preview-volume-up]");
  if (volumeUp) {
    volumeUp.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      stepPreviewVolume(card, 1);
    });
  }
  const video = card.querySelector("video");
  if (video) {
    applyPreviewVolume(video);
    video.addEventListener("play", () => {
      const values = trimValues(card);
      if (video.currentTime < values.trimStart || video.currentTime >= values.duration - values.trimEnd) {
        video.currentTime = values.trimStart;
      }
      syncPreviewPlayButton(card);
    });
    video.addEventListener("pause", () => {
      syncPreviewPlayButton(card);
    });
    video.addEventListener("volumechange", () => {
      syncPreviewVolumeButton(card);
    });
    video.addEventListener("timeupdate", () => {
      const values = trimValues(card);
      if (video.currentTime >= values.duration - values.trimEnd) {
        video.pause();
        video.currentTime = values.trimStart;
      }
    });
  }
  syncPreviewPlayButton(card);
  syncPreviewVolumeButton(card);
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
    if (btn.dataset.action === "next-card") {
      openNextCard(card);
      return;
    }
    setCardState(card.dataset.rank, { status: btn.dataset.action === "like" ? "liked" : "discarded" });
    paint(card);
    updatePlatformUi(card);
    renderCaptionQueue();
  }));
  if (card.open) activateCard(card);
});
document.getElementById("export").addEventListener("click", async () => {
  downloadJson(buildExportData(), "selected-clips.json");
});
document.getElementById("reset-ui").addEventListener("click", () => {
  if (!confirm("Zerar cortes, formatos e estado desta interface?")) return;
  localStorage.removeItem("cutted-state");
  localStorage.removeItem("cutted-format");
  localStorage.removeItem("cutted-tab");
  localStorage.removeItem("cutted-caption-lines");
  localStorage.removeItem("cutted-caption-width");
  location.reload();
});
document.getElementById("export-final-queue").addEventListener("click", async () => {
  downloadJson(buildExportData(), "caption-queue.json");
});
document.getElementById("finalize-videos").addEventListener("click", finalizeVideos);
document.querySelectorAll("[data-caption-lines],[data-caption-width]").forEach(input => {
  const update = () => {
    if (input.matches("[data-caption-lines]")) localStorage.setItem("cutted-caption-lines", input.value);
    if (input.matches("[data-caption-width]")) localStorage.setItem("cutted-caption-width", input.value);
    syncCaptionInputs();
    renderFinalStage();
  };
  input.addEventListener("input", update);
  input.addEventListener("change", update);
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
