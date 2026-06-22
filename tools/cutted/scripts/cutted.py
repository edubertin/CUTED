from __future__ import annotations

import argparse
import base64
import hashlib
import html
import http.server
import json
import math
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import SimpleNamespace

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cuted_contracts import (
    CAMERA_PRESETS,
    CAMERA_SEGMENT_LABELS,
    CAMERA_SEGMENT_PARTS,
    DIRECTOR_INTENTS,
    EFFECT_PRESETS,
    OVERLAY_PRESETS,
    PLATFORM_PRESETS,
    PLATFORM_RESOLUTION_PRESETS,
    RESOLUTION_PRESETS,
    AnimatedCaptionWindow,
    CameraAnalysisMedia,
    CameraPreset,
    CaptionEvent,
    CutedConfig,
    CuttedConfig,
    EffectPreset,
    Moment,
    OverlayPreset,
    PlatformPreset,
    PublishSourceContext,
    ResolutionPreset,
    Segment,
    SourceMedia,
)
from cuted_project_catalog import (
    clean_project_id as catalog_clean_project_id,
    directory_size as catalog_directory_size,
    empty_project_catalog as catalog_empty_project_catalog,
    iso_timestamp as catalog_iso_timestamp,
    move_project_dir_to_recycle_bin as catalog_move_project_dir_to_recycle_bin,
    project_id_for_path as catalog_project_id_for_path,
    project_source_label as catalog_project_source_label,
    project_url_for_workspace as catalog_project_url_for_workspace,
    read_gallery_moments as catalog_read_gallery_moments,
    safe_project_delete_dir as catalog_safe_project_delete_dir,
    valid_recent_project_dir as catalog_valid_recent_project_dir,
)
from cuted_launch import (
    append_launch_log as launch_append_launch_log,
    cuted_server_alive as launch_cuted_server_alive,
    default_workspace_dir as launch_default_workspace_dir,
    find_free_port as launch_find_free_port,
    launch_data_dir as launch_launch_data_dir,
    launch_lock_path as launch_launch_lock_path,
    open_browser_later as launch_open_browser_later,
    prepare_workspace_dir as launch_prepare_workspace_dir,
    running_workspace_port as launch_running_workspace_port,
    workspace_index_is_empty_shell as launch_workspace_index_is_empty_shell,
)
from cuted_media_source import (
    bundled_node_path as media_bundled_node_path,
    caption_event_to_segment as media_caption_event_to_segment,
    cleanup_sources as media_cleanup_sources,
    download_youtube_audio as media_download_youtube_audio,
    download_youtube_render_source as media_download_youtube_render_source,
    find_ffmpeg as media_find_ffmpeg,
    find_ffprobe as media_find_ffprobe,
    friendly_ytdlp_error as media_friendly_ytdlp_error,
    probe_duration as media_probe_duration,
    probe_media_metadata as media_probe_media_metadata,
    require_file as media_require_file,
    resolved_youtube_render_file as media_resolved_youtube_render_file,
    run_ytdlp as media_run_ytdlp,
    source_media_metadata as media_source_media_metadata,
    try_youtube_transcript as media_try_youtube_transcript,
    write_source_metadata as media_write_source_metadata,
    write_youtube_transcript as media_write_youtube_transcript,
    youtube_caption_lang as media_youtube_caption_lang,
    youtube_high_quality_format as media_youtube_high_quality_format,
    youtube_render_url as media_youtube_render_url,
    youtube_title as media_youtube_title,
    yt_dlp_command as media_yt_dlp_command,
    yt_dlp_extra_args as media_yt_dlp_extra_args,
    yt_dlp_runtime_args as media_yt_dlp_runtime_args,
)
from cuted_render_queue import (
    clean_render_resource_profile as queue_clean_render_resource_profile,
    read_render_queue_manifest as queue_read_render_queue_manifest,
    render_job_fingerprint as queue_render_job_fingerprint,
    render_job_output_dir as queue_render_job_output_dir,
    render_job_summary as queue_render_job_summary,
    render_profile_label as queue_render_profile_label,
    render_queue_cleanup_temp_manifest as queue_render_queue_cleanup_temp_manifest,
    render_queue_manifest_path as queue_render_queue_manifest_path,
    render_queue_temp_manifest_path as queue_render_queue_temp_manifest_path,
    render_queue_write_error_is_retryable as queue_render_queue_write_error_is_retryable,
    write_render_queue_manifest as queue_write_render_queue_manifest,
)


BRAND_LOGO_FILE = "cuted-logo-transparent.png"
LIVE_TIMELINE_ASSET_FILES = ("live-timeline.css", "live-timeline.js")
CONTROL_BAR_ASSET_FILES = ("control-bar.css", "control-bar.js")
PROJECT_CATALOG_VERSION = 1
PROJECT_CATALOG_LIMIT = 12
PROJECT_CATALOG_SIZE_FILE_LIMIT = 3000
PROJECTS_DIR_NAME = "projects"
PROJECT_RENDERS_DIR_NAME = "renders"
CUTTED_SERVER_SCRIPT_PATH = Path(__file__).resolve()
try:
    CUTTED_SERVER_SCRIPT_MTIME_NS = CUTTED_SERVER_SCRIPT_PATH.stat().st_mtime_ns
except OSError:
    CUTTED_SERVER_SCRIPT_MTIME_NS = 0
GROUP_FIT_LOGO_TOP_RATIO = 0.11
GROUP_FIT_LOGO_WIDTH_RATIO = 0.38
GROUP_FIT_LOGO_OPACITY = 0.9
GROUP_FIT_MIN_HOLD_SECONDS = 3.0
AI_DIRECTOR_MIN_MOVE_HOLD_SECONDS = 4.0
RANGE_MEDIA_EXTENSIONS = {".m4v", ".mov", ".mp4", ".webm"}
BUMPER_VIDEO_MIME_EXTENSIONS = {
    "video/mp4": "mp4",
    "video/quicktime": "mov",
    "video/webm": "webm",
    "video/x-m4v": "m4v",
}
BUMPER_MAX_SOURCE_BYTES = 48_000_000
BUMPER_SLOTS = {"intro", "outro"}
YOUTUBE_HIGH_QUALITY_FORMAT = (
    "bv*[height<=1440][vcodec^=avc1]+ba[ext=m4a]/"
    "bv*[height<=1440]+ba/"
    "b[height<=1440]/"
    "bv*[height<=1080][vcodec^=avc1]+ba[ext=m4a]/"
    "b[height<=1080]/best"
)
YOUTUBE_STREAM_FALLBACK_FORMAT = "b[height<=1080]/b[height<=720]/18/b[height<=480]/best"
IMPORT_PROGRESS_PREFIX = "CUTED_IMPORT_EVENT "
PREVIEW_VIDEO_CRF = "20"
PREVIEW_DRAFT_VIDEO_CRF = "28"
LOCAL_IMPORT_MAX_INITIAL_CLIPS = 4
FINAL_VIDEO_CRF = "20"
FINAL_EFFECT_VIDEO_CRF = "19"
MANUAL_ALTERNATE_HOLD_SECONDS = 3.5
MANUAL_ALTERNATE_MOVE_SECONDS = 1.2
CAMERA_ANALYSIS_VERSION = "auto-face-v31"
CAMERA_ANALYSIS_SAMPLE_SECONDS = 0.3
CAMERA_ANALYSIS_MAX_FRAMES = 140
CAMERA_FAST_SAMPLE_SECONDS = 1.5
CAMERA_FAST_MAX_FRAMES = 48
VISUAL_MAP_VERSION = "visual-map-v2"
VISUAL_MAP_SAMPLE_SECONDS = 2.0
VISUAL_MAP_MAX_FRAMES = 120
YOLO_PERSON_CONFIDENCE = 0.34
YOLO_DEFAULT_MODEL = "yolo26n.pt"
CAMERA_UNCERTAIN_MIN_SECONDS = 0.85
CAMERA_TWO_CLOSE_PAN_SPREAD = 10.0
CAMERA_TWO_CLOSE_PAN_SPAN = 20.0
CAMERA_SCENE_FIRST_CUT_SECONDS = 1.4
CAMERA_HARD_CUT_MIN_HOLD_SECONDS = 4.2
CAMERA_GROUP_ALTERNATE_MIN_HOLD_SECONDS = 4.0
CAMERA_MIN_TARGET_SHIFT = 10.0
CAMERA_GROUP_FIT_SPREAD = 38.0
CAMERA_GROUP_FIT_SPAN = 52.0
CAMERA_SOLO_MAX_MULTI_FACE_RATIO = 0.08
CAMERA_SOLO_MAX_EDGE_FACE_RATIO = 0.35
CAMERA_SOLO_MIN_HOLD_SECONDS = 5.5
CAMERA_DISTANT_FACE_PAN_X_DELTA = 12.0
CAMERA_LOW_CONFIDENCE_DETECTION_RATE = 0.18
CAMERA_LOW_CONFIDENCE_EDGE_RATIO = 0.55
CAMERA_LOW_CONFIDENCE_FIT_INTERVAL = 6.0
CAMERA_FIT_BREAKAWAY_MIN_SECONDS = 14.0
CAMERA_FIT_BREAKAWAY_LEAD_SECONDS = 4.6
CAMERA_FIT_BREAKAWAY_PRIMARY_HOLD_SECONDS = 4.4
CAMERA_FIT_BREAKAWAY_SECONDARY_HOLD_SECONDS = 3.8
CAMERA_FIT_BREAKAWAY_INTERVAL_SECONDS = 8.2
CAMERA_FIT_BREAKAWAY_MAX_PER_BLOCK = 3
CAMERA_GROUP_BREAKAWAY_MIN_SECONDS = 10.0
CAMERA_GROUP_BREAKAWAY_LEAD_SECONDS = 3.8
CAMERA_GROUP_SPEAKER_HOLD_SECONDS = 4.8
CAMERA_GROUP_REACTION_HOLD_SECONDS = 3.8
CAMERA_GROUP_BREAKAWAY_INTERVAL_SECONDS = 8.2
CAMERA_GROUP_BREAKAWAY_MAX_PER_BLOCK = 3
AI_DYNAMIC_SPEAKER_MAX_ZOOM = 1.08
AI_DYNAMIC_REACTION_MAX_ZOOM = 1.14
AI_DYNAMIC_FOCUS_X_MIN = 20.0
AI_DYNAMIC_FOCUS_X_MAX = 80.0
AI_DIRECTOR_MAX_FRAME_SAMPLES = 10
AI_DIRECTOR_MAX_CONTEXT_ROWS = 36
AI_DIRECTOR_MAX_FALLBACK_FRAMES = 28
AI_DIRECTOR_OPENAI_TIMEOUT_SECONDS = 45
CAMERA_ANALYSIS_FETCH_TIMEOUT_MS = 180000
AI_DIRECTOR_MAX_SPEAKER_RATIO = 0.72
AI_DIRECTOR_MIN_VARIATION_FRAMES = 2
AI_DIRECTOR_MAX_STILL_SECONDS = 10.0
AI_DIRECTOR_SIDE_X_DELTA = 8.0
AI_DIRECTOR_MAX_GROUP_DURATION_RATIO = 0.60
AI_DIRECTOR_MIN_ACTIVE_DURATION_RATIO = 0.36
AI_DIRECTOR_GROUP_BALANCE_MIN_SECONDS = 4.6
AI_DIRECTOR_GROUP_BALANCE_MAX_FRAMES = 10
AI_DIRECTOR_SOFT_GROUP_RETURN_SUPPRESSION_SECONDS = 4.8
CAMERA_SAFE_X_MIN = 30.0
CAMERA_SAFE_X_MAX = 70.0
SMART_CAMERA_MODES = {
    "auto-director": "Auto Director",
    "ai-director": "IA",
    "ai-director-group": "AI Grupo",
    "ai-director-speaker": "AI Fala",
    "ai-director-reactions": "AI Reacoes",
    "ai-director-cuts": "AI Cortes",
    "follow-face": "Seguir rosto",
    "stable-face": "Enquadramento estavel",
    "face-zoom": "Zoom no rosto",
    "alternate-faces": "Alternar rostos",
    "cut-between-faces": "Corte entre rostos",
}
AI_DIRECTOR_INTENTS = {
    "ai-director": {
        "label": "Dinamico",
        "priority": "Misture plano aberto, foco medio em quem fala, reacoes de 3 a 4 segundos e retornos seguros sem cortar pessoas visiveis.",
    },
    "ai-director-group": {
        "label": "Grupo / podcast",
        "priority": "Use grupo como base de seguranca, mas quebre holds longos com reacoes confiaveis e volte para grupo ou speaker.",
    },
    "ai-director-speaker": {
        "label": "Quem fala",
        "priority": "Priorize a pessoa principal em plano medio, preservando mais corpo e contexto; reserve close de rosto para reacao clara.",
    },
    "ai-director-reactions": {
        "label": "Reacoes",
        "priority": "Alterne foco entre pessoas visiveis com pausas editoriais e use planos abertos para manter contexto.",
    },
    "ai-director-cuts": {
        "label": "Cortes",
        "priority": "Use cortes secos entre enquadramentos, sem pan suave. Segure cada foco por 2.5 a 4.5 segundos.",
    },
}


TERMINAL_ENDINGS = (".", "!", "?", "…")
WEAK_ENDINGS = (
    "porque", "por que", "entao", "então", "mas", "aí", "ai", "só que", "so que",
    "ou seja", "tipo", "enfim", "daí", "dai", "logo", "portanto",
)
WEAK_STARTINGS = (
    "e ", "mas ", "aí ", "ai ", "então ", "entao ", "porque ", "por que ", "só que ", "so que ",
)


OPENAI_TRANSCRIBE_LIMIT_BYTES = 22 * 1024 * 1024
OPENAI_TRANSCRIBE_CHUNK_SECONDS = 600
AI_CONTEXT_AUDIO_MAX_BYTES = 12 * 1024 * 1024
AI_CONTEXT_AUDIO_MAX_SECONDS = 120
AI_CONTEXT_MIN_AUDIO_SECONDS = 0.8
OPENAI_PRICING_SOURCE = "https://developers.openai.com/api/docs/pricing"
OPENAI_PRICING_UPDATED = "2026-06-20"
OPENAI_TEXT_PRICES_USD_PER_1M = {
    "gpt-5": {"input": 1.25, "cached_input": 0.125, "output": 10.0},
    "gpt-5-mini": {"input": 0.25, "cached_input": 0.025, "output": 2.0},
    "gpt-5-nano": {"input": 0.05, "cached_input": 0.005, "output": 0.40},
}
OPENAI_TRANSCRIBE_PRICES_USD_PER_MINUTE = {
    "whisper-1": 0.006,
    "gpt-4o-transcribe": 0.006,
    "gpt-4o-mini-transcribe": 0.003,
}
PUBLISH_INTELLIGENCE_VERSION = "publish-intelligence-v1"
PUBLISH_INTELLIGENCE_TIMEOUT_SECONDS = 35
PUBLISH_CLIP_TEXT_LIMIT = 900
PUBLISH_SOURCE_TEXT_LIMIT = 1800
PUBLISH_MAX_HASHTAGS = 6
PUBLISH_DEFAULT_HASHTAGS = ["#Podcast", "#Cortes"]
CUTTED_CAPTION_BOTTOM_OFFSET_MULTIPLIER = 1.25
ANIMATED_CAPTION_LEAD_SECONDS = 0.14
ANIMATED_CAPTION_MIN_RENDER_SECONDS = 0.22
ANIMATED_CAPTION_TARGET_MIN_WORD_SECONDS = 0.24
ANIMATED_CAPTION_FAST_WORD_SECONDS = 0.20
ANIMATED_CAPTION_MAX_GROUP_WORDS = 3
ANIMATED_CAPTION_BOX_OPACITY = 0.80
ANIMATED_CAPTION_BOX_SHADOW_OPACITY = 0.28
COVER_LAYER_VERTICAL_LIFT = 0.30
COVER_PREVIEW_CANONICAL_WIDTH = 252.0
COVER_LAYER_PREVIEW_FONT_SCALE = 0.42
COVER_SPEECH_RADIUS_PREVIEW_PX = 11.0
COVER_SPEECH_TAIL_WIDTH_PREVIEW_PX = 15.0
COVER_SPEECH_TAIL_HEIGHT_PREVIEW_PX = 12.0
COVER_SPEECH_TAIL_BOTTOM_PREVIEW_PX = -8.0
COVER_FRAME_TAIL_SECONDS = 0.5
RENDER_JOB_FINGERPRINT_VERSION = "cuted-render-queue-v10-canonical-animated-captions"
RENDER_QUEUE_WRITE_ATTEMPTS = 6
RENDER_QUEUE_WRITE_RETRY_SECONDS = 0.08
STALE_RENDER_SERVER_ERROR = (
    "Servidor CUTED antigo. Reinicie o app antes de renderizar para usar as ultimas mudancas."
)
MAX_SELECTION_OVERLAP = 0.35
MAX_SELECTION_TEXT_SIMILARITY = 0.72
SELECTION_CLUSTER_SECONDS = 120.0
COMMON_TOKENS = {
    "que", "para", "com", "uma", "por", "tem", "mas", "vai", "voce", "vocÃª",
    "isso", "essa", "esse", "aqui", "porque", "entao", "entÃ£o", "como",
}
DURATION_PROFILES = {
    "short": (20.0, 30.0, 45.0),
    "medium": (30.0, 45.0, 70.0),
    "long": (60.0, 90.0, 120.0),
}


@dataclass
class ImportJob:
    id: str
    status: str
    created_at: float
    updated_at: float
    output_dir: Path
    base_dir: Path
    output_url: str
    process: subprocess.Popen[str] | None
    message: str = ""
    source_kind: str = "local"
    ai_provider: str = "local"
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    progress: dict[str, object] = field(default_factory=dict)
    events: list[dict[str, object]] = field(default_factory=list)


@dataclass
class RenderJob:
    id: str
    fingerprint: str
    status: str
    created_at: float
    updated_at: float
    gallery_dir: Path
    base_dir: Path
    output_dir: Path
    resource_profile: str
    payload: dict[str, object]
    message: str = ""
    progress: int = 0
    speed: str = ""
    eta_seconds: float | None = None
    processed_seconds: float = 0.0
    files: list[dict[str, object]] | None = None
    export_dir: str = ""
    error: str = ""


IMPORT_JOBS: dict[str, ImportJob] = {}
IMPORT_JOBS_LOCK = threading.Lock()
RENDER_JOBS: dict[str, RenderJob] = {}
RENDER_JOBS_LOCK = threading.Lock()
VISUAL_MAP_TASKS: set[str] = set()
VISUAL_MAP_TASKS_LOCK = threading.Lock()
YOLO_MODEL_CACHE: dict[str, object | None] = {}
YOLO_MODEL_ERRORS: dict[str, str] = {}


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
    analyze.add_argument("--ai-provider", choices=("auto", "local", "openai"), default=None)
    analyze.add_argument("--context-prompt", default="")
    analyze.add_argument("--skip-render", action="store_true")
    analyze.add_argument("--cleanup-source", action="store_true")
    visual_map = subparsers.add_parser("visual-map", help="Build a visual map for a local source video.")
    visual_map.add_argument("video", type=Path)
    visual_map.add_argument("--out", type=Path, required=True)
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
    caption.add_argument("--cover-frame", action=argparse.BooleanOptionalAction, default=False)
    serve = subparsers.add_parser("serve", help="Serve a generated gallery with local finalize API.")
    serve.add_argument("--dir", type=Path, required=True)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8777)
    launch = subparsers.add_parser("launch", help="Open the CUTED workspace for local beta use.")
    launch.add_argument("--workspace", type=Path, default=None)
    launch.add_argument("--host", default="127.0.0.1")
    launch.add_argument("--no-browser", action="store_true")
    return parser.parse_args()


def main() -> int:
    load_local_env()
    args = parse_args()
    if args.command == "analyze":
        analyze(args)
        return 0
    if args.command == "visual-map":
        visual_map_command(args)
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
    if args.command == "launch":
        launch_workspace(args)
        return 0
    raise RuntimeError(f"Unsupported command: {args.command}")


def analyze(args: argparse.Namespace) -> None:
    emit_import_progress("prepare", "Preparing", "Creating project folder...", 8)
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    config = build_config(args)
    emit_import_progress("prepare", "Preparing", "Checking local tools...", 12)
    ffmpeg = find_ffmpeg()
    ffprobe = find_ffprobe()
    media_message = "Downloading and preparing YouTube video..." if args.youtube_url else "Reading local video..."
    emit_import_progress("media", "Media", media_message, 18)
    source = prepare_source(args, out_dir, ffmpeg, ffprobe)
    write_source_metadata(out_dir, source.metadata)
    emit_import_progress("media", "Media", "Media ready for analysis.", 30, detail=source.label)
    duration = probe_duration(source.render_source, ffprobe)
    provider = requested_ai_provider(args)
    audio_detail = "OpenAI" if provider == "openai" else "local transcription"
    emit_import_progress("audio", "Audio", "Transcribing audio...", 36, detail=audio_detail)
    segments = load_segments(args, source.transcribe_source)
    emit_import_progress("analysis", "Analysis", "Analyzing transcript...", 58, detail=f"{len(segments)} segments")
    moments = pick_moments_for_import(args, segments, config, duration)
    emit_import_progress("suggestions", "Suggestions", "Generating clip suggestions...", 66, detail=f"{len(moments)} clips")
    emit_import_progress("previews", "Previews", "Rendering previews...", 72, step=0, steps=len(moments))
    rendered = render_outputs(source.render_source, out_dir, moments, ffmpeg, args.skip_render, emit_preview_import_progress)
    emit_import_progress("publish", "Post AI", "Analyzing SEO and trends...", 93, detail="SEO and hashtags")
    rendered = apply_publish_intelligence(rendered, source.label, config, args, source.metadata)
    emit_import_progress("editor", "Editor", "Building editing workspace...", 94)
    write_json(out_dir / "moments.json", rendered, source.label, duration, config)
    write_html(out_dir / "index.html", rendered, source.label)
    start_visual_map_background(out_dir, source)
    if args.cleanup_source:
        cleanup_sources(source.cleanup_paths)
    emit_import_progress("ready", "Ready", "Project imported. Opening editor...", 100)
    print(f"[cutted] Generated {len(rendered)} moments in {out_dir}")
    print(f"[cutted] Open: {out_dir / 'index.html'}")


def emit_preview_import_progress(step: int, steps: int) -> None:
    total = max(steps, 1)
    percent = min(92, int(72 + (step / total) * 18))
    emit_import_progress(
        "previews",
        "Previews",
        "Renderizando previews...",
        percent,
        step=step,
        steps=steps,
        detail=f"{step} de {steps} previews",
    )


def emit_import_progress(
    stage: str, label: str, message: str, percent: int,
    step: int | None = None, steps: int | None = None, detail: str = "",
) -> None:
    payload: dict[str, object] = {
        "stage": stage,
        "label": label,
        "message": message,
        "percent": max(0, min(100, int(percent))),
    }
    if step is not None:
        payload["step"] = max(0, int(step))
    if steps is not None:
        payload["steps"] = max(0, int(steps))
    if detail:
        payload["detail"] = detail
    print(f"{IMPORT_PROGRESS_PREFIX}{json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}", flush=True)


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


LAUNCH_PORT_RANGE = range(8779, 8800)


def launch_workspace(args: argparse.Namespace) -> None:
    workspace = prepare_workspace_dir(args.workspace)
    existing = running_workspace_port(args.host)
    if existing is not None:
        print(f"[cutted] CUTED ja esta aberto em http://{args.host}:{existing}/index.html (workspace da instancia atual mantido)")
        if not args.no_browser:
            open_browser_later(args.host, existing, 0.0)
        return
    bootstrap_workspace_gallery(workspace)
    for _ in range(3):
        port = find_free_port(args.host)
        try:
            start_workspace_server(workspace, args.host, port, args.no_browser)
            return
        except OSError as error:
            append_launch_log(f"bind failed on port {port}: {error}")
    print("[cutted] Nao consegui abrir o servidor local. Feche outras janelas do CUTED e tente novamente.")
    raise SystemExit(1)


def start_workspace_server(workspace: Path, host: str, port: int, no_browser: bool) -> None:
    handler = gallery_handler(workspace)
    server = http.server.ThreadingHTTPServer((host, port), handler)
    lock_path = launch_lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(str(port), encoding="utf-8")
    append_launch_log(f"launch workspace={workspace} port={port}")
    print(f"[cutted] Serving {workspace}")
    print(f"[cutted] Open: http://{host}:{port}/index.html")
    if not no_browser:
        open_browser_later(host, port, 0.5)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[cutted] Server stopped")
    finally:
        server.server_close()
        try:
            lock_path.unlink()
        except OSError as error:
            append_launch_log(f"lock cleanup failed: {error}")


def prepare_workspace_dir(value: Path | None) -> Path:
    return launch_prepare_workspace_dir(value, default_workspace_dir())


def default_workspace_dir() -> Path:
    return launch_default_workspace_dir()


def launch_data_dir() -> Path:
    return launch_launch_data_dir()


def launch_lock_path() -> Path:
    return launch_launch_lock_path(launch_data_dir())


def append_launch_log(message: str) -> None:
    launch_append_launch_log(launch_data_dir(), message)


def running_workspace_port(host: str) -> int | None:
    return launch_running_workspace_port(launch_lock_path(), host, cuted_server_alive, append_launch_log)


def cuted_server_alive(host: str, port: int) -> bool:
    return launch_cuted_server_alive(host, port)


def find_free_port(host: str) -> int:
    return launch_find_free_port(host, LAUNCH_PORT_RANGE)


def open_browser_later(host: str, port: int, delay: float) -> None:
    launch_open_browser_later(host, port, delay)


def bootstrap_workspace_gallery(workspace: Path) -> None:
    index_path = workspace / "index.html"
    if index_path.exists() and not workspace_index_is_empty_shell(index_path):
        return
    write_project_home(index_path, workspace)


def workspace_index_is_empty_shell(index_path: Path) -> bool:
    return launch_workspace_index_is_empty_shell(index_path)


def project_catalog_path() -> Path:
    return launch_data_dir() / "projects.json"


def empty_project_catalog() -> dict[str, object]:
    return catalog_empty_project_catalog(PROJECT_CATALOG_VERSION)


def read_project_catalog(path: Path | None = None) -> dict[str, object]:
    catalog_path = path or project_catalog_path()
    if not catalog_path.exists():
        return empty_project_catalog()
    try:
        data = json.loads(catalog_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return empty_project_catalog()
    if not isinstance(data, dict):
        return empty_project_catalog()
    projects = data.get("projects")
    if not isinstance(projects, list):
        projects = []
    return {"version": PROJECT_CATALOG_VERSION, "projects": [item for item in projects if isinstance(item, dict)]}


def write_project_catalog(catalog: dict[str, object], path: Path | None = None) -> None:
    catalog_path = path or project_catalog_path()
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    rows = catalog.get("projects") if isinstance(catalog, dict) else []
    projects = rows if isinstance(rows, list) else []
    payload = {"version": PROJECT_CATALOG_VERSION, "projects": projects[:200]}
    temp_path = catalog_path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(catalog_path)


def project_catalog_recent(workspace: Path, limit: int = PROJECT_CATALOG_LIMIT) -> list[dict[str, object]]:
    catalog = read_project_catalog()
    projects = catalog.get("projects")
    source_rows = projects if isinstance(projects, list) else []
    rows = []
    kept_projects = []
    for row in source_rows:
        if not isinstance(row, dict):
            continue
        entry = project_home_entry(row, workspace)
        if not entry:
            continue
        rows.append(entry)
        kept_projects.append(row)
    if kept_projects != source_rows:
        catalog["projects"] = kept_projects
        write_project_catalog(catalog)
    rows.sort(key=lambda row: str(row.get("last_opened_at") or row.get("updated_at") or ""), reverse=True)
    return rows[:limit]


def project_home_entry(row: dict[str, object], workspace: Path) -> dict[str, object]:
    project_id = clean_project_id(row.get("id"))
    raw_path = str(row.get("path") or "").strip()
    if not project_id or not raw_path:
        return {}
    project_path = Path(raw_path).expanduser()
    if not valid_recent_project_dir(project_path, workspace):
        return {}
    url = project_url_for_workspace(project_path, workspace)
    if not url:
        return {}
    return {
        "id": project_id,
        "title": clean_optional_text(row.get("title"), 100) or project_path.name,
        "path": str(project_path),
        "url": url,
        "clip_count": clamp_int(row.get("clip_count"), 0, 9999, 0),
        "render_count": clamp_int(row.get("render_count"), 0, 9999, 0),
        "size_bytes": clamp_int(row.get("size_bytes"), 0, 10_000_000_000, 0),
        "last_opened_at": clean_optional_text(row.get("last_opened_at"), 40),
        "source_label": clean_optional_text(row.get("source_label"), 140),
    }


def clean_project_id(value: object) -> str:
    return catalog_clean_project_id(value)


def upsert_project_catalog_entry(entry: dict[str, object], path: Path | None = None) -> None:
    project_id = clean_project_id(entry.get("id"))
    project_path = str(entry.get("path") or "")
    if not project_id or not project_path:
        return
    catalog = read_project_catalog(path)
    existing = catalog.get("projects")
    projects = existing if isinstance(existing, list) else []
    filtered = [
        row for row in projects
        if isinstance(row, dict) and clean_project_id(row.get("id")) != project_id and str(row.get("path") or "") != project_path
    ]
    filtered.insert(0, {**entry, "id": project_id, "path": project_path})
    catalog["projects"] = filtered
    write_project_catalog(catalog, path)


def delete_project_from_catalog(project_id: str, workspace: Path, delete_files: bool) -> dict[str, object]:
    catalog = read_project_catalog()
    projects = catalog.get("projects")
    rows = projects if isinstance(projects, list) else []
    target = next((row for row in rows if isinstance(row, dict) and clean_project_id(row.get("id")) == project_id), None)
    if target is None:
        raise ValueError("Projeto nao encontrado.")
    deleted = False
    delete_method = ""
    if delete_files:
        project_dir = safe_project_delete_dir(Path(str(target.get("path") or "")), workspace)
        delete_method = delete_project_dir(project_dir)
        deleted = True
    catalog["projects"] = [row for row in rows if not (isinstance(row, dict) and clean_project_id(row.get("id")) == project_id)]
    write_project_catalog(catalog)
    return {"ok": True, "deleted_files": deleted, "delete_method": delete_method, "projects": project_catalog_recent(workspace)}


def delete_project_dir(project_dir: Path) -> str:
    if move_project_dir_to_recycle_bin(project_dir):
        return "recycle-bin"
    shutil.rmtree(project_dir)
    return "permanent-delete"


def move_project_dir_to_recycle_bin(project_dir: Path) -> bool:
    return catalog_move_project_dir_to_recycle_bin(project_dir)


def touch_project_catalog_entry(gallery_dir: Path, workspace: Path) -> dict[str, object]:
    if not valid_recent_project_dir(gallery_dir, workspace):
        raise ValueError("Projeto invalido para recentes.")
    entry = project_entry_from_gallery(gallery_dir, workspace)
    upsert_project_catalog_entry(entry)
    return {
        "ok": True,
        "project": project_home_entry(entry, workspace),
        "projects": project_catalog_recent(workspace),
    }


def valid_recent_project_dir(project_dir: Path, workspace: Path) -> bool:
    return catalog_valid_recent_project_dir(project_dir, workspace)


def safe_project_delete_dir(project_dir: Path, workspace: Path) -> Path:
    return catalog_safe_project_delete_dir(project_dir, workspace)


def project_entry_from_gallery(gallery_dir: Path, workspace: Path) -> dict[str, object]:
    metadata = read_import_metadata(gallery_dir)
    source_label = project_source_label(metadata, gallery_dir)
    return {
        "id": project_id_for_path(gallery_dir),
        "title": source_label,
        "path": str(gallery_dir.resolve()),
        "source_label": source_label,
        "clip_count": len(read_gallery_moments(gallery_dir)),
        "render_count": len(recovered_captioned_files(gallery_dir)),
        "size_bytes": directory_size(gallery_dir),
        "updated_at": iso_timestamp(),
        "last_opened_at": iso_timestamp(),
        "workspace": str(workspace.resolve()),
    }


def project_source_label(metadata: dict[str, object], gallery_dir: Path) -> str:
    return catalog_project_source_label(metadata, gallery_dir)


def read_gallery_moments(gallery_dir: Path) -> list[object]:
    return catalog_read_gallery_moments(gallery_dir)


def project_id_for_path(path: Path) -> str:
    return catalog_project_id_for_path(path, safe_slug(path.name))


def project_url_for_workspace(project_path: Path, workspace: Path) -> str:
    return catalog_project_url_for_workspace(project_path, workspace)


def directory_size(path: Path) -> int:
    return catalog_directory_size(path, PROJECT_CATALOG_SIZE_FILE_LIMIT)


def iso_timestamp() -> str:
    return catalog_iso_timestamp()


def gallery_handler(base_dir: Path) -> type[http.server.SimpleHTTPRequestHandler]:
    class CuttedGalleryHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, directory=str(base_dir), **kwargs)

        def do_POST(self) -> None:
            path = urllib.parse.urlparse(self.path).path
            if path == "/api/finalize":
                self.handle_finalize(base_dir)
                return
            if path == "/api/import-jobs":
                self.handle_import_job(base_dir)
                return
            if path == "/api/ai-context/audio":
                self.handle_ai_context_audio()
                return
            if path == "/api/render-jobs":
                self.handle_render_job(base_dir)
                return
            if path == "/api/camera/analyze":
                self.handle_camera_analyze(base_dir)
                return
            if path == "/api/bumper-assets":
                self.handle_bumper_asset(base_dir)
                return
            if path == "/api/select-folder":
                self.handle_select_folder()
                return
            if path == "/api/select-video-file":
                self.handle_select_video_file()
                return
            if path == "/api/open-folder":
                self.handle_open_folder()
                return
            if path == "/api/projects/touch":
                self.handle_project_touch(base_dir)
                return
            if re.fullmatch(r"/api/projects/[^/]+/delete", path):
                self.handle_project_delete(base_dir, path)
                return
            if path == "/api/settings/openai":
                self.handle_openai_settings_save()
                return
            if path == "/api/settings/openai/test":
                self.handle_openai_settings_test()
                return
            if re.fullmatch(r"/api/import-jobs/[^/]+/cancel", path):
                self.handle_import_cancel(path)
                return
            if re.fullmatch(r"/api/render-jobs/[^/]+/cancel", path):
                self.handle_render_cancel(path)
                return
            if re.fullmatch(r"/api/render-jobs/[^/]+/profile", path):
                self.handle_render_profile(base_dir, path)
                return
            if re.fullmatch(r"/api/render-jobs/[^/]+/remove", path):
                self.handle_render_remove(base_dir, path)
                return
            if path != "/api/finalize":
                self.send_error(404, "Not found")
                return

        def do_GET(self) -> None:
            path = urllib.parse.urlparse(self.path).path
            if path == "/api/finalize-results":
                self.handle_finalize_results(base_dir)
                return
            if path == "/api/render-jobs":
                self.handle_render_jobs(base_dir)
                return
            if path == "/api/projects":
                self.handle_projects(base_dir)
                return
            if path == "/api/camera/status":
                self.handle_camera_status(base_dir)
                return
            if path == "/api/settings/openai":
                self.handle_openai_settings_get()
                return
            if path == "/api/usage/local":
                send_json_response(self, 200, local_usage_payload())
                return
            if re.fullmatch(r"/api/import-jobs/[^/]+", path):
                self.handle_import_status(path)
                return
            if re.fullmatch(r"/api/render-jobs/[^/]+", path):
                self.handle_render_status(path)
                return
            if self.handle_range_request():
                return
            super().do_GET()

        def handle_range_request(self) -> bool:
            range_header = self.headers.get("Range")
            if not range_header:
                return False
            file_path = Path(self.translate_path(self.path))
            if file_path.suffix.lower() not in RANGE_MEDIA_EXTENSIONS or not file_path.is_file():
                return False
            file_size = file_path.stat().st_size
            byte_range = parse_range_header(range_header, file_size)
            if byte_range is None:
                self.send_error(416, "Requested Range Not Satisfiable")
                return True
            self.send_media_range(file_path, file_size, byte_range)
            return True

        def send_media_range(self, file_path: Path, file_size: int, byte_range: tuple[int, int]) -> None:
            start, end = byte_range
            length = end - start + 1
            self.send_response(206)
            self.send_header("Content-type", self.guess_type(str(file_path)))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(length))
            self.end_headers()
            with file_path.open("rb") as source:
                source.seek(start)
                self.copy_range(source, length)

        def copy_range(self, source, length: int) -> None:
            remaining = length
            while remaining > 0:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

        def reject_stale_render_server(self) -> bool:
            if not server_code_changed_since_start():
                return False
            send_json_response(self, 409, stale_server_payload())
            return True

        def handle_finalize(self, request_base_dir: Path) -> None:
            if self.reject_stale_render_server():
                return
            try:
                result = finalize_from_request(self, request_base_dir)
                send_json_response(self, 200, result)
            except Exception as error:
                send_json_response(self, 500, {"ok": False, "error": str(error)})

        def handle_finalize_results(self, request_base_dir: Path) -> None:
            try:
                result = finalize_results_from_request(self, request_base_dir)
                send_json_response(self, 200, result)
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_import_job(self, request_base_dir: Path) -> None:
            try:
                result = start_import_job(self, request_base_dir)
                send_json_response(self, 200, result)
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_ai_context_audio(self) -> None:
            try:
                result = ai_context_audio_from_request(self)
                send_json_response(self, 200, result)
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_import_status(self, path: str) -> None:
            job_id = path.rsplit("/", 1)[-1]
            job = import_job_snapshot(job_id)
            if job is None:
                send_json_response(self, 404, {"ok": False, "error": "Import job not found."})
                return
            send_json_response(self, 200, {"ok": True, "job": job})

        def handle_import_cancel(self, path: str) -> None:
            job_id = path.split("/")[-2]
            result = cancel_import_job(job_id)
            send_json_response(self, 200 if result.get("ok") else 404, result)

        def handle_render_job(self, request_base_dir: Path) -> None:
            if self.reject_stale_render_server():
                return
            try:
                result = start_render_job(self, request_base_dir)
                send_json_response(self, 200, result)
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_render_jobs(self, request_base_dir: Path) -> None:
            try:
                result = render_jobs_from_request(self, request_base_dir)
                send_json_response(self, 200, result)
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_render_status(self, path: str) -> None:
            job_id = path.rsplit("/", 1)[-1]
            job = render_job_snapshot(job_id)
            if job is None:
                send_json_response(self, 404, {"ok": False, "error": "Render job not found."})
                return
            send_json_response(self, 200, {"ok": True, "job": job})

        def handle_render_cancel(self, path: str) -> None:
            job_id = path.split("/")[-2]
            result = cancel_render_job(job_id)
            send_json_response(self, 200 if result.get("ok") else 404, result)

        def handle_render_profile(self, request_base_dir: Path, path: str) -> None:
            try:
                job_id = path.split("/")[-2]
                payload = read_json_body(self)
                gallery_dir = resolve_request_gallery_dir(request_base_dir, payload)
                result = update_render_job_profile(job_id, gallery_dir, payload.get("resource_profile"))
                send_json_response(self, 200 if result.get("ok") else 404, result)
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_render_remove(self, request_base_dir: Path, path: str) -> None:
            try:
                job_id = path.split("/")[-2]
                payload = read_json_body(self)
                gallery_dir = resolve_request_gallery_dir(request_base_dir, payload)
                result = remove_render_job(job_id, gallery_dir)
                send_json_response(self, 200 if result.get("ok") else 404, result)
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_projects(self, request_base_dir: Path) -> None:
            send_json_response(self, 200, {"ok": True, "projects": project_catalog_recent(request_base_dir)})

        def handle_project_touch(self, request_base_dir: Path) -> None:
            try:
                payload = read_json_body(self)
                gallery_dir = resolve_request_gallery_dir(request_base_dir, payload)
                result = touch_project_catalog_entry(gallery_dir, request_base_dir)
                send_json_response(self, 200, result)
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_project_delete(self, request_base_dir: Path, path: str) -> None:
            try:
                project_id = urllib.parse.unquote(path.split("/")[-2])
                payload = read_json_body(self)
                result = delete_project_from_catalog(project_id, request_base_dir, bool(payload.get("delete_files")))
                send_json_response(self, 200, result)
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_camera_analyze(self, request_base_dir: Path) -> None:
            try:
                result = analyze_camera_from_request(self, request_base_dir)
                send_json_response(self, 200 if result.get("ok") else 422, result)
            except Exception as error:
                send_json_response(self, 500, {"ok": False, "error": str(error)})

        def handle_camera_status(self, request_base_dir: Path) -> None:
            try:
                result = camera_status_from_request(self, request_base_dir)
                send_json_response(self, 200, result)
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_bumper_asset(self, request_base_dir: Path) -> None:
            try:
                result = save_bumper_asset_from_request(self, request_base_dir)
                send_json_response(self, 200, result)
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_select_folder(self) -> None:
            try:
                path = select_folder_path()
                send_json_response(self, 200, {"ok": True, "path": path})
            except Exception as error:
                send_json_response(self, 500, {"ok": False, "error": str(error)})

        def handle_select_video_file(self) -> None:
            try:
                path = select_video_file_path()
                send_json_response(self, 200, {"ok": True, "path": path})
            except Exception as error:
                send_json_response(self, 500, {"ok": False, "error": str(error)})

        def handle_open_folder(self) -> None:
            try:
                payload = read_json_body(self)
                path = open_local_folder(payload.get("path"))
                send_json_response(self, 200, {"ok": True, "path": str(path)})
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_openai_settings_get(self) -> None:
            send_json_response(self, 200, {"ok": True, "settings": openai_settings_payload(), "usage": usage_summary_payload()})

        def handle_openai_settings_save(self) -> None:
            try:
                payload = read_json_body(self)
                save_openai_settings(payload)
                send_json_response(self, 200, {"ok": True, "settings": openai_settings_payload(), "usage": usage_summary_payload()})
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

        def handle_openai_settings_test(self) -> None:
            try:
                payload = read_json_body(self)
                key = clean_optional_text(payload.get("api_key"), 2048) or openai_api_key()
                test_openai_connection(key)
                send_json_response(self, 200, {"ok": True, "message": "OpenAI connection validated."})
            except Exception as error:
                send_json_response(self, 400, {"ok": False, "error": str(error)})

    return CuttedGalleryHandler


def parse_range_header(header: str, file_size: int) -> tuple[int, int] | None:
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", header.strip())
    if not match or file_size <= 0:
        return None
    start_text, end_text = match.groups()
    if not start_text and not end_text:
        return None
    if not start_text:
        suffix_length = int(end_text)
        start = max(file_size - suffix_length, 0)
        end = file_size - 1
    else:
        start = int(start_text)
        end = int(end_text) if end_text else file_size - 1
    if start >= file_size or end < start:
        return None
    return start, min(end, file_size - 1)


def finalize_from_request(handler: http.server.BaseHTTPRequestHandler, base_dir: Path) -> dict[str, object]:
    payload = read_json_body(handler)
    return finalize_payload(payload, base_dir)


def finalize_payload(
    payload: dict[str, object], base_dir: Path, out_dir: Path | None = None,
    resource_profile: str = "medium", render_job_id: str = "",
) -> dict[str, object]:
    queue = payload.get("queue") if isinstance(payload, dict) else None
    if not isinstance(queue, dict):
        raise ValueError("Missing queue data.")
    gallery_dir = resolve_request_gallery_dir(base_dir, payload)
    caption_path = gallery_dir / "caption-queue.json"
    target_dir = out_dir or gallery_dir / "captioned-clips"
    target_dir.mkdir(parents=True, exist_ok=True)
    materialize_queue_image_assets(queue, gallery_dir / "overlay-assets")
    materialize_queue_bumper_assets(queue, gallery_dir / "bumper-assets")
    caption_path.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = caption_rows_from_data(queue)
    apply_render_resource_to_rows(rows, resource_profile)
    apply_render_job_id_to_rows(rows, render_job_id)
    options = SimpleNamespace(
        chars_per_line=int(payload.get("chars_per_line") or 28),
        max_lines=int(payload.get("max_lines") or 2),
        captions_enabled=bool(payload.get("captions_enabled", True)),
        cover_frame_enabled=bool(payload.get("cover_frame_enabled", False)),
    )
    captioned = caption_selected_rows(rows, gallery_dir, target_dir, find_ffmpeg(), options)
    captioned, export_dir = export_captioned_rows(captioned, gallery_dir)
    manifest = {"source_caption_queue": str(caption_path), "captioned": captioned}
    if export_dir:
        manifest["export_dir"] = str(export_dir)
    (target_dir / "captioned-clips.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "count": len(captioned), "files": finalized_file_urls(captioned, gallery_dir), "export_dir": str(export_dir) if export_dir else ""}


def finalize_results_from_request(handler: http.server.BaseHTTPRequestHandler, base_dir: Path) -> dict[str, object]:
    parsed = urllib.parse.urlparse(handler.path)
    query = urllib.parse.parse_qs(parsed.query)
    gallery_dir = resolve_request_gallery_dir(base_dir, {"gallery_path": query.get("gallery_path", [""])[0]})
    return finalized_results_from_gallery(gallery_dir)


def render_jobs_from_request(handler: http.server.BaseHTTPRequestHandler, base_dir: Path) -> dict[str, object]:
    parsed = urllib.parse.urlparse(handler.path)
    query = urllib.parse.parse_qs(parsed.query)
    gallery_dir = resolve_request_gallery_dir(base_dir, {"gallery_path": query.get("gallery_path", [""])[0]})
    restore_render_jobs_from_manifest(gallery_dir, base_dir)
    return {"ok": True, "jobs": render_queue_snapshot(gallery_dir)}


def start_render_job(handler: http.server.BaseHTTPRequestHandler, base_dir: Path) -> dict[str, object]:
    payload = read_json_body(handler)
    queue = payload.get("queue") if isinstance(payload, dict) else None
    if not isinstance(queue, dict) or not isinstance(queue.get("caption_queue"), list) or not queue.get("caption_queue"):
        raise ValueError("Selecione ao menos um corte para enviar ao render.")
    gallery_dir = resolve_request_gallery_dir(base_dir, payload)
    profile = clean_render_resource_profile(payload.get("resource_profile"))
    fingerprint = render_job_fingerprint(payload, profile)
    restore_render_jobs_from_manifest(gallery_dir, base_dir)
    existing = render_job_by_fingerprint(gallery_dir, fingerprint)
    if existing is not None:
        return {"ok": True, "job": existing, "duplicate": True}
    job_id = f"render-{uuid.uuid4().hex[:10]}"
    output_dir = render_job_output_dir(gallery_dir, job_id)
    job = RenderJob(
        job_id,
        fingerprint,
        "queued",
        time.time(),
        time.time(),
        gallery_dir,
        base_dir,
        output_dir,
        profile,
        payload,
        "Na fila de render.",
        4,
        "",
        None,
        0.0,
        [],
    )
    with RENDER_JOBS_LOCK:
        RENDER_JOBS[job.id] = job
    persist_render_queue(gallery_dir)
    thread = threading.Thread(target=run_render_job, args=(job.id,), daemon=True)
    thread.start()
    return {"ok": True, "job": render_job_to_dict(job), "duplicate": False}


def run_render_job(job_id: str) -> None:
    with RENDER_JOBS_LOCK:
        job = RENDER_JOBS.get(job_id)
        if job is None:
            return
        job.status = "rendering"
        job.message = "Renderizando em background."
        job.progress = 12
        job.speed = ""
        job.eta_seconds = None
        job.processed_seconds = 0.0
        job.updated_at = time.time()
        persist_render_queue(job.gallery_dir)
    try:
        result = finalize_payload(job.payload, job.base_dir, job.output_dir, job.resource_profile, job.id)
        with RENDER_JOBS_LOCK:
            current = RENDER_JOBS.get(job_id)
            if current is None or current.status == "cancelled":
                return
            current.status = "ready"
            current.message = "Render pronto."
            current.progress = 100
            current.speed = ""
            current.eta_seconds = 0.0
            current.updated_at = time.time()
            current.files = list(result.get("files") or [])
            current.export_dir = str(result.get("export_dir") or "")
            persist_render_queue(current.gallery_dir)
            upsert_project_catalog_entry(project_entry_from_gallery(current.gallery_dir, current.base_dir))
    except Exception as error:
        with RENDER_JOBS_LOCK:
            current = RENDER_JOBS.get(job_id)
            if current is None or current.status == "cancelled":
                return
            current.status = "failed"
            current.message = "Falha ao renderizar."
            current.progress = 100
            current.updated_at = time.time()
            current.error = str(error)
            persist_render_queue(current.gallery_dir)


def cancel_render_job(job_id: str) -> dict[str, object]:
    with RENDER_JOBS_LOCK:
        job = RENDER_JOBS.get(job_id)
        if job is None:
            return {"ok": False, "error": "Render job not found."}
        if job.status not in {"queued", "rendering"}:
            return {"ok": True, "job": render_job_to_dict(job)}
        job.status = "cancelled"
        job.message = "Render cancelado."
        job.progress = 100
        job.updated_at = time.time()
        persist_render_queue(job.gallery_dir)
        return {"ok": True, "job": render_job_to_dict(job)}


def remove_render_job(job_id: str, gallery_dir: Path) -> dict[str, object]:
    with RENDER_JOBS_LOCK:
        job = RENDER_JOBS.pop(job_id, None)
        target_dir = job.gallery_dir if job is not None else gallery_dir
        manifest = read_render_queue_manifest(target_dir)
        manifest_jobs = manifest.get("jobs") if isinstance(manifest, dict) else []
        kept = [item for item in manifest_jobs if isinstance(item, dict) and str(item.get("id")) != job_id]
        removed = job is not None or len(kept) != len(manifest_jobs if isinstance(manifest_jobs, list) else [])
        if not removed:
            return {"ok": False, "error": "Render job not found."}
        write_render_queue_manifest(target_dir, kept)
        return {"ok": True, "jobs": render_queue_snapshot_without_lock(target_dir)}


def update_render_job_profile(job_id: str, gallery_dir: Path, profile_value: object) -> dict[str, object]:
    profile = clean_render_resource_profile(profile_value)
    with RENDER_JOBS_LOCK:
        job = RENDER_JOBS.get(job_id)
        if job is not None:
            if job.status != "queued":
                return {
                    "ok": True,
                    "changed": False,
                    "job": render_job_to_dict(job),
                    "message": "Perfil salvo para proximos renders; este render ja iniciou.",
                    "jobs": render_queue_snapshot_without_lock(job.gallery_dir),
                }
            job.resource_profile = profile
            job.payload["resource_profile"] = profile
            job.fingerprint = render_job_fingerprint(job.payload, profile)
            job.updated_at = time.time()
            job.message = f"Perfil alterado para {render_profile_label(profile)}."
            persist_render_queue(job.gallery_dir)
            return {
                "ok": True,
                "changed": True,
                "job": render_job_to_dict(job),
                "jobs": render_queue_snapshot_without_lock(job.gallery_dir),
            }
        manifest = read_render_queue_manifest(gallery_dir)
        items = manifest.get("jobs") if isinstance(manifest, dict) else []
        if not isinstance(items, list):
            return {"ok": False, "error": "Render job not found."}
        changed = False
        for item in items:
            if not isinstance(item, dict) or str(item.get("id")) != job_id:
                continue
            if item.get("status") != "queued":
                return {
                    "ok": True,
                    "changed": False,
                    "message": "Perfil salvo para proximos renders; este render ja iniciou.",
                    "jobs": render_queue_snapshot_without_lock(gallery_dir),
                }
            item["resource_profile"] = profile
            item["updated_at"] = time.time()
            item["message"] = f"Perfil alterado para {render_profile_label(profile)}."
            changed = True
            break
        if not changed:
            return {"ok": False, "error": "Render job not found."}
        write_render_queue_manifest(gallery_dir, items)
        return {"ok": True, "changed": True, "jobs": render_queue_snapshot_without_lock(gallery_dir)}


def render_job_cancelled(job_id: object) -> bool:
    if not job_id:
        return False
    with RENDER_JOBS_LOCK:
        job = RENDER_JOBS.get(str(job_id))
        return bool(job and job.status == "cancelled")


def render_job_snapshot(job_id: str) -> dict[str, object] | None:
    with RENDER_JOBS_LOCK:
        job = RENDER_JOBS.get(job_id)
        return render_job_to_dict(job) if job else None


def render_job_by_fingerprint(gallery_dir: Path, fingerprint: str) -> dict[str, object] | None:
    for job in render_queue_snapshot(gallery_dir):
        if job.get("fingerprint") == fingerprint and job.get("status") in {"queued", "rendering", "ready"}:
            return job
    return None


def render_queue_snapshot(gallery_dir: Path) -> list[dict[str, object]]:
    manifest_jobs = read_render_queue_manifest(gallery_dir).get("jobs", [])
    jobs = [item for item in manifest_jobs if isinstance(item, dict)]
    with RENDER_JOBS_LOCK:
        live = [render_job_to_dict(job) for job in RENDER_JOBS.values() if job.gallery_dir == gallery_dir]
    merged: dict[str, dict[str, object]] = {str(job.get("id")): job for job in jobs if job.get("id")}
    for job in live:
        merged[str(job["id"])] = job
    return sorted(merged.values(), key=lambda item: float(item.get("created_at") or 0), reverse=True)


def render_job_to_dict(job: RenderJob) -> dict[str, object]:
    return {
        "id": job.id,
        "fingerprint": job.fingerprint,
        "status": job.status,
        "message": job.message,
        "progress": job.progress,
        "speed": job.speed,
        "eta_seconds": job.eta_seconds,
        "processed_seconds": job.processed_seconds,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "resource_profile": job.resource_profile,
        "output_dir": str(job.output_dir),
        "export_dir": job.export_dir,
        "files": job.files or [],
        "error": job.error,
        "summary": render_job_summary(job.payload),
    }


def restore_render_jobs_from_manifest(gallery_dir: Path, base_dir: Path) -> None:
    manifest = read_render_queue_manifest(gallery_dir)
    items = manifest.get("jobs") if isinstance(manifest, dict) else []
    if not isinstance(items, list):
        return
    with RENDER_JOBS_LOCK:
        for item in items:
            if not isinstance(item, dict) or not item.get("id") or item.get("id") in RENDER_JOBS:
                continue
            if item.get("status") not in {"queued", "rendering"}:
                continue
            item["status"] = "queued"
            job = RenderJob(
                str(item["id"]),
                str(item.get("fingerprint") or ""),
                "queued",
                float(item.get("created_at") or time.time()),
                time.time(),
                gallery_dir,
                base_dir,
                Path(str(item.get("output_dir") or render_job_output_dir(gallery_dir, str(item["id"])))),
                clean_render_resource_profile(item.get("resource_profile")),
                {},
                "Aguardando novo envio para retomar.",
                0,
                "",
                None,
                0.0,
                [],
                str(item.get("export_dir") or ""),
                "Servidor reiniciado antes de concluir este render.",
            )
            RENDER_JOBS[job.id] = job


def render_job_fingerprint(payload: dict[str, object], profile: str) -> str:
    return queue_render_job_fingerprint(payload, profile, RENDER_JOB_FINGERPRINT_VERSION)


def render_job_summary(payload: dict[str, object]) -> dict[str, object]:
    return queue_render_job_summary(payload)


def render_queue_manifest_path(gallery_dir: Path) -> Path:
    return queue_render_queue_manifest_path(gallery_dir, PROJECT_RENDERS_DIR_NAME)


def render_job_output_dir(gallery_dir: Path, job_id: str) -> Path:
    return queue_render_job_output_dir(gallery_dir, PROJECT_RENDERS_DIR_NAME, job_id)


def read_render_queue_manifest(gallery_dir: Path) -> dict[str, object]:
    return queue_read_render_queue_manifest(render_queue_manifest_path(gallery_dir))


def persist_render_queue(gallery_dir: Path) -> None:
    jobs = render_queue_snapshot_without_lock(gallery_dir)
    write_render_queue_manifest(gallery_dir, jobs)


def write_render_queue_manifest(gallery_dir: Path, jobs: list[dict[str, object]]) -> None:
    queue_write_render_queue_manifest(
        render_queue_manifest_path(gallery_dir),
        jobs,
        RENDER_QUEUE_WRITE_ATTEMPTS,
        RENDER_QUEUE_WRITE_RETRY_SECONDS,
    )


def render_queue_temp_manifest_path(path: Path) -> Path:
    return queue_render_queue_temp_manifest_path(path)


def render_queue_write_error_is_retryable(error: OSError) -> bool:
    return queue_render_queue_write_error_is_retryable(error)


def render_queue_cleanup_temp_manifest(path: Path) -> None:
    queue_render_queue_cleanup_temp_manifest(path)


def render_queue_snapshot_without_lock(gallery_dir: Path) -> list[dict[str, object]]:
    manifest_jobs = read_render_queue_manifest(gallery_dir).get("jobs", [])
    jobs = [item for item in manifest_jobs if isinstance(item, dict)]
    live = [render_job_to_dict(job) for job in RENDER_JOBS.values() if job.gallery_dir == gallery_dir]
    merged: dict[str, dict[str, object]] = {str(job.get("id")): job for job in jobs if job.get("id")}
    for job in live:
        merged[str(job["id"])] = job
    return sorted(merged.values(), key=lambda item: float(item.get("created_at") or 0), reverse=True)


def clean_render_resource_profile(value: object) -> str:
    return queue_clean_render_resource_profile(value)


def render_profile_label(profile: str) -> str:
    return queue_render_profile_label(profile)


def finalized_results_from_gallery(gallery_dir: Path) -> dict[str, object]:
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
    recovered = recovered_captioned_files(gallery_dir)
    return {
        "ok": True,
        "ready": False,
        "partial": bool(recovered),
        "count": len(recovered),
        "files": finalized_file_urls(recovered, gallery_dir) if recovered else [],
        "export_dir": "",
    }


def recovered_captioned_files(gallery_dir: Path) -> list[dict[str, object]]:
    out_dir = gallery_dir / "captioned-clips"
    if not out_dir.exists():
        return []
    queue_rows = caption_queue_rows_by_output(gallery_dir)
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


def caption_queue_rows_by_output(gallery_dir: Path) -> dict[tuple[int, str], dict[str, object]]:
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


def analyze_camera_from_request(handler: http.server.BaseHTTPRequestHandler, base_dir: Path) -> dict[str, object]:
    payload = read_json_body(handler)
    gallery_dir = resolve_request_gallery_dir(base_dir, payload)
    clip_file = clean_optional_text(payload.get("clip_file"), 1000)
    if not clip_file:
        raise ValueError("Missing clip_file.")
    clip_path = resolve_request_media_path(gallery_dir, clip_file)
    start = max(0.0, float(payload.get("trim_start_seconds") or 0.0))
    duration = max(0.3, float(payload.get("adjusted_duration") or payload.get("duration") or 0.0))
    source_start = optional_camera_float(payload.get("source_start_seconds"))
    platform = str(payload.get("platform") or "tiktok")
    mode = normalize_camera_analysis_mode(payload.get("mode"))
    force_refresh = camera_analysis_bypasses_cache(payload, mode)
    title = clean_optional_text(payload.get("title"), 240)
    transcript = clean_optional_text(payload.get("transcript"), 3500)
    if force_refresh and camera_analysis_uses_ai(mode) and payload.get("allow_completed_cache", True):
        previous = latest_good_ai_cache(gallery_dir, mode, platform, clip_file)
        if previous is not None:
            return {**previous, "ok": True, "cached": True, "completed_cache": True}
    last_analysis: dict[str, object] | None = None
    last_error = ""
    visual_map_ready = (gallery_dir / "visual-map.json").exists()
    for media in camera_analysis_media_candidates(gallery_dir, clip_path, start, source_start):
        if camera_analysis_uses_ai(mode) and not visual_map_ready and media.kind == "source":
            continue
        cache_path = camera_analysis_cache_path(gallery_dir, media, duration, platform, mode)
        if not force_refresh and cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8-sig"))
            if isinstance(cached, dict) and isinstance(cached.get("camera_path"), list):
                if not isinstance(cached.get("director_plan"), dict):
                    cached["director_plan"] = director_plan_from_camera_path(
                        cached["camera_path"], duration, platform, str(cached.get("source") or mode), mode
                    )
                return {**cached, "ok": True, "cached": True}
        try:
            visual_analysis = visual_map_camera_analysis(gallery_dir, media, duration, mode, platform, title, transcript)
            allow_ai = not ai_director_should_wait_for_visual_map(gallery_dir, media, mode, visual_analysis)
            fast_analysis = camera_analysis_uses_ai(mode) and not visual_map_ready and media.kind == "clip"
            analysis = visual_analysis or opencv_face_camera_analysis(
                media.ref, media.start, duration, mode, media.kind, media.label, platform, title, transcript, allow_ai, fast_analysis
            )
        except RuntimeError as error:
            last_error = str(error)
            continue
        last_analysis = analysis
        camera_path = analysis["camera_path"]
        if camera_path:
            result = {
                "ok": True,
                "cached": False,
                "cache_bypassed": force_refresh,
                "version": CAMERA_ANALYSIS_VERSION,
                "source": analysis["source"],
                "mode": mode,
                "mode_label": SMART_CAMERA_MODES[mode],
                "platform": platform,
                "resolution_preset": resolution_key_for_platform(platform),
                "clip_file": clip_file,
                "trim_start_seconds": round(start, 3),
                "source_start_seconds": round(media.start, 3) if media.kind == "source" else None,
                "adjusted_duration": round(duration, 3),
                "detected_faces": analysis["detected_faces"],
                "detection_frames": analysis["detection_frames"],
                "diagnostics": analysis.get("diagnostics", {}),
                "camera_path": camera_path,
                "director_plan": analysis.get("director_plan", {}),
            }
            recovered = recover_previous_good_ai_result(
                gallery_dir, result, mode, platform, clip_file, analysis.get("detections"), duration
            )
            if recovered is not None:
                return recovered
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            return result
    diagnostics = last_analysis.get("diagnostics", {}) if last_analysis else {"analysis_error": last_error}
    return {
        "ok": False,
        "error": "Nenhum rosto confiavel foi detectado. Mantive a camera atual.",
        "diagnostics": diagnostics,
    }


def camera_status_from_request(handler: http.server.BaseHTTPRequestHandler, base_dir: Path) -> dict[str, object]:
    parsed = urllib.parse.urlparse(handler.path)
    params = {key: values[-1] for key, values in urllib.parse.parse_qs(parsed.query).items() if values}
    return camera_status_from_payload(params, base_dir)


def camera_status_from_payload(
    payload: dict[str, object], base_dir: Path, start_background: bool = True
) -> dict[str, object]:
    gallery_dir = resolve_request_gallery_dir(base_dir, payload)
    clip_file = clean_optional_text(payload.get("clip_file"), 1000)
    if not clip_file:
        raise ValueError("Missing clip_file.")
    clip_path = resolve_request_media_path(gallery_dir, clip_file)
    mode = normalize_camera_analysis_mode(payload.get("mode"))
    platform = str(payload.get("platform") or "tiktok")
    cache_ready = (
        latest_good_ai_cache(gallery_dir, mode, platform, clip_file) is not None
        if camera_analysis_uses_ai(mode)
        else False
    )
    visual_status = camera_clip_visual_map_status(gallery_dir, clip_path, start_background)
    ready = bool(cache_ready or not camera_analysis_uses_ai(mode) or visual_status["ready"])
    return {
        "ok": True,
        "mode": mode,
        "clip_file": clip_file,
        "cache_ready": cache_ready,
        "ready": ready,
        "visual_map": visual_status,
    }


def camera_clip_visual_map_status(gallery_dir: Path, clip_path: Path, start_background: bool) -> dict[str, object]:
    media = CameraAnalysisMedia(clip_path, local_media_cache_key(clip_path), clip_path.name, "clip", 0.0)
    path = visual_map_path_for_media(gallery_dir, media)
    if visual_map_file_ready(path, clip_path):
        return {"ready": True, "preparing": False, "path": str(path), "kind": "clip"}
    preparing = visual_map_task_running(path)
    if start_background and not preparing:
        preparing = start_visual_map_task(path, clip_path)
    return {"ready": False, "preparing": preparing, "path": str(path), "kind": "clip"}


def visual_map_file_ready(path: Path, source_path: Path) -> bool:
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        isinstance(payload, dict)
        and bool(payload.get("ok"))
        and payload.get("version") == VISUAL_MAP_VERSION
        and visual_map_matches_media(payload, source_path)
    )


def visual_map_task_running(path: Path) -> bool:
    key = str(path.resolve())
    with VISUAL_MAP_TASKS_LOCK:
        return key in VISUAL_MAP_TASKS


def start_visual_map_task(path: Path, media_path: Path) -> bool:
    key = str(path.resolve())
    with VISUAL_MAP_TASKS_LOCK:
        if VISUAL_MAP_TASKS:
            return key in VISUAL_MAP_TASKS
        VISUAL_MAP_TASKS.add(key)
    thread = threading.Thread(target=run_visual_map_task, args=(key, path, media_path), daemon=True)
    thread.start()
    return True


def run_visual_map_task(key: str, path: Path, media_path: Path) -> None:
    try:
        write_media_visual_map(path, media_path)
    finally:
        with VISUAL_MAP_TASKS_LOCK:
            VISUAL_MAP_TASKS.discard(key)


def save_bumper_asset_from_request(handler: http.server.BaseHTTPRequestHandler, base_dir: Path) -> dict[str, object]:
    payload = read_json_body(handler)
    gallery_dir = resolve_request_gallery_dir(base_dir, payload)
    slot = normalize_bumper_slot(payload.get("slot"))
    platform = str(payload.get("platform") or "tiktok")
    if platform not in PLATFORM_PRESETS:
        raise ValueError("Plataforma invalida para vinheta.")
    preset = PLATFORM_PRESETS[platform]
    width = int(float(payload.get("width") or 0))
    height = int(float(payload.get("height") or 0))
    if width != preset.width or height != preset.height:
        raise ValueError(f"Use um video {preset.width}x{preset.height} para {preset.label}.")
    duration = clamp(float(payload.get("duration") or 0.0), 0.0, 3600.0)
    if duration <= 0:
        raise ValueError("Nao consegui ler a duracao da vinheta.")
    label = clean_bumper_label(payload.get("label"))
    video_bytes, extension = decode_data_url_video(str(payload.get("data_url") or ""))
    if len(video_bytes) > BUMPER_MAX_SOURCE_BYTES:
        raise ValueError("Vinheta muito pesada. Use um video menor para o MVP local.")
    asset_dir = gallery_dir / "bumper-assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(video_bytes).hexdigest()[:16]
    asset_path = asset_dir / f"{slot}-{platform}-{digest}.{extension}"
    if not asset_path.exists():
        asset_path.write_bytes(video_bytes)
    rel_path = asset_path.resolve().relative_to(gallery_dir.resolve()).as_posix()
    bumper = {
        "id": f"bumper-{slot}-{digest}",
        "slot": slot,
        "label": label,
        "asset_file": rel_path,
        "width": width,
        "height": height,
        "duration": round(duration, 3),
    }
    return {"ok": True, "bumper": bumper}


def normalize_bumper_slot(value: object) -> str:
    slot = str(value or "").strip().lower()
    if slot not in BUMPER_SLOTS:
        raise ValueError("Slot de vinheta invalido.")
    return slot


def clean_bumper_label(value: object) -> str:
    label = clean_optional_text(value, 180)
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


def normalize_camera_analysis_mode(value: object) -> str:
    key = str(value or "auto-director").strip()
    return key if key in SMART_CAMERA_MODES else "auto-director"


def camera_analysis_uses_ai(mode: str) -> bool:
    return mode in AI_DIRECTOR_INTENTS


def camera_analysis_bypasses_cache(payload: dict[str, object], mode: str) -> bool:
    return bool(payload.get("force_refresh")) and camera_analysis_uses_ai(mode)


def recover_previous_good_ai_result(
    gallery_dir: Path, result: dict[str, object], mode: str, platform: str, clip_file: str,
    detections: object = None, duration: float = 0.0
) -> dict[str, object] | None:
    if not camera_analysis_uses_ai(mode) or ai_director_result_is_good(result):
        return None
    previous = latest_good_ai_cache(gallery_dir, mode, platform, clip_file)
    if previous is None:
        return None
    diagnostics = previous.get("diagnostics")
    if not isinstance(diagnostics, dict):
        diagnostics = {}
        previous["diagnostics"] = diagnostics
    diagnostics["ai_cache_recovered"] = {
        "used": True,
        "reason": ai_director_failure_reason(result),
    }
    if isinstance(detections, list) and isinstance(previous.get("camera_path"), list):
        upgrade_recovered_ai_result(previous, detections, duration, platform, mode)
    return {**previous, "ok": True, "cached": True, "cache_recovered": True}


def upgrade_recovered_ai_result(
    payload: dict[str, object], detections: list[dict[str, object]], duration: float, platform: str, mode: str
) -> None:
    path = payload.get("camera_path")
    if not isinstance(path, list):
        return
    hard_cut = ai_director_uses_hard_cuts(mode)
    upgraded = dense_protected_camera_path(path, detections, duration, platform, mode)
    payload["camera_path"] = upgraded
    payload["director_plan"] = director_plan_from_camera_path(upgraded, duration, platform, "ai-director-cache-upgraded", mode)
    diagnostics = payload.get("diagnostics")
    if isinstance(diagnostics, dict):
        diagnostics.update(camera_path_quality_diagnostics(detections, upgraded, duration, platform))
        diagnostics["cache_upgrade"] = {
            "dense_protection": True,
            "speaker_side_coverage": True,
            "max_still_seconds": AI_DIRECTOR_MAX_STILL_SECONDS,
        }


def latest_good_ai_cache(gallery_dir: Path, mode: str, platform: str, clip_file: str) -> dict[str, object] | None:
    cache_dir = gallery_dir / "camera-analysis"
    if not cache_dir.exists():
        return None
    candidates: list[dict[str, object]] = []
    for path in sorted(cache_dir.glob(f"*-{mode}-*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if ai_cache_matches_request(payload, mode, platform, clip_file) and ai_director_result_is_good(payload):
            payload["cache_path"] = str(path)
            candidates.append(payload)
    return candidates[0] if candidates else None


def ai_cache_matches_request(payload: dict[str, object], mode: str, platform: str, clip_file: str) -> bool:
    if payload.get("version") != CAMERA_ANALYSIS_VERSION:
        return False
    if payload.get("mode") != mode:
        return False
    if payload.get("resolution_preset") != resolution_key_for_platform(platform):
        return False
    return clean_optional_text(payload.get("clip_file"), 1000) == clip_file


def ai_director_result_is_good(payload: dict[str, object]) -> bool:
    diagnostics = payload.get("diagnostics")
    if not isinstance(diagnostics, dict):
        return False
    ai = diagnostics.get("ai_director")
    if not isinstance(ai, dict):
        return False
    if ai.get("status") == "applied":
        return True
    legacy_success = bool(ai.get("enabled")) and not ai.get("error") and int(float(ai.get("frame_samples") or 0)) > 0
    return legacy_success and str(payload.get("source") or "").endswith("ai-director")


def ai_director_failure_reason(payload: dict[str, object]) -> str:
    diagnostics = payload.get("diagnostics")
    if not isinstance(diagnostics, dict):
        return "unknown"
    ai = diagnostics.get("ai_director")
    if not isinstance(ai, dict):
        return "unknown"
    return str(ai.get("status") or ai.get("error") or "fallback")


def ai_director_should_wait_for_visual_map(
    gallery_dir: Path, media: CameraAnalysisMedia, mode: str, visual_analysis: dict[str, object] | None
) -> bool:
    return (
        camera_analysis_uses_ai(mode)
        and media.kind == "source"
        and visual_analysis is None
        and not (gallery_dir / "visual-map.json").exists()
    )


def pending_visual_map_ai_diagnostics(mode: str) -> dict[str, object]:
    return {
        "enabled": bool(openai_api_key()),
        "fallback": "auto-director",
        "intent": ai_director_intent(mode)["label"],
        "status": "visual_map_pending",
        "error": "Mapa visual ainda preparando; apliquei Auto Director local.",
    }


def ai_director_intent(mode: str) -> dict[str, str]:
    return AI_DIRECTOR_INTENTS.get(mode, AI_DIRECTOR_INTENTS["ai-director"])


def ai_director_uses_hard_cuts(mode: str) -> bool:
    return mode == "ai-director-cuts"


def optional_camera_float(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def resolve_request_media_path(gallery_dir: Path, clip_file: str) -> Path:
    candidate = resolve_media_path(gallery_dir, clip_file).resolve()
    try:
        candidate.relative_to(gallery_dir.resolve())
    except ValueError as error:
        raise ValueError("Invalid clip_file path.") from error
    require_file(candidate)
    if candidate.suffix.lower() not in RANGE_MEDIA_EXTENSIONS:
        raise ValueError("Camera analysis requires a local video clip.")
    return candidate


def camera_analysis_media_candidates(
    gallery_dir: Path, clip_path: Path, clip_start: float, source_start: float | None
) -> list[CameraAnalysisMedia]:
    candidates: list[CameraAnalysisMedia] = []
    source_media = resolve_camera_source_media(gallery_dir)
    if source_media and source_start is not None:
        candidates.append(CameraAnalysisMedia(source_media.ref, source_media.cache_key, source_media.label, "source", max(source_start, 0.0)))
    candidates.append(CameraAnalysisMedia(clip_path, local_media_cache_key(clip_path), clip_path.name, "clip", clip_start))
    return candidates


def resolve_camera_source_media(gallery_dir: Path) -> CameraAnalysisMedia | None:
    metadata = read_import_metadata(gallery_dir)
    local = local_camera_source_media(metadata.get("source_path"))
    if local:
        return local
    local = source_folder_camera_media(gallery_dir)
    if local:
        return local
    source_url = str(metadata.get("source_url") or "").strip()
    if source_url.startswith(("http://", "https://")):
        try:
            render_url = youtube_render_url(source_url)
        except (subprocess.SubprocessError, RuntimeError, OSError):
            return None
        return CameraAnalysisMedia(render_url, f"url:{source_url}", "YouTube source", "source", 0.0)
    return None


def local_camera_source_media(value: object) -> CameraAnalysisMedia | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    if not path.exists() or not path.is_file() or path.suffix.lower() not in RANGE_MEDIA_EXTENSIONS:
        return None
    resolved = path.resolve()
    return CameraAnalysisMedia(resolved, local_media_cache_key(resolved), resolved.name, "source", 0.0)


def source_folder_camera_media(gallery_dir: Path) -> CameraAnalysisMedia | None:
    source_dir = gallery_dir / "_source"
    if not source_dir.exists():
        return None
    videos = sorted(path for path in source_dir.iterdir() if path.is_file() and path.suffix.lower() in RANGE_MEDIA_EXTENSIONS)
    if not videos:
        return None
    resolved = videos[0].resolve()
    return CameraAnalysisMedia(resolved, local_media_cache_key(resolved), resolved.name, "source", 0.0)


def local_media_cache_key(path: Path) -> str:
    stat = path.stat()
    return json.dumps({"path": str(path.resolve()), "mtime": stat.st_mtime, "size": stat.st_size}, sort_keys=True)


def camera_analysis_cache_path(gallery_dir: Path, media: CameraAnalysisMedia, duration: float, platform: str, mode: str) -> Path:
    cache_scope = camera_analysis_cache_scope(platform, mode)
    fingerprint = json.dumps(
        {
            "version": CAMERA_ANALYSIS_VERSION,
            "media": media.cache_key,
            "kind": media.kind,
            "start": round(media.start, 3),
            "duration": round(duration, 3),
            "scope": cache_scope,
            "mode": mode,
        },
        sort_keys=True,
    )
    digest = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:16]
    stem = safe_cache_stem(media.label)
    return gallery_dir / "camera-analysis" / f"{stem}-{media.kind}-{cache_scope}-{mode}-{digest}.json"


def camera_analysis_cache_scope(platform: str, mode: str) -> str:
    if camera_analysis_uses_ai(mode):
        return resolution_key_for_platform(platform)
    return platform if platform in PLATFORM_PRESETS else "tiktok"


def safe_cache_stem(value: str) -> str:
    stem = Path(value).stem or "media"
    clean = re.sub(r"[^a-zA-Z0-9_.-]+", "-", stem).strip("-")
    return clean[:48] or "media"


def opencv_face_camera_path(input_path: Path, start: float, duration: float) -> list[dict[str, object]]:
    return opencv_face_camera_analysis(
        input_path, start, duration, "auto-director", "clip", Path(input_path).name, "tiktok", "", ""
    )["camera_path"]


def visual_map_command(args: argparse.Namespace) -> None:
    source_path = args.video.expanduser().resolve()
    require_file(source_path)
    out_dir = args.out.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_visual_map(source_path)
    (out_dir / "visual-map.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def start_visual_map_background(out_dir: Path, source: SourceMedia) -> None:
    source_path = visual_map_source_path(source)
    if source_path is None:
        return
    command = [sys.executable, str(Path(__file__).resolve()), "visual-map", str(source_path), "--out", str(out_dir)]
    try:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except (OSError, ValueError):
        return


def write_visual_map(out_dir: Path, source: SourceMedia) -> None:
    source_path = visual_map_source_path(source)
    if source_path is None:
        return
    try:
        payload = build_visual_map(source_path)
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        payload = failed_visual_map(source_path, error)
    (out_dir / "visual-map.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def visual_map_source_path(source: SourceMedia) -> Path | None:
    if not source.metadata or source.metadata.get("kind") != "local":
        return None
    path = Path(str(source.render_source)).expanduser()
    if not path.exists() or not path.is_file() or path.suffix.lower() not in RANGE_MEDIA_EXTENSIONS:
        return None
    return path.resolve()


def build_visual_map(source_path: Path) -> dict[str, object]:
    cv2 = import_cv2()
    capture = cv2.VideoCapture(str(source_path))
    if not capture.isOpened():
        raise RuntimeError("OpenCV could not open source video for visual map.")
    try:
        metadata = opencv_video_metadata(capture)
        duration = float(metadata.get("duration") or 0.0)
        sample_times = visual_map_sample_times(duration)
        yolo_model = load_yolo_person_model()
        cascades = [] if yolo_model is not None else opencv_face_cascades(cv2)
        detections = opencv_face_detections(cv2, capture, cascades, 0.0, sample_times, yolo_model)
    finally:
        capture.release()
    return visual_map_payload(source_path, metadata, sample_times, detections)


def visual_map_payload(
    source_path: Path, metadata: dict[str, object], sample_times: list[float], detections: list[dict[str, object]]
) -> dict[str, object]:
    diagnostics = vision_engine_diagnostics(detections)
    return {
        "ok": True,
        "version": VISUAL_MAP_VERSION,
        "source": str(source_path),
        "fingerprint": json.loads(local_media_cache_key(source_path)),
        "metadata": metadata,
        "sample_seconds": VISUAL_MAP_SAMPLE_SECONDS,
        "sample_count": len(sample_times),
        "summary": visual_map_summary(detections, sample_times),
        "vision_engine": diagnostics["vision_engine"],
        "vision_model": diagnostics["vision_model"],
        "vision_error": diagnostics["vision_error"],
        "detections": detections,
    }


def failed_visual_map(source_path: Path, error: Exception) -> dict[str, object]:
    return {"ok": False, "version": VISUAL_MAP_VERSION, "source": str(source_path), "error": str(error)}


def visual_map_sample_times(duration: float) -> list[float]:
    safe_duration = max(duration, 0.3)
    step = max(VISUAL_MAP_SAMPLE_SECONDS, safe_duration / VISUAL_MAP_MAX_FRAMES)
    times = [round(min(index * step, safe_duration), 3) for index in range(int(math.ceil(safe_duration / step)) + 1)]
    return sorted(set(times))


def visual_map_summary(detections: list[dict[str, object]], sample_times: list[float]) -> dict[str, object]:
    sample_count = len(sample_times)
    face_frames = sum(1 for row in detections if reliable_opencv_faces(row))
    person_frames = sum(1 for row in detections if reliable_persons(row))
    group_frames = sum(1 for row in detections if len(reliable_faces(row)) >= 2)
    return {
        "detection_rows": len(detections),
        "face_detection_rate": round(face_frames / sample_count, 3) if sample_count else 0.0,
        "person_detection_rate": round(person_frames / sample_count, 3) if sample_count else 0.0,
        "group_rate": round(group_frames / sample_count, 3) if sample_count else 0.0,
        "max_faces": max((len(reliable_faces(row)) for row in detections), default=0),
        "max_persons": max((len(reliable_persons(row)) for row in detections), default=0),
    }


def visual_map_camera_analysis(
    gallery_dir: Path, media: CameraAnalysisMedia, duration: float, mode: str, platform: str, title: str, transcript: str
) -> dict[str, object] | None:
    payload = visual_map_for_media(gallery_dir, media)
    if payload is None:
        return None
    detections = visual_map_segment_detections(payload, media.start, duration)
    if not detections:
        return None
    safe_mode = normalize_camera_analysis_mode(mode)
    local_mode = "auto-director" if camera_analysis_uses_ai(safe_mode) else safe_mode
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    camera_path = smart_camera_path(detections, duration, local_mode)
    diagnostics = visual_map_camera_diagnostics(media, metadata, detections, camera_path, duration, platform, payload)
    source = f"visual-map-{local_mode}"
    if camera_analysis_uses_ai(safe_mode):
        ai_result = ai_director_camera_result(media.ref, media.start, duration, platform, title, transcript, metadata, detections, camera_path, safe_mode)
        diagnostics["ai_director"] = ai_result["diagnostics"]
        if ai_result["camera_path"]:
            camera_path = ai_result["camera_path"]
            diagnostics["director_plan"] = ai_result.get("director_plan", {})
            diagnostics["camera_keyframes"] = len(camera_path)
            source = f"visual-map-{safe_mode}"
        else:
            camera_path = ai_director_local_fallback_path(camera_path, detections, duration, platform, safe_mode)
            diagnostics["director_plan"] = director_plan_from_camera_path(
                camera_path, duration, platform, "visual-map-ai-director-fallback", safe_mode
            )
            diagnostics["camera_keyframes"] = len(camera_path)
            diagnostics["fallback_quality"] = ai_director_quality_report(
                camera_path, diagnostics["director_plan"], detections, duration
            )
            source = f"visual-map-{safe_mode}-fallback"
    diagnostics.update(camera_path_quality_diagnostics(detections, camera_path, duration, platform))
    director_plan = diagnostics.get("director_plan")
    if not isinstance(director_plan, dict):
        director_plan = director_plan_from_camera_path(camera_path, duration, platform, source, mode)
    return {
        "source": source,
        "detected_faces": max((len(reliable_faces(row)) for row in detections), default=0),
        "detection_frames": detection_frame_count(detections),
        "diagnostics": diagnostics,
        "camera_path": camera_path,
        "director_plan": director_plan,
        "detections": detections,
    }


def visual_map_for_media(gallery_dir: Path, media: CameraAnalysisMedia) -> dict[str, object] | None:
    if not isinstance(media.ref, Path):
        return None
    path = visual_map_path_for_media(gallery_dir, media)
    if not path.exists() and media.kind == "clip":
        write_media_visual_map(path, media.ref)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or not payload.get("ok"):
        return None
    if payload.get("version") != VISUAL_MAP_VERSION:
        return None
    return payload if visual_map_matches_media(payload, media.ref) else None


def visual_map_path_for_media(gallery_dir: Path, media: CameraAnalysisMedia) -> Path:
    if media.kind == "clip":
        return gallery_dir / "camera-analysis" / f"{safe_cache_stem(media.label)}-visual-map.json"
    return gallery_dir / "visual-map.json"


def write_media_visual_map(path: Path, media_path: Path) -> None:
    try:
        payload = build_visual_map(media_path)
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        payload = failed_visual_map(media_path, error)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def visual_map_matches_media(payload: dict[str, object], source_path: Path) -> bool:
    fingerprint = payload.get("fingerprint")
    if isinstance(fingerprint, dict) and fingerprint.get("path") == str(source_path.resolve()):
        return True
    return str(payload.get("source") or "") == str(source_path.resolve())


def visual_map_segment_detections(payload: dict[str, object], start: float, duration: float) -> list[dict[str, object]]:
    raw_rows = payload.get("detections")
    if not isinstance(raw_rows, list):
        return []
    end = start + max(duration, 0.3)
    rows: list[dict[str, object]] = []
    for item in raw_rows:
        if not isinstance(item, dict):
            continue
        absolute_time = float(item.get("time") or 0.0)
        if absolute_time < start - 0.2 or absolute_time > end + 0.2:
            continue
        rows.append({**item, "time": round(clamp(absolute_time - start, 0.0, duration), 3)})
    return rows


def visual_map_camera_diagnostics(
    media: CameraAnalysisMedia, metadata: dict[str, object], detections: list[dict[str, object]],
    camera_path: list[dict[str, object]], duration: float, platform: str, payload: dict[str, object]
) -> dict[str, object]:
    sample_times = [float(row.get("time") or 0.0) for row in detections]
    diagnostics = camera_analysis_diagnostics("visual-map", media.label, metadata, media.start, duration, sample_times, detections, camera_path)
    diagnostics.update(vision_engine_diagnostics(detections))
    if payload.get("vision_engine"):
        diagnostics["vision_engine"] = payload.get("vision_engine")
        diagnostics["vision_model"] = payload.get("vision_model") or ""
        diagnostics["vision_error"] = payload.get("vision_error") or ""
    diagnostics.update(camera_path_quality_diagnostics(detections, camera_path, duration, platform))
    diagnostics["visual_map"] = {"used": True, "version": payload.get("version"), "source_samples": payload.get("sample_count"), "segment_samples": len(detections)}
    return diagnostics


def opencv_face_camera_analysis(
    input_ref: Path | str, start: float, duration: float, mode: str, input_kind: str,
    label: str, platform: str, title: str, transcript: str, allow_ai: bool = True, fast_analysis: bool = False
) -> dict[str, object]:
    cv2 = import_cv2()
    capture = cv2.VideoCapture(str(input_ref))
    if not capture.isOpened():
        raise RuntimeError(f"OpenCV could not open the {input_kind} for camera analysis.")
    try:
        metadata = opencv_video_metadata(capture)
        video_duration = float(metadata["duration"])
        safe_start = min(max(start, 0.0), max(video_duration - 0.3, 0.0)) if video_duration else max(start, 0.0)
        safe_duration = duration
        if video_duration:
            safe_duration = min(duration, max(video_duration - safe_start, 0.3))
        cascades = opencv_face_cascades(cv2)
        yolo_model = None if fast_analysis else load_yolo_person_model()
        sample_times = camera_fast_sample_times(safe_duration) if fast_analysis else camera_sample_times(safe_duration)
        detections = opencv_face_detections(cv2, capture, cascades, safe_start, sample_times, yolo_model)
    finally:
        capture.release()
    safe_mode = normalize_camera_analysis_mode(mode)
    local_mode = "auto-director" if camera_analysis_uses_ai(safe_mode) else safe_mode
    camera_path = smart_camera_path(detections, safe_duration, local_mode)
    diagnostics = camera_analysis_diagnostics(input_kind, label, metadata, safe_start, safe_duration, sample_times, detections, camera_path)
    diagnostics.update(vision_engine_diagnostics(detections))
    if fast_analysis:
        diagnostics["fast_analysis"] = True
    source = f"auto-face-{local_mode}"
    if camera_analysis_uses_ai(safe_mode) and not allow_ai:
        diagnostics["ai_director"] = pending_visual_map_ai_diagnostics(safe_mode)
    elif camera_analysis_uses_ai(safe_mode):
        ai_result = ai_director_camera_result(
            input_ref, safe_start, safe_duration, platform, title, transcript, metadata, detections, camera_path, safe_mode
        )
        diagnostics["ai_director"] = ai_result["diagnostics"]
        if ai_result["camera_path"]:
            camera_path = ai_result["camera_path"]
            diagnostics["director_plan"] = ai_result.get("director_plan", {})
            diagnostics["camera_keyframes"] = len(camera_path)
            source = safe_mode
        else:
            camera_path = ai_director_local_fallback_path(camera_path, detections, safe_duration, platform, safe_mode)
            diagnostics["director_plan"] = director_plan_from_camera_path(camera_path, safe_duration, platform, "ai-director-fallback", safe_mode)
            diagnostics["camera_keyframes"] = len(camera_path)
            diagnostics["fallback_quality"] = ai_director_quality_report(camera_path, diagnostics["director_plan"], detections, safe_duration)
            source = f"auto-face-{safe_mode}-fallback"
    diagnostics.update(camera_path_quality_diagnostics(detections, camera_path, safe_duration, platform))
    director_plan = diagnostics.get("director_plan")
    if not isinstance(director_plan, dict):
        director_plan = director_plan_from_camera_path(camera_path, safe_duration, platform, source, mode)
    return {
        "source": source,
        "detected_faces": max((len(reliable_faces(row)) for row in detections), default=0),
        "detection_frames": detection_frame_count(detections),
        "diagnostics": diagnostics,
        "camera_path": camera_path,
        "director_plan": director_plan,
        "detections": detections,
    }


def import_cv2():
    try:
        import cv2  # type: ignore[import-not-found]
    except ModuleNotFoundError as error:
        raise RuntimeError("OpenCV nao esta instalado. Rode: python -m pip install opencv-python-headless") from error
    return cv2


def opencv_video_metadata(capture: object) -> dict[str, object]:
    fps = float(capture.get(5) or 0.0)
    frames = float(capture.get(7) or 0.0)
    width = int(capture.get(3) or 0)
    height = int(capture.get(4) or 0)
    duration = frames / fps if fps > 0 and frames > 0 else 0.0
    return {
        "width": width,
        "height": height,
        "fps": round(fps, 3),
        "frame_count": int(frames),
        "duration": round(duration, 3),
    }


def opencv_video_duration(capture: object) -> float:
    return float(opencv_video_metadata(capture)["duration"])


def opencv_face_cascades(cv2: object) -> list[dict[str, object]]:
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(str(cascade_path))
    if cascade.empty():
        raise RuntimeError("OpenCV face cascade is unavailable.")
    cascades: list[dict[str, object]] = [{"kind": "frontal", "cascade": cascade, "mirror": False, "confidence_weight": 1.0}]
    profile_path = Path(cv2.data.haarcascades) / "haarcascade_profileface.xml"
    if profile_path.exists():
        profile = cv2.CascadeClassifier(str(profile_path))
        if not profile.empty():
            cascades.extend([
                {"kind": "profile", "cascade": profile, "mirror": False, "confidence_weight": 0.88},
                {"kind": "profile-mirror", "cascade": profile, "mirror": True, "confidence_weight": 0.88},
            ])
    return cascades


def opencv_face_cascade(cv2: object) -> object:
    return opencv_face_cascades(cv2)[0]["cascade"]


def yolo_vision_enabled() -> bool:
    value = os.environ.get("CUTED_VISION_ENGINE", "hybrid").strip().lower()
    return value not in {"opencv", "off", "disabled", "none"}


def yolo_model_name() -> str:
    return os.environ.get("CUTED_YOLO_MODEL", "").strip() or YOLO_DEFAULT_MODEL


def yolo_model_reference() -> str:
    model_name = yolo_model_name()
    model_path = Path(model_name)
    if model_path.is_absolute() or model_path.parent != Path(".") or model_name.startswith(("http://", "https://")):
        return model_name
    model_dir = Path(os.environ.get("CUTED_YOLO_MODEL_DIR", "") or Path.home() / ".cuted" / "models")
    model_dir.mkdir(parents=True, exist_ok=True)
    return str(model_dir / model_name)


def load_yolo_person_model() -> object | None:
    if not yolo_vision_enabled():
        return None
    model_reference = yolo_model_reference()
    if model_reference in YOLO_MODEL_CACHE:
        return YOLO_MODEL_CACHE[model_reference]
    try:
        from ultralytics import YOLO  # type: ignore[import-not-found]

        model = YOLO(model_reference)
    except Exception as error:
        YOLO_MODEL_ERRORS[yolo_model_name()] = str(error)
        YOLO_MODEL_CACHE[model_reference] = None
        return None
    YOLO_MODEL_CACHE[model_reference] = model
    return model


def opencv_face_detections(
    cv2: object,
    capture: object,
    cascades: list[dict[str, object]],
    start: float,
    sample_times: list[float],
    yolo_model: object | None = None,
) -> list[dict[str, object]]:
    detections: list[dict[str, object]] = []
    previous_x = 50.0
    for relative_time in sample_times:
        capture.set(0, (start + relative_time) * 1000.0)
        ok, frame = capture.read()
        if not ok or frame is None:
            continue
        opencv_faces = detect_frame_faces(cv2, cascades, frame)
        persons = detect_frame_people_yolo(yolo_model, frame) if yolo_model is not None else []
        faces = merge_vision_subjects(opencv_faces, persons)
        reliable = [face for face in faces if float(face.get("confidence") or 0.0) >= 0.35]
        if not reliable:
            detections.append({
                "time": round(relative_time, 3),
                "primary": None,
                "faces": [],
                "opencv_faces": opencv_faces,
                "persons": persons,
                "missing": True,
            })
            continue
        primary = select_primary_face(reliable, previous_x)
        if primary:
            previous_x = float(primary["x"])
            detections.append({
                "time": round(relative_time, 3),
                "primary": primary,
                "faces": reliable,
                "opencv_faces": opencv_faces,
                "persons": persons,
            })
    return detections


def camera_analysis_diagnostics(
    input_kind: str,
    label: str,
    metadata: dict[str, object],
    start: float,
    duration: float,
    sample_times: list[float],
    detections: list[dict[str, object]],
    camera_path: list[dict[str, object]],
) -> dict[str, object]:
    sample_count = len(sample_times)
    detection_frames = detection_frame_count(detections)
    missing_frames = sum(1 for row in detections if not reliable_faces(row))
    multi_face_frames = sum(1 for row in detections if len(reliable_opencv_faces(row)) > 1)
    edge_face_frames = sum(1 for row in detections if row_has_edge_face(row))
    detected_faces = max((len(reliable_opencv_faces(row)) for row in detections), default=0)
    detected_times = [float(row.get("time") or 0.0) for row in detections if reliable_faces(row)]
    return {
        "analysis_input": input_kind,
        "analysis_file": label,
        "video_width": metadata.get("width", 0),
        "video_height": metadata.get("height", 0),
        "video_fps": metadata.get("fps", 0.0),
        "video_duration": metadata.get("duration", 0.0),
        "analysis_start": round(start, 3),
        "analysis_duration": round(duration, 3),
        "sample_count": sample_count,
        "sample_rows": len(detections),
        "detection_frames": detection_frames,
        "missing_detection_frames": missing_frames,
        "detection_rate": round(detection_frames / sample_count, 3) if sample_count else 0.0,
        "detected_faces_max": detected_faces,
        "multi_face_frames": multi_face_frames,
        "edge_face_frames": edge_face_frames,
        "first_detection_time": round(min(detected_times), 3) if detected_times else None,
        "last_detection_time": round(max(detected_times), 3) if detected_times else None,
        "camera_keyframes": len(camera_path),
        "detection_preview": compact_detection_preview(detections),
    }


def vision_engine_diagnostics(detections: list[dict[str, object]]) -> dict[str, object]:
    model_name = yolo_model_name()
    model_reference = yolo_model_reference()
    yolo_loaded = YOLO_MODEL_CACHE.get(model_reference) is not None
    person_frames = sum(1 for row in detections if reliable_persons(row))
    multi_person_frames = sum(1 for row in detections if len(reliable_persons(row)) >= 2)
    detected_persons = max((len(reliable_persons(row)) for row in detections), default=0)
    return {
        "vision_engine": "yolo-visual-map" if yolo_loaded else "opencv-fallback",
        "vision_model": model_name if yolo_loaded else "",
        "vision_error": YOLO_MODEL_ERRORS.get(model_name, ""),
        "person_detection_frames": person_frames,
        "person_detection_rate": round(person_frames / len(detections), 3) if detections else 0.0,
        "multi_person_frames": multi_person_frames,
        "detected_persons_max": detected_persons,
    }


def detection_frame_count(detections: list[dict[str, object]]) -> int:
    return sum(1 for row in detections if reliable_faces(row))


def camera_path_quality_diagnostics(
    detections: list[dict[str, object]], camera_path: list[dict[str, object]], duration: float, platform: str
) -> dict[str, object]:
    gaps = camera_path_gaps(camera_path, duration)
    risks = camera_path_risk_count(camera_path, detections, platform)
    protected = sum(1 for frame in camera_path if camera_frame_priority(frame) >= 2)
    return {
        "camera_keyframes": len(camera_path),
        "camera_max_gap_seconds": round(max(gaps), 3) if gaps else 0.0,
        "camera_avg_gap_seconds": round(sum(gaps) / len(gaps), 3) if gaps else 0.0,
        "camera_risk_frames": risks,
        "camera_protected_keyframes": protected,
    }


def dense_camera_diagnostics(
    camera_path: list[dict[str, object]], detections: list[dict[str, object]], duration: float, platform: str
) -> dict[str, object]:
    quality = camera_path_quality_diagnostics(detections, camera_path, duration, platform)
    return {
        "final_keyframes": quality["camera_keyframes"],
        "max_gap_seconds": quality["camera_max_gap_seconds"],
        "avg_gap_seconds": quality["camera_avg_gap_seconds"],
        "remaining_risk_frames": quality["camera_risk_frames"],
        "protected_keyframes": quality["camera_protected_keyframes"],
    }


def camera_path_gaps(camera_path: list[dict[str, object]], duration: float) -> list[float]:
    if not camera_path:
        return [max(duration, 0.3)]
    times = sorted(clamp(float(frame.get("time") or 0.0), 0.0, max(duration, 0.3)) for frame in camera_path)
    if times[0] > 0.001:
        times.insert(0, 0.0)
    if times[-1] < max(duration, 0.3) - 0.05:
        times.append(max(duration, 0.3))
    return [times[index + 1] - times[index] for index in range(len(times) - 1)]


def camera_path_risk_count(
    camera_path: list[dict[str, object]], detections: list[dict[str, object]], platform: str
) -> int:
    risks = 0
    for row in detections:
        faces = sorted(reliable_faces(row), key=face_x)
        if not faces:
            continue
        active = camera_path_frame_at_time(camera_path, float(row.get("time") or 0.0)) if camera_path else {}
        if camera_frame_cuts_faces(active, faces):
            risks += 1
    return risks


def compact_detection_preview(detections: list[dict[str, object]]) -> list[dict[str, object]]:
    preview = []
    for row in detections[:8]:
        primary = row.get("primary") if isinstance(row.get("primary"), dict) else {}
        preview.append({
            "time": row.get("time", 0.0),
            "faces": len(reliable_faces(row)),
            "opencv_faces": len(reliable_opencv_faces(row)),
            "persons": len(reliable_persons(row)),
            "x": primary.get("x"),
            "y": primary.get("y"),
            "zoom": primary.get("zoom"),
            "confidence": primary.get("confidence"),
            "missing": not reliable_faces(row),
            "face_xs": [face.get("x") for face in reliable_faces(row)[:4]],
            "face_widths": [face.get("width") for face in reliable_faces(row)[:4]],
        })
    return preview


def row_has_edge_face(row: dict[str, object]) -> bool:
    return any(face_outside_safe_zone(face) for face in reliable_faces(row))


def camera_sample_times(duration: float) -> list[float]:
    safe_duration = max(duration, 0.3)
    step = max(CAMERA_ANALYSIS_SAMPLE_SECONDS, safe_duration / CAMERA_ANALYSIS_MAX_FRAMES)
    times = [round(min(index * step, safe_duration), 3) for index in range(int(math.ceil(safe_duration / step)) + 1)]
    if times[-1] < safe_duration - 0.05:
        times.append(round(safe_duration, 3))
    return sorted(set(times))


def camera_fast_sample_times(duration: float) -> list[float]:
    safe_duration = max(duration, 0.3)
    step = max(CAMERA_FAST_SAMPLE_SECONDS, safe_duration / CAMERA_FAST_MAX_FRAMES)
    times = [round(min(index * step, safe_duration), 3) for index in range(int(math.ceil(safe_duration / step)) + 1)]
    if times[-1] < safe_duration - 0.05:
        times.append(round(safe_duration, 3))
    return sorted(set(times))


def detect_frame_faces(cv2: object, cascades: list[dict[str, object]], frame: object) -> list[dict[str, float]]:
    height, width = frame.shape[:2]
    scale = min(1.0, 640.0 / max(width, height))
    small = cv2.resize(frame, (int(width * scale), int(height * scale))) if scale < 1.0 else frame
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    rows: list[dict[str, float]] = []
    for spec in cascades:
        mirror = bool(spec.get("mirror"))
        source_gray = cv2.flip(gray, 1) if mirror else gray
        cascade = spec["cascade"]
        faces = cascade.detectMultiScale(source_gray, scaleFactor=1.1, minNeighbors=5, minSize=(36, 36))
        rows.extend(face_rows_from_detections(faces, width, height, scale, mirror, float(spec.get("confidence_weight") or 1.0)))
    return dedupe_detected_faces(rows)


def detect_frame_people_yolo(yolo_model: object, frame: object) -> list[dict[str, float]]:
    height, width = frame.shape[:2]
    try:
        predict = getattr(yolo_model, "predict")
        results = predict(frame, classes=[0], conf=YOLO_PERSON_CONFIDENCE, verbose=False)
    except Exception as error:
        YOLO_MODEL_ERRORS[yolo_model_name()] = str(error)
        return []
    return yolo_person_rows_from_results(results, int(width), int(height))


def yolo_person_rows_from_results(results: object, width: int, height: int) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for result in list(results or [])[:1]:
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            continue
        xyxy_rows = tensor_rows_to_list(getattr(boxes, "xyxy", []))
        confidences = tensor_values_to_list(getattr(boxes, "conf", []))
        classes = tensor_values_to_list(getattr(boxes, "cls", []))
        for index, box in enumerate(xyxy_rows):
            class_value = int(float(classes[index])) if index < len(classes) else 0
            if class_value != 0:
                continue
            confidence = float(confidences[index]) if index < len(confidences) else YOLO_PERSON_CONFIDENCE
            row = yolo_person_row_from_box(box, width, height, confidence)
            if row is not None:
                rows.append(row)
    return dedupe_detected_faces(rows)


def tensor_values_to_list(value: object) -> list[float]:
    converted = tensor_to_python(value)
    if isinstance(converted, list):
        return [float(item) for item in converted]
    return []


def tensor_rows_to_list(value: object) -> list[list[float]]:
    converted = tensor_to_python(value)
    if not isinstance(converted, list):
        return []
    return [[float(item) for item in row] for row in converted if isinstance(row, list) and len(row) >= 4]


def tensor_to_python(value: object) -> object:
    for method in ("detach", "cpu"):
        if hasattr(value, method):
            value = getattr(value, method)()
    return value.tolist() if hasattr(value, "tolist") else value


def yolo_person_row_from_box(box: list[float], width: int, height: int, confidence: float) -> dict[str, float] | None:
    if len(box) < 4:
        return None
    x1, y1, x2, y2 = box[:4]
    source_w = max(x2 - x1, 0.0)
    source_h = max(y2 - y1, 0.0)
    if source_w <= 1.0 or source_h <= 1.0:
        return None
    center_x = (x1 + source_w / 2.0) / max(width, 1) * 100.0
    focus_y = (y1 + source_h * 0.25) / max(height, 1) * 100.0
    area = source_w * source_h
    return {
        "x": round(clamp(center_x, 8.0, 92.0), 2),
        "y": round(clamp(focus_y, 32.0, 61.0), 2),
        "zoom": round(person_zoom(source_w, width), 3),
        "confidence": round(clamp(confidence, 0.0, 1.0), 3),
        "area": round(area * 0.08, 3),
        "body_area": round(area, 3),
        "width": round(source_w / max(width, 1) * 100.0, 2),
        "height": round(source_h / max(height, 1) * 100.0, 2),
        "kind": "person",
        "source": "yolo-person",
    }


def person_zoom(person_width: float, frame_width: float) -> float:
    ratio = person_width / max(frame_width, 1.0)
    if ratio < 0.16:
        return 1.28
    if ratio < 0.26:
        return 1.18
    if ratio < 0.38:
        return 1.1
    return 1.04


def merge_vision_subjects(opencv_faces: list[dict[str, float]], persons: list[dict[str, float]]) -> list[dict[str, float]]:
    rows = [dict(face) for face in opencv_faces]
    for person in persons:
        if any(face_rows_overlap(person, face) for face in rows):
            continue
        rows.append(dict(person))
    return dedupe_detected_faces(rows)


def face_rows_from_detections(
    faces: object, width: int, height: int, scale: float, mirror: bool, confidence_weight: float
) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for face in faces:
        x, y, face_w, face_h = [float(value) for value in face]
        row = face_row_from_detection(x, y, face_w, face_h, width, height, scale, mirror, confidence_weight)
        if row is not None:
            rows.append(row)
    return rows


def face_row_from_detection(
    x: float, y: float, face_w: float, face_h: float, width: int, height: int, scale: float, mirror: bool, confidence_weight: float
) -> dict[str, float] | None:
    if face_w <= 0 or face_h <= 0:
        return None
    source_w = face_w / scale
    source_h = face_h / scale
    center_x = ((x + face_w / 2.0) / scale) / width * 100.0
    focus_y = ((y + face_h * 0.42) / scale) / height * 100.0
    if mirror:
        center_x = 100.0 - center_x
    area_ratio = (source_w * source_h) / max(width * height, 1)
    return {
        "x": round(clamp(center_x, 8.0, 92.0), 2),
        "y": round(clamp(focus_y, 32.0, 61.0), 2),
        "zoom": round(face_zoom(source_w, width), 3),
        "confidence": round(clamp((area_ratio / 0.08) * confidence_weight, 0.3, 1.0), 3),
        "area": round(source_w * source_h, 3),
        "width": round(source_w / max(width, 1) * 100.0, 2),
    }


def dedupe_detected_faces(rows: list[dict[str, float]]) -> list[dict[str, float]]:
    result: list[dict[str, float]] = []
    for candidate in sorted(rows, key=lambda item: item["area"], reverse=True):
        if any(face_rows_overlap(candidate, existing) for existing in result):
            continue
        result.append(candidate)
    return result


def face_rows_overlap(first: dict[str, float], second: dict[str, float]) -> bool:
    return abs(face_x(first) - face_x(second)) < 7.0 and abs(float(first.get("y") or 50.0) - float(second.get("y") or 50.0)) < 8.0


def select_primary_face(faces: list[dict[str, float]], previous_x: float) -> dict[str, float] | None:
    best: dict[str, float] | None = None
    best_score = -math.inf
    for face in faces:
        area = float(face.get("area") or 0.0)
        confidence = float(face.get("confidence") or 0.0)
        stability_penalty = abs(face_x(face) - previous_x) * max(area, 1.0) * 0.0015
        edge_bonus = area * 0.16 if face_outside_safe_zone(face) and confidence >= 0.35 else 0.0
        score = area + edge_bonus - stability_penalty
        if score > best_score:
            best = face
            best_score = score
    return best


def face_x(face: dict[str, float]) -> float:
    return float(face.get("x") or 50.0)


def face_width(face: dict[str, float]) -> float:
    return max(float(face.get("width") or 0.0), 0.0)


def face_left_edge(face: dict[str, float]) -> float:
    return face_x(face) - face_width(face) * 0.55


def face_right_edge(face: dict[str, float]) -> float:
    return face_x(face) + face_width(face) * 0.55


def face_outside_safe_zone(face: dict[str, float]) -> bool:
    x_value = face_x(face)
    return x_value < CAMERA_SAFE_X_MIN or x_value > CAMERA_SAFE_X_MAX


def face_zoom(face_width: float, frame_width: float) -> float:
    ratio = face_width / max(frame_width, 1.0)
    if ratio < 0.12:
        return 1.28
    if ratio < 0.18:
        return 1.2
    if ratio < 0.26:
        return 1.12
    return 1.04


def primary_detections(detections: list[dict[str, object]]) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for row in detections:
        primary = row.get("primary")
        if not isinstance(primary, dict):
            continue
        rows.append({**primary, "time": float(row.get("time") or 0.0)})
    return rows


def smart_camera_path(detections: list[dict[str, object]], duration: float, mode: str) -> list[dict[str, object]]:
    primary = primary_detections(detections)
    if not primary:
        return []
    if mode == "auto-director":
        return auto_director_camera_path(detections, primary, duration)
    if mode == "stable-face":
        return stable_face_camera_path(primary)
    if mode == "face-zoom":
        return primary_face_camera_path(boost_face_zoom(primary), "auto-face-face-zoom", duration)
    if mode == "alternate-faces":
        path = multi_face_camera_path(detections, duration, smooth=True)
        return path or primary_face_camera_path(primary, "auto-face-follow-face", duration)
    if mode == "cut-between-faces":
        path = multi_face_camera_path(detections, duration, smooth=False)
        return path or primary_face_camera_path(primary, "auto-face-follow-face", duration)
    return follow_face_camera_path(detections, primary, duration)


def ai_director_camera_result(
    input_ref: Path | str, start: float, duration: float, platform: str, title: str, transcript: str,
    metadata: dict[str, object], detections: list[dict[str, object]], fallback_path: list[dict[str, object]], mode: str
) -> dict[str, object]:
    diagnostics: dict[str, object] = {"enabled": bool(openai_api_key()), "fallback": "auto-director", "status": "pending"}
    diagnostics["intent"] = ai_director_intent(mode)["label"]
    if not openai_api_key():
        diagnostics["status"] = "no_key"
        diagnostics["error"] = "OPENAI_API_KEY nao configurada."
        return {"camera_path": [], "diagnostics": diagnostics}
    try:
        frames = ai_director_frame_samples(input_ref, start, duration) if ai_director_needs_frame_samples(detections) else []
        payload = request_ai_director_path(platform, title, transcript, metadata, detections, fallback_path, frames, duration, mode)
        director_plan = validated_ai_director_plan(payload, duration, platform, mode)
        path = camera_path_from_director_plan(director_plan, detections, duration, platform, mode)
        if not path:
            path = validated_ai_director_path(payload, duration)
            director_plan = director_plan_from_camera_path(path, duration, platform, "ai-director", mode)
        path = protected_ai_director_path(path, detections, duration, platform)
        if ai_director_uses_hard_cuts(mode):
            path = hard_cut_ai_director_path(path, detections, duration, platform)
        path = dense_protected_camera_path(path, detections, duration, platform, mode)
    except Exception as error:
        diagnostics["status"] = "timeout" if "demorou demais" in str(error).lower() else "fallback"
        diagnostics["error"] = str(error)
        return {"camera_path": [], "diagnostics": diagnostics}
    quality = ai_director_quality_report(path, director_plan, detections, duration)
    if quality["rejected"]:
        diagnostics["status"] = "quality_rejected"
        diagnostics["error"] = str(quality["reason"])
        diagnostics["quality"] = quality
        return {"camera_path": [], "director_plan": director_plan, "diagnostics": diagnostics}
    diagnostics.update({
        "status": "applied",
        "frame_samples": len(frames),
        "frame_sample_policy": "uncertain_only" if frames else "structured_map_only",
        "summary": str(payload.get("summary") or "")[:220],
        "multi_face_coverage": ai_director_multi_face_coverage(detections),
        "dense_camera": dense_camera_diagnostics(path, detections, duration, platform),
        "quality": quality,
    })
    diagnostics["director_plan_shots"] = len(director_plan.get("shots", []))
    return {"camera_path": path, "director_plan": director_plan, "diagnostics": diagnostics}


def ai_director_needs_frame_samples(detections: list[dict[str, object]]) -> bool:
    if len(detections) < 8:
        return True
    detection_rows = [row for row in detections if reliable_faces(row) or reliable_persons(row)]
    if len(detection_rows) / max(len(detections), 1) < 0.24:
        return True
    multi_person_rows = [row for row in detections if len(reliable_persons(row)) >= 2]
    multi_face_rows = [row for row in detections if len(reliable_opencv_faces(row)) >= 2]
    return not multi_person_rows and not multi_face_rows and len(detection_rows) < 12


def ai_director_quality_report(
    path: list[dict[str, object]], director_plan: dict[str, object], detections: list[dict[str, object]], duration: float
) -> dict[str, object]:
    frames = path or []
    kinds = [dynamic_frame_kind(frame) for frame in frames]
    speaker_frames = sum(1 for kind in kinds if kind == "speaker")
    variation_frames = len(frames) - speaker_frames
    fit_frames = sum(1 for frame in frames if camera_path_frame_uses_group_fit(frame))
    raw_shots = director_plan.get("shots")
    shots = raw_shots if isinstance(raw_shots, list) else []
    shot_intents = [normalize_director_intent(shot.get("intent")) for shot in shots if isinstance(shot, dict)]
    speaker_shots = sum(1 for intent in shot_intents if intent in {"speaker_hold", "speaker_close"})
    shot_variations = len(shot_intents) - speaker_shots
    speaker_ratio = speaker_frames / max(len(frames), 1)
    duration_ratios = camera_kind_duration_ratios(frames, duration) if frames else {"group": 0.0, "speaker": 0.0, "reaction": 0.0}
    active_duration_ratio = duration_ratios["speaker"] + duration_ratios["reaction"]
    needs_variation = ai_director_scene_needs_variation(detections, duration)
    speaker_only = bool(
        needs_variation
        and len(frames) >= 5
        and speaker_ratio > AI_DIRECTOR_MAX_SPEAKER_RATIO
        and variation_frames + fit_frames < AI_DIRECTOR_MIN_VARIATION_FRAMES
        and shot_variations < AI_DIRECTOR_MIN_VARIATION_FRAMES
    )
    group_dominant = bool(
        needs_variation
        and len(frames) >= 5
        and duration_ratios["group"] > AI_DIRECTOR_MAX_GROUP_DURATION_RATIO
        and active_duration_ratio < AI_DIRECTOR_MIN_ACTIVE_DURATION_RATIO
    )
    rejected = speaker_only or group_dominant
    reason = "speaker_only" if speaker_only else ("group_dominant" if group_dominant else "")
    return {
        "rejected": rejected,
        "reason": reason,
        "speaker_ratio": round(speaker_ratio, 3),
        "group_duration_ratio": round(duration_ratios["group"], 3),
        "active_duration_ratio": round(active_duration_ratio, 3),
        "speaker_frames": speaker_frames,
        "variation_frames": variation_frames,
        "fit_frames": fit_frames,
        "shot_variations": shot_variations,
        "needs_variation": needs_variation,
    }


def ai_director_scene_needs_variation(detections: list[dict[str, object]], duration: float) -> bool:
    rows = [row for row in detections if reliable_faces(row)]
    if len(rows) < 4:
        return False
    multi_rows = [row for row in rows if len(reliable_faces(row)) >= 2]
    edge_rows = [row for row in rows if row_has_edge_face(row)]
    return duration >= 18.0 and (len(multi_rows) >= 2 or len(edge_rows) >= 3 or len(rows) >= 12)


def ai_director_local_fallback_path(
    camera_path: list[dict[str, object]], detections: list[dict[str, object]], duration: float, platform: str, mode: str
) -> list[dict[str, object]]:
    if not camera_path:
        return []
    safe_mode = "ai-director-cuts" if ai_director_uses_hard_cuts(mode) else "ai-director"
    enhanced = dense_protected_camera_path(camera_path, detections, duration, platform, safe_mode)
    plan = director_plan_from_camera_path(enhanced, duration, platform, "ai-director-fallback", mode)
    if not ai_director_quality_report(enhanced, plan, detections, duration)["rejected"]:
        return enhanced
    context = ai_director_fallback_context_frames(detections, duration, platform, ai_director_uses_hard_cuts(mode))
    if not context:
        context = [open_center_camera_frame(0.0), open_center_camera_frame(max(duration * 0.5, 0.1))]
    merged = merge_camera_path_frames(enhanced, context, duration)
    return dense_protected_camera_path(merged, detections, duration, platform, safe_mode)


def ai_director_fallback_context_frames(
    detections: list[dict[str, object]], duration: float, platform: str, hard_cut: bool
) -> list[dict[str, object]]:
    frames: list[dict[str, object]] = []
    last_time = -999.0
    for row in sorted(detections, key=lambda item: float(item.get("time") or 0.0)):
        time_value = clamp(float(row.get("time") or 0.0), 0.0, max(duration, 0.3))
        if time_value - last_time < 6.0:
            continue
        frame = ai_director_fallback_context_frame(row, time_value, platform)
        if frame is None:
            continue
        if hard_cut:
            frame = hard_cut_ai_director_frame(frame, time_value, str(frame.get("source") or "ai-director-fallback-context"))
        frames.append(frame)
        last_time = time_value
    return frames[:8]


def ai_director_fallback_context_frame(
    row: dict[str, object], time_value: float, platform: str
) -> dict[str, object] | None:
    faces = sorted(reliable_faces(row), key=face_x)
    if len(faces) >= 2:
        frame = group_face_frame(faces, time_value, platform)
        return {**frame, "source": "ai-director-fallback-group", "intent": "group_open"}
    if row_has_edge_face(row):
        frame = open_center_camera_frame(time_value)
        return {**frame, "source": "ai-director-fallback-open", "intent": "center_hold"}
    return None


def director_plan_from_camera_path(
    camera_path: list[dict[str, object]], duration: float, platform: str, source: str, mode: str
) -> dict[str, object]:
    frames = sorted(camera_path, key=lambda frame: float(frame.get("time") or 0.0))
    shots = director_plan_shots(frames, duration)
    return {
        "version": 1,
        "source": source,
        "mode": mode,
        "resolution_preset": resolution_key_for_platform(platform),
        "style": "normal",
        "energy": "normal",
        "shots": shots,
    }


def director_plan_shots(camera_path: list[dict[str, object]], duration: float) -> list[dict[str, object]]:
    safe_duration = max(duration, 0.3)
    frames = camera_path or [{"time": 0.0, "x": 50.0, "y": 50.0, "zoom": 1.0, "source": "director-plan-empty"}]
    shots: list[dict[str, object]] = []
    for index, frame in enumerate(frames[:56]):
        start = clamp(float(frame.get("time") or 0.0), 0.0, safe_duration)
        end = safe_duration if index + 1 >= len(frames) else clamp(float(frames[index + 1].get("time") or safe_duration), start, safe_duration)
        shots.append(director_plan_shot(frame, index, start, max(end, start + 0.1)))
    return shots


def director_plan_shot(frame: dict[str, object], index: int, start: float, end: float) -> dict[str, object]:
    intent, label, subject, transition = director_plan_intent(frame)
    return {
        "id": f"shot-{index + 1:03d}",
        "start": round(start, 3),
        "end": round(end, 3),
        "intent": intent,
        "label": label,
        "subject": subject,
        "transition": transition,
        "reason": director_plan_reason(frame, label),
    }


def director_plan_intent(frame: dict[str, object]) -> tuple[str, str, str, str]:
    source = str(frame.get("source") or "")
    zoom = float(frame.get("zoom") or 1.0)
    if camera_path_frame_uses_group_fit(frame) or "group" in source:
        return "group_open", "Group", "group", "hold"
    if "reaction" in source:
        return "reaction_focus", "Reaction", "secondary", "smooth"
    if "cuts" in source:
        return "cut_focus", "Cut", "primary", "cut"
    if zoom >= 1.18:
        return "speaker_close", "Speaker", "primary", "smooth"
    return "speaker_hold", "Speaker", "primary", "hold"


def director_plan_reason(frame: dict[str, object], label: str) -> str:
    if label == "Group":
        return "Preserva pessoas visiveis e reduz risco de crop apertado."
    if label == "Cut":
        return "Mantem troca seca para dar ritmo sem pan atravessando o quadro."
    if label == "Reaction":
        return "Alterna foco para capturar resposta ou mudanca de atencao."
    zoom = float(frame.get("zoom") or 1.0)
    return "Aproxima o foco principal." if zoom >= 1.18 else "Segura enquadramento estavel no foco principal."


def validated_ai_director_plan(payload: dict[str, object], duration: float, platform: str, mode: str) -> dict[str, object]:
    raw = payload.get("director_plan")
    if not isinstance(raw, dict):
        return {}
    shots = raw.get("shots")
    if not isinstance(shots, list):
        return {}
    valid_shots = [validated_ai_director_shot(row, duration, index) for index, row in enumerate(shots) if isinstance(row, dict)]
    valid_shots = [shot for shot in valid_shots if shot is not None]
    if not valid_shots:
        return {}
    return {
        "version": 1,
        "source": "ai-director",
        "mode": mode,
        "resolution_preset": resolution_key_for_platform(platform),
        "style": str(raw.get("style") or "normal")[:32],
        "energy": str(raw.get("energy") or "normal")[:32],
        "shots": valid_shots[:24],
    }


def validated_ai_director_shot(row: dict[str, object], duration: float, index: int) -> dict[str, object] | None:
    start = clamp(float(row.get("start") or 0.0), 0.0, max(duration, 0.3))
    end = clamp(float(row.get("end") or max(duration, 0.3)), start, max(duration, 0.3))
    if end - start < 0.1:
        end = min(start + 0.1, max(duration, 0.3))
    intent = normalize_director_intent(row.get("intent"))
    return {
        "id": clean_optional_text(row.get("id"), 48) or f"shot-{index + 1:03d}",
        "start": round(start, 3),
        "end": round(end, 3),
        "intent": intent,
        "label": clean_optional_text(row.get("label"), 40) or director_intent_label(intent),
        "subject": clean_optional_text(row.get("subject"), 40) or director_intent_subject(intent),
        "transition": clean_optional_text(row.get("transition"), 40) or director_intent_transition(intent),
        "reason": clean_optional_text(row.get("reason"), 220) or director_intent_reason(intent),
    }


def normalize_director_intent(value: object) -> str:
    intent = str(value or "speaker_hold").strip().lower().replace("-", "_")
    return intent if intent in DIRECTOR_INTENTS else "speaker_hold"


def director_intent_label(intent: str) -> str:
    return str(DIRECTOR_INTENTS.get(intent, DIRECTOR_INTENTS["speaker_hold"])["label"])


def director_intent_subject(intent: str) -> str:
    return str(DIRECTOR_INTENTS.get(intent, DIRECTOR_INTENTS["speaker_hold"])["subject"])


def director_intent_transition(intent: str) -> str:
    return str(DIRECTOR_INTENTS.get(intent, DIRECTOR_INTENTS["speaker_hold"])["transition"])


def director_intent_reason(intent: str) -> str:
    return str(DIRECTOR_INTENTS.get(intent, DIRECTOR_INTENTS["speaker_hold"])["reason"])


def camera_path_from_director_plan(
    plan: dict[str, object], detections: list[dict[str, object]], duration: float, platform: str, mode: str
) -> list[dict[str, object]]:
    shots = plan.get("shots")
    if not isinstance(shots, list):
        return []
    frames = [camera_frame_from_director_shot(shot, detections, platform, mode) for shot in shots if isinstance(shot, dict)]
    frames = [frame for frame in frames if frame is not None]
    if not frames:
        return []
    frames = sorted(frames, key=lambda item: float(item.get("time") or 0.0))
    if float(frames[0].get("time") or 0.0) > 0.001:
        frames.insert(0, {**frames[0], "time": 0.0})
    return stable_camera_targets(frames)


def camera_frame_from_director_shot(
    shot: dict[str, object], detections: list[dict[str, object]], platform: str, mode: str
) -> dict[str, object] | None:
    time_value = float(shot.get("start") or 0.0)
    intent = normalize_director_intent(shot.get("intent"))
    row = nearest_detection(time_value, detections)
    frame = director_shot_target_frame(intent, row, time_value, platform)
    if frame is None:
        frame = open_center_camera_frame(time_value)
    frame = {**frame, "intent": intent, "label": director_intent_label(intent), "reason": str(shot.get("reason") or director_intent_reason(intent))}
    if intent == "cut_focus" or ai_director_uses_hard_cuts(mode):
        return hard_cut_ai_director_frame(frame, time_value, f"ai-director-plan-{intent}")
    return {**frame, "time": round(time_value, 3), "source": f"ai-director-plan-{intent}"}


def director_shot_target_frame(
    intent: str, row: dict[str, object] | None, time_value: float, platform: str
) -> dict[str, object] | None:
    if intent in {"group_open", "center_hold"}:
        return director_group_or_center_frame(intent, row, time_value, platform)
    if intent == "reaction_focus":
        return director_reaction_frame(row, time_value)
    primary = director_primary_frame(row, time_value)
    if primary is not None and intent == "speaker_close":
        return {**primary, "zoom": speaker_focus_zoom(primary, 0.04)}
    return primary


def director_group_or_center_frame(intent: str, row: dict[str, object] | None, time_value: float, platform: str) -> dict[str, object]:
    faces = sorted(reliable_faces(row or {}), key=face_x)
    if intent == "group_open" and faces:
        return group_face_frame(faces, time_value, platform)
    return open_center_camera_frame(time_value)


def director_reaction_frame(row: dict[str, object] | None, time_value: float) -> dict[str, object] | None:
    if row is None:
        return None
    secondary = secondary_speaker_face_for_row(row)
    if secondary is None:
        return None
    return {**secondary, "time": time_value, "zoom": reaction_focus_zoom(secondary), "intent": "reaction_focus"}


def director_primary_frame(row: dict[str, object] | None, time_value: float) -> dict[str, object] | None:
    if row is None:
        return None
    primary = primary_speaker_face_for_row(row)
    if primary is None:
        return None
    return {**primary, "time": time_value, "zoom": speaker_focus_zoom(primary, 0.0), "intent": "speaker_hold"}


def speaker_focus_zoom(face: dict[str, object], boost: float) -> float:
    return round(min(float(face.get("zoom") or 1.0) + boost, AI_DYNAMIC_SPEAKER_MAX_ZOOM), 3)


def reaction_focus_zoom(face: dict[str, object]) -> float:
    return round(min(float(face.get("zoom") or 1.0) + 0.06, AI_DYNAMIC_REACTION_MAX_ZOOM), 3)


def ai_director_frame_samples(input_ref: Path | str, start: float, duration: float) -> list[dict[str, object]]:
    cv2 = import_cv2()
    capture = cv2.VideoCapture(str(input_ref))
    if not capture.isOpened():
        return []
    try:
        samples = []
        for time_value in ai_director_sample_times(duration):
            capture.set(0, (start + time_value) * 1000.0)
            ok, frame = capture.read()
            if ok and frame is not None:
                samples.append({"time": time_value, "image_url": frame_to_jpeg_data_url(cv2, frame)})
        return samples
    finally:
        capture.release()


def ai_director_sample_times(duration: float) -> list[float]:
    safe_duration = max(duration, 0.3)
    count = min(AI_DIRECTOR_MAX_FRAME_SAMPLES, max(4, int(math.ceil(safe_duration / 5.0)) + 1))
    if count <= 1:
        return [0.0]
    return [round((safe_duration * index) / (count - 1), 3) for index in range(count)]


def frame_to_jpeg_data_url(cv2: object, frame: object) -> str:
    height, width = frame.shape[:2]
    scale = min(1.0, 640.0 / max(width, height))
    resized = cv2.resize(frame, (int(width * scale), int(height * scale))) if scale < 1.0 else frame
    ok, buffer = cv2.imencode(".jpg", resized, [int(cv2.IMWRITE_JPEG_QUALITY), 72])
    if not ok:
        raise RuntimeError("Nao foi possivel gerar frame para AI Director.")
    return "data:image/jpeg;base64," + base64.b64encode(buffer.tobytes()).decode("ascii")


def request_ai_director_path(
    platform: str, title: str, transcript: str, metadata: dict[str, object],
    detections: list[dict[str, object]], fallback_path: list[dict[str, object]],
    frames: list[dict[str, object]], duration: float, mode: str
) -> dict[str, object]:
    intent = ai_director_intent(mode)
    system = (
        "Voce e o AI Director do CUTED. Crie primeiro um director_plan editorial para video social. "
        "Use os frames apenas para enquadramento e composicao; nao identifique pessoas. "
        f"Intencao editorial: {intent['label']}. {intent['priority']} "
        "Prefira poucos shots seguros e profissionais. Inclua keyframes apenas como compatibilidade. Responda somente no schema JSON."
    )
    user = ai_director_user_payload(platform, title, transcript, metadata, detections, fallback_path, duration, mode)
    return openai_vision_structured_response(system, user, frames, "cuted_ai_director", ai_director_schema(), "ai_director")


def ai_director_user_payload(
    platform: str, title: str, transcript: str, metadata: dict[str, object],
    detections: list[dict[str, object]], fallback_path: list[dict[str, object]], duration: float, mode: str
) -> str:
    intent = ai_director_intent(mode)
    rules = ai_director_rules(mode)
    return json.dumps({
        "task": "Crie um director_plan: quando focar uma pessoa, abrir para grupo, segurar, alternar, aplicar zoom ou fazer cut.",
        "allowed_intents": list(DIRECTOR_INTENTS),
        "editorial_intent": intent,
        "platform": platform if platform in PLATFORM_PRESETS else "tiktok",
        "platform_viewport": platform_viewport(platform),
        "duration_seconds": round(duration, 3),
        "title": title,
        "transcript_excerpt": transcript[:2200],
        "video": metadata,
        "visual_map_detection_summary": ai_director_detection_summary(detections, platform),
        "visual_map_detections": ai_director_detection_context(detections, platform),
        "vision_detection_summary": ai_director_vision_summary(detections),
        "vision_detections": ai_director_vision_context(detections, platform),
        "scene_direction": ai_director_scene_context(detections, duration, platform),
        "local_auto_director_fallback": fallback_path[:AI_DIRECTOR_MAX_FALLBACK_FRAMES],
        "rules": rules,
    }, ensure_ascii=False)


def platform_viewport(platform: str) -> dict[str, object]:
    preset = PLATFORM_PRESETS.get(platform, PLATFORM_PRESETS["tiktok"])
    resolution = resolution_preset_for_platform(platform)
    aspect = preset.width / max(preset.height, 1)
    orientation = "landscape" if preset.width > preset.height else "portrait"
    return {
        "key": preset.key,
        "label": preset.label,
        "width": preset.width,
        "height": preset.height,
        "aspect_ratio": round(aspect, 4),
        "orientation": orientation,
        "format_note": preset.note,
        "resolution_preset": resolution.key,
        "resolution_label": resolution.label,
        "shared_destinations": list(resolution.destinations),
        "safe_crop_notes": platform_safe_crop_notes(preset),
    }


def resolution_key_for_platform(platform: str) -> str:
    return PLATFORM_RESOLUTION_PRESETS.get(platform, "vertical_9_16")


def resolution_preset_for_platform(platform: str) -> ResolutionPreset:
    return RESOLUTION_PRESETS[resolution_key_for_platform(platform)]


def resolution_preset_to_dict(preset: ResolutionPreset) -> dict[str, object]:
    aspect = preset.width / max(preset.height, 1)
    orientation = "landscape" if preset.width > preset.height else "portrait"
    return {
        "key": preset.key,
        "label": preset.label,
        "width": preset.width,
        "height": preset.height,
        "aspect_ratio": round(aspect, 4),
        "orientation": orientation,
        "destinations": list(preset.destinations),
        "note": preset.note,
    }


def resolution_presets_payload() -> dict[str, dict[str, object]]:
    return {key: resolution_preset_to_dict(preset) for key, preset in RESOLUTION_PRESETS.items()}


def platform_safe_crop_notes(preset: PlatformPreset) -> str:
    if preset.width < preset.height and preset.width / max(preset.height, 1) < 0.65:
        return "Vertical estreito: abra o quadro cedo quando 2+ rostos estiverem distantes ou houver 3+ pessoas."
    if preset.width < preset.height:
        return "Feed vertical moderado: preserve grupo quando houver 3+ pessoas, mas permite closes de reacao com 2 pessoas."
    return "Landscape: preserve contexto lateral e evite zoom excessivo em grupos."


def ai_director_rules(mode: str) -> list[str]:
    rules = [
        "x e y sao centros percentuais de crop, 0 a 100.",
        "zoom deve ficar entre 1.0 e 1.45.",
        "Use 6 a 20 keyframes quando houver deslocamento ou multiplos rostos; menos so se a cena for estavel.",
        "Sempre inclua um keyframe em time 0.",
        "Segure bons enquadramentos por alguns segundos; evite tremedeira.",
        "Grupo e plano aberto sao contexto, nao repouso infinito: depois de 6 a 8 segundos, busque speaker medio ou reacao confiavel.",
        "Quando YOLO enxergar uma pessoa mesmo sem rosto OpenCV, pode usar essa pessoa como speaker medio; close continua reservado para rosto/reacao confiavel.",
        "Se 3 pessoas aparecem no mesmo frame, use grupo para contexto, mas nao fique em grupo por mais de 8 segundos sem buscar uma reacao confiavel.",
        "Se 2 ou mais rostos ficariam fora do crop, reduza zoom e centralize entre os rostos.",
        "Use speaker_hold e speaker_close como plano medio; preserve mais corpo e contexto, nao apenas cara.",
        "Reserve close de rosto para reaction_focus ou cut_focus quando a reacao estiver clara e puder segurar 3 a 4 segundos.",
        "Quando scene_direction.uncertain_windows indicar baixa deteccao, nao persiga rosto antigo; prefira plano aberto com blur.",
        "Siga scene_direction.scene_intent_windows: solo=center, two_close=movimento suave somente com rostos quase colados, two_far=corte seco com holds longos, group_close=cortes fixos entre focos, group_fit=plano aberto com blur.",
        "Com um rosto so, nao use cortes secos frequentes; prefira camera estavel com no maximo pequenos ajustes ou push-in.",
        "Com dois rostos distantes, nunca faca pan atravessando o vazio entre eles; use corte seco ou plano aberto.",
    ]
    if ai_director_uses_hard_cuts(mode):
        rules.extend([
            "Este modo deve parecer corte seco: nao crie keyframes para pans graduais.",
            "Prefira 4.0 a 5.0 segundos entre cortes, salvo mudanca clara de fala ou reacao.",
            "Nao crie pans longos; quando houver duvida, use corte seco ou mantenha o plano atual.",
            "Alterne entre grupo, speaker medio e reacao quando houver rostos confiaveis.",
            "Quando cortar para uma pessoa secundaria, volte para a pessoa principal depois de 2 a 3 segundos.",
            "Use as janelas em scene_direction.reaction_windows como candidatos preferenciais de corte.",
        ])
    elif mode == "ai-director":
        rules.append("Pode usar cortes editoriais pontuais, mas mantenha o modo dinamico misturando holds, leves ajustes e reacoes.")
    return rules


def ai_director_detection_summary(detections: list[dict[str, object]], platform: str) -> dict[str, object]:
    rows = [ai_director_detection_row(row, platform) for row in detections if reliable_faces(row)]
    multi = [row for row in rows if int(row["face_count"]) >= 2]
    group = [row for row in rows if int(row["face_count"]) >= 3 or float(row["spread"]) >= 24.0]
    return {
        "sample_rows": len(detections),
        "sampled_detection_frames": len(rows),
        "uncertain_frames": max(len(detections) - len(rows), 0),
        "multi_face_frames": len(multi),
        "group_priority_frames": len(group),
        "multi_face_coverage": ai_director_multi_face_coverage(detections),
        "max_faces": max((int(row["face_count"]) for row in rows), default=0),
        "group_intervals": ai_director_group_intervals(rows),
    }


def ai_director_detection_context(detections: list[dict[str, object]], platform: str) -> list[dict[str, object]]:
    rows = [ai_director_detection_row(row, platform) for row in detections if reliable_faces(row)]
    if len(rows) <= AI_DIRECTOR_MAX_CONTEXT_ROWS:
        return rows
    step = max(1, int(math.ceil(len(rows) / float(AI_DIRECTOR_MAX_CONTEXT_ROWS))))
    return rows[::step][:AI_DIRECTOR_MAX_CONTEXT_ROWS]


def ai_director_vision_summary(detections: list[dict[str, object]]) -> dict[str, object]:
    person_rows = [row for row in detections if reliable_persons(row)]
    multi_person = [row for row in person_rows if len(reliable_persons(row)) >= 2]
    return {
        "sample_rows": len(detections),
        "person_detection_frames": len(person_rows),
        "person_detection_rate": round(len(person_rows) / len(detections), 3) if detections else 0.0,
        "multi_person_frames": len(multi_person),
        "max_persons": max((len(reliable_persons(row)) for row in detections), default=0),
    }


def ai_director_vision_context(detections: list[dict[str, object]], platform: str) -> list[dict[str, object]]:
    rows = [ai_director_detection_row(row, platform) for row in detections if reliable_faces(row) or reliable_persons(row)]
    if len(rows) <= AI_DIRECTOR_MAX_CONTEXT_ROWS:
        return rows
    step = max(1, int(math.ceil(len(rows) / float(AI_DIRECTOR_MAX_CONTEXT_ROWS))))
    return rows[::step][:AI_DIRECTOR_MAX_CONTEXT_ROWS]


def ai_director_detection_row(row: dict[str, object], platform: str) -> dict[str, object]:
    faces = sorted(reliable_faces(row), key=lambda item: face_x(item))
    opencv_faces = sorted(reliable_opencv_faces(row), key=lambda item: face_x(item))
    persons = sorted(reliable_persons(row), key=lambda item: face_x(item))
    xs = [round(face_x(face), 2) for face in faces[:5]]
    primary = row.get("primary") if isinstance(row.get("primary"), dict) else {}
    intent = camera_scene_intent_for_faces(faces, platform)
    return {
        "time": round(float(row.get("time") or 0.0), 3),
        "face_count": len(faces),
        "opencv_face_count": len(opencv_faces),
        "person_count": len(persons),
        "spread": round(xs[-1] - xs[0], 2) if len(xs) >= 2 else 0.0,
        "face_xs": xs,
        "person_xs": [round(face_x(person), 2) for person in persons[:5]],
        "face_ys": [round(float(face.get("y") or 50.0), 2) for face in faces[:5]],
        "face_zooms": [round(float(face.get("zoom") or 1.0), 3) for face in faces[:5]],
        "face_widths": [round(face_width(face), 2) for face in faces[:5]],
        "primary_x": round(float(primary.get("x") or 50.0), 2),
        "group_priority": len(faces) >= 3 or should_use_group_frame(faces),
        "edge_risk": any(face_outside_safe_zone(face) for face in faces),
        "scene_intent": intent["intent"],
        "scene_motion": intent["motion"],
    }


def ai_director_group_intervals(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    intervals: list[dict[str, object]] = []
    start: float | None = None
    end = 0.0
    max_faces = 0
    for row in rows:
        time_value = float(row["time"])
        priority = bool(row["group_priority"])
        if priority and start is None:
            start = time_value
            max_faces = int(row["face_count"])
        if priority:
            end = time_value
            max_faces = max(max_faces, int(row["face_count"]))
        elif start is not None:
            intervals.append({"start": round(start, 3), "end": round(end, 3), "max_faces": max_faces})
            start = None
            max_faces = 0
    if start is not None:
        intervals.append({"start": round(start, 3), "end": round(end, 3), "max_faces": max_faces})
    return intervals[:6]


def ai_director_multi_face_coverage(detections: list[dict[str, object]]) -> float:
    if not detections:
        return 0.0
    multi = sum(1 for row in detections if len(reliable_faces(row)) >= 2)
    return round(multi / len(detections), 3)


def ai_director_scene_context(detections: list[dict[str, object]], duration: float, platform: str) -> dict[str, object]:
    rows = [row for row in detections if reliable_faces(row)]
    return {
        "duration_seconds": round(max(duration, 0.3), 3),
        "platform_viewport": platform_viewport(platform),
        "primary_track": ai_director_primary_track(rows),
        "reaction_windows": ai_director_reaction_windows(rows, duration),
        "group_windows": ai_director_group_windows(rows, platform),
        "scene_intent_windows": camera_scene_intent_windows(detections, duration, platform),
        "uncertain_windows": detection_uncertainty_windows(detections, duration),
        "cut_pattern": "principal -> reaction 2-3s -> principal; use group when close would cut visible faces",
    }


def camera_scene_intent_windows(
    detections: list[dict[str, object]], duration: float, platform: str
) -> list[dict[str, object]]:
    windows: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for row in sorted(detections, key=lambda item: float(item.get("time") or 0.0)):
        time_value = clamp(float(row.get("time") or 0.0), 0.0, max(duration, 0.3))
        intent = camera_scene_intent_for_row(row, platform)
        if current is None or current.get("intent") != intent["intent"]:
            if current is not None:
                windows.append(current)
            current = {**intent, "start": round(time_value, 3), "end": round(time_value, 3)}
            continue
        current["end"] = round(time_value, 3)
    if current is not None:
        current["end"] = round(max(float(current.get("end") or 0.0), max(duration, 0.3)), 3)
        windows.append(current)
    return windows[:12]


def camera_scene_intent_for_row(row: dict[str, object], platform: str) -> dict[str, object]:
    faces = sorted(reliable_faces(row), key=face_x)
    if not faces:
        return camera_scene_intent("uncertain_fit", 0, 0.0, 0.0, "fit")
    return camera_scene_intent_for_faces(faces, platform)


def camera_scene_intent_for_faces(faces: list[dict[str, float]], platform: str) -> dict[str, object]:
    count = len(faces)
    spread = camera_face_spread(faces)
    span = camera_face_span(faces)
    if count <= 0:
        return camera_scene_intent("uncertain_fit", 0, 0.0, 0.0, "fit")
    if count == 1:
        return camera_scene_intent("solo_center", count, spread, span, "smooth")
    if should_use_group_fit_frame(faces, platform):
        return camera_scene_intent("group_fit", count, spread, span, "fit")
    if count == 2:
        motion = "smooth_pan" if camera_two_faces_are_close(faces, platform) else "hard_cut"
        intent = "two_close_pan" if motion == "smooth_pan" else "two_far_cut"
        return camera_scene_intent(intent, count, spread, span, motion)
    return camera_scene_intent("group_close_alternate", count, spread, span, "focus_alternate")


def camera_scene_intent(intent: str, count: int, spread: float, span: float, motion: str) -> dict[str, object]:
    return {
        "intent": intent,
        "face_count": count,
        "spread": round(spread, 2),
        "span": round(span, 2),
        "motion": motion,
    }


def camera_two_faces_are_close(faces: list[dict[str, float]], platform: str) -> bool:
    preset = PLATFORM_PRESETS.get(platform, PLATFORM_PRESETS["tiktok"])
    aspect = preset.width / max(preset.height, 1)
    spread_limit = CAMERA_TWO_CLOSE_PAN_SPREAD + (4.0 if aspect >= 0.95 else 0.0)
    span_limit = CAMERA_TWO_CLOSE_PAN_SPAN + (6.0 if aspect >= 0.95 else 0.0)
    return camera_face_spread(faces) <= spread_limit and camera_face_span(faces) <= span_limit


def camera_face_spread(faces: list[dict[str, float]]) -> float:
    if len(faces) < 2:
        return 0.0
    ordered = sorted(faces, key=face_x)
    return max(face_x(ordered[-1]) - face_x(ordered[0]), 0.0)


def camera_face_span(faces: list[dict[str, float]]) -> float:
    if len(faces) < 2:
        return face_width(faces[0]) if faces else 0.0
    ordered = sorted(faces, key=face_x)
    return max(face_right_edge(ordered[-1]) - face_left_edge(ordered[0]), 0.0)


def detection_uncertainty_windows(detections: list[dict[str, object]], duration: float) -> list[dict[str, object]]:
    windows: list[dict[str, object]] = []
    start: float | None = None
    end = 0.0
    for row in sorted(detections, key=lambda item: float(item.get("time") or 0.0)):
        time_value = clamp(float(row.get("time") or 0.0), 0.0, max(duration, 0.3))
        if not reliable_faces(row):
            if start is None:
                start = time_value
            end = time_value
            continue
        if start is not None:
            append_uncertainty_window(windows, start, end)
            start = None
    if start is not None:
        append_uncertainty_window(windows, start, max(end, max(duration, 0.3)))
    return windows[:8]


def append_uncertainty_window(windows: list[dict[str, object]], start: float, end: float) -> None:
    length = max(end - start, 0.0)
    if length >= CAMERA_UNCERTAIN_MIN_SECONDS:
        windows.append({"start": round(start, 3), "end": round(end, 3), "duration": round(length, 3)})


def ai_director_primary_track(rows: list[dict[str, object]]) -> dict[str, object]:
    primary_rows = [row for row in rows if isinstance(row.get("primary"), dict)]
    if not primary_rows:
        return {"coverage": 0.0}
    xs = [face_x(row["primary"]) for row in primary_rows if isinstance(row.get("primary"), dict)]
    areas = [float(row["primary"].get("area") or 0.0) for row in primary_rows if isinstance(row.get("primary"), dict)]
    return {
        "coverage": round(len(primary_rows) / max(len(rows), 1), 3),
        "median_x": round(median_value(sorted(xs)), 2),
        "avg_area": round(sum(areas) / max(len(areas), 1), 3),
    }


def ai_director_reaction_windows(rows: list[dict[str, object]], duration: float) -> list[dict[str, object]]:
    windows: list[dict[str, object]] = []
    last_time = -999.0
    for row in rows:
        time_value = float(row.get("time") or 0.0)
        secondary = secondary_face_for_row(row)
        if secondary is None or time_value < 1.2 or time_value - last_time < 3.0:
            continue
        windows.append({
            "time": round(time_value, 3),
            "return_time": round(min(time_value + 2.6, max(duration, 0.3)), 3),
            "secondary_x": round(face_x(secondary), 2),
            "secondary_zoom": round(min(float(secondary.get("zoom") or 1.0) + 0.08, 1.34), 3),
            "face_count": len(reliable_faces(row)),
        })
        last_time = time_value
        if len(windows) >= 8:
            break
    return windows


def ai_director_group_windows(rows: list[dict[str, object]], platform: str) -> list[dict[str, object]]:
    return [
        {"time": round(float(row.get("time") or 0.0), 3), "face_count": len(reliable_faces(row))}
        for row in rows
        if should_use_platform_group_frame(sorted(reliable_faces(row), key=face_x), platform)
    ][:8]


def ai_director_schema() -> dict[str, object]:
    frame_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "time": {"type": "number"},
            "x": {"type": "number"},
            "y": {"type": "number"},
            "zoom": {"type": "number"},
            "reason": {"type": "string"},
        },
        "required": ["time", "x", "y", "zoom", "reason"],
    }
    shot_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string"},
            "start": {"type": "number"},
            "end": {"type": "number"},
            "intent": {"type": "string", "enum": list(DIRECTOR_INTENTS)},
            "label": {"type": "string"},
            "subject": {"type": "string"},
            "transition": {"type": "string"},
            "reason": {"type": "string"},
        },
        "required": ["id", "start", "end", "intent", "label", "subject", "transition", "reason"],
    }
    plan_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "style": {"type": "string"},
            "energy": {"type": "string"},
            "shots": {"type": "array", "items": shot_schema},
        },
        "required": ["style", "energy", "shots"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string"},
            "director_plan": plan_schema,
            "keyframes": {"type": "array", "items": frame_schema},
        },
        "required": ["summary", "director_plan", "keyframes"],
    }


def validated_ai_director_path(payload: dict[str, object], duration: float) -> list[dict[str, object]]:
    rows = payload.get("keyframes")
    if not isinstance(rows, list):
        raise RuntimeError("AI Director nao retornou keyframes.")
    frames = [ai_director_frame_from_row(row, duration) for row in rows if isinstance(row, dict)]
    frames = [frame for frame in frames if frame is not None]
    if not frames:
        raise RuntimeError("AI Director retornou camera vazia.")
    frames = sorted(frames, key=lambda item: float(item["time"]))[:24]
    if float(frames[0]["time"]) > 0.001:
        frames.insert(0, {**frames[0], "time": 0.0})
    return stable_camera_targets(frames)


def protected_ai_director_path(
    frames: list[dict[str, object]], detections: list[dict[str, object]], duration: float, platform: str
) -> list[dict[str, object]]:
    protected: list[dict[str, object]] = []
    for frame in frames:
        safe = protected_ai_director_frame(frame, detections, platform)
        protected.append(safe)
    return stable_camera_targets(compressed_camera_path(protected, duration, max_gap=2.6, x_threshold=1.4, zoom_threshold=0.012))


def hard_cut_ai_director_path(
    frames: list[dict[str, object]], detections: list[dict[str, object]], duration: float, platform: str
) -> list[dict[str, object]]:
    scene_path = cinematic_cut_scene_path(detections, duration, platform)
    if scene_path:
        return scene_path
    return hard_cut_spaced_ai_frames(frames, duration)


def hard_cut_spaced_ai_frames(frames: list[dict[str, object]], duration: float) -> list[dict[str, object]]:
    if not frames:
        return []
    safe_duration = max(duration, 0.3)
    sorted_frames = sorted(frames, key=lambda item: float(item.get("time") or 0.0))
    result: list[dict[str, object]] = []
    for frame in sorted_frames:
        time_value = clamp(float(frame.get("time") or 0.0), 0.0, safe_duration)
        if result and time_value - float(result[-1].get("time") or 0.0) < CAMERA_HARD_CUT_MIN_HOLD_SECONDS:
            continue
        result.append(hard_cut_ai_director_frame(frame, time_value))
    if not result:
        return []
    if float(result[0].get("time") or 0.0) > 0.001:
        result.insert(0, {**result[0], "time": 0.0})
    return result[:14]


def dense_protected_camera_path(
    frames: list[dict[str, object]], detections: list[dict[str, object]], duration: float, platform: str, mode: str
) -> list[dict[str, object]]:
    if not frames or not detections:
        return frames
    hard_cut = ai_director_uses_hard_cuts(mode)
    mandatory = dense_camera_risk_frames(frames, detections, duration, platform, mode)
    merged = merge_camera_path_frames(frames, mandatory, duration) if mandatory else frames
    grammar = scene_grammar_camera_frames(detections, duration, platform, hard_cut)
    if grammar:
        merged = merge_camera_path_frames(merged, grammar, duration)
    fallback = forced_group_fit_camera_frames(merged, detections, duration, platform, hard_cut)
    if fallback:
        merged = merge_camera_path_frames(merged, fallback, duration)
    uncertain = uncertain_center_camera_frames(merged, detections, duration, hard_cut)
    if uncertain:
        merged = merge_camera_path_frames(merged, uncertain, duration)
    stabilized = stabilize_ai_director_path(merged, duration, hard_cut)
    breakaways = fit_breakaway_camera_frames(stabilized, detections, duration, hard_cut)
    if breakaways:
        stabilized = merge_camera_path_frames(stabilized, breakaways, duration)
    group_breakaways = group_breakaway_camera_frames(
        stabilized, detections, duration, platform, hard_cut, include_fit=mode == "ai-director"
    )
    if group_breakaways:
        stabilized = merge_camera_path_frames(stabilized, group_breakaways, duration)
    side_coverage = side_coverage_camera_frames(stabilized, detections, duration, platform, hard_cut)
    if side_coverage:
        stabilized = merge_camera_path_frames(stabilized, side_coverage, duration)
    speaker_side_coverage = speaker_side_coverage_camera_frames(stabilized, detections, duration, platform, hard_cut)
    if speaker_side_coverage:
        stabilized = merge_camera_path_frames(stabilized, speaker_side_coverage, duration)
    motion_frames = max_still_camera_frames(stabilized, detections, duration, platform, hard_cut)
    if motion_frames:
        stabilized = merge_camera_path_frames(stabilized, motion_frames, duration)
    editorial = enforce_editorial_motion_rules(stabilized, detections, duration, platform, hard_cut, mode)
    final_side_coverage = side_coverage_camera_frames(editorial, detections, duration, platform, hard_cut)
    if final_side_coverage:
        editorial = merge_camera_path_frames(editorial, final_side_coverage, duration)
    final_speaker_side_coverage = speaker_side_coverage_camera_frames(editorial, detections, duration, platform, hard_cut)
    if final_speaker_side_coverage:
        editorial = merge_camera_path_frames(editorial, final_speaker_side_coverage, duration)
    group_balance = dominant_group_balance_camera_frames(editorial, detections, duration, platform, hard_cut)
    if group_balance:
        editorial = merge_camera_path_frames(editorial, group_balance, duration)
    editorial = suppress_soft_group_returns(editorial)
    final_motion_frames = max_still_camera_frames(editorial, detections, duration, platform, hard_cut)
    if final_motion_frames:
        editorial = merge_camera_path_frames(editorial, final_motion_frames, duration)
    return editorial[:56]


def enforce_editorial_motion_rules(
    frames: list[dict[str, object]],
    detections: list[dict[str, object]],
    duration: float,
    platform: str,
    hard_cut: bool,
    mode: str = "",
) -> list[dict[str, object]]:
    if not frames:
        return []
    if mode == "ai-director":
        return dynamic_editorial_camera_path(frames, detections, duration, platform)
    if not hard_cut and solo_dominant_camera_scene(detections):
        return solo_stable_ai_director_path(detections, duration)
    return enforce_distant_face_hard_cuts(frames, detections, platform, hard_cut)


def side_coverage_camera_frames(
    frames: list[dict[str, object]], detections: list[dict[str, object]], duration: float, platform: str, hard_cut: bool
) -> list[dict[str, object]]:
    needed = missing_camera_sides(frames, detections)
    if not needed:
        return []
    result: list[dict[str, object]] = []
    for side in needed:
        wanted = missing_side_frame_count(frames + result, side)
        added = 0
        for row in representative_side_rows(detections, side, duration):
            time_value = float(row.get("time") or 0.0)
            if side_recently_covered(frames + result, side, time_value, 3.2):
                continue
            frame = side_focus_camera_frame(row, side, time_value)
            if frame is None:
                continue
            if hard_cut:
                frame = hard_cut_ai_director_frame(frame, time_value, str(frame.get("source")))
            result.append(frame)
            added += 1
            if added >= wanted or side not in missing_camera_sides(frames + result, detections):
                break
    return result


def speaker_side_coverage_camera_frames(
    frames: list[dict[str, object]], detections: list[dict[str, object]], duration: float, platform: str, hard_cut: bool
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for side in missing_speaker_sides(frames, detections):
        for row in representative_side_rows(detections, side, duration):
            time_value = float(row.get("time") or 0.0)
            if speaker_side_recently_covered(frames + result, side, time_value, 3.2):
                continue
            frame = side_focus_camera_frame(row, side, time_value)
            if frame is None:
                continue
            result.append(
                hard_cut_ai_director_frame(frame, time_value, str(frame.get("source"))) if hard_cut else frame
            )
            break
    return result


def missing_speaker_sides(frames: list[dict[str, object]], detections: list[dict[str, object]]) -> list[str]:
    detected = side_counts_from_detections(detections)
    if detected["left"] < 2 or detected["right"] < 2:
        return []
    covered = speaker_side_counts_from_frames(frames)
    return [side for side in ("left", "right") if covered[side] == 0]


def speaker_side_counts_from_frames(frames: list[dict[str, object]]) -> dict[str, int]:
    counts = {"left": 0, "right": 0}
    for frame in frames:
        if dynamic_frame_kind(frame) != "speaker":
            continue
        side = x_side(float(frame.get("x") or 50.0))
        if side in counts:
            counts[side] += 1
    return counts


def speaker_side_recently_covered(frames: list[dict[str, object]], side: str, time_value: float, window: float) -> bool:
    for frame in frames:
        if dynamic_frame_kind(frame) != "speaker":
            continue
        near_time = abs(float(frame.get("time") or 0.0) - time_value) <= window
        if near_time and x_side(float(frame.get("x") or 50.0)) == side:
            return True
    return False


def dominant_group_balance_camera_frames(
    frames: list[dict[str, object]], detections: list[dict[str, object]], duration: float, platform: str, hard_cut: bool
) -> list[dict[str, object]]:
    if not frames or not ai_director_scene_needs_variation(detections, duration):
        return []
    ratios = camera_kind_duration_ratios(frames, duration)
    active_ratio = ratios["speaker"] + ratios["reaction"]
    if ratios["group"] <= AI_DIRECTOR_MAX_GROUP_DURATION_RATIO and active_ratio >= AI_DIRECTOR_MIN_ACTIVE_DURATION_RATIO:
        return []
    needed = dominant_group_balance_frame_budget(active_ratio)
    result: list[dict[str, object]] = []
    intervals = dominant_group_candidate_intervals(frames, duration)
    for slot, (start, end, _frame) in enumerate(intervals):
        if len(result) >= needed:
            break
        time_value = round(start + min(max((end - start) * 0.45, 1.6), 2.6), 3)
        if active_frame_near(frames + result, time_value, 2.4):
            continue
        row = nearest_detection(time_value, detections)
        if row is None:
            continue
        focus = dominant_group_balance_frame(row, time_value, slot, hard_cut)
        if focus is not None:
            result.append(focus)
    return result


def camera_kind_duration_ratios(frames: list[dict[str, object]], duration: float) -> dict[str, float]:
    seconds = {"group": 0.0, "speaker": 0.0, "reaction": 0.0}
    safe_duration = max(duration, 0.3)
    for start, end, frame in camera_path_bounds_from_frames(frames, safe_duration):
        kind = dynamic_frame_kind(frame)
        if kind in seconds:
            seconds[kind] += max(end - start, 0.0)
    return {key: seconds[key] / safe_duration for key in seconds}


def dominant_group_balance_frame_budget(active_ratio: float) -> int:
    deficit = max(AI_DIRECTOR_MIN_ACTIVE_DURATION_RATIO - active_ratio, 0.04)
    estimated_seconds_per_frame = 2.6
    budget = math.ceil(deficit / estimated_seconds_per_frame * 100.0)
    return max(1, min(budget, AI_DIRECTOR_GROUP_BALANCE_MAX_FRAMES))


def dominant_group_candidate_intervals(
    frames: list[dict[str, object]], duration: float
) -> list[tuple[float, float, dict[str, object]]]:
    intervals = [
        (start, end, frame)
        for start, end, frame in camera_path_bounds_from_frames(frames, duration)
        if dynamic_frame_kind(frame) == "group" and end - start >= AI_DIRECTOR_GROUP_BALANCE_MIN_SECONDS
    ]
    return sorted(intervals, key=lambda item: item[1] - item[0], reverse=True)


def active_frame_near(frames: list[dict[str, object]], time_value: float, window: float) -> bool:
    for frame in frames:
        if dynamic_frame_kind(frame) == "group":
            continue
        if abs(float(frame.get("time") or 0.0) - time_value) <= window:
            return True
    return False


def suppress_soft_group_returns(frames: list[dict[str, object]]) -> list[dict[str, object]]:
    ordered = sorted(frames, key=lambda item: float(item.get("time") or 0.0))
    if len(ordered) <= 1:
        return ordered
    result: list[dict[str, object]] = []
    for frame in ordered:
        if should_drop_soft_group_return(result, frame):
            continue
        result.append(frame)
    return result or ordered[:1]


def should_drop_soft_group_return(previous: list[dict[str, object]], frame: dict[str, object]) -> bool:
    if not previous or not soft_group_return_frame(frame):
        return False
    anchor = previous[-1]
    if dynamic_frame_kind(anchor) == "group":
        return False
    gap = float(frame.get("time") or 0.0) - float(anchor.get("time") or 0.0)
    return 0.0 < gap < AI_DIRECTOR_SOFT_GROUP_RETURN_SUPPRESSION_SECONDS


def soft_group_return_frame(frame: dict[str, object]) -> bool:
    source = str(frame.get("source") or "")
    if dynamic_frame_kind(frame) != "group":
        return False
    if any(token in source for token in ("group-safe", "group-fit", "uncertain", "motion-group")):
        return False
    return any(token in source for token in ("dynamic-group", "dynamic-open", "group-return", "fit-return"))


def dominant_group_balance_frame(
    row: dict[str, object], time_value: float, slot: int, hard_cut: bool
) -> dict[str, object] | None:
    faces = sorted(reliable_faces(row), key=face_x)
    if len(faces) < 2:
        return None
    primary = primary_breakaway_face(row, faces, slot)
    if slot % 2 == 1:
        reaction = secondary_breakaway_face(row, primary, faces)
        if reaction is not None:
            return group_breakaway_reaction_frame(reaction, time_value, hard_cut)
    return group_breakaway_speaker_frame(primary, time_value, hard_cut)


def missing_side_frame_count(frames: list[dict[str, object]], side: str) -> int:
    covered = side_counts_from_frames(frames)
    other = "right" if side == "left" else "left"
    target = max(1, math.ceil(max(covered[other], 1) / 2))
    return max(1, min(target - covered[side], 3))


def missing_camera_sides(frames: list[dict[str, object]], detections: list[dict[str, object]]) -> list[str]:
    detected = side_counts_from_detections(detections)
    if detected["left"] < 2 or detected["right"] < 2:
        return []
    covered = side_counts_from_frames(frames)
    missing: list[str] = []
    for side in ("left", "right"):
        other = "right" if side == "left" else "left"
        if covered[side] == 0 or covered[side] * 2 < max(covered[other], 1):
            missing.append(side)
    return missing


def side_counts_from_detections(detections: list[dict[str, object]]) -> dict[str, int]:
    counts = {"left": 0, "right": 0}
    for row in detections:
        sides = {face_side(face) for face in reliable_faces(row)}
        for side in sides:
            if side in counts:
                counts[side] += 1
    return counts


def side_counts_from_frames(frames: list[dict[str, object]]) -> dict[str, int]:
    counts = {"left": 0, "right": 0}
    for frame in frames:
        if camera_path_frame_uses_group_fit(frame):
            continue
        side = x_side(float(frame.get("x") or 50.0))
        if side in counts:
            counts[side] += 1
    return counts


def representative_side_rows(detections: list[dict[str, object]], side: str, duration: float) -> list[dict[str, object]]:
    rows = [row for row in detections if side_faces(row, side)]
    midpoint = max(duration, 0.3) / 2.0
    return sorted(rows, key=lambda row: (abs(float(row.get("time") or 0.0) - midpoint), float(row.get("time") or 0.0)))


def side_faces(row: dict[str, object], side: str) -> list[dict[str, float]]:
    return [face for face in reliable_faces(row) if face_side(face) == side]


def side_focus_camera_frame(row: dict[str, object], side: str, time_value: float) -> dict[str, object] | None:
    faces = side_faces(row, side)
    if not faces:
        return None
    face = max(faces, key=speaker_face_score)
    frame = normalized_focus_face(face)
    return {
        **frame,
        "time": round(time_value, 3),
        "zoom": speaker_focus_zoom(frame, 0.0),
        "source": f"ai-director-side-speaker-{side}",
        "intent": "speaker_hold",
    }


def side_recently_covered(frames: list[dict[str, object]], side: str, time_value: float, window: float) -> bool:
    for frame in frames:
        if abs(float(frame.get("time") or 0.0) - time_value) > window:
            continue
        if x_side(float(frame.get("x") or 50.0)) == side and not camera_path_frame_uses_group_fit(frame):
            return True
    return False


def face_side(face: dict[str, object]) -> str:
    return x_side(face_x(face))


def x_side(x_value: float) -> str:
    if x_value <= 50.0 - AI_DIRECTOR_SIDE_X_DELTA:
        return "left"
    if x_value >= 50.0 + AI_DIRECTOR_SIDE_X_DELTA:
        return "right"
    return "center"


def max_still_camera_frames(
    frames: list[dict[str, object]], detections: list[dict[str, object]], duration: float, platform: str, hard_cut: bool
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for start, end, frame in camera_path_bounds_from_frames(frames, duration):
        if end - start <= AI_DIRECTOR_MAX_STILL_SECONDS:
            continue
        cursor = start + AI_DIRECTOR_MAX_STILL_SECONDS
        while cursor < end - 1.0:
            candidate = motion_break_frame(frame, cursor, detections, platform, hard_cut)
            if candidate is not None:
                result.append(candidate)
            cursor += AI_DIRECTOR_MAX_STILL_SECONDS
    return result[:10]


def motion_break_frame(
    active: dict[str, object], time_value: float, detections: list[dict[str, object]], platform: str, hard_cut: bool
) -> dict[str, object] | None:
    row = nearest_detection(time_value, detections)
    frame = motion_break_target(active, row, time_value, platform)
    if frame is None:
        frame = soft_motion_camera_frame(active, time_value)
    if camera_frames_are_similar(active, frame):
        frame = open_center_camera_frame(time_value) if not camera_frame_is_open_center(active) else None
    if frame is None:
        frame = soft_motion_camera_frame(active, time_value)
    if frame is None:
        return None
    if hard_cut:
        return hard_cut_ai_director_frame(frame, time_value, str(frame.get("source") or "ai-director-motion-break"))
    return frame


def motion_break_target(
    active: dict[str, object], row: dict[str, object] | None, time_value: float, platform: str
) -> dict[str, object] | None:
    if row is None:
        return open_center_camera_frame(time_value)
    faces = sorted(reliable_faces(row), key=face_x)
    active_side = x_side(float(active.get("x") or 50.0))
    opposite = "left" if active_side == "right" else "right"
    if len(faces) >= 2 and side_faces(row, opposite):
        return side_focus_camera_frame(row, opposite, time_value)
    if len(faces) >= 2:
        frame = group_face_frame(faces, time_value, platform)
        return {**frame, "source": "ai-director-motion-group", "intent": "group_open"}
    primary = primary_reliable_face(row)
    return {**normalized_focus_face(primary), "time": time_value, "zoom": speaker_focus_zoom(primary, 0.0), "source": "ai-director-motion-speaker"} if primary else None


def soft_motion_camera_frame(active: dict[str, object], time_value: float) -> dict[str, object]:
    active_zoom = float(active.get("zoom") or 1.0)
    next_zoom = 1.04 if active_zoom <= 1.02 else 1.0
    next_x = 53.0 if float(active.get("x") or 50.0) <= 50.0 else 47.0
    return {
        "time": round(time_value, 3),
        "x": next_x,
        "y": 50.0,
        "zoom": next_zoom,
        "confidence": 0.5,
        "source": "ai-director-motion-soft",
        "intent": "center_hold",
    }


def dynamic_editorial_camera_path(
    frames: list[dict[str, object]],
    detections: list[dict[str, object]],
    duration: float,
    platform: str,
) -> list[dict[str, object]]:
    if solo_dominant_camera_scene(detections):
        return [dynamic_safe_camera_frame(frame, detections, platform) for frame in solo_stable_ai_director_path(detections, duration)]
    safe_duration = max(duration, 0.3)
    result: list[dict[str, object]] = []
    for frame in sorted(frames, key=lambda item: float(item.get("time") or 0.0)):
        time_value = clamp(float(frame.get("time") or 0.0), 0.0, safe_duration)
        candidate = dynamic_safe_camera_frame({**frame, "time": time_value}, detections, platform)
        if result and dynamic_frame_should_merge(result[-1], candidate):
            continue
        result.append(candidate)
    return result


def dynamic_frame_should_merge(previous: dict[str, object], current: dict[str, object]) -> bool:
    time_gap = float(current.get("time") or 0.0) - float(previous.get("time") or 0.0)
    if time_gap >= 1.8:
        return False
    return camera_frames_are_similar(previous, current) or dynamic_frame_kind(previous) == dynamic_frame_kind(current)


def dynamic_safe_camera_frame(
    frame: dict[str, object], detections: list[dict[str, object]], platform: str
) -> dict[str, object]:
    if dynamic_focus_frame_is_unsafe(frame):
        return dynamic_open_context_frame(frame, detections, platform)
    kind = dynamic_frame_kind(frame)
    zoom_limit = AI_DYNAMIC_REACTION_MAX_ZOOM if kind == "reaction" else AI_DYNAMIC_SPEAKER_MAX_ZOOM
    if kind == "group":
        zoom_limit = 1.02
    return {
        **frame,
        "x": round(clamp(float(frame.get("x") or 50.0), AI_DYNAMIC_FOCUS_X_MIN, AI_DYNAMIC_FOCUS_X_MAX), 2),
        "zoom": round(min(float(frame.get("zoom") or 1.0), zoom_limit), 3),
        "source": dynamic_frame_source(kind),
    }


def dynamic_focus_frame_is_unsafe(frame: dict[str, object]) -> bool:
    if dynamic_frame_kind(frame) == "group":
        return False
    source = str(frame.get("source") or "")
    if "fit-return" in source or "uncertain" in source:
        return False
    x_value = float(frame.get("x") or 50.0)
    return x_value < AI_DYNAMIC_FOCUS_X_MIN or x_value > AI_DYNAMIC_FOCUS_X_MAX


def dynamic_open_context_frame(
    frame: dict[str, object], detections: list[dict[str, object]], platform: str
) -> dict[str, object]:
    time_value = float(frame.get("time") or 0.0)
    row = nearest_detection(time_value, detections)
    faces = sorted(reliable_faces(row or {}), key=face_x)
    if len(faces) >= 2:
        group = group_face_frame(faces, time_value, platform)
        return {**group, "source": "ai-director-dynamic-group", "intent": "group_open"}
    return {**open_center_camera_frame(time_value), "source": "ai-director-dynamic-open", "intent": "center_hold"}


def dynamic_frame_kind(frame: dict[str, object]) -> str:
    source = str(frame.get("source") or "")
    intent = str(frame.get("intent") or "")
    if "reaction" in source or intent == "reaction_focus":
        return "reaction"
    if "speaker" in source or intent in {"speaker_hold", "speaker_close"}:
        return "speaker"
    if camera_path_frame_uses_group_fit(frame) or "group" in source or intent == "group_open":
        return "group"
    if "return" in source or intent == "center_hold":
        return "group"
    return "speaker"


def dynamic_frame_source(kind: str) -> str:
    if kind == "reaction":
        return "ai-director-dynamic-reaction"
    if kind == "group":
        return "ai-director-dynamic-group"
    return "ai-director-dynamic-speaker"


def solo_dominant_camera_scene(detections: list[dict[str, object]]) -> bool:
    rows = [row for row in detections if reliable_faces(row)]
    if len(rows) < 2:
        return False
    multi = [row for row in rows if len(reliable_faces(row)) >= 2]
    ratio = len(multi) / max(len(rows), 1)
    return (
        len(multi) <= 1
        and ratio <= CAMERA_SOLO_MAX_MULTI_FACE_RATIO
        and solo_edge_face_ratio(rows) <= CAMERA_SOLO_MAX_EDGE_FACE_RATIO
    )


def solo_edge_face_ratio(rows: list[dict[str, object]]) -> float:
    faces = [primary_reliable_face(row) for row in rows]
    reliable = [face for face in faces if face is not None]
    if not reliable:
        return 1.0
    edge_count = sum(1 for face in reliable if face_outside_safe_zone(face))
    return edge_count / max(len(reliable), 1)


def primary_reliable_face(row: dict[str, object]) -> dict[str, float] | None:
    primary = row.get("primary")
    if isinstance(primary, dict) and float(primary.get("confidence") or 0.0) >= 0.35:
        return primary
    faces = reliable_faces(row)
    if not faces:
        return None
    return max(faces, key=lambda face: float(face.get("area") or 0.0))


def primary_speaker_face_for_row(row: dict[str, object]) -> dict[str, float] | None:
    faces = focusable_speaker_faces(row)
    if not faces:
        return None
    primary = row.get("primary")
    if isinstance(primary, dict):
        real_matches = [
            face
            for face in faces
            if same_face_target(primary, face) and str(face.get("kind") or "face") != "person"
        ]
        if real_matches:
            return max(real_matches, key=speaker_face_score)
        matches = [face for face in faces if same_face_target(primary, face)]
        if matches:
            return max(matches, key=speaker_face_score)
    return max(faces, key=speaker_face_score)


def secondary_speaker_face_for_row(row: dict[str, object]) -> dict[str, float] | None:
    primary = primary_speaker_face_for_row(row)
    if primary is None:
        return None
    candidates = [face for face in focusable_speaker_faces(row) if abs(face_x(face) - face_x(primary)) >= 8.0]
    if not candidates:
        return None
    return max(candidates, key=speaker_face_score)


def focusable_speaker_faces(row: dict[str, object]) -> list[dict[str, float]]:
    faces = reliable_opencv_faces(row)
    if not faces:
        faces = [face for face in reliable_faces(row) if str(face.get("kind") or "face") != "person"]
    subjects = [*faces, *speaker_person_candidates(row, faces)]
    return [normalized_focus_face(face) for face in subjects if dynamic_focus_face_is_safe(face)]


def speaker_person_candidates(row: dict[str, object], faces: list[dict[str, float]]) -> list[dict[str, float]]:
    candidates: list[dict[str, float]] = []
    for person in reliable_persons(row):
        if any(abs(face_x(person) - face_x(face)) <= 6.0 for face in faces):
            continue
        candidates.append(person)
    return candidates


def normalized_focus_face(face: dict[str, float]) -> dict[str, float]:
    return {
        **face,
        "x": round(clamp(face_x(face), AI_DYNAMIC_FOCUS_X_MIN, AI_DYNAMIC_FOCUS_X_MAX), 2),
    }


def dynamic_focus_face_is_safe(face: dict[str, object]) -> bool:
    confidence = float(face.get("confidence") or 0.0)
    x_value = face_x(face)
    return confidence >= 0.35 and AI_DYNAMIC_FOCUS_X_MIN <= x_value <= AI_DYNAMIC_FOCUS_X_MAX


def speaker_face_score(face: dict[str, object]) -> float:
    x_value = face_x(face)
    center_bonus = max(0.0, 18.0 - abs(x_value - 50.0)) * 0.12
    area = float(face.get("area") or 0.0)
    confidence = float(face.get("confidence") or 0.0)
    return confidence * max(area, 1.0) + center_bonus


def same_face_target(first: dict[str, object], second: dict[str, object]) -> bool:
    return abs(face_x(first) - face_x(second)) <= 4.0


def solo_stable_ai_director_path(detections: list[dict[str, object]], duration: float) -> list[dict[str, object]]:
    primary = primary_detections(detections)
    if not primary:
        return []
    frames = primary_face_camera_path(primary, "ai-director-solo", duration)
    held = enforce_minimum_camera_holds(frames, duration, CAMERA_SOLO_MIN_HOLD_SECONDS)
    return [{**frame, "source": "ai-director-solo"} for frame in held[:8]]


def enforce_distant_face_hard_cuts(
    frames: list[dict[str, object]],
    detections: list[dict[str, object]],
    platform: str,
    hard_cut: bool,
) -> list[dict[str, object]]:
    if hard_cut or len(frames) < 2:
        return frames
    result = [{**frames[0]}]
    for frame in sorted(frames[1:], key=lambda item: float(item.get("time") or 0.0)):
        candidate = {**frame}
        if distant_face_transition_needs_cut(result[-1], candidate, detections, platform):
            result[-1] = hard_cut_ai_director_frame(
                result[-1],
                float(result[-1].get("time") or 0.0),
                "ai-director-cuts-hold",
            )
            candidate = hard_cut_ai_director_frame(
                candidate,
                float(candidate.get("time") or 0.0),
                "ai-director-cuts-distant",
            )
        result.append(candidate)
    return result


def distant_face_transition_needs_cut(
    previous: dict[str, object],
    current: dict[str, object],
    detections: list[dict[str, object]],
    platform: str,
) -> bool:
    x_delta = abs(float(current.get("x") or 50.0) - float(previous.get("x") or 50.0))
    if x_delta < CAMERA_DISTANT_FACE_PAN_X_DELTA:
        return False
    start = float(previous.get("time") or 0.0)
    end = float(current.get("time") or 0.0)
    return any(row_has_separated_faces(row, platform) for row in detection_rows_between(detections, start, end))


def detection_rows_between(detections: list[dict[str, object]], start: float, end: float) -> list[dict[str, object]]:
    low, high = sorted((start, end))
    rows = [
        row
        for row in detections
        if low <= float(row.get("time") or 0.0) <= high and reliable_faces(row)
    ]
    if rows:
        return rows
    midpoint = (low + high) / 2.0
    nearest = nearest_detection(midpoint, detections)
    return [nearest] if nearest is not None else []


def row_has_separated_faces(row: dict[str, object], platform: str) -> bool:
    faces = sorted(reliable_faces(row), key=face_x)
    if len(faces) < 2:
        return False
    intent = str(camera_scene_intent_for_faces(faces, platform)["intent"])
    return intent in {"two_far_cut", "group_fit"}


def group_breakaway_camera_frames(
    frames: list[dict[str, object]],
    detections: list[dict[str, object]],
    duration: float,
    platform: str,
    hard_cut: bool = True,
    include_fit: bool = False,
) -> list[dict[str, object]]:
    if not frames or not detections:
        return []
    result: list[dict[str, object]] = []
    for start, end in coalesced_group_intervals(frames, duration, include_fit):
        if end - start < CAMERA_GROUP_BREAKAWAY_MIN_SECONDS:
            continue
        result.extend(group_breakaways_for_interval(start, end, detections, platform, hard_cut))
    return result


def coalesced_group_intervals(
    frames: list[dict[str, object]], duration: float, include_fit: bool = False
) -> list[tuple[float, float]]:
    intervals: list[tuple[float, float]] = []
    current_start: float | None = None
    current_end = 0.0
    for start, end, frame in camera_path_bounds_from_frames(frames, duration):
        if camera_frame_is_group_view(frame) and (include_fit or not camera_path_frame_uses_group_fit(frame)):
            if current_start is None:
                current_start = start
            current_end = end
            continue
        if current_start is not None:
            intervals.append((current_start, current_end))
            current_start = None
    if current_start is not None:
        intervals.append((current_start, current_end))
    return intervals


def camera_frame_is_group_view(frame: dict[str, object]) -> bool:
    source = str(frame.get("source") or "")
    return str(frame.get("intent") or "") == "group_open" or "group" in source or camera_frame_is_group_safe(frame)


def group_breakaways_for_interval(
    start: float,
    end: float,
    detections: list[dict[str, object]],
    platform: str,
    hard_cut: bool,
) -> list[dict[str, object]]:
    rows = reliable_detection_rows_between(detections, start, end)
    if not rows:
        return []
    frames: list[dict[str, object]] = []
    cursor = start + CAMERA_GROUP_BREAKAWAY_LEAD_SECONDS
    max_frames = CAMERA_GROUP_BREAKAWAY_MAX_PER_BLOCK * 3
    face_slot = 0
    while cursor + CAMERA_GROUP_REACTION_HOLD_SECONDS < end and len(frames) < max_frames:
        row = next_breakaway_row(rows, cursor)
        if row is None:
            break
        time_value = max(cursor, float(row.get("time") or cursor))
        sequence = group_breakaway_sequence_for_row(row, time_value, face_slot, end, platform, hard_cut)
        if not sequence:
            cursor += CAMERA_GROUP_BREAKAWAY_INTERVAL_SECONDS
            continue
        frames.extend(sequence)
        cursor = float(sequence[-1].get("time") or time_value) + CAMERA_GROUP_BREAKAWAY_INTERVAL_SECONDS
        face_slot += 1
    return frames


def group_breakaway_sequence_for_row(
    row: dict[str, object], time_value: float, face_slot: int, interval_end: float, platform: str, hard_cut: bool
) -> list[dict[str, object]]:
    faces = sorted(reliable_faces(row), key=face_x)
    if len(faces) < 2:
        return []
    primary = primary_breakaway_face(row, faces, face_slot)
    reaction = secondary_breakaway_face(row, primary, faces)
    reaction_time = time_value + CAMERA_GROUP_SPEAKER_HOLD_SECONDS
    return_time = reaction_time + CAMERA_GROUP_REACTION_HOLD_SECONDS
    if reaction is None or return_time >= interval_end:
        return group_speaker_only_breakaway(row, primary, time_value, interval_end, platform, hard_cut)
    return [
        group_breakaway_speaker_frame(primary, time_value, hard_cut),
        group_breakaway_reaction_frame(reaction, reaction_time, hard_cut),
        group_breakaway_return_frame(row, return_time, platform, hard_cut),
    ]


def group_speaker_only_breakaway(
    row: dict[str, object],
    primary: dict[str, float],
    time_value: float,
    interval_end: float,
    platform: str,
    hard_cut: bool,
) -> list[dict[str, object]]:
    return_time = time_value + CAMERA_GROUP_SPEAKER_HOLD_SECONDS
    if return_time >= interval_end:
        return []
    return [
        group_breakaway_speaker_frame(primary, time_value, hard_cut),
        group_breakaway_return_frame(row, return_time, platform, hard_cut),
    ]


def group_breakaway_speaker_frame(face: dict[str, float], time_value: float, hard_cut: bool) -> dict[str, object]:
    frame = {**normalized_focus_face(face), "time": time_value, "zoom": speaker_focus_zoom(face, 0.0), "intent": "speaker_hold"}
    source = "ai-director-cuts-group-speaker" if hard_cut else "ai-director-dynamic-group-speaker"
    return hard_cut_ai_director_frame(frame, time_value, source)


def group_breakaway_reaction_frame(face: dict[str, float], time_value: float, hard_cut: bool) -> dict[str, object]:
    frame = {**normalized_focus_face(face), "time": time_value, "zoom": reaction_focus_zoom(face), "intent": "reaction_focus"}
    source = "ai-director-cuts-group-reaction" if hard_cut else "ai-director-dynamic-group-reaction"
    return hard_cut_ai_director_frame(frame, time_value, source)


def group_breakaway_return_frame(row: dict[str, object], time_value: float, platform: str, hard_cut: bool) -> dict[str, object]:
    faces = sorted(reliable_faces(row), key=face_x)
    frame = group_face_frame(faces, time_value, platform)
    frame["intent"] = "group_open"
    source = "ai-director-cuts-group-return" if hard_cut else "ai-director-dynamic-group"
    return hard_cut_ai_director_frame(frame, time_value, source)


def fit_breakaway_camera_frames(
    frames: list[dict[str, object]],
    detections: list[dict[str, object]],
    duration: float,
    hard_cut: bool = True,
) -> list[dict[str, object]]:
    if not frames or not detections:
        return []
    result: list[dict[str, object]] = []
    for start, end in coalesced_fit_intervals(frames, duration):
        if end - start < CAMERA_FIT_BREAKAWAY_MIN_SECONDS:
            continue
        result.extend(fit_breakaways_for_interval(start, end, detections, hard_cut))
    return result


def coalesced_fit_intervals(frames: list[dict[str, object]], duration: float) -> list[tuple[float, float]]:
    intervals: list[tuple[float, float]] = []
    current_start: float | None = None
    current_end = 0.0
    for start, end, frame in camera_path_bounds_from_frames(frames, duration):
        if camera_path_frame_uses_group_fit(frame):
            if current_start is None:
                current_start = start
            current_end = end
            continue
        if current_start is not None:
            intervals.append((current_start, current_end))
            current_start = None
    if current_start is not None:
        intervals.append((current_start, current_end))
    return intervals


def camera_path_bounds_from_frames(
    frames: list[dict[str, object]], duration: float
) -> list[tuple[float, float, dict[str, object]]]:
    safe_duration = max(duration, 0.3)
    ordered = sorted(frames, key=lambda item: float(item.get("time") or 0.0))
    if not ordered:
        return []
    if float(ordered[0].get("time") or 0.0) > 0.001:
        ordered.insert(0, {**ordered[0], "time": 0.0})
    bounds: list[tuple[float, float, dict[str, object]]] = []
    for index, frame in enumerate(ordered):
        start = clamp(float(frame.get("time") or 0.0), 0.0, safe_duration)
        end = safe_duration
        if index + 1 < len(ordered):
            end = clamp(float(ordered[index + 1].get("time") or safe_duration), start + 0.001, safe_duration)
        if end > start:
            bounds.append((start, end, frame))
    return bounds


def fit_breakaways_for_interval(
    start: float,
    end: float,
    detections: list[dict[str, object]],
    hard_cut: bool,
) -> list[dict[str, object]]:
    rows = reliable_detection_rows_between(detections, start, end)
    if not rows:
        return []
    frames: list[dict[str, object]] = []
    cursor = start + CAMERA_FIT_BREAKAWAY_LEAD_SECONDS
    face_slot = 0
    max_frames = CAMERA_FIT_BREAKAWAY_MAX_PER_BLOCK * 3
    while cursor + CAMERA_FIT_BREAKAWAY_PRIMARY_HOLD_SECONDS < end and len(frames) < max_frames:
        row = next_breakaway_row(rows, cursor)
        if row is None:
            break
        time_value = max(cursor, float(row.get("time") or cursor))
        sequence = fit_breakaway_sequence_for_row(row, time_value, face_slot, end, hard_cut)
        if not sequence:
            cursor += CAMERA_FIT_BREAKAWAY_INTERVAL_SECONDS
            continue
        frames.extend(sequence)
        cursor = float(sequence[-1].get("time") or time_value) + CAMERA_FIT_BREAKAWAY_INTERVAL_SECONDS
        face_slot += 1
    return frames


def reliable_detection_rows_between(
    detections: list[dict[str, object]], start: float, end: float
) -> list[dict[str, object]]:
    return [
        row
        for row in sorted(detections, key=lambda item: float(item.get("time") or 0.0))
        if start <= float(row.get("time") or 0.0) <= end and reliable_faces(row)
    ]


def next_breakaway_row(rows: list[dict[str, object]], time_value: float) -> dict[str, object] | None:
    return min(rows, key=lambda row: abs(float(row.get("time") or 0.0) - time_value))


def fit_breakaway_sequence_for_row(
    row: dict[str, object], time_value: float, face_slot: int, interval_end: float, hard_cut: bool
) -> list[dict[str, object]]:
    faces = sorted(reliable_faces(row), key=face_x)
    if not faces:
        return []
    primary = primary_breakaway_face(row, faces, face_slot)
    secondary = secondary_breakaway_face(row, primary, faces)
    secondary_time = time_value + CAMERA_FIT_BREAKAWAY_PRIMARY_HOLD_SECONDS
    if secondary and secondary_time + CAMERA_FIT_BREAKAWAY_SECONDARY_HOLD_SECONDS < interval_end:
        return [
            fit_breakaway_face_frame(primary, time_value, fit_breakaway_source("primary", hard_cut)),
            fit_breakaway_face_frame(secondary, secondary_time, fit_breakaway_source("secondary", hard_cut)),
            fit_breakaway_return_frame(secondary_time + CAMERA_FIT_BREAKAWAY_SECONDARY_HOLD_SECONDS, hard_cut),
        ]
    return_time = time_value + CAMERA_FIT_BREAKAWAY_PRIMARY_HOLD_SECONDS
    if return_time >= interval_end:
        return []
    return [
        fit_breakaway_face_frame(primary, time_value, fit_breakaway_source("primary", hard_cut)),
        fit_breakaway_return_frame(return_time, hard_cut),
    ]


def fit_breakaway_source(slot: str, hard_cut: bool) -> str:
    if hard_cut:
        return f"ai-director-cuts-fit-{slot}"
    return "ai-director-dynamic-reaction" if slot == "secondary" else "ai-director-dynamic-speaker"


def primary_breakaway_face(
    row: dict[str, object], faces: list[dict[str, float]], face_slot: int
) -> dict[str, float]:
    primary = primary_reliable_face(row)
    if primary is not None and face_slot % max(len(faces), 1) == 0:
        return primary
    return faces[face_slot % len(faces)]


def secondary_breakaway_face(
    row: dict[str, object], primary: dict[str, float], faces: list[dict[str, float]]
) -> dict[str, float] | None:
    secondary = secondary_speaker_face_for_row(row)
    if secondary is not None:
        return secondary
    candidates = [face for face in focusable_speaker_faces(row) if abs(face_x(face) - face_x(primary)) >= 8.0]
    if not candidates:
        return None
    return max(candidates, key=lambda face: abs(face_x(face) - face_x(primary)))


def fit_breakaway_face_frame(face: dict[str, float], time_value: float, source: str) -> dict[str, object]:
    zoom = reaction_focus_zoom(face) if "secondary" in source else speaker_focus_zoom(face, 0.02)
    frame = {**face, "time": time_value, "zoom": zoom}
    return hard_cut_ai_director_frame(frame, time_value, source)


def fit_breakaway_return_frame(time_value: float, hard_cut: bool = True) -> dict[str, object]:
    source = "ai-director-cuts-fit-return" if hard_cut else "ai-director-dynamic-group"
    return hard_cut_ai_director_frame(
        open_center_camera_frame(time_value),
        time_value,
        source,
    )


def stabilize_ai_director_path(frames: list[dict[str, object]], duration: float, hard_cut: bool) -> list[dict[str, object]]:
    if hard_cut:
        return frames
    held = enforce_minimum_camera_holds(frames, duration, AI_DIRECTOR_MIN_MOVE_HOLD_SECONDS)
    return enforce_group_fit_holds(held, duration, GROUP_FIT_MIN_HOLD_SECONDS)


def enforce_minimum_camera_holds(
    frames: list[dict[str, object]], duration: float, min_hold: float
) -> list[dict[str, object]]:
    if len(frames) <= 1:
        return frames
    safe_duration = max(duration, 0.3)
    result = [frames[0]]
    for frame in frames[1:]:
        time_value = clamp(float(frame.get("time") or 0.0), 0.0, safe_duration)
        previous_time = float(result[-1].get("time") or 0.0)
        if time_value - previous_time < min_hold and not camera_path_frame_uses_group_fit(frame):
            if previous_time > 0.001 and camera_frame_priority(frame) > camera_frame_priority(result[-1]):
                result[-1] = {**frame, "time": round(previous_time, 3)}
            continue
        result.append({**frame, "time": round(time_value, 3)})
    return result


def enforce_group_fit_holds(
    frames: list[dict[str, object]], duration: float, min_hold: float
) -> list[dict[str, object]]:
    if len(frames) <= 1:
        return frames
    safe_duration = max(duration, 0.3)
    result: list[dict[str, object]] = []
    for frame in sorted(frames, key=lambda item: float(item.get("time") or 0.0)):
        time_value = clamp(float(frame.get("time") or 0.0), 0.0, safe_duration)
        if result and camera_path_frame_uses_group_fit(result[-1]) and time_value - float(result[-1].get("time") or 0.0) < min_hold:
            continue
        result.append({**frame, "time": round(time_value, 3)})
    return result


def dense_camera_risk_frames(
    frames: list[dict[str, object]], detections: list[dict[str, object]], duration: float, platform: str, mode: str
) -> list[dict[str, object]]:
    mandatory: list[dict[str, object]] = []
    hard_cut = ai_director_uses_hard_cuts(mode)
    min_gap = 1.25 if hard_cut else 0.85
    for row in detections:
        time_value = float(row.get("time") or 0.0)
        if time_value > max(duration, 0.3):
            continue
        active = camera_path_frame_at_time(frames, time_value)
        target = dense_camera_target_for_row(row, active, platform, hard_cut)
        if target is None or recent_similar_camera_frame(mandatory, target, min_gap):
            continue
        mandatory.append(target)
    return mandatory


def dense_camera_target_for_row(
    row: dict[str, object], active: dict[str, object], platform: str, hard_cut: bool
) -> dict[str, object] | None:
    faces = sorted(reliable_faces(row), key=face_x)
    if not faces:
        return None
    time_value = float(row.get("time") or 0.0)
    scene_intent = str(camera_scene_intent_for_faces(faces, platform)["intent"])
    if scene_intent == "group_fit":
        return forced_group_fit_frame(faces, time_value, platform, hard_cut)
    if scene_intent in {"two_far_cut", "group_close_alternate"}:
        return None
    group_required = should_use_platform_group_frame(faces, platform)
    active_cuts = camera_frame_cuts_faces(active, faces)
    if active_cuts or (group_required and not camera_frame_is_group_safe(active)):
        group = group_face_frame(faces, time_value, platform)
        return hard_cut_ai_director_frame(group, time_value, group_frame_source(group, hard_cut))
    primary = primary_speaker_face_for_row(row)
    if isinstance(primary, dict) and not group_required and dense_primary_focus_is_needed(active, primary):
        primary_source = "ai-director-cuts-primary" if hard_cut else "ai-director-dense-primary"
        return hard_cut_ai_director_frame(
            {**primary, "time": time_value, "zoom": speaker_focus_zoom(primary, 0.02)},
            time_value,
            primary_source,
        )
    return None


def dense_primary_focus_is_needed(active: dict[str, object], primary: dict[str, object]) -> bool:
    if dynamic_focus_frame_is_unsafe(active):
        return True
    if camera_frame_is_open_center(active):
        return True
    return abs(float(active.get("x") or 50.0) - face_x(primary)) >= CAMERA_MIN_TARGET_SHIFT


def scene_grammar_camera_frames(
    detections: list[dict[str, object]], duration: float, platform: str, hard_cut: bool
) -> list[dict[str, object]]:
    frames: list[dict[str, object]] = []
    last_time = -999.0
    last_intent = ""
    for row in detections:
        time_value = float(row.get("time") or 0.0)
        intent = str(camera_scene_intent_for_row(row, platform)["intent"])
        if scene_grammar_should_wait(time_value, duration, intent, last_time, last_intent):
            continue
        target = scene_grammar_target_for_row(row, time_value, platform, hard_cut, intent)
        if target is None or scene_target_too_small(frames, target):
            continue
        frames.append(target)
        last_time = time_value
        last_intent = intent
    return frames


def scene_grammar_should_wait(
    time_value: float, duration: float, intent: str, last_time: float, last_intent: str
) -> bool:
    if time_value > max(duration, 0.3):
        return True
    if intent != "group_fit" and time_value < CAMERA_SCENE_FIRST_CUT_SECONDS:
        return True
    return time_value - last_time < camera_scene_min_hold(intent, last_intent)


def scene_grammar_target_for_row(
    row: dict[str, object], time_value: float, platform: str, hard_cut: bool, intent: str | None = None
) -> dict[str, object] | None:
    faces = sorted(reliable_faces(row), key=face_x)
    intent = intent or str(camera_scene_intent_for_faces(faces, platform)["intent"])
    if intent == "group_fit":
        return forced_group_fit_frame(faces, time_value, platform, hard_cut)
    if intent not in {"two_far_cut", "group_close_alternate"}:
        return None
    source = "ai-director-cuts-reaction" if hard_cut else "ai-director-dense-reaction"
    return hard_cut_ai_director_frame(director_alternate_target(row, time_value, intent), time_value, source)


def scene_target_too_small(frames: list[dict[str, object]], target: dict[str, object]) -> bool:
    if not frames:
        return False
    previous = frames[-1]
    return abs(float(previous.get("x") or 50.0) - float(target.get("x") or 50.0)) < CAMERA_MIN_TARGET_SHIFT


def camera_scene_min_hold(intent: str, previous_intent: str) -> float:
    if intent == "group_fit":
        return 0.8
    if intent == "two_far_cut":
        return CAMERA_HARD_CUT_MIN_HOLD_SECONDS
    if intent == "group_close_alternate":
        return CAMERA_GROUP_ALTERNATE_MIN_HOLD_SECONDS
    if previous_intent == "two_far_cut":
        return CAMERA_HARD_CUT_MIN_HOLD_SECONDS
    return 2.8


def forced_group_fit_camera_frames(
    frames: list[dict[str, object]],
    detections: list[dict[str, object]],
    duration: float,
    platform: str,
    hard_cut: bool,
) -> list[dict[str, object]]:
    forced: list[dict[str, object]] = []
    for row in risky_group_detection_rows(frames, detections, duration, platform):
        faces = sorted(reliable_faces(row), key=face_x)
        time_value = float(row.get("time") or 0.0)
        target = forced_group_fit_frame(faces, time_value, platform, hard_cut)
        if not recent_similar_camera_frame(forced, target, 0.7):
            forced.append(target)
    return forced


def uncertain_center_camera_frames(
    frames: list[dict[str, object]], detections: list[dict[str, object]], duration: float, hard_cut: bool
) -> list[dict[str, object]]:
    forced: list[dict[str, object]] = []
    source = "ai-director-cuts-uncertain-fit" if hard_cut else "ai-director-uncertain-fit"
    low_confidence = low_confidence_camera_scene(detections)
    for window in detection_uncertainty_windows(detections, duration):
        for time_value in uncertainty_fit_times(window, low_confidence):
            active = camera_path_frame_at_time(frames, time_value)
            if camera_frame_is_open_center(active) and not low_confidence:
                continue
            target = hard_cut_ai_director_frame(open_center_camera_frame(time_value), time_value, source)
            if not recent_similar_camera_frame(forced, target, 1.1):
                forced.append(target)
    return forced


def low_confidence_camera_scene(detections: list[dict[str, object]]) -> bool:
    sample_count = max(len(detections), 1)
    detected = detection_frame_count(detections)
    if detected <= 0:
        return True
    edge_ratio = sum(1 for row in detections if row_has_edge_face(row)) / max(detected, 1)
    detection_rate = detected / sample_count
    return (
        sample_count >= 8
        and detection_rate <= CAMERA_LOW_CONFIDENCE_DETECTION_RATE
        and edge_ratio >= CAMERA_LOW_CONFIDENCE_EDGE_RATIO
    )


def uncertainty_fit_times(window: dict[str, object], low_confidence: bool) -> list[float]:
    start = float(window.get("start") or 0.0)
    end = float(window.get("end") or start)
    if not low_confidence:
        return [start]
    times = [start]
    next_time = start + CAMERA_LOW_CONFIDENCE_FIT_INTERVAL
    while next_time < end - 0.5:
        times.append(round(next_time, 3))
        next_time += CAMERA_LOW_CONFIDENCE_FIT_INTERVAL
    return times


def camera_frame_is_open_center(frame: dict[str, object]) -> bool:
    return camera_path_frame_uses_group_fit(frame) or (
        abs(float(frame.get("x") or 50.0) - 50.0) <= 4.0 and float(frame.get("zoom") or 1.0) <= 1.06
    )


def open_center_camera_frame(time_value: float) -> dict[str, object]:
    return {"time": round(time_value, 3), "x": 50.0, "y": 50.0, "zoom": 1.0, "confidence": 0.55, "fit": "contain"}


def risky_group_detection_rows(
    frames: list[dict[str, object]],
    detections: list[dict[str, object]],
    duration: float,
    platform: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    safe_duration = max(duration, 0.3)
    for row in detections:
        time_value = float(row.get("time") or 0.0)
        faces = sorted(reliable_faces(row), key=face_x)
        if len(faces) < 2:
            continue
        active = camera_path_frame_at_time(frames, time_value)
        if camera_path_frame_uses_group_fit(active):
            continue
        if camera_frame_cuts_faces(active, faces) or is_final_section_group_risk(
            faces, time_value, safe_duration, platform
        ):
            rows.append(row)
    return rows


def is_final_section_group_risk(
    faces: list[dict[str, float]], time_value: float, duration: float, platform: str
) -> bool:
    final_window = max(duration - 5.0, duration * 0.82)
    if time_value < final_window:
        return False
    return should_use_platform_group_frame(faces, platform) or any(face_outside_safe_zone(face) for face in faces)


def forced_group_fit_frame(
    faces: list[dict[str, float]],
    time_value: float,
    platform: str,
    hard_cut: bool,
) -> dict[str, object]:
    frame: dict[str, object] = group_face_frame(faces, time_value, platform)
    frame["fit"] = "contain"
    return hard_cut_ai_director_frame(frame, time_value, group_frame_source(frame, hard_cut))


def camera_path_frame_at_time(frames: list[dict[str, object]], time_value: float) -> dict[str, object]:
    ordered = sorted(frames, key=lambda item: float(item.get("time") or 0.0))
    active = ordered[0]
    for frame in ordered:
        if float(frame.get("time") or 0.0) > time_value:
            break
        active = frame
    return active


def recent_similar_camera_frame(frames: list[dict[str, object]], target: dict[str, object], min_gap: float) -> bool:
    if not frames:
        return False
    previous = frames[-1]
    time_gap = float(target.get("time") or 0.0) - float(previous.get("time") or 0.0)
    return time_gap < min_gap and camera_frames_are_similar(previous, target)


def merge_camera_path_frames(
    frames: list[dict[str, object]], mandatory: list[dict[str, object]], duration: float
) -> list[dict[str, object]]:
    merged = sorted([*frames, *mandatory], key=lambda item: float(item.get("time") or 0.0))
    result: list[dict[str, object]] = []
    for frame in merged:
        time_value = clamp(float(frame.get("time") or 0.0), 0.0, max(duration, 0.3))
        candidate = {**frame, "time": round(time_value, 3)}
        if result and abs(time_value - float(result[-1].get("time") or 0.0)) < 0.45:
            if camera_frame_priority(candidate) >= camera_frame_priority(result[-1]):
                result[-1] = candidate
            continue
        result.append(candidate)
    return result


def camera_frame_priority(frame: dict[str, object]) -> int:
    source = str(frame.get("source") or "")
    if "group-speaker" in source or "group-reaction" in source:
        return 5
    if "fit-close" in source or "fit-primary" in source or "fit-secondary" in source:
        return 5
    if camera_path_frame_uses_group_fit(frame):
        return 4
    if "group-fit" in source:
        return 4
    if "group-safe" in source:
        return 3
    if "uncertain" in source:
        return 2
    if "dense" in source or "cuts-primary" in source or "cuts-reaction" in source:
        return 2
    return 1


def camera_frame_is_group_safe(frame: dict[str, object]) -> bool:
    source = str(frame.get("source") or "")
    return camera_path_frame_uses_group_fit(frame) or "group-safe" in source or "group-fit" in source


def cinematic_cut_scene_path(detections: list[dict[str, object]], duration: float, platform: str) -> list[dict[str, object]]:
    rows = [row for row in detections if reliable_faces(row)]
    if not rows:
        return []
    safe_duration = max(duration, 0.3)
    frames = [cinematic_primary_frame(rows[0], 0.0, platform)]
    last_return = 0.0
    for row in rows:
        time_value = float(row.get("time") or 0.0)
        if time_value < 1.6 or time_value - last_return < 2.8:
            continue
        target = cinematic_reaction_frame(row, time_value, platform)
        if target is None or camera_frames_are_similar(frames[-1], target):
            continue
        frames.append(target)
        return_time = min(time_value + 2.6, safe_duration)
        if return_time - time_value >= 1.2:
            frames.append(cinematic_primary_frame(nearest_scene_row(return_time, rows), return_time, platform))
            last_return = return_time
        if len(frames) >= 13:
            break
    return frames if len(frames) > 1 else []


def cinematic_reaction_frame(row: dict[str, object], time_value: float, platform: str) -> dict[str, object] | None:
    faces = sorted(reliable_faces(row), key=face_x)
    scene_intent = str(camera_scene_intent_for_faces(faces, platform)["intent"])
    if scene_intent == "group_fit":
        group = group_face_frame(faces, time_value, platform)
        return hard_cut_ai_director_frame(group, time_value, group_frame_source(group, True))
    secondary = secondary_speaker_face_for_row(row)
    if secondary is None:
        if should_use_platform_group_frame(faces, platform):
            group = group_face_frame(faces, time_value, platform)
            return hard_cut_ai_director_frame(group, time_value, group_frame_source(group, True))
        return None
    return hard_cut_ai_director_frame({
        **secondary,
        "time": time_value,
        "zoom": reaction_focus_zoom(secondary),
    }, time_value, "ai-director-cuts-reaction")


def cinematic_primary_frame(row: dict[str, object], time_value: float, platform: str) -> dict[str, object]:
    faces = sorted(reliable_faces(row), key=face_x)
    if str(camera_scene_intent_for_faces(faces, platform)["intent"]) == "group_fit":
        group = group_face_frame(faces, time_value, platform)
        return hard_cut_ai_director_frame(group, time_value, group_frame_source(group, True))
    source = primary_speaker_face_for_row(row) or (faces[0] if faces else {})
    return hard_cut_ai_director_frame(
        {**source, "time": time_value, "zoom": speaker_focus_zoom(source, 0.02)},
        time_value,
        "ai-director-cuts-primary",
    )


def secondary_face_for_row(row: dict[str, object]) -> dict[str, float] | None:
    primary = primary_speaker_face_for_row(row)
    if primary is None:
        return None
    primary_x = face_x(primary)
    candidates = [face for face in focusable_speaker_faces(row) if abs(face_x(face) - primary_x) >= 9.0]
    if not candidates:
        return None
    return max(candidates, key=lambda face: float(face.get("confidence") or 0.0) * max(float(face.get("area") or 1.0), 1.0))


def nearest_scene_row(time_value: float, rows: list[dict[str, object]]) -> dict[str, object]:
    return min(rows, key=lambda row: abs(float(row.get("time") or 0.0) - time_value))


def camera_frames_are_similar(first: dict[str, object], second: dict[str, object]) -> bool:
    return (
        abs(float(first.get("x") or 50.0) - float(second.get("x") or 50.0)) < 7.0
        and abs(float(first.get("zoom") or 1.0) - float(second.get("zoom") or 1.0)) < 0.035
    )


def hard_cut_ai_director_frame(
    frame: dict[str, object], time_value: float, source_override: str | None = None
) -> dict[str, object]:
    source = str(frame.get("source") or "ai-director")
    next_source = source_override or ("ai-director-cuts-group-safe" if source == "ai-director-group-safe" else "ai-director-cuts")
    return {
        **frame,
        "time": round(time_value, 3),
        "x": round(float(frame.get("x") or 50.0), 2),
        "y": round(float(frame.get("y") or 50.0), 2),
        "zoom": round(float(frame.get("zoom") or 1.0), 3),
        "source": next_source,
    }


def protected_ai_director_frame(frame: dict[str, object], detections: list[dict[str, object]], platform: str) -> dict[str, object]:
    time_value = float(frame.get("time") or 0.0)
    nearest = nearest_detection(time_value, detections)
    if nearest is None:
        return frame
    faces = sorted(reliable_faces(nearest), key=lambda item: face_x(item))
    if not faces or not ai_frame_needs_group_protection(frame, faces, platform):
        return frame
    group = group_face_frame(faces, time_value, platform)
    source = "ai-director-group-fit" if camera_path_frame_uses_group_fit(group) else "ai-director-group-safe"
    protected = {
        **frame,
        "x": round(float(group["x"]), 2),
        "y": round(float(group["y"]), 2),
        "zoom": round(min(float(frame.get("zoom") or 1.0), float(group["zoom"])), 3),
        "source": source,
        "confidence": max(float(frame.get("confidence") or 0.72), float(group.get("confidence") or 0.72)),
    }
    if camera_path_frame_uses_group_fit(group):
        protected["fit"] = "contain"
    else:
        protected.pop("fit", None)
    return protected


def nearest_detection(time_value: float, detections: list[dict[str, object]]) -> dict[str, object] | None:
    candidates = [row for row in detections if reliable_faces(row)]
    if not candidates:
        return None
    nearest = min(candidates, key=lambda row: abs(float(row.get("time") or 0.0) - time_value))
    return nearest if abs(float(nearest.get("time") or 0.0) - time_value) <= 2.6 else None


def ai_frame_needs_group_protection(frame: dict[str, object], faces: list[dict[str, float]], platform: str) -> bool:
    if len(faces) >= 3:
        return True
    if len(faces) < 2:
        return False
    return should_use_platform_group_frame(faces, platform) or camera_frame_cuts_faces(frame, faces)


def camera_frame_cuts_faces(frame: dict[str, object], faces: list[dict[str, float]]) -> bool:
    if camera_path_frame_uses_group_fit(frame):
        return False
    center = clamp(float(frame.get("x") or 50.0), 0.0, 100.0)
    zoom = clamp(float(frame.get("zoom") or 1.0), 1.0, 1.45)
    half_width = max(24.0, 50.0 / zoom)
    left = center - half_width + 5.0
    right = center + half_width - 5.0
    return any(face_left_edge(face) < left or face_right_edge(face) > right for face in faces)


def ai_director_frame_from_row(row: dict[str, object], duration: float) -> dict[str, float] | None:
    try:
        time_value = clamp(float(row.get("time") or 0.0), 0.0, max(duration, 0.3))
        return {
            "time": round(time_value, 3),
            "x": round(clamp(float(row.get("x") or 50.0), 12.0, 88.0), 2),
            "y": round(clamp(float(row.get("y") or 50.0), 35.0, 65.0), 2),
            "zoom": round(clamp(float(row.get("zoom") or 1.0), 1.0, 1.45), 3),
            "source": "ai-director",
            "confidence": 0.72,
        }
    except (TypeError, ValueError):
        return None


def auto_director_camera_path(detections: list[dict[str, object]], primary: list[dict[str, float]], duration: float) -> list[dict[str, object]]:
    if has_reliable_multi_face_context(detections):
        path = director_multi_face_path(detections, duration)
        if path:
            return path
    return primary_face_camera_path(primary, "auto-face-auto-director", duration)


def primary_face_camera_path(detections: list[dict[str, float]], source: str, duration: float) -> list[dict[str, object]]:
    frames = smoothed_camera_frames(detections, source, x_weight=0.48, y_weight=0.32, zoom_weight=0.28)
    return compressed_camera_path(frames, duration, max_gap=2.1, x_threshold=2.0, zoom_threshold=0.016)


def follow_face_camera_path(detections: list[dict[str, object]], primary: list[dict[str, float]], duration: float) -> list[dict[str, object]]:
    if not has_reliable_multi_face_context(detections):
        return primary_face_camera_path(primary, "auto-face-follow-face", duration)
    frames = safe_follow_frames(detections)
    if not frames:
        return primary_face_camera_path(primary, "auto-face-follow-face", duration)
    rows = smoothed_camera_frames(frames, "auto-face-follow-face", x_weight=0.54, y_weight=0.36, zoom_weight=0.32)
    path = compressed_camera_path(rows, duration, max_gap=1.9, x_threshold=1.9, zoom_threshold=0.015)
    return stable_camera_targets(path)


def safe_follow_frames(detections: list[dict[str, object]]) -> list[dict[str, float]]:
    frames: list[dict[str, float]] = []
    for row in detections:
        time_value = float(row.get("time") or 0.0)
        faces = sorted(reliable_faces(row), key=lambda item: face_x(item))
        primary = row.get("primary") if isinstance(row.get("primary"), dict) else None
        intent = str(camera_scene_intent_for_faces(faces, "tiktok")["intent"])
        if intent == "group_fit":
            frames.append(group_face_frame(faces, time_value))
        elif isinstance(primary, dict):
            frames.append({**primary, "time": time_value})
    return frames


def has_reliable_multi_face_context(detections: list[dict[str, object]]) -> bool:
    multi_frames = [row for row in detections if len(reliable_faces(row)) >= 2]
    return len(multi_frames) >= max(3, int(len(detections) * 0.2))


def reliable_faces(row: dict[str, object]) -> list[dict[str, float]]:
    faces = row.get("faces")
    if not isinstance(faces, list):
        return []
    return [face for face in faces if isinstance(face, dict) and float(face.get("confidence") or 0.0) >= 0.35]


def reliable_opencv_faces(row: dict[str, object]) -> list[dict[str, float]]:
    faces = row.get("opencv_faces")
    if isinstance(faces, list):
        return [face for face in faces if isinstance(face, dict) and float(face.get("confidence") or 0.0) >= 0.35]
    return [face for face in reliable_faces(row) if str(face.get("kind") or "face") != "person"]


def reliable_persons(row: dict[str, object]) -> list[dict[str, float]]:
    persons = row.get("persons")
    if isinstance(persons, list):
        return [person for person in persons if isinstance(person, dict) and float(person.get("confidence") or 0.0) >= 0.35]
    return [face for face in reliable_faces(row) if str(face.get("kind") or "") == "person"]


def director_multi_face_path(detections: list[dict[str, object]], duration: float) -> list[dict[str, object]]:
    frames: list[dict[str, float]] = []
    last_reaction = -999.0
    for row in detections:
        time_value = float(row.get("time") or 0.0)
        faces = sorted(reliable_faces(row), key=lambda item: float(item.get("x") or 50.0))
        target = row.get("primary") if isinstance(row.get("primary"), dict) else None
        intent = str(camera_scene_intent_for_faces(faces, "tiktok")["intent"])
        if intent == "group_fit":
            frames.append(group_face_frame(faces, time_value))
            last_reaction = time_value
        elif len(faces) >= 2 and time_value - last_reaction >= 3.0:
            frames.append(director_alternate_target(row, time_value, intent))
            last_reaction = time_value
        elif isinstance(target, dict):
            frames.append({**target, "time": time_value})
    if len(frames) < 2:
        return []
    rows = smoothed_camera_frames(frames, "auto-face-auto-director", x_weight=0.58, y_weight=0.38, zoom_weight=0.34)
    path = compressed_camera_path(rows, duration, max_gap=1.8, x_threshold=1.8, zoom_threshold=0.014)
    return stable_camera_targets(path)


def director_alternate_target(row: dict[str, object], time_value: float, intent: str) -> dict[str, float]:
    faces = sorted(reliable_faces(row), key=face_x)
    secondary = secondary_face_for_row(row)
    target = secondary if secondary is not None else (faces[-1] if faces else {})
    return {**target, "time": time_value, "zoom": reaction_focus_zoom(target)}


def should_use_group_frame(faces: list[dict[str, float]]) -> bool:
    if len(faces) < 2:
        return False
    spread = face_x(faces[-1]) - face_x(faces[0])
    return spread >= 24.0 or any(face_outside_safe_zone(face) for face in faces)


def should_use_platform_group_frame(faces: list[dict[str, float]], platform: str) -> bool:
    if len(faces) < 2:
        return False
    spread = face_x(faces[-1]) - face_x(faces[0])
    preset = PLATFORM_PRESETS.get(platform, PLATFORM_PRESETS["tiktok"])
    aspect = preset.width / max(preset.height, 1)
    if len(faces) >= 3:
        return True
    if aspect < 0.65:
        return spread >= 20.0 or any(face_outside_safe_zone(face) for face in faces)
    if aspect < 0.95:
        return spread >= 28.0 or any(face_outside_safe_zone(face) for face in faces)
    return spread >= 34.0 or any(face_outside_safe_zone(face) for face in faces)


def group_face_frame(faces: list[dict[str, float]], time_value: float, platform: str | None = None) -> dict[str, float]:
    left = faces[0]
    right = faces[-1]
    confidence = max(float(left.get("confidence") or 0.35), float(right.get("confidence") or 0.35))
    spread = max(face_x(right) - face_x(left), 0.0)
    min_x, max_x = platform_group_x_bounds(platform)
    frame = {
        "time": time_value,
        "x": clamp((face_x(left) + face_x(right)) / 2.0, min_x, max_x),
        "y": clamp((float(left.get("y") or 50.0) + float(right.get("y") or 50.0)) / 2.0, 38.0, 62.0),
        "zoom": group_face_zoom(spread, len(faces), platform),
        "confidence": confidence,
    }
    if should_use_group_fit_frame(faces, platform):
        frame["fit"] = "contain"
    return frame


def platform_group_x_bounds(platform: str | None) -> tuple[float, float]:
    if platform == "youtube":
        return (8.0, 92.0)
    if platform == "facebook":
        return (14.0, 86.0)
    return (16.0, 84.0)


def group_face_zoom(spread: float, face_count: int = 2, platform: str | None = None) -> float:
    if spread >= 42.0:
        base = 1.0
    elif spread >= 30.0:
        base = 1.03
    else:
        base = 1.07
    preset = PLATFORM_PRESETS.get(platform or "", PLATFORM_PRESETS["tiktok"])
    aspect = preset.width / max(preset.height, 1)
    if aspect < 0.65 and face_count >= 3:
        return min(base, 1.0)
    if aspect < 0.65:
        return min(base, 1.0)
    if aspect < 0.95 and face_count >= 3:
        return min(base, 1.02)
    if aspect >= 1.0 and face_count >= 2:
        return min(base, 1.0)
    return base


def should_use_group_fit_frame(faces: list[dict[str, float]], platform: str | None) -> bool:
    if len(faces) < 2:
        return False
    preset = PLATFORM_PRESETS.get(platform or "", PLATFORM_PRESETS["tiktok"])
    aspect = preset.width / max(preset.height, 1)
    if aspect >= 0.95:
        return False
    sorted_faces = sorted(faces, key=face_x)
    spread = face_x(sorted_faces[-1]) - face_x(sorted_faces[0])
    face_span = face_right_edge(sorted_faces[-1]) - face_left_edge(sorted_faces[0])
    both_edges = face_left_edge(sorted_faces[0]) <= 24.0 and face_right_edge(sorted_faces[-1]) >= 76.0
    if aspect < 0.65:
        has_edge = any(face_outside_safe_zone(face) for face in sorted_faces)
        many_spread = len(sorted_faces) >= 4 and face_span >= CAMERA_GROUP_FIT_SPAN - 6.0
        return spread >= CAMERA_GROUP_FIT_SPREAD or face_span >= CAMERA_GROUP_FIT_SPAN or both_edges or many_spread or (has_edge and spread >= 30.0)
    many_spread = len(sorted_faces) >= 3 and face_span >= 48.0
    return many_spread or both_edges


def group_frame_source(frame: dict[str, object], hard_cut: bool) -> str:
    if camera_path_frame_uses_group_fit(frame):
        return "ai-director-cuts-group-fit" if hard_cut else "ai-director-group-fit"
    return "ai-director-cuts-group-safe" if hard_cut else "ai-director-group-safe"


def boost_face_zoom(detections: list[dict[str, float]]) -> list[dict[str, float]]:
    return [{**row, "zoom": min(float(row.get("zoom") or 1.0) + 0.12, 1.45)} for row in detections]


def stable_face_camera_path(detections: list[dict[str, float]]) -> list[dict[str, object]]:
    x_values = sorted(float(item["x"]) for item in detections)
    y_values = sorted(float(item["y"]) for item in detections)
    zoom_values = sorted(float(item["zoom"]) for item in detections)
    confidence = sum(float(item.get("confidence") or 0.0) for item in detections) / max(len(detections), 1)
    return [{
        "time": 0.0,
        "x": round(median_value(x_values), 2),
        "y": round(median_value(y_values), 2),
        "zoom": round(median_value(zoom_values), 3),
        "source": "auto-face-stable-face",
        "confidence": round(confidence, 3),
    }]


def median_value(values: list[float]) -> float:
    if not values:
        return 50.0
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2.0


def multi_face_camera_path(detections: list[dict[str, object]], duration: float, smooth: bool) -> list[dict[str, object]]:
    frames: list[dict[str, float]] = []
    use_left = True
    last_switch = -999.0
    interval = 2.4 if smooth else 1.6
    for row in detections:
        faces = row.get("faces")
        if not isinstance(faces, list) or len(faces) < 2:
            continue
        time_value = float(row.get("time") or 0.0)
        if time_value - last_switch >= interval:
            use_left = not use_left
            last_switch = time_value
        sorted_faces = sorted([face for face in faces if isinstance(face, dict)], key=lambda item: float(item.get("x") or 50.0))
        target = sorted_faces[0] if use_left else sorted_faces[-1]
        frames.append({**target, "time": time_value, "zoom": min(float(target.get("zoom") or 1.0) + 0.06, 1.36)})
    if len(frames) < 2:
        return []
    source = "auto-face-alternate-faces" if smooth else "auto-face-cut-between-faces"
    rows = smoothed_camera_frames(frames, source) if smooth else camera_frames_from_detections(frames, source)
    return compressed_camera_path(rows, duration)


def camera_frames_from_detections(detections: list[dict[str, float]], source: str) -> list[dict[str, object]]:
    return [{
        "time": round(float(item.get("time") or 0.0), 3),
        "x": round(float(item.get("x") or 50.0), 2),
        "y": round(float(item.get("y") or 50.0), 2),
        "zoom": round(float(item.get("zoom") or 1.0), 3),
        "source": source,
        "confidence": round(float(item.get("confidence") or 0.35), 3),
    } for item in detections]


def smoothed_camera_frames(
    detections: list[dict[str, float]],
    source: str,
    x_weight: float = 0.32,
    y_weight: float = 0.25,
    zoom_weight: float = 0.22,
) -> list[dict[str, object]]:
    frames: list[dict[str, object]] = []
    smooth_x: float | None = None
    smooth_y: float | None = None
    smooth_zoom: float | None = None
    for detection in detections:
        smooth_x = weighted_smooth(smooth_x, detection["x"], x_weight)
        smooth_y = weighted_smooth(smooth_y, detection["y"], y_weight)
        smooth_zoom = weighted_smooth(smooth_zoom, detection["zoom"], zoom_weight)
        frames.append({
            "time": detection["time"],
            "x": round(smooth_x, 2),
            "y": round(smooth_y, 2),
            "zoom": round(smooth_zoom, 3),
            "source": source,
            "confidence": detection["confidence"],
        })
    return frames


def stable_camera_targets(frames: list[dict[str, float]]) -> list[dict[str, float]]:
    if len(frames) < 3:
        return frames
    stable = [frames[0]]
    for index in range(1, len(frames) - 1):
        previous = frames[index - 1]
        current = frames[index]
        next_frame = frames[index + 1]
        stable.append(stabilized_camera_target(previous, current, next_frame))
    stable.append(frames[-1])
    return stable


def stabilized_camera_target(
    previous: dict[str, float],
    current: dict[str, float],
    next_frame: dict[str, float],
) -> dict[str, float]:
    if not is_camera_outlier(previous, current, next_frame):
        return current
    return {
        **current,
        "x": round((face_x(previous) + face_x(next_frame)) / 2.0, 2),
        "y": round((float(previous.get("y") or 50.0) + float(next_frame.get("y") or 50.0)) / 2.0, 2),
        "zoom": round(min(float(previous.get("zoom") or 1.0), float(next_frame.get("zoom") or 1.0)), 3),
    }


def is_camera_outlier(previous: dict[str, float], current: dict[str, float], next_frame: dict[str, float]) -> bool:
    if float(next_frame["time"]) - float(previous["time"]) > 2.2:
        return False
    previous_x = face_x(previous)
    current_x = face_x(current)
    next_x = face_x(next_frame)
    center_snap = current_x < 50.0 and previous_x > 55.0 and next_x > 55.0
    strong_jump = abs(current_x - previous_x) > 14.0 and abs(current_x - next_x) > 14.0
    return center_snap and strong_jump and abs(previous_x - next_x) < 10.0


def weighted_smooth(previous: float | None, current: float, weight: float) -> float:
    if previous is None:
        return current
    safe_weight = clamp(weight, 0.05, 0.95)
    return previous * (1.0 - safe_weight) + current * safe_weight


def compressed_camera_path(
    frames: list[dict[str, object]],
    duration: float,
    min_gap: float = 0.8,
    max_gap: float = 2.4,
    x_threshold: float = 2.4,
    zoom_threshold: float = 0.018,
) -> list[dict[str, object]]:
    if not frames:
        return []
    compressed = [frames[0]]
    for frame in frames[1:]:
        last = compressed[-1]
        time_gap = float(frame["time"]) - float(last["time"])
        x_delta = abs(float(frame["x"]) - float(last["x"]))
        zoom_delta = abs(float(frame["zoom"]) - float(last["zoom"]))
        has_moved = x_delta >= x_threshold or zoom_delta >= zoom_threshold
        if time_gap >= max_gap or (time_gap >= min_gap and has_moved):
            compressed.append(frame)
    last_frame = frames[-1]
    if compressed[-1] is not last_frame and float(last_frame["time"]) < max(duration, 0.3) - 0.05:
        compressed.append(last_frame)
    return compressed[:48]


def resolve_request_gallery_dir(base_dir: Path, payload: dict[str, object]) -> Path:
    raw = str(payload.get("gallery_path") or "").strip()
    if not raw or raw in {"/", "."}:
        return base_dir
    path = urllib.parse.unquote(urllib.parse.urlparse(raw).path).strip("/")
    if not path:
        return base_dir
    candidate = (base_dir / path).resolve()
    try:
        candidate.relative_to(base_dir.resolve())
    except ValueError as error:
        raise ValueError("Invalid gallery path.") from error
    require_file(candidate / "index.html")
    return candidate


def export_captioned_rows(rows: list[dict[str, object]], gallery_dir: Path) -> tuple[list[dict[str, object]], Path | None]:
    export_dir = render_export_dir(gallery_dir)
    if export_dir is None:
        return rows, None
    export_dir.mkdir(parents=True, exist_ok=True)
    exported: list[dict[str, object]] = []
    for row in rows:
        source = Path(str(row.get("file") or ""))
        if not source.exists():
            exported.append(row)
            continue
        destination = unique_export_path(export_dir / source.name)
        shutil.copy2(source, destination)
        exported_row = {**row, "local_file": str(destination)}
        cover_source_value = str(row.get("cover_file") or "")
        cover_source = Path(cover_source_value)
        if cover_source_value and cover_source.exists():
            cover_destination = unique_export_path(export_dir / cover_source.name)
            shutil.copy2(cover_source, cover_destination)
            exported_row["local_cover_file"] = str(cover_destination)
        cover_frame_source_value = str(row.get("cover_frame_file") or "")
        cover_frame_source = Path(cover_frame_source_value)
        if cover_frame_source_value and cover_frame_source.exists():
            cover_frame_destination = unique_export_path(export_dir / cover_frame_source.name)
            shutil.copy2(cover_frame_source, cover_frame_destination)
            exported_row["local_cover_frame_file"] = str(cover_frame_destination)
        exported.append(exported_row)
    return exported, export_dir


def render_export_dir(gallery_dir: Path) -> Path | None:
    metadata = read_import_metadata(gallery_dir)
    render_raw = str(metadata.get("render_output_path") or "").strip()
    if render_raw:
        return Path(render_raw).expanduser()
    raw = str(metadata.get("output_path") or "").strip()
    if not raw and metadata.get("source_url"):
        legacy_path = Path(str(metadata.get("source_path") or "")).expanduser()
        if legacy_path.exists() and legacy_path.is_dir():
            raw = str(legacy_path)
    if not raw:
        return None
    base = Path(raw).expanduser()
    if base.suffix and not base.exists():
        base = base.parent
    return base / "CUTED Renders" / gallery_dir.name


def read_import_metadata(gallery_dir: Path) -> dict[str, object]:
    path = gallery_dir / "import-request.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def unique_export_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(2, 1000):
        candidate = path.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    return path.with_name(f"{stem}-{uuid.uuid4().hex[:8]}{suffix}")


def import_request_metadata(payload: dict[str, object]) -> dict[str, object]:
    source_url = str(payload.get("source_url") or "").strip()
    source_path = str(payload.get("source_path") or "").strip()
    if not source_url and not source_path:
        raise ValueError("Provide a link or a local file to import.")
    output_path = clean_output_path(payload.get("output_path"))
    ai_provider = configured_ai_provider()
    if ai_provider == "openai" and not openai_api_key():
        raise ValueError("Add your OpenAI key in Settings before importing with AI.")
    return {
        "source_url": source_url,
        "source_path": source_path,
        "output_path": output_path,
        "preview_count": clamp_int(payload.get("preview_count"), 1, 10, 10),
        "language": clean_optional_text(payload.get("language"), 24) or "pt",
        "preset": clean_preset(payload.get("preset")),
        "duration_profile": clean_duration_profile(payload.get("duration_profile")),
        "context_prompt": clean_optional_text(payload.get("context_prompt"), 5000),
        "render_previews": bool(payload.get("render_previews", True)),
        "ai_provider": ai_provider,
        "mode": "openai_import" if ai_provider == "openai" else "local_fallback",
    }


def start_import_job(handler: http.server.BaseHTTPRequestHandler, base_dir: Path) -> dict[str, object]:
    payload = read_json_body(handler)
    metadata = import_request_metadata(payload)
    source_url = str(metadata["source_url"])
    source_path = str(metadata["source_path"])
    out_dir = next_import_output_dir(base_dir, source_url or source_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    metadata["project_dir"] = str(out_dir)
    metadata["render_output_path"] = str(project_render_output_dir(out_dir))
    (out_dir / "import-request.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    command = import_command(out_dir, source_url, source_path, metadata)
    job_id = uuid.uuid4().hex[:12]
    output_url = import_output_url(base_dir, out_dir)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
    source_kind = "youtube" if source_url else "local"
    job = ImportJob(
        job_id,
        "running",
        time.time(),
        time.time(),
        out_dir,
        base_dir,
        output_url,
        process,
        "Import started.",
        source_kind,
        str(metadata["ai_provider"]),
    )
    with IMPORT_JOBS_LOCK:
        IMPORT_JOBS[job_id] = job
    thread = threading.Thread(target=wait_for_import_job, args=(job_id,), daemon=True)
    thread.start()
    return {"ok": True, "job": import_job_to_dict(job)}


def ai_context_audio_from_request(handler: http.server.BaseHTTPRequestHandler) -> dict[str, object]:
    language = ai_context_language(handler.path)
    suffix = ai_context_audio_suffix(handler.headers.get("Content-Type", ""))
    raw = read_binary_body(handler, AI_CONTEXT_AUDIO_MAX_BYTES)
    temp_path = write_ai_context_audio(raw, suffix)
    try:
        audio = ai_context_audio_info(temp_path, len(raw))
        validate_ai_context_audio(audio)
        context = transcribe_ai_context_audio(temp_path, language, audio)
    finally:
        remove_temp_file(temp_path)
    return {"ok": True, "context": context, "warnings": []}


def ai_context_language(path: str) -> str | None:
    query = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
    value = clean_optional_text((query.get("language") or ["auto"])[0], 12).lower()
    return None if value in {"", "auto", "detect"} else value


def ai_context_audio_suffix(content_type: str) -> str:
    mime = content_type.split(";", 1)[0].strip().lower()
    mapping = {"audio/webm": ".webm", "audio/mp4": ".mp4", "audio/wav": ".wav", "audio/ogg": ".ogg"}
    if mime not in mapping:
        raise ValueError("Unsupported microphone audio format.")
    return mapping[mime]


def write_ai_context_audio(raw: bytes, suffix: str) -> Path:
    folder = cuted_data_dir() / "drafts" / "ai-context-audio"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex}{suffix}"
    path.write_bytes(raw)
    return path


def remove_temp_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def transcribe_ai_context_audio(path: Path, language: str | None, audio: dict[str, object]) -> dict[str, object]:
    if openai_api_key():
        return transcribe_ai_context_with_openai(path, language, audio)
    return transcribe_ai_context_with_faster_whisper(path, language, audio)


def transcribe_ai_context_with_openai(path: Path, language: str | None, audio: dict[str, object]) -> dict[str, object]:
    model = ai_context_transcribe_model()
    fields = {"model": model, "response_format": "json"}
    if language:
        fields["language"] = language
    data = openai_multipart_request(
        "https://api.openai.com/v1/audio/transcriptions",
        openai_api_key(),
        fields,
        "file",
        path,
        ai_context_audio_content_type(path),
    )
    text = clean_optional_text(data.get("text"), 5000)
    if not text:
        raise RuntimeError(ai_context_empty_transcript_message(audio))
    duration = ai_context_audio_seconds(audio) or openai_transcription_response_duration(data)
    record_openai_transcribe_usage(model, duration)
    return ai_context_payload(text, language, "openai", model, duration)


def transcribe_ai_context_with_faster_whisper(path: Path, language: str | None, audio: dict[str, object]) -> dict[str, object]:
    try:
        rows = transcribe_with_faster_whisper(path, "small", language)
    except ModuleNotFoundError as exc:
        raise RuntimeError("Set up OpenAI or install faster-whisper to transcribe microphone briefings.") from exc
    text = clean_optional_text(" ".join(row.text for row in rows), 5000)
    if not text:
        raise RuntimeError(ai_context_empty_transcript_message(audio))
    return ai_context_payload(text, language, "local", "faster-whisper-small", transcription_duration(rows))


def ai_context_payload(text: str, language: str | None, provider: str, model: str, duration: float) -> dict[str, object]:
    return {
        "text": text,
        "language": language or "auto",
        "provider": provider,
        "model": model,
        "audio_seconds": round(min(duration, AI_CONTEXT_AUDIO_MAX_SECONDS), 3),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def openai_transcription_response_duration(data: dict[str, object]) -> float:
    value = data.get("duration")
    return clamp(float(value), 0.0, float(AI_CONTEXT_AUDIO_MAX_SECONDS)) if isinstance(value, (int, float)) else 0.0


def import_command(
    out_dir: Path, source_url: str, source_path: str, metadata: dict[str, object]
) -> list[str]:
    command = [sys.executable, str(Path(__file__).resolve()), "analyze"]
    if source_url:
        command.extend(["--youtube-url", source_url])
    else:
        local_source = Path(source_path).expanduser().resolve()
        require_file(local_source)
        command.append(str(local_source))
    preview_count = import_preview_count(source_url, metadata)
    command.extend(["--out", str(out_dir), "--clips", str(preview_count), "--preset", str(metadata["preset"])])
    command.extend(duration_profile_args(str(metadata["duration_profile"])))
    command.extend(["--ai-provider", str(metadata["ai_provider"]), "--context-prompt", str(metadata["context_prompt"])])
    language = str(metadata["language"])
    if language:
        command.extend(["--language", language])
    if not metadata["render_previews"]:
        command.append("--skip-render")
    return command


def import_preview_count(source_url: str, metadata: dict[str, object]) -> int:
    requested = int(metadata.get("preview_count") or 10)
    if source_url:
        return requested
    return min(requested, LOCAL_IMPORT_MAX_INITIAL_CLIPS)


def wait_for_import_job(job_id: str) -> None:
    with IMPORT_JOBS_LOCK:
        job = IMPORT_JOBS.get(job_id)
    if job is None or job.process is None:
        return
    process = job.process
    stderr_lines: list[str] = []
    stderr_thread = threading.Thread(target=collect_import_pipe_lines, args=(process.stderr, stderr_lines), daemon=True)
    stderr_thread.start()
    stdout_lines = read_import_stdout(job_id, process)
    return_code = process.wait()
    stderr_thread.join(timeout=1.0)
    stdout = "".join(stdout_lines)
    stderr = "".join(stderr_lines)
    status = "ready" if return_code == 0 else "failed"
    message = "Project imported." if status == "ready" else "Project import failed."
    with IMPORT_JOBS_LOCK:
        current = IMPORT_JOBS.get(job_id)
        if current is None:
            return
        if current.status == "cancelled":
            current.updated_at = time.time()
            current.return_code = return_code
            current.stdout = stdout[-6000:]
            current.stderr = stderr[-6000:]
            current.process = None
            return
        current.status = status
        current.updated_at = time.time()
        current.return_code = return_code
        current.stdout = stdout[-6000:]
        current.stderr = import_job_error_message(stderr) if status == "failed" else stderr[-6000:]
        current.message = message
        current.process = None
        if status == "ready":
            upsert_project_catalog_entry(project_entry_from_gallery(current.output_dir, current.base_dir))


def read_import_stdout(job_id: str, process: subprocess.Popen[str]) -> list[str]:
    lines: list[str] = []
    if process.stdout is None:
        return lines
    for line in process.stdout:
        lines.append(line)
        event = parse_import_progress_line(line)
        if event:
            update_import_job_progress(job_id, event)
    return lines


def collect_import_pipe_lines(pipe: object, lines: list[str]) -> None:
    if pipe is None:
        return
    try:
        for line in pipe:
            lines.append(str(line))
    except OSError:
        return


def parse_import_progress_line(line: str) -> dict[str, object] | None:
    text = line.strip()
    if not text.startswith(IMPORT_PROGRESS_PREFIX):
        return None
    try:
        data = json.loads(text[len(IMPORT_PROGRESS_PREFIX):])
    except json.JSONDecodeError:
        return None
    return import_progress_payload(data) if isinstance(data, dict) else None


def import_progress_payload(data: dict[str, object]) -> dict[str, object]:
    stage = clean_optional_text(data.get("stage"), 32) or "running"
    label = clean_optional_text(data.get("label"), 32) or "Import"
    message = clean_optional_text(data.get("message"), 180) or "Processing import..."
    payload: dict[str, object] = {
        "stage": stage,
        "label": label,
        "message": message,
        "percent": clamp_int(data.get("percent"), 0, 100, 35),
        "updated_at": time.time(),
    }
    detail = clean_optional_text(data.get("detail"), 160)
    if detail:
        payload["detail"] = detail
    if "step" in data:
        payload["step"] = clamp_int(data.get("step"), 0, 9999, 0)
    if "steps" in data:
        payload["steps"] = clamp_int(data.get("steps"), 0, 9999, 0)
    return payload


def update_import_job_progress(job_id: str, progress: dict[str, object]) -> None:
    with IMPORT_JOBS_LOCK:
        job = IMPORT_JOBS.get(job_id)
        if job is None or job.status != "running":
            return
        previous_percent = int(job.progress.get("percent", 0) or 0) if job.progress else 0
        next_percent = int(progress.get("percent", 0) or 0)
        if next_percent < previous_percent and previous_percent < 96:
            progress["percent"] = previous_percent
        job.progress = dict(progress)
        job.events = [*job.events[-7:], dict(progress)]
        job.message = str(progress.get("message") or job.message)
        job.updated_at = time.time()


def cancel_import_job(job_id: str) -> dict[str, object]:
    with IMPORT_JOBS_LOCK:
        job = IMPORT_JOBS.get(job_id)
        if job is None:
            return {"ok": False, "error": "Import job not found."}
        if job.process is not None and job.status == "running":
            job.process.terminate()
            job.status = "cancelled"
            job.message = "Import cancelled."
            job.updated_at = time.time()
    return {"ok": True, "job": import_job_to_dict(job)}


def import_job_snapshot(job_id: str) -> dict[str, object] | None:
    with IMPORT_JOBS_LOCK:
        job = IMPORT_JOBS.get(job_id)
        return import_job_to_dict(job) if job else None


def import_job_to_dict(job: ImportJob) -> dict[str, object]:
    progress = import_job_progress(job)
    return {
        "id": job.id,
        "status": job.status,
        "message": progress["message"],
        "progress": progress,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "output_url": job.output_url,
        "output_dir": str(job.output_dir),
        "return_code": job.return_code,
        "stderr": job.stderr,
        "events": job.events[-8:],
    }


def import_job_progress(job: ImportJob) -> dict[str, object]:
    if job.status == "ready":
        return {"percent": 100, "stage": "editor", "label": "Ready", "message": "Project imported. Opening editor..."}
    if job.status == "failed":
        return {"percent": 100, "stage": str(job.progress.get("stage") or "prepare"), "label": "Failed", "message": job.message or "Project import failed."}
    if job.status == "cancelled":
        return {"percent": 100, "stage": str(job.progress.get("stage") or "prepare"), "label": "Cancelled", "message": job.message or "Import cancelled."}
    if job.progress:
        return job.progress
    elapsed = max(0.0, time.time() - job.created_at)
    stages = import_job_running_stages(job.source_kind, job.ai_provider)
    index = min(int(elapsed // 7), len(stages) - 1)
    percent = min(92, int(8 + elapsed * 4))
    label, message = stages[index]
    return {"percent": percent, "label": label, "message": message}


def import_job_running_stages(source_kind: str, ai_provider: str) -> list[tuple[str, str]]:
    media_message = "Downloading video..." if source_kind == "youtube" else "Reading local video..."
    ai_message = "Consulting AI..." if ai_provider == "openai" else "Analyzing clips..."
    return [
        ("Preparing", "Preparing project..."),
        ("Media", media_message),
        ("Audio", "Transcribing audio..."),
        ("Analysis", ai_message),
        ("Suggestions", "Generating clip suggestions..."),
        ("Post AI", "Analyzing SEO and trends..."),
        ("Editor", "Building editing workspace..."),
    ]


def import_job_error_message(stderr: str) -> str:
    clean = stderr.strip()
    if not clean:
        return ""
    friendly = friendly_ytdlp_error(clean)
    return friendly if friendly != clean else clean[-6000:]


def next_import_output_dir(base_dir: Path, source: str) -> Path:
    imports_dir = base_dir / PROJECTS_DIR_NAME
    slug = safe_slug(Path(urllib.parse.urlparse(source).path).stem or source)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    candidate = imports_dir / f"{stamp}-{slug}"
    index = 2
    while candidate.exists():
        candidate = imports_dir / f"{stamp}-{slug}-{index}"
        index += 1
    return candidate


def project_render_output_dir(project_dir: Path) -> Path:
    return project_dir / PROJECT_RENDERS_DIR_NAME


def import_output_url(base_dir: Path, out_dir: Path) -> str:
    rel = out_dir.resolve().relative_to(base_dir.resolve()).as_posix()
    return f"/{rel}/index.html"


def safe_slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.lower()).strip("-")
    return normalized[:48] or "project"


def clean_optional_text(value: object, limit: int) -> str:
    return str(value or "").strip()[:limit]


def clean_preset(value: object) -> str:
    preset = str(value or "tiktok").strip().lower()
    return preset if preset in {"tiktok", "shorts", "reels"} else "tiktok"


def clean_duration_profile(value: object) -> str:
    profile = str(value or "medium").strip().lower()
    return profile if profile in DURATION_PROFILES else "medium"


def clean_output_path(value: object) -> str:
    raw = str(value or "").strip().strip('"')
    if not raw:
        return ""
    return str(Path(raw).expanduser())


def duration_profile_args(profile: str) -> list[str]:
    min_duration, target_duration, max_duration = DURATION_PROFILES[profile]
    return [
        "--min-duration", str(min_duration),
        "--target-duration", str(target_duration),
        "--max-duration", str(max_duration),
    ]


def default_desktop_path() -> str:
    for candidate in desktop_path_candidates():
        if candidate.exists():
            return str(candidate)
    return str(Path.home() / "Desktop")


def desktop_path_candidates() -> list[Path]:
    home = Path.home()
    candidates = [home / "Desktop"]
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        profile = Path(user_profile)
        candidates.extend([profile / "OneDrive" / "Desktop", profile / "Desktop"])
    one_drive = os.environ.get("OneDrive") or os.environ.get("OneDriveCommercial") or os.environ.get("OneDriveConsumer")
    if one_drive:
        candidates.append(Path(one_drive) / "Desktop")
    return candidates


def select_folder_path() -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as error:
        raise RuntimeError("Seletor de pasta indisponivel neste ambiente.") from error
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    selected = filedialog.askdirectory(initialdir=default_desktop_path(), title="Selecionar pasta do projeto")
    root.destroy()
    if not selected:
        raise RuntimeError("Nenhuma pasta selecionada.")
    return selected


def select_video_file_path() -> str:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as error:
        raise RuntimeError("Seletor de arquivo indisponivel neste ambiente.") from error
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    selected = filedialog.askopenfilename(
        initialdir=default_desktop_path(),
        title="Selecionar video local",
        filetypes=(("Videos", "*.mp4 *.mov *.m4v *.webm"), ("Todos os arquivos", "*.*")),
    )
    root.destroy()
    if not selected:
        raise RuntimeError("Nenhum arquivo selecionado.")
    return selected


def open_local_folder(value: object) -> Path:
    raw = clean_optional_text(value, 2000)
    if not raw:
        raise ValueError("Missing folder path.")
    path = Path(raw).expanduser()
    if path.is_file():
        path = path.parent
    if not path.exists() or not path.is_dir():
        raise ValueError("Folder not found.")
    resolved = path.resolve()
    if sys.platform.startswith("win"):
        os.startfile(str(resolved))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(resolved)])
    else:
        subprocess.Popen(["xdg-open", str(resolved)])
    return resolved


def clean_smart_boundaries(value: object) -> str:
    mode = str(value or "auto").strip().lower()
    return mode if mode in {"auto", "on", "off"} else "auto"


def clamp_int(value: object, minimum: int, maximum: int, fallback: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return min(max(number, minimum), maximum)


def optional_float(value: object, minimum: float, maximum: float) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return min(max(number, minimum), maximum)


def clamp_float(value: object, minimum: float, maximum: float, fallback: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return min(max(number, minimum), maximum)


def load_local_env() -> None:
    for env_path in local_env_candidates():
        if not env_path.exists():
            continue
        for raw_line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip().strip('"').strip("'")


def local_env_candidates() -> list[Path]:
    script_dir = Path(__file__).resolve().parent
    roots = [Path.cwd(), *script_dir.parents]
    candidates: list[Path] = []
    for root in roots:
        for name in (".env.cuted.local", ".env.local", ".env"):
            path = root / name
            if path not in candidates:
                candidates.append(path)
    return candidates


def project_root() -> Path:
    script_dir = Path(__file__).resolve().parent
    for root in [Path.cwd(), *script_dir.parents]:
        if (root / ".git").exists():
            return root.resolve()
    return Path.cwd().resolve()


def cuted_data_dir() -> Path:
    raw = os.environ.get("CUTED_HOME", "").strip()
    return Path(raw).expanduser() if raw else Path.home() / ".cuted"


def cuted_settings_path() -> Path:
    return cuted_data_dir() / "settings.json"


def cuted_usage_path() -> Path:
    raw = os.environ.get("CUTED_USAGE_LEDGER", "").strip()
    return Path(raw).expanduser() if raw else cuted_data_dir() / "usage-ledger.json"


def cuted_secret_env_path() -> Path:
    return project_root() / ".env.cuted.local"


def read_cuted_settings() -> dict[str, object]:
    path = cuted_settings_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_cuted_settings(data: dict[str, object]) -> None:
    path = cuted_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def configured_ai_provider() -> str:
    settings = read_cuted_settings()
    provider = str(settings.get("ai_provider") or os.environ.get("CUTED_AI_PROVIDER") or "local")
    provider = provider.strip().lower()
    return provider if provider in {"auto", "local", "openai"} else "local"


def requested_ai_provider(args: argparse.Namespace) -> str:
    provider = str(getattr(args, "ai_provider", "") or configured_ai_provider()).strip().lower()
    return provider if provider in {"auto", "local", "openai"} else "local"


def openai_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "").strip()


def openai_model() -> str:
    settings = read_cuted_settings()
    model = str(settings.get("openai_model") or os.environ.get("CUTED_OPENAI_MODEL") or "gpt-5-mini")
    return clean_openai_model(model)


def openai_transcribe_model() -> str:
    settings = read_cuted_settings()
    model = str(settings.get("transcribe_model") or os.environ.get("CUTED_TRANSCRIBE_MODEL") or "whisper-1")
    return clean_transcribe_model(model)


def clean_openai_model(value: object) -> str:
    model = str(value or "gpt-5-mini").strip()
    return model if model in OPENAI_TEXT_PRICES_USD_PER_1M else "gpt-5-mini"


def clean_transcribe_model(value: object) -> str:
    model = str(value or "whisper-1").strip()
    return model if model in OPENAI_TRANSCRIBE_PRICES_USD_PER_MINUTE else "whisper-1"


def save_openai_settings(payload: dict[str, object]) -> None:
    provider = str(payload.get("ai_provider") or "openai").strip().lower()
    if provider not in {"auto", "local", "openai"}:
        raise ValueError("Provedor de IA invalido.")
    model = clean_openai_model(payload.get("openai_model"))
    transcribe_model = clean_transcribe_model(payload.get("transcribe_model"))
    api_key = clean_optional_text(payload.get("api_key"), 2048)
    if api_key:
        write_openai_key(api_key)
        os.environ["OPENAI_API_KEY"] = api_key
    settings = read_cuted_settings()
    settings.update({"ai_provider": provider, "openai_model": model, "transcribe_model": transcribe_model})
    write_cuted_settings(settings)
    os.environ["CUTED_AI_PROVIDER"] = provider
    os.environ["CUTED_OPENAI_MODEL"] = model
    os.environ["CUTED_TRANSCRIBE_MODEL"] = transcribe_model


def write_openai_key(api_key: str) -> None:
    key = api_key.strip()
    if len(key) < 20 or not key.startswith("sk-"):
        raise ValueError("Token OpenAI invalido.")
    path = cuted_secret_env_path()
    path.write_text(f"OPENAI_API_KEY={key}\n", encoding="utf-8")


def openai_settings_payload() -> dict[str, object]:
    key = openai_api_key()
    return {
        "ai_provider": configured_ai_provider(),
        "openai_model": openai_model(),
        "transcribe_model": openai_transcribe_model(),
        "key_configured": bool(key),
        "secret_path": str(cuted_secret_env_path()),
        "settings_path": str(cuted_settings_path()),
        "pricing": pricing_payload(),
    }


def pricing_payload() -> dict[str, object]:
    return {
        "source": OPENAI_PRICING_SOURCE,
        "updated": OPENAI_PRICING_UPDATED,
        "text_usd_per_1m": OPENAI_TEXT_PRICES_USD_PER_1M,
        "transcribe_usd_per_minute": OPENAI_TRANSCRIBE_PRICES_USD_PER_MINUTE,
    }


def test_openai_connection(api_key: str) -> None:
    if not api_key:
        raise RuntimeError("Configure an OpenAI token before testing.")
    request = urllib.request.Request(
        "https://api.openai.com/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status >= 400:
                raise RuntimeError("OpenAI refused the connection.")
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"OpenAI refused the connection (HTTP {error.code}).") from error
    except urllib.error.URLError as error:
        raise RuntimeError("Could not connect to OpenAI right now.") from error


def local_usage_payload() -> dict[str, object]:
    return {"ok": True, "usage": usage_summary_payload(), "pricing": pricing_payload()}


def usage_summary_payload() -> dict[str, object]:
    ledger = read_usage_ledger()
    events = ledger.get("events") if isinstance(ledger, dict) else []
    rows = events if isinstance(events, list) else []
    total = sum(float(row.get("estimated_usd") or 0.0) for row in rows if isinstance(row, dict))
    last = next((row for row in reversed(rows) if isinstance(row, dict)), None)
    return {
        "ledger_path": str(cuted_usage_path()),
        "event_count": len(rows),
        "estimated_total_usd": round(total, 6),
        "last_event": last or {},
        "recent_events": rows[-12:],
    }


def read_usage_ledger() -> dict[str, object]:
    path = cuted_usage_path()
    if not path.exists():
        return {"version": 1, "events": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "events": []}
    return data if isinstance(data, dict) else {"version": 1, "events": []}


def append_usage_event(event: dict[str, object]) -> None:
    path = cuted_usage_path()
    ledger = read_usage_ledger()
    events = ledger.get("events")
    if not isinstance(events, list):
        events = []
    events.append(event)
    ledger["version"] = 1
    ledger["events"] = events[-500:]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json_body(handler: http.server.BaseHTTPRequestHandler) -> dict[str, object]:
    length = int(handler.headers.get("Content-Length") or "0")
    if length <= 0 or length > 80_000_000:
        raise ValueError("Invalid request body.")
    raw = handler.rfile.read(length)
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    return data


def read_binary_body(handler: http.server.BaseHTTPRequestHandler, limit: int) -> bytes:
    length = int(handler.headers.get("Content-Length") or "0")
    if length <= 0:
        raise ValueError("No audio was received.")
    if length > limit:
        raise ValueError("Microphone briefing is too long.")
    return handler.rfile.read(length)


def ai_context_transcribe_model() -> str:
    raw = os.environ.get("CUTED_CONTEXT_TRANSCRIBE_MODEL", "").strip()
    model = raw or openai_transcribe_model()
    if model in OPENAI_TRANSCRIBE_PRICES_USD_PER_MINUTE:
        return model
    return "whisper-1"


def ai_context_audio_info(path: Path, byte_count: int) -> dict[str, object]:
    seconds = ai_context_audio_duration(path)
    return {"bytes": byte_count, "seconds": seconds, "duration_known": seconds > 0}


def validate_ai_context_audio(audio: dict[str, object]) -> None:
    seconds = ai_context_audio_seconds(audio)
    if seconds and seconds < AI_CONTEXT_MIN_AUDIO_SECONDS:
        raise ValueError(f"Recording is too short ({seconds:.1f}s). Hold the mic for at least 1 second and speak clearly.")


def ai_context_audio_seconds(audio: dict[str, object]) -> float:
    value = audio.get("seconds")
    return clamp(float(value), 0.0, float(AI_CONTEXT_AUDIO_MAX_SECONDS)) if isinstance(value, (int, float)) else 0.0


def ai_context_empty_transcript_message(audio: dict[str, object]) -> str:
    seconds = ai_context_audio_seconds(audio)
    size = file_size_label(int(audio.get("bytes") or 0))
    detail = f" The app received {seconds:.1f}s / {size}." if seconds else f" The app received {size}, but could not read the duration."
    return f"No speech was detected.{detail} Check the selected browser microphone and try recording a clear sentence."


def ai_context_audio_duration(path: Path) -> float:
    try:
        duration = probe_duration(path, find_ffprobe())
    except Exception:
        return 0.0
    return clamp(duration, 0.0, float(AI_CONTEXT_AUDIO_MAX_SECONDS))


def ai_context_audio_content_type(path: Path) -> str:
    mapping = {".webm": "audio/webm", ".mp4": "audio/mp4", ".wav": "audio/wav", ".ogg": "audio/ogg"}
    return mapping.get(path.suffix.lower(), "application/octet-stream")


def finalized_file_urls(rows: list[dict[str, object]], base_dir: Path) -> list[dict[str, object]]:
    files: list[dict[str, object]] = []
    resolved_base_dir = base_dir.resolve()
    for row in rows:
        file_path = Path(str(row.get("file") or ""))
        rel = file_path.resolve().relative_to(resolved_base_dir)
        final_path = exported_file_path(row, file_path)
        cover_path = exported_cover_file_path(row)
        cover_frame_path = exported_cover_frame_file_path(row)
        cover_url = ""
        raw_cover_value = str(row.get("cover_file") or "")
        raw_cover = Path(raw_cover_value)
        if raw_cover_value and raw_cover.exists():
            cover_url = raw_cover.resolve().relative_to(resolved_base_dir).as_posix()
        cover_frame_url = ""
        raw_cover_frame_value = str(row.get("cover_frame_file") or "")
        raw_cover_frame = Path(raw_cover_frame_value)
        if raw_cover_frame_value and raw_cover_frame.exists():
            cover_frame_url = raw_cover_frame.resolve().relative_to(resolved_base_dir).as_posix()
        files.append({
            **row,
            "url": rel.as_posix(),
            "preview_url": rel.as_posix(),
            "cover_url": cover_url,
            "cover_frame_url": cover_frame_url,
            "download_name": final_path.name,
            "download_cover_frame_name": cover_frame_path.name if cover_frame_path else "",
            "final_file": str(final_path),
            "final_dir": str(final_path.parent),
            "final_cover_file": str(cover_path) if cover_path else "",
            "final_cover_frame_file": str(cover_frame_path) if cover_frame_path else "",
            "is_exported": final_path != file_path,
        })
    return files


def exported_file_path(row: dict[str, object], fallback: Path) -> Path:
    local_file = row.get("local_file")
    if isinstance(local_file, str) and local_file.strip():
        path = Path(local_file)
        if path.exists():
            return path
    return fallback


def exported_cover_file_path(row: dict[str, object]) -> Path | None:
    local_cover = row.get("local_cover_file")
    if isinstance(local_cover, str) and local_cover.strip():
        path = Path(local_cover)
        if path.exists():
            return path
    cover_file = row.get("cover_file")
    if isinstance(cover_file, str) and cover_file.strip():
        path = Path(cover_file)
        return path if path.exists() else None
    return None


def exported_cover_frame_file_path(row: dict[str, object]) -> Path | None:
    local_cover_frame = row.get("local_cover_frame_file")
    if isinstance(local_cover_frame, str) and local_cover_frame.strip():
        path = Path(local_cover_frame)
        if path.exists():
            return path
    cover_frame_file = row.get("cover_frame_file")
    if isinstance(cover_frame_file, str) and cover_frame_file.strip():
        path = Path(cover_frame_file)
        return path if path.exists() else None
    return None


def send_json_response(handler: http.server.BaseHTTPRequestHandler, status: int, data: dict[str, object]) -> None:
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def current_server_script_mtime_ns() -> int:
    try:
        return CUTTED_SERVER_SCRIPT_PATH.stat().st_mtime_ns
    except OSError:
        return CUTTED_SERVER_SCRIPT_MTIME_NS


def server_code_changed_since_start() -> bool:
    current_mtime_ns = current_server_script_mtime_ns()
    return bool(CUTTED_SERVER_SCRIPT_MTIME_NS and current_mtime_ns and current_mtime_ns != CUTTED_SERVER_SCRIPT_MTIME_NS)


def stale_server_payload() -> dict[str, object]:
    return {
        "ok": False,
        "code": "stale_render_server",
        "error": STALE_RENDER_SERVER_ERROR,
        "started_mtime_ns": CUTTED_SERVER_SCRIPT_MTIME_NS,
        "current_mtime_ns": current_server_script_mtime_ns(),
    }


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
        for layer in image_layers_to_materialize(row):
            if not isinstance(layer, dict) or str(layer.get("kind") or layer.get("key") or "") != "image":
                continue
            materialize_image_layer(layer, asset_dir)


def image_layers_to_materialize(row: dict[str, object]) -> list[dict[str, object]]:
    layers: list[dict[str, object]] = []
    overlays = row.get("overlays")
    if isinstance(overlays, list):
        layers.extend(layer for layer in overlays if isinstance(layer, dict))
    cover = publish_cover_from_row(row)
    cover_layers = cover.get("layers")
    if isinstance(cover_layers, list):
        layers.extend(layer for layer in cover_layers if isinstance(layer, dict))
    return layers


def materialize_queue_bumper_assets(data: object, asset_dir: Path) -> None:
    rows = queue_rows_for_assets(data)
    for row in rows:
        bumpers = normalize_bumpers_from_row(row)
        for slot, bumper in bumpers.items():
            if str(bumper.get("asset_file") or ""):
                continue
            data_url = str(bumper.get("video_data_url") or "")
            if not data_url:
                continue
            video_bytes, extension = decode_data_url_video(data_url)
            asset_dir.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256(video_bytes).hexdigest()[:16]
            path = asset_dir / f"{slot}-{digest}.{extension}"
            if not path.exists():
                path.write_bytes(video_bytes)
            bumper["asset_file"] = str(path)
            bumper["video_data_url"] = ""
        if bumpers:
            row["bumpers"] = bumpers


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
            if key != "caption_queue":
                rows.extend(selected_rows_to_caption_rows(value))
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
            queue.append(row_for_platform(row, platform))
    return queue


def row_for_platform(row: dict[str, object], platform: str) -> dict[str, object]:
    result = {**row, "platform": platform}
    edit = platform_edit_from_row(row, platform)
    if edit:
        result.update(edit)
    return result


def platform_edit_from_row(row: dict[str, object], platform: str) -> dict[str, object]:
    edits = row.get("platform_edits")
    raw = edits.get(platform) if isinstance(edits, dict) else None
    if not isinstance(raw, dict):
        raw = resolution_edit_from_row(row, platform)
    if not isinstance(raw, dict):
        return {}
    result: dict[str, object] = {}
    for key in ("camera", "camera_path", "effect", "overlay", "overlays", "bumpers", "director_plan"):
        if key in raw:
            result[key] = raw[key]
    return result


def resolution_edit_from_row(row: dict[str, object], platform: str) -> dict[str, object]:
    edits = row.get("resolution_edits")
    if not isinstance(edits, dict):
        return {}
    raw = edits.get(resolution_key_for_platform(platform))
    return raw if isinstance(raw, dict) else {}


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
            cover_path = render_publish_cover_image(row, preset, base_dir, out_dir, ffmpeg)
            rendered.append(rendered_row(row, preset, output_path, cover_path))
    return rendered


def caption_selected_rows(
    rows: list[dict[str, object]], base_dir: Path, out_dir: Path, ffmpeg: str, args: argparse.Namespace
) -> list[dict[str, object]]:
    subtitles_dir = out_dir / "subtitles"
    subtitles_dir.mkdir(exist_ok=True)
    captioned: list[dict[str, object]] = []
    captions_enabled = bool(getattr(args, "captions_enabled", True))
    for row in rows:
        platform = str(row.get("platform") or "")
        if platform not in PLATFORM_PRESETS:
            continue
        input_path = caption_input_path(row, base_dir)
        if input_path is None:
            continue
        preset = PLATFORM_PRESETS[platform]
        stem = f"clip-{int(row.get('rank', 0)):03d}-{preset.key}"
        row_captions_enabled = captions_enabled and bool(row.get("captions_enabled", True))
        subtitle_path = subtitles_dir / f"{stem}.ass" if row_captions_enabled else None
        output_path = out_dir / f"{stem}-captioned.mp4"
        if subtitle_path:
            write_ass_subtitles(subtitle_path, row, preset, args.chars_per_line, args.max_lines)
        bumper_info = render_captioned_clip(input_path, output_path, subtitle_path, row, preset, base_dir, out_dir, ffmpeg)
        cover_path = render_publish_cover_image(row, preset, base_dir, out_dir, ffmpeg)
        cover_frame_path = render_cover_frame_tail_video(output_path, cover_path, row, preset, out_dir, ffmpeg) if caption_cover_frame_enabled(args) else None
        result = captioned_row(row, preset, output_path, subtitle_path, cover_path, cover_frame_path)
        result.update(bumper_info)
        if cover_frame_path:
            result["cover_frame_duration"] = round(float(result.get("final_duration") or caption_duration(row)) + COVER_FRAME_TAIL_SECONDS, 3)
        captioned.append(result)
    return captioned


def caption_cover_frame_enabled(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "cover_frame_enabled", False) or getattr(args, "cover_frame", False))


def apply_render_resource_to_rows(rows: list[dict[str, object]], profile: str) -> None:
    settings = render_resource_settings(profile)
    for row in rows:
        row["_render_threads"] = settings["threads"]
        row["_render_priority"] = settings["priority"]


def apply_render_job_id_to_rows(rows: list[dict[str, object]], job_id: str) -> None:
    if not job_id:
        return
    for row in rows:
        row["_render_job_id"] = job_id


def render_resource_settings(profile: str) -> dict[str, object]:
    cpus = max(os.cpu_count() or 2, 1)
    if profile == "eco":
        return {"threads": 1, "priority": "idle"}
    if profile == "high":
        return {"threads": max(cpus - 1, 1), "priority": "below_normal"}
    return {"threads": max(cpus // 2, 1), "priority": "below_normal"}


def ffmpeg_filter_thread_args(row: dict[str, object]) -> list[str]:
    threads = int(row.get("_render_threads") or 0)
    return ["-filter_complex_threads", str(max(threads, 1))] if threads > 0 else []


def ffmpeg_codec_thread_args(row: dict[str, object]) -> list[str]:
    threads = int(row.get("_render_threads") or 0)
    return ["-threads", str(max(threads, 1))] if threads > 0 else []


def ffmpeg_creation_flags(row: dict[str, object]) -> int:
    if os.name != "nt":
        return 0
    priority = str(row.get("_render_priority") or "below_normal")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if priority == "idle":
        return flags | getattr(subprocess, "IDLE_PRIORITY_CLASS", 0)
    return flags | getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)


def ffmpeg_command_with_progress(command: list[str]) -> list[str]:
    if not command:
        return command
    return [command[0], "-hide_banner", "-nostats", "-loglevel", "error", "-progress", "pipe:1", *command[1:]]


def parse_ffmpeg_time(value: str) -> float | None:
    text = value.strip()
    if not text or text == "N/A":
        return None
    match = re.fullmatch(r"(\d+):(\d{2}):(\d{2})(?:\.(\d+))?", text)
    if match:
        hours, minutes, seconds, fraction = match.groups()
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + float(f"0.{fraction or '0'}")
    try:
        return max(float(text), 0.0)
    except ValueError:
        return None


def parse_ffmpeg_progress_seconds(key: str, value: str) -> float | None:
    if key in {"out_time_us", "out_time_ms"}:
        try:
            return max(float(value) / 1_000_000.0, 0.0)
        except ValueError:
            return None
    if key == "out_time":
        return parse_ffmpeg_time(value)
    return None


def parse_ffmpeg_speed(value: str) -> float | None:
    text = value.strip().lower().removesuffix("x")
    try:
        speed = float(text)
    except ValueError:
        return None
    return speed if speed > 0 else None


def update_render_job_progress(job_id: object, processed: float, duration: float, speed_label: str = "") -> None:
    if not job_id or duration <= 0:
        return
    progress = int(clamp((processed / duration) * 84 + 12, 12, 96))
    speed = parse_ffmpeg_speed(speed_label) if speed_label else None
    remaining = max(duration - processed, 0.0)
    eta = (remaining / speed) if speed else None
    with RENDER_JOBS_LOCK:
        job = RENDER_JOBS.get(str(job_id))
        if job is None or job.status != "rendering":
            return
        if progress < job.progress and job.progress < 96:
            progress = job.progress
        job.progress = progress
        job.processed_seconds = round(max(processed, job.processed_seconds), 3)
        job.speed = speed_label.strip()
        job.eta_seconds = round(eta, 1) if eta is not None else None
        job.message = render_progress_message(job.processed_seconds, duration, job.speed, job.eta_seconds)
        job.updated_at = time.time()
        persist_render_queue(job.gallery_dir)


def render_progress_message(processed: float, duration: float, speed: str, eta: float | None) -> str:
    parts = [f"Renderizando {int(clamp((processed / max(duration, 0.1)) * 100, 0, 99))}%"]
    if speed:
        parts.append(speed)
    if eta is not None and eta >= 1:
        parts.append(f"{format_eta_seconds(eta)} restantes")
    return " - ".join(parts)


def format_eta_seconds(value: float) -> str:
    seconds = int(max(value, 0))
    minutes, sec = divmod(seconds, 60)
    if minutes:
        return f"{minutes}m {sec:02d}s"
    return f"{sec}s"


def run_ffmpeg_command(command: list[str], row: dict[str, object], cwd: str | None = None) -> None:
    duration = caption_duration(row)
    job_id = row.get("_render_job_id")
    process = subprocess.Popen(
        ffmpeg_command_with_progress(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd,
        creationflags=ffmpeg_creation_flags(row),
    )
    stdout_lines: list[str] = []
    stderr = ""
    last_progress_update = 0.0
    last_seconds = 0.0
    last_speed = ""
    while True:
        line = process.stdout.readline() if process.stdout else ""
        if line:
            stdout_lines.append(line)
            key, separator, value = line.strip().partition("=")
            if separator:
                seconds = parse_ffmpeg_progress_seconds(key, value)
                if seconds is not None:
                    last_seconds = seconds
                if key == "speed":
                    last_speed = value.strip()
                now = time.time()
                if last_seconds > 0 and now - last_progress_update >= 0.8:
                    update_render_job_progress(job_id, last_seconds, duration, last_speed)
                    last_progress_update = now
            continue
        if process.poll() is not None:
            break
        if not render_job_cancelled(job_id):
            time.sleep(0.1)
            continue
        process.terminate()
        try:
            _, stderr = process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            _, stderr = process.communicate(timeout=3)
        raise RuntimeError("Render cancelado.")
    if process.stdout:
        remaining_stdout = process.stdout.read()
        if remaining_stdout:
            stdout_lines.append(remaining_stdout)
    if process.stderr:
        stderr = process.stderr.read()
    return_code = process.wait()
    if last_seconds > 0:
        update_render_job_progress(job_id, last_seconds, duration, last_speed)
    stdout = "".join(stdout_lines)
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, command, output=stdout, stderr=stderr)


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
    style = caption_style_from_row(row, preset)
    style_width = int(style.get("width") or chars_per_line)
    events = caption_events(row, style_width, max_lines, duration)
    path.write_text(
        ass_document_with_style(events, duration, preset, style_width, max_lines, row),
        encoding="utf-8"
    )


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
    fallback_end = start + float(row.get("adjusted_duration") or 0.0)
    end = float(row.get("adjusted_end") or row.get("end") or fallback_end)
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
    clean = re.sub(r"(\d)([.,:])\s+(?=\d)", r"\1\2", clean)
    clean = re.sub(r"([,.;:!?])([^\s,.;:!?])", space_after_caption_punctuation, clean)
    clean = re.sub(r"^(né\??|aham|uhum|hum|então|mas)\s+", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\b(\w+)(\s+\1\b){2,}", r"\1", clean, flags=re.IGNORECASE)
    return clean.strip(" -")


def space_after_caption_punctuation(match: re.Match[str]) -> str:
    punctuation, next_char = match.group(1), match.group(2)
    previous_index = match.start(1) - 1
    previous_char = match.string[previous_index] if previous_index >= 0 else ""
    if punctuation in ".,:" and previous_char.isdigit() and next_char.isdigit():
        return f"{punctuation}{next_char}"
    return f"{punctuation} {next_char}"


ANIMATED_CAPTION_PROPER_NOUN_STOPWORDS = {
    "a", "as", "o", "os", "um", "uma", "uns", "umas", "de", "da", "das", "do", "dos",
    "e", "ou", "mas", "porque", "por", "para", "pra", "com", "sem", "em", "no", "na",
    "nos", "nas", "ao", "aos", "aí", "ai", "então", "entao", "só", "so", "que", "quem",
    "qual", "quando", "onde", "como", "isso", "essa", "esse", "isto", "esta", "este",
    "eu", "tu", "ele", "ela", "nós", "nos", "vocês", "voces", "você", "voce", "meu",
    "minha", "seu", "sua", "me", "te", "se", "lhe", "não", "nao", "sim", "é", "eh",
    "foi", "era", "ser", "ter", "tem", "tá", "ta", "tava", "vai", "vou", "vão", "vao",
    "fui", "faz", "fazer", "dá", "da", "dar", "precisa", "preciso", "precisava", "acho",
    "tipo", "cara", "né", "ne", "olha", "bom", "certo", "agora",
}


ANIMATED_CAPTION_FILLER_WORDS = {
    "ah", "aham", "uhum", "hum", "eh", "Ã©", "e", "aÃ­", "ai", "entÃ£o", "entao",
    "tipo", "assim", "nÃ©", "ne", "cara", "mano", "bom", "olha", "certo",
}


ANIMATED_CAPTION_ATTACH_PREVIOUS: set[str] = set()


ANIMATED_CAPTION_ATTACH_NEXT = {
    "a", "as", "o", "os", "um", "uma", "uns", "umas", "me", "te", "se", "meu", "minha", "seu", "sua",
    "de", "da", "das", "do", "dos", "com", "sem", "pra", "para", "por", "em", "no", "na", "nos", "nas", "ao", "aos",
}


def clean_animated_caption_text(text: str) -> str:
    clean = clean_caption_text(text)
    proper_nouns = animated_caption_proper_nouns(clean)
    words = [animated_caption_display_word(word, proper_nouns) for word in clean.split()]
    return " ".join(word for word in words if word)


def animated_caption_proper_nouns(text: str) -> set[str]:
    matches = list(re.finditer(r"[\wÀ-ÖØ-öø-ÿ]+", text, flags=re.UNICODE))
    result: set[str] = set()
    for index, match in enumerate(matches):
        word = match.group(0)
        if not animated_caption_is_capitalized_word(word):
            continue
        key = animated_caption_word_key(word)
        if key in ANIMATED_CAPTION_PROPER_NOUN_STOPWORDS:
            continue
        sentence_start = match.start() == 0 or bool(re.search(r"[.!?…]\s*$", text[:match.start()]))
        previous_capitalized = index > 0 and animated_caption_is_capitalized_word(matches[index - 1].group(0))
        next_capitalized = index + 1 < len(matches) and animated_caption_is_capitalized_word(matches[index + 1].group(0))
        if not sentence_start or previous_capitalized or next_capitalized:
            result.add(key)
    return result


def animated_caption_display_word(word: str, proper_nouns: set[str]) -> str:
    clean = animated_caption_clean_word(word)
    if not clean:
        return ""
    key = animated_caption_word_key(clean)
    if animated_caption_is_acronym(clean) or key in proper_nouns:
        return clean
    return clean.lower()


def animated_caption_clean_word(word: str) -> str:
    clean = re.sub(r"[^\wÀ-ÖØ-öø-ÿ.,:%]+", "", word, flags=re.UNICODE)
    result: list[str] = []
    for index, char in enumerate(clean):
        if char in ".,:":
            previous_digit = index > 0 and clean[index - 1].isdigit()
            next_digit = index + 1 < len(clean) and clean[index + 1].isdigit()
            if previous_digit and next_digit:
                result.append(char)
            continue
        if char == "%":
            if index > 0 and clean[index - 1].isdigit():
                result.append(char)
            continue
        result.append(char)
    return "".join(result)


def animated_caption_word_key(word: str) -> str:
    return re.sub(r"[^\wÀ-ÖØ-öø-ÿ]+", "", word, flags=re.UNICODE).casefold()


def animated_caption_is_capitalized_word(word: str) -> bool:
    letters = [char for char in word if char.isalpha()]
    return bool(letters) and letters[0].isupper() and not animated_caption_is_acronym(word)


def animated_caption_is_acronym(word: str) -> bool:
    letters = [char for char in word if char.isalpha()]
    return 1 < len(letters) <= 6 and "".join(letters).isupper()


def animated_caption_is_numeric_token(word: str) -> bool:
    return bool(re.search(r"\d", word))


def animated_caption_is_low_value_word(word: str) -> bool:
    return animated_caption_word_key(word) in ANIMATED_CAPTION_FILLER_WORDS


def smart_animated_caption_words(text: str, max_word_length: int, duration: float) -> list[str]:
    words = split_animated_caption_words(text, max_word_length)
    if not words:
        return []
    words = smart_animated_caption_drop_fillers(words, duration)
    return smart_animated_caption_group_words(words, duration)


def smart_animated_caption_drop_fillers(words: list[str], duration: float) -> list[str]:
    word_seconds = duration / max(len(words), 1)
    if word_seconds >= ANIMATED_CAPTION_FAST_WORD_SECONDS:
        return words
    filtered = [word for word in words if animated_caption_is_numeric_token(word) or not animated_caption_is_low_value_word(word)]
    return filtered or words


def smart_animated_caption_group_words(words: list[str], duration: float) -> list[str]:
    word_seconds = duration / max(len(words), 1)
    if word_seconds >= ANIMATED_CAPTION_TARGET_MIN_WORD_SECONDS:
        return words
    groups: list[str] = []
    for word in words:
        if smart_animated_caption_should_attach_to_previous(groups, word):
            groups[-1] = f"{groups[-1]} {word}"
            continue
        if smart_animated_caption_should_attach_next(groups, words):
            groups.append(word)
            continue
        groups.append(word)
    return smart_animated_caption_balance_groups(groups)


def smart_animated_caption_should_attach_to_previous(groups: list[str], word: str) -> bool:
    if not groups:
        return False
    key = animated_caption_word_key(word)
    if key in ANIMATED_CAPTION_ATTACH_PREVIOUS:
        return smart_animated_caption_group_size(groups[-1]) < ANIMATED_CAPTION_MAX_GROUP_WORDS
    previous = groups[-1].split()[-1]
    if animated_caption_word_key(previous) in ANIMATED_CAPTION_ATTACH_NEXT:
        return smart_animated_caption_group_size(groups[-1]) < ANIMATED_CAPTION_MAX_GROUP_WORDS
    return key == animated_caption_word_key(previous) and smart_animated_caption_group_size(groups[-1]) < ANIMATED_CAPTION_MAX_GROUP_WORDS


def smart_animated_caption_should_attach_next(groups: list[str], words: list[str]) -> bool:
    index = sum(smart_animated_caption_group_size(group) for group in groups)
    if index >= len(words):
        return False
    return animated_caption_word_key(words[index]) in ANIMATED_CAPTION_ATTACH_NEXT and index + 1 < len(words)


def smart_animated_caption_balance_groups(groups: list[str]) -> list[str]:
    result: list[str] = []
    for group in groups:
        key = animated_caption_word_key(group)
        if result and key in ANIMATED_CAPTION_ATTACH_PREVIOUS and smart_animated_caption_group_size(result[-1]) < ANIMATED_CAPTION_MAX_GROUP_WORDS:
            result[-1] = f"{result[-1]} {group}"
            continue
        result.append(group)
    return result


def smart_animated_caption_group_size(group: str) -> int:
    return len([word for word in group.split() if word])


CAPTION_MOJIBAKE_REPLACEMENTS = {
    "\u00c3\u00a1": "\u00e1",
    "\u00c3\u00a0": "\u00e0",
    "\u00c3\u00a2": "\u00e2",
    "\u00c3\u00a3": "\u00e3",
    "\u00c3\u00a4": "\u00e4",
    "\u00c3\u00a9": "\u00e9",
    "\u00c3\u00aa": "\u00ea",
    "\u00c3\u00ad": "\u00ed",
    "\u00c3\u00b3": "\u00f3",
    "\u00c3\u00b4": "\u00f4",
    "\u00c3\u00b5": "\u00f5",
    "\u00c3\u00ba": "\u00fa",
    "\u00c3\u00bc": "\u00fc",
    "\u00c3\u00a7": "\u00e7",
    "\u00c3\u0081": "\u00c1",
    "\u00c3\u0080": "\u00c0",
    "\u00c3\u0082": "\u00c2",
    "\u00c3\u0083": "\u00c3",
    "\u00c3\u0089": "\u00c9",
    "\u00c3\u008a": "\u00ca",
    "\u00c3\u008d": "\u00cd",
    "\u00c3\u0093": "\u00d3",
    "\u00c3\u0094": "\u00d4",
    "\u00c3\u0095": "\u00d5",
    "\u00c3\u009a": "\u00da",
    "\u00c3\u009c": "\u00dc",
    "\u00c3\u0087": "\u00c7",
    "\u00c2\u00ba": "\u00ba",
    "\u00c2\u00aa": "\u00aa",
    "\u00c2\u00b7": "\u00b7",
    "\u00c2\u00b4": "\u00b4",
}


def repair_caption_encoding(text: str) -> str:
    if not any(marker in text for marker in ("Ã", "Â", "â")):
        return text
    candidate = repair_caption_encoding_as_utf8(text)
    mapped = replace_caption_mojibake_sequences(candidate)
    return mapped if caption_mojibake_score(mapped) <= caption_mojibake_score(text) else text


def repair_caption_encoding_as_utf8(text: str) -> str:
    try:
        repaired = text.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return text
    return repaired if caption_mojibake_score(repaired) < caption_mojibake_score(text) else text


def replace_caption_mojibake_sequences(text: str) -> str:
    clean = text
    for source, target in CAPTION_MOJIBAKE_REPLACEMENTS.items():
        clean = clean.replace(source, target)
    return clean


def caption_mojibake_score(text: str) -> int:
    return sum(text.count(marker) for marker in ("Ã", "Â", "â€", "â™", "�"))


def normalize_caption_symbols(text: str) -> str:
    text = repair_caption_encoding(text)
    return (
        text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        .replace("…", "...").replace("♪", " ").replace("\ufeff", " ")
        .replace("–", "-").replace("—", "-")
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
    return ass_document_with_style(events, duration, preset, chars_per_line, max_lines, {})


def ass_document_with_style(
    events: list[CaptionEvent], duration: float, preset: PlatformPreset, chars_per_line: int, max_lines: int,
    row: dict[str, object]
) -> str:
    style = caption_style_from_row(row, preset)
    animated = style.get("mode") == "animated"
    dialogue = (
        ass_animated_dialogue_lines(events, duration, chars_per_line, preset, style, row)
        if animated
        else ass_dialogue_lines(events, duration, chars_per_line, max_lines)
    )
    style_lines = [ass_style_line(preset, style)]
    if animated:
        style_lines.append(ass_caption_active_style_line(preset, style))
        style_lines.append(ass_caption_side_style_line(preset, style))
        style_lines.append(ass_caption_box_style_line(preset))
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
        *style_lines,
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        *dialogue,
        "",
    ])


def ass_style_line(preset: PlatformPreset, style: dict[str, object] | None = None) -> str:
    style = style or {}
    mode = str(style.get("mode") or "on")
    font_size = int(style.get("size") or (72 if preset.height >= 1600 else 54))
    if mode == "animated":
        font_size = max(24, int(font_size * 0.82))
    margin_v = caption_margin_v(preset, style)
    outline = 7 if preset.height >= 1600 else 5
    primary = ass_color(str(style.get("text_color") or "#ffffff"), "00")
    background_key = "highlight_background_color" if mode == "animated" else "background_color"
    background = str(style.get(background_key) or style.get("background_color") or "transparent")
    if mode == "animated" and background == "transparent":
        background = "#000000"
    border_style = 3 if background != "transparent" else 1
    back_color = ass_color(background if background != "transparent" else "#000000", "33" if border_style == 3 else "99")
    outline_color = back_color if border_style == 3 else "&H00000000"
    return (
        "Style: Default,Arial,"
        f"{font_size},{primary},&H0000FFFF,{outline_color},{back_color},-1,0,0,0,100,100,0,0,{border_style},"
        f"{outline},0,2,80,80,{margin_v},1"
    )


def ass_caption_active_style_line(preset: PlatformPreset, style: dict[str, object]) -> str:
    base_size = int(style.get("size") or (72 if preset.height >= 1600 else 54))
    font_size = max(24, int(base_size * 0.82))
    outline = 7 if preset.height >= 1600 else 5
    primary = ass_color(str(style.get("text_color") or "#ffffff"), "00")
    return (
        "Style: CaptionActive,Arial,"
        f"{font_size},{primary},&H0000FFFF,&H66000000,&H99000000,-1,0,0,0,100,100,0,0,1,"
        f"{outline},0,5,80,80,{caption_margin_v(preset, style)},1"
    )


def ass_caption_side_style_line(preset: PlatformPreset, style: dict[str, object]) -> str:
    base_size = int(style.get("size") or (72 if preset.height >= 1600 else 54))
    font_size = max(22, int(base_size * 0.66))
    outline = 6 if preset.height >= 1600 else 4
    primary = ass_color(str(style.get("text_color") or "#ffffff"), "18")
    background = str(style.get("background_color") or "transparent")
    border_style = 3 if background != "transparent" else 1
    back_color = ass_color(background if background != "transparent" else "#000000", "33" if border_style == 3 else "99")
    outline_color = back_color if border_style == 3 else "&H00000000"
    return (
        "Style: CaptionSide,Arial,"
        f"{font_size},{primary},&H0000FFFF,{outline_color},{back_color},-1,0,0,0,100,100,0,0,{border_style},"
        f"{outline},0,5,80,80,{caption_margin_v(preset, style)},1"
    )


def ass_caption_box_style_line(preset: PlatformPreset) -> str:
    return (
        "Style: CaptionBox,Arial,"
        "1,&H00FFFFFF,&H0000FFFF,&HFF000000,&HFF000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1"
    )


def caption_margin_v(preset: PlatformPreset, style: dict[str, object] | None = None) -> int:
    if style and style.get("bottom") is not None:
        return int(preset.height * clamp_float(style.get("bottom"), 6.0, 32.0, 16.0) / 100.0 + 0.5)
    base_margin = 250 if preset.height >= 1600 else 95
    return int(base_margin * CUTTED_CAPTION_BOTTOM_OFFSET_MULTIPLIER + 0.5)


def caption_style_from_row(row: dict[str, object], preset: PlatformPreset) -> dict[str, object]:
    raw = row.get("caption_style")
    if not isinstance(raw, dict):
        return {}
    mode = normalize_caption_mode(raw.get("mode") or raw.get("captionMode") or raw.get("caption_mode"))
    background = normalize_caption_background_color(raw.get("backgroundColor") or raw.get("background_color"))
    highlight = normalize_caption_background_color(
        raw.get("highlightBackgroundColor")
        or raw.get("highlight_background_color")
        or raw.get("activeBackgroundColor")
        or raw.get("active_background_color")
        or background
    )
    return {
        "size": clamp_int(raw.get("size"), 24, 140, 72 if preset.height >= 1600 else 54),
        "width": clamp_int(raw.get("width"), 12, 56, 28),
        "bottom": clamp_float(raw.get("bottom") or raw.get("height"), 6.0, 32.0, default_caption_bottom_percent(preset)),
        "mode": mode,
        "text_color": normalize_hex_color(raw.get("textColor") or raw.get("text_color"), "#ffffff"),
        "background_color": background,
        "highlight_background_color": highlight,
    }


def default_caption_bottom_percent(preset: PlatformPreset) -> float:
    return round(caption_margin_v(preset) / max(preset.height, 1) * 100.0, 2)


def normalize_caption_mode(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"animated", "animada"}:
        return "animated"
    if text in {"off", "false", "0"}:
        return "off"
    return "on"


def clamp_float(value: object, minimum: float, maximum: float, fallback: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    return max(minimum, min(maximum, number))


def clamp_int(value: object, minimum: int, maximum: int, fallback: int) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return fallback
    return max(minimum, min(maximum, number))


def normalize_hex_color(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    return text.lower() if re.fullmatch(r"#[0-9a-fA-F]{6}", text) else fallback


def normalize_caption_background_color(value: object) -> str:
    text = str(value or "").strip().lower()
    if not text or text in {"none", "transparent"}:
        return "transparent"
    return normalize_hex_color(text, "#000000")


def ass_color(value: str, alpha: str) -> str:
    color = normalize_hex_color(value, "#000000").lstrip("#")
    red, green, blue = color[0:2], color[2:4], color[4:6]
    return f"&H{alpha}{blue}{green}{red}".upper()


def ass_alpha_from_opacity(opacity: float) -> str:
    alpha = int(round((1.0 - clamp(opacity, 0.0, 1.0)) * 255))
    return f"{alpha:02X}"


def ass_rgb_color(value: str) -> str:
    color = normalize_hex_color(value, "#000000").lstrip("#")
    red, green, blue = color[0:2], color[2:4], color[4:6]
    return f"&H{blue}{green}{red}&".upper()


def ass_dialogue_lines(events: list[CaptionEvent], duration: float, chars_per_line: int, max_lines: int) -> list[str]:
    lines: list[str] = []
    for event in events:
        start = min(max(event.start, 0.0), duration)
        end = min(max(event.end, start + 0.15), duration)
        text = ass_escape_text(wrap_caption_text(event.text, chars_per_line, max_lines))
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{text}")
    return lines


def ass_animated_dialogue_lines(
    events: list[CaptionEvent], duration: float, chars_per_line: int, preset: PlatformPreset, style: dict[str, object],
    row: dict[str, object] | None = None,
) -> list[str]:
    lines: list[str] = []
    active_size = max(24, int(int(style.get("size") or (72 if preset.height >= 1600 else 54)) * 0.82))
    side_size = max(22, int(int(style.get("size") or active_size) * 0.66))
    center_x = preset.width // 2
    center_y = ass_animated_caption_center_y(preset, style, active_size)
    side_y = center_y + max(3, int(active_size * 0.08))
    previous_end = 0.0
    canonical_windows = animated_caption_windows_from_row(row or {}, duration)
    windows = canonical_windows or animated_caption_window_events(events, duration, chars_per_line)
    for window in windows:
        start, end = (
            animated_caption_canonical_window_times(window, duration, previous_end)
            if canonical_windows
            else animated_caption_render_window_times(window, duration, previous_end)
        )
        if end <= start:
            continue
        previous_end = end
        if window.previous:
            prev_x = int(clamp(center_x - ass_caption_side_offset(window.previous, window.active, active_size, side_size), 70, preset.width - 70))
            lines.append(ass_animated_dialogue_line(0, start, end, "CaptionSide", window.previous, prev_x, side_y, ""))
        if window.next:
            next_x = int(clamp(center_x + ass_caption_side_offset(window.next, window.active, active_size, side_size), 70, preset.width - 70))
            lines.append(ass_animated_dialogue_line(0, start, end, "CaptionSide", window.next, next_x, side_y, ""))
        pop = r"\fad(25,70)\t(0,90,\fscx112\fscy112)\t(90,190,\fscx100\fscy100)"
        lines.extend(ass_animated_caption_box_lines(start, end, window.active, center_x, center_y, active_size, style))
        lines.append(ass_animated_dialogue_line(3, start, end, "CaptionActive", window.active, center_x, center_y, pop))
    return lines


def animated_caption_windows_from_row(row: dict[str, object], duration: float) -> list[AnimatedCaptionWindow]:
    raw = row.get("animated_caption_windows")
    if not isinstance(raw, list):
        return []
    windows: list[AnimatedCaptionWindow] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        active = clean_animated_caption_text(str(item.get("active") or ""))
        if not active:
            continue
        start = clamp_float(item.get("start"), 0.0, duration, 0.0)
        end = clamp_float(item.get("end"), 0.0, duration, start)
        if end <= start:
            continue
        previous = clean_animated_caption_text(str(item.get("previous") or ""))
        next_text = clean_animated_caption_text(str(item.get("next") or ""))
        windows.append(AnimatedCaptionWindow(round(start, 3), round(end, 3), previous, active, next_text))
    return sorted(windows, key=lambda window: (window.start, window.end))


def animated_caption_canonical_window_times(
    window: AnimatedCaptionWindow, duration: float, previous_end: float = 0.0
) -> tuple[float, float]:
    start = min(max(window.start, previous_end, 0.0), duration)
    end = min(max(window.end, start + 0.08), duration)
    return round(start, 3), round(end, 3)


def animated_caption_render_window_times(
    window: AnimatedCaptionWindow, duration: float, previous_end: float = 0.0
) -> tuple[float, float]:
    raw_start = min(max(window.start, 0.0), duration)
    raw_end = min(max(window.end, raw_start + ANIMATED_CAPTION_MIN_RENDER_SECONDS), duration)
    raw_duration = max(raw_end - raw_start, ANIMATED_CAPTION_MIN_RENDER_SECONDS)
    start = min(max(raw_start - ANIMATED_CAPTION_LEAD_SECONDS, 0.0), duration)
    end = min(max(raw_end - ANIMATED_CAPTION_LEAD_SECONDS, start + ANIMATED_CAPTION_MIN_RENDER_SECONDS), duration)
    if raw_start <= ANIMATED_CAPTION_LEAD_SECONDS:
        end = min(max(end, start + raw_duration), duration)
    if start < previous_end:
        start = min(previous_end, duration)
        end = min(max(end, start + ANIMATED_CAPTION_MIN_RENDER_SECONDS), duration)
    return round(start, 3), round(end, 3)


def ass_animated_caption_box_lines(
    start: float, end: float, text: str, center_x: int, center_y: int, font_size: int,
    style: dict[str, object],
) -> list[str]:
    width = int(ass_caption_word_width(text, font_size) + font_size * 0.88 + 0.5)
    height = int(font_size * 1.28 + 0.5)
    radius = max(6, int(font_size * 0.25 + 0.5))
    shape = ass_rounded_rect_path(width, height, radius)
    color = ass_rgb_color(str(style.get("highlight_background_color") or "#000000"))
    top_left_x = center_x - (width // 2)
    top_left_y = center_y - (height // 2) + max(5, int(font_size * 0.16 + 0.5))
    shadow_y = top_left_y + max(5, font_size // 9)
    shadow_alpha = ass_alpha_from_opacity(ANIMATED_CAPTION_BOX_SHADOW_OPACITY)
    fill_alpha = ass_alpha_from_opacity(ANIMATED_CAPTION_BOX_OPACITY)
    border_alpha = ass_alpha_from_opacity(0.12)
    shadow = ass_vector_dialogue_line(1, start, end, top_left_x, shadow_y, shape, "&H000000&", shadow_alpha, "", "")
    fill = ass_vector_dialogue_line(
        2, start, end, top_left_x, top_left_y, shape, color, fill_alpha, r"\fad(25,70)", rf"\bord2\3c&HFFFFFF&\3a&H{border_alpha}"
    )
    return [shadow, fill]


def ass_vector_dialogue_line(
    layer: int, start: float, end: float, x: int, y: int, shape: str, color: str, alpha: str, tags: str, border: str
) -> str:
    vector_tags = rf"{{\an7\pos({x},{y})\p1\1c{color}\1a&H{alpha}&\bord0\shad0{border}{tags}}}"
    return f"Dialogue: {layer},{ass_time(start)},{ass_time(end)},CaptionBox,,0,0,0,,{vector_tags}{shape}"


def ass_rounded_rect_path(width: int, height: int, radius: int) -> str:
    width = max(2, width)
    height = max(2, height)
    radius = max(1, min(radius, width // 2, height // 2))
    points = ass_rounded_rect_points(width, height, radius)
    first, *rest = points
    return " ".join([f"m {first[0]} {first[1]}", *(f"l {x} {y}" for x, y in rest)])


def ass_rounded_rect_points(width: int, height: int, radius: int) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    corners = (
        (width - radius, radius, -90, 0),
        (width - radius, height - radius, 0, 90),
        (radius, height - radius, 90, 180),
        (radius, radius, 180, 270),
    )
    for cx, cy, start_angle, end_angle in corners:
        for step in range(5):
            angle = math.radians(start_angle + (end_angle - start_angle) * step / 4)
            points.append((int(round(cx + math.cos(angle) * radius)), int(round(cy + math.sin(angle) * radius))))
    return points


def ass_animated_dialogue_line(
    layer: int, start: float, end: float, style_name: str, text: str, x: int, y: int, tags: str
) -> str:
    text_value = ass_escape_text(text)
    position = rf"{{\an5\pos({x},{y}){tags}}}"
    return f"Dialogue: {layer},{ass_time(start)},{ass_time(end)},{style_name},,0,0,0,,{position}{text_value}"


def ass_animated_caption_center_y(preset: PlatformPreset, style: dict[str, object], font_size: int) -> int:
    margin = caption_margin_v(preset, style)
    return int(max(font_size, preset.height - margin - (font_size * 0.55)) + 0.5)


def ass_caption_side_offset(side: str, active: str, active_size: int, side_size: int) -> int:
    active_width = ass_caption_word_width(active, active_size)
    side_width = ass_caption_word_width(side, side_size)
    gap = max(22, int(active_size * 0.62))
    return int((active_width / 2) + (side_width / 2) + gap + 0.5)


def ass_caption_word_width(text: str, font_size: int) -> float:
    wide = sum(1 for char in text if char in "mwMW@#%&")
    narrow = sum(1 for char in text if char in "ilI.,'!|")
    normal = max(len(text) - wide - narrow, 0)
    return (normal * 0.56 + wide * 0.78 + narrow * 0.28) * font_size


def animated_caption_word_events(events: list[CaptionEvent], duration: float, chars_per_line: int) -> list[CaptionEvent]:
    result: list[CaptionEvent] = []
    max_word_length = max(8, min(chars_per_line, 18))
    for event in events:
        start = clamp(event.start, 0.0, duration)
        end = clamp(event.end, start + 0.12, duration)
        words = smart_animated_caption_words(event.text, max_word_length, end - start)
        if not words:
            continue
        for index, word, word_start, word_end in animated_caption_word_timings(words, start, end):
            if word_end - word_start >= 0.08:
                result.append(CaptionEvent(round(word_start, 3), round(word_end, 3), word))
    return result


def animated_caption_word_timings(words: list[str], start: float, end: float) -> list[tuple[int, str, float, float]]:
    duration = max(end - start, 0.12)
    weights = [animated_caption_word_weight(word) for word in words]
    total = sum(weights) or float(len(words) or 1)
    cursor = start
    timings: list[tuple[int, str, float, float]] = []
    for index, word in enumerate(words):
        word_end = end if index == len(words) - 1 else min(end, cursor + (duration * weights[index] / total))
        timings.append((index, word, cursor, word_end))
        cursor = word_end
    return merge_fast_animated_caption_timings(timings)


def merge_fast_animated_caption_timings(
    timings: list[tuple[int, str, float, float]]
) -> list[tuple[int, str, float, float]]:
    groups = [{"word": word, "start": start, "end": end} for _, word, start, end in timings]
    while len(groups) > 1:
        index = next(
            (
                current
                for current, group in enumerate(groups)
                if float(group["end"]) - float(group["start"]) < ANIMATED_CAPTION_MIN_RENDER_SECONDS
            ),
            -1,
        )
        if index < 0:
            break
        target = index + 1 if index + 1 < len(groups) else index - 1
        first_index, second_index = sorted((index, target))
        first = groups[first_index]
        second = groups[second_index]
        merged = {
            "word": f'{first["word"]} {second["word"]}',
            "start": first["start"],
            "end": second["end"],
        }
        groups[first_index:second_index + 1] = [merged]
    return [
        (index, str(group["word"]), float(group["start"]), float(group["end"]))
        for index, group in enumerate(groups)
    ]


def animated_caption_word_weight(word: str) -> float:
    core = re.sub(r"\W+", "", word, flags=re.UNICODE)
    return max(0.7, min(math.sqrt(max(len(core), 1)), 3.0))


def animated_caption_window_events(events: list[CaptionEvent], duration: float, chars_per_line: int) -> list[AnimatedCaptionWindow]:
    result: list[AnimatedCaptionWindow] = []
    max_word_length = max(8, min(chars_per_line, 18))
    for event in events:
        start = clamp(event.start, 0.0, duration)
        end = clamp(event.end, start + 0.12, duration)
        words = smart_animated_caption_words(event.text, max_word_length, end - start)
        if not words:
            continue
        timings = animated_caption_word_timings(words, start, end)
        for index, word, word_start, word_end in timings:
            if word_end - word_start < 0.08:
                continue
            result.append(AnimatedCaptionWindow(
                round(word_start, 3),
                round(word_end, 3),
                timings[index - 1][1] if index > 0 else "",
                word,
                timings[index + 1][1] if index + 1 < len(timings) else "",
            ))
    return result


def split_animated_caption_words(text: str, max_word_length: int) -> list[str]:
    words = [word.strip() for word in re.split(r"\s+", clean_animated_caption_text(text)) if word.strip()]
    return [word if len(word) <= max_word_length else f"{word[:max_word_length - 1]}..." for word in words]


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
    input_path: Path, output_path: Path, subtitle_path: Path | None, row: dict[str, object],
    preset: PlatformPreset, base_dir: Path, out_dir: Path, ffmpeg: str
) -> dict[str, object]:
    filters = [f"ass={subtitle_filter_path(subtitle_path, out_dir)}"] if subtitle_path else []
    effect = effect_filter(row)
    if effect:
        filters.append(effect)
    overlay = overlay_filter(row, preset)
    if overlay:
        filters.append(overlay)
    command = captioned_ffmpeg_command(input_path, output_path, row, preset, ffmpeg, filters)
    run_ffmpeg_command(command, row, cwd=str(out_dir))
    return apply_bumpers_to_output(output_path, row, preset, base_dir, out_dir, ffmpeg)


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
    row: dict[str, object], preset: PlatformPreset, output_path: Path, subtitle_path: Path | None,
    cover_path: Path | None = None, cover_frame_path: Path | None = None,
) -> dict[str, object]:
    base_duration = caption_duration(row)
    return {
        "rank": row.get("rank"),
        "platform": preset.key,
        "label": preset.label,
        "width": preset.width,
        "height": preset.height,
        "file": str(output_path),
        "subtitle_file": str(subtitle_path) if subtitle_path else "",
        "captions_enabled": bool(subtitle_path),
        "caption_style": caption_style_from_row(row, preset),
        "adjusted_start": row.get("adjusted_start"),
        "adjusted_end": row.get("adjusted_end"),
        "adjusted_duration": base_duration,
        "base_duration": base_duration,
        "final_duration": base_duration,
        "cover_file": str(cover_path) if cover_path else "",
        "cover_frame_file": str(cover_frame_path) if cover_frame_path else "",
        "cover_frame_duration": round(base_duration + COVER_FRAME_TAIL_SECONDS, 3) if cover_frame_path else 0.0,
        "publish_metadata": row.get("publish_metadata") if isinstance(row.get("publish_metadata"), dict) else {},
        "camera": camera_from_row(row),
        "camera_path": camera_path_from_row(row, base_duration),
        "effect": effect_from_row(row),
        "overlay": overlay_from_row(row),
        "overlays": overlay_layers_from_row(row),
        "bumpers": normalize_bumpers_from_row(row),
    }


def apply_bumpers_to_output(
    output_path: Path, row: dict[str, object], preset: PlatformPreset, base_dir: Path, out_dir: Path, ffmpeg: str
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
        intro = resolve_bumper_asset_path(base_dir, bumpers["intro"])
        intro_duration = bumper_duration(bumpers["intro"], intro, ffmpeg)
        intro_segment = work_dir / "intro.mp4"
        normalize_bumper_segment(intro, intro_segment, intro_duration, preset, ffmpeg, row)
        segments.append(intro_segment)
    core_segment = work_dir / "core.mp4"
    normalize_bumper_segment(core_source, core_segment, base_duration, preset, ffmpeg, row)
    segments.append(core_segment)
    if "outro" in bumpers:
        outro = resolve_bumper_asset_path(base_dir, bumpers["outro"])
        outro_duration = bumper_duration(bumpers["outro"], outro, ffmpeg)
        outro_segment = work_dir / "outro.mp4"
        normalize_bumper_segment(outro, outro_segment, outro_duration, preset, ffmpeg, row)
        segments.append(outro_segment)
    concat_path = work_dir / "concat.txt"
    concat_path.write_text("".join(concat_file_entry(path) for path in segments), encoding="utf-8")
    temp_output = work_dir / "final.mp4"
    command = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_path), "-c", "copy", "-movflags", "+faststart", str(temp_output)]
    run_ffmpeg_command(command, row)
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
    source: Path, output: Path, duration: float, preset: PlatformPreset, ffmpeg: str, row: dict[str, object]
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
    if media_has_audio(source, ffmpeg):
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
        "-crf", FINAL_VIDEO_CRF,
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-movflags", "+faststart",
        str(output),
    ])
    run_ffmpeg_command(command, row)


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


def resolve_bumper_asset_path(base_dir: Path, bumper: dict[str, object]) -> Path:
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


def normalize_platforms(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    seen_resolutions: set[str] = set()
    for item in value:
        platform = str(item)
        if platform not in PLATFORM_PRESETS:
            continue
        representative = representative_platform(platform)
        resolution = resolution_key_for_platform(representative)
        if resolution in seen_resolutions:
            continue
        seen_resolutions.add(resolution)
        result.append(representative)
    return result


def representative_platform(platform: str) -> str:
    destinations = resolution_preset_for_platform(platform).destinations
    return destinations[0] if destinations else "tiktok"


def resolve_media_path(base_dir: Path, clip_file: str) -> Path:
    path = Path(clip_file)
    return path if path.is_absolute() else base_dir / path


def render_cover_frame_tail_video(
    video_path: Path,
    cover_path: Path | None,
    row: dict[str, object],
    preset: PlatformPreset,
    out_dir: Path,
    ffmpeg: str,
) -> Path | None:
    if cover_path is None or not cover_path.exists() or not video_path.exists():
        return None
    output = out_dir / f"clip-{int(row.get('rank', 0)):03d}-{preset.key}-cover-frame.mp4"
    work_dir = out_dir / "cover-frame-work" / f"{output.stem}-{uuid.uuid4().hex[:8]}"
    work_dir.mkdir(parents=True, exist_ok=False)
    try:
        cover_segment = work_dir / "cover-frame.mp4"
        render_cover_frame_segment(cover_path, cover_segment, media_has_audio(video_path, ffmpeg), preset, row, ffmpeg)
        concat_path = work_dir / "concat.txt"
        concat_path.write_text(concat_file_entry(video_path) + concat_file_entry(cover_segment), encoding="utf-8")
        temp_output = work_dir / "cover-frame-final.mp4"
        command = [
            ffmpeg,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(temp_output),
        ]
        try:
            run_ffmpeg_command(command, row, cwd=str(out_dir))
        except subprocess.CalledProcessError:
            temp_output = work_dir / "cover-frame-final-reencoded.mp4"
            fallback = [
                ffmpeg,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_path),
                *mp4_output_args(row),
                str(temp_output),
            ]
            run_ffmpeg_command(fallback, row, cwd=str(out_dir))
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
) -> None:
    duration = fmt_time(COVER_FRAME_TAIL_SECONDS)
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
    run_ffmpeg_command(command, row)


def render_publish_cover_image(
    row: dict[str, object], preset: PlatformPreset, base_dir: Path, out_dir: Path, ffmpeg: str
) -> Path | None:
    cover = publish_cover_from_row(row)
    frame = str(cover.get("selected_frame") or "").strip()
    if not frame:
        return None
    source = resolve_media_path(base_dir, frame)
    if not source.exists() or not source.is_file():
        return None
    output = out_dir / f"clip-{int(row.get('rank', 0)):03d}-{preset.key}-cover.jpg"
    if render_publish_cover_image_with_pillow(source, output, cover, preset):
        return output
    command = publish_cover_ffmpeg_command(source, output, cover, preset, ffmpeg)
    run_ffmpeg_command(command, row, cwd=str(out_dir))
    return output


def render_publish_cover_image_with_pillow(source: Path, output: Path, cover: dict[str, object], preset: PlatformPreset) -> bool:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False
    with Image.open(source) as loaded:
        canvas = pillow_cover_base_image(loaded.convert("RGBA"), cover, preset, Image)
    draw = ImageDraw.Draw(canvas, "RGBA")
    for layer in cover_overlay_layers(cover):
        if layer.get("kind") == "image":
            pillow_draw_cover_image_layer(canvas, layer, preset, Image)
        elif layer.get("kind") == "speech":
            pillow_draw_cover_text_layer(draw, layer, preset, ImageFont, True)
        elif layer.get("kind") == "text":
            pillow_draw_cover_text_layer(draw, layer, preset, ImageFont, False)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output, "JPEG", quality=94, optimize=True)
    return output.exists() and output.stat().st_size > 0


def pillow_cover_base_image(image: object, cover: dict[str, object], preset: PlatformPreset, image_module: object) -> object:
    zoom = clamp(float(cover.get("zoom") if cover.get("zoom") is not None else 1.0), 1.0, 1.8)
    base = pillow_cover_object_fit_image(image, preset, image_module)
    if zoom <= 1.001:
        return base
    resized = base.resize((int(round(preset.width * zoom)), int(round(preset.height * zoom))), pillow_resampling_filter(image_module))
    crop_x = clamp(float(cover.get("x") if cover.get("x") is not None else 50.0), 0.0, 100.0) / 100.0
    crop_y = clamp(float(cover.get("y") if cover.get("y") is not None else 50.0), 0.0, 100.0) / 100.0
    left = int(round(preset.width * (zoom - 1.0) * crop_x))
    top = int(round(preset.height * (zoom - 1.0) * crop_y))
    return resized.crop((left, top, left + preset.width, top + preset.height))


def pillow_cover_object_fit_image(image: object, preset: PlatformPreset, image_module: object) -> object:
    scale = max(preset.width / max(image.width, 1), preset.height / max(image.height, 1))
    resized_w = max(preset.width, int(math.ceil(image.width * scale)))
    resized_h = max(preset.height, int(math.ceil(image.height * scale)))
    resized = image.resize((resized_w, resized_h), pillow_resampling_filter(image_module))
    left = int(round(max(resized_w - preset.width, 0) * 0.5))
    top = int(round(max(resized_h - preset.height, 0) * 0.5))
    return resized.crop((left, top, left + preset.width, top + preset.height))


def pillow_resampling_filter(image_module: object) -> object:
    resampling = getattr(image_module, "Resampling", None)
    return getattr(resampling, "LANCZOS", getattr(image_module, "LANCZOS", 1))


def pillow_draw_cover_image_layer(canvas: object, layer: dict[str, object], preset: PlatformPreset, image_module: object) -> None:
    image_file = str(layer.get("image_file") or "")
    if not image_file:
        return
    with image_module.open(image_file) as loaded:
        image = loaded.convert("RGBA")
    width = max(1, int(round(preset.width * float(layer.get("width") or 0.28))))
    height = max(1, int(round(image.height * (width / max(image.width, 1)))))
    image = image.resize((width, height), pillow_resampling_filter(image_module))
    opacity = clamp(float(layer.get("opacity") or 100.0) / 100.0, 0.1, 1.0)
    if opacity < 0.999:
        alpha = image.getchannel("A").point(lambda value: int(value * opacity))
        image.putalpha(alpha)
    x = min(int(round(preset.width * float(layer.get("x") or 0.0))), max(preset.width - width, 0))
    y = min(int(round(preset.height * float(layer.get("y") or 0.0))), max(preset.height - height, 0))
    canvas.alpha_composite(image, (x, y))


def pillow_cover_preview_px(value: float, preset: PlatformPreset) -> int:
    return int(round(value * preset.width / COVER_PREVIEW_CANONICAL_WIDTH))


def pillow_cover_font_size(layer: dict[str, object], preset: PlatformPreset) -> int:
    preview_size = float(layer.get("font_size") or 34.0) * COVER_LAYER_PREVIEW_FONT_SCALE
    return max(18, pillow_cover_preview_px(preview_size, preset))


def pillow_draw_cover_text_layer(
    draw: object, layer: dict[str, object], preset: PlatformPreset, image_font: object, speech: bool
) -> None:
    text = str(layer.get("text") or layer.get("label") or "").strip()
    if not text:
        return
    font_size = pillow_cover_font_size(layer, preset)
    font = image_font.truetype(str(find_overlay_font()), font_size)
    box = pillow_cover_text_box(draw, layer, preset, font, font_size, speech)
    x, y, box_w, box_h, pad_x, pad_y, line_height, lines = box
    opacity = clamp(float(layer.get("opacity") or 100.0) / 100.0, 0.1, 1.0)
    if speech or bool(layer.get("background_enabled")):
        pillow_draw_cover_text_background(draw, layer, (x, y, box_w, box_h), font_size, opacity, speech, preset)
    text_color = pillow_rgba(layer.get("color"), "#050505" if speech else "#ffffff", opacity)
    for index, line in enumerate(lines):
        draw.text((x + pad_x, y + pad_y + index * line_height), line, fill=text_color, font=font)


def pillow_cover_text_box(
    draw: object, layer: dict[str, object], preset: PlatformPreset, font: object, font_size: int, speech: bool
) -> tuple[int, int, int, int, int, int, int, list[str]]:
    box_w = max(1, int(round(preset.width * float(layer.get("width") or 0.42))))
    x = min(int(round(preset.width * float(layer.get("x") or 0.0))), max(preset.width - box_w, 0))
    pad_x = max(10, int(round(font_size * (0.44 if speech else 0.35))))
    pad_y = max(8, int(round(font_size * (0.32 if speech else 0.26))))
    lines = pillow_wrap_text(draw, str(layer.get("text") or layer.get("label") or ""), font, max(box_w - pad_x * 2, 1))
    line_height = max(font_size, pillow_text_size(draw, "Ag", font)[1]) + max(2, int(round(font_size * 0.12)))
    min_height = int(round(font_size * (1.95 if speech else 1.65)))
    box_h = max(min_height, len(lines) * line_height + pad_y * 2)
    y = min(int(round(preset.height * float(layer.get("y") or 0.0))), max(preset.height - box_h, 0))
    return x, y, box_w, box_h, pad_x, pad_y, line_height, lines


def pillow_wrap_text(draw: object, text: str, font: object, max_width: int) -> list[str]:
    words = text.split()
    if not words:
        return [text]
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or pillow_text_size(draw, candidate, font)[0] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:2] or [text]


def pillow_text_size(draw: object, text: str, font: object) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return max(1, right - left), max(1, bottom - top)


def pillow_draw_cover_text_background(
    draw: object,
    layer: dict[str, object],
    rect: tuple[int, int, int, int],
    font_size: int,
    opacity: float,
    speech: bool,
    preset: PlatformPreset,
) -> None:
    x, y, box_w, box_h = rect
    bg_opacity = clamp(float(layer.get("background_opacity") if layer.get("background_opacity") is not None else 94.0) / 100.0, 0.0, 1.0)
    background = pillow_rgba(layer.get("background_color"), "#ffffff" if speech else "#000000", opacity * bg_opacity)
    radius = pillow_cover_preview_px(COVER_SPEECH_RADIUS_PREVIEW_PX, preset) if speech else max(6, int(round(font_size * 0.18)))
    if speech:
        pillow_draw_cover_speech_tail(draw, (x, y, box_w, box_h), background, preset)
        draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=radius, fill=background)
    else:
        draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=radius, fill=background)


def pillow_draw_cover_speech_tail(
    draw: object, rect: tuple[int, int, int, int], color: tuple[int, int, int, int], preset: PlatformPreset
) -> None:
    x, y, box_w, box_h = rect
    tail_w = pillow_cover_preview_px(COVER_SPEECH_TAIL_WIDTH_PREVIEW_PX, preset)
    tail_h = pillow_cover_preview_px(COVER_SPEECH_TAIL_HEIGHT_PREVIEW_PX, preset)
    tail_x = x + int(round(box_w * 0.18))
    tail_y = y + box_h + pillow_cover_preview_px(COVER_SPEECH_TAIL_BOTTOM_PREVIEW_PX, preset)
    skew = max(2, int(round(math.tan(math.radians(18.0)) * tail_h)))
    points = [
        (tail_x + skew, tail_y),
        (tail_x + tail_w + skew, tail_y),
        (tail_x + tail_w, tail_y + tail_h),
        (tail_x, tail_y + tail_h),
    ]
    draw.polygon(points, fill=color)


def pillow_rgba(value: object, fallback: str, opacity: float) -> tuple[int, int, int, int]:
    color = normalize_hex_color(value, fallback).lstrip("#")
    alpha = int(round(255 * clamp(opacity, 0.0, 1.0)))
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16), alpha


def publish_cover_from_row(row: dict[str, object]) -> dict[str, object]:
    metadata = row.get("publish_metadata")
    if not isinstance(metadata, dict):
        return {}
    cover = metadata.get("cover")
    return cover if isinstance(cover, dict) else {}


def publish_cover_ffmpeg_command(
    source: Path, output: Path, cover: dict[str, object], preset: PlatformPreset, ffmpeg: str
) -> list[str]:
    layers = cover_overlay_layers(cover)
    image_layers = [layer for layer in layers if layer.get("kind") == "image" and str(layer.get("image_file") or "")]
    base = [ffmpeg, "-y", "-i", str(source)]
    if image_layers:
        return [
            *base, "-filter_complex", publish_cover_complex_filter(cover, layers, preset),
            "-map", "[vout]", "-frames:v", "1", "-q:v", "2", str(output),
        ]
    return [
        *base, "-vf", publish_cover_simple_filter(cover, layers, preset),
        "-frames:v", "1", "-q:v", "2", str(output),
    ]


def publish_cover_simple_filter(cover: dict[str, object], layers: list[dict[str, object]], preset: PlatformPreset) -> str:
    filters = [publish_cover_base_filter(cover, preset)]
    overlay = overlay_filter({"overlays": layers}, preset)
    if overlay:
        filters.append(overlay)
    filters.append("format=yuv420p")
    return ",".join(filters)


def publish_cover_complex_filter(cover: dict[str, object], layers: list[dict[str, object]], preset: PlatformPreset) -> str:
    non_image_layers = [layer for layer in layers if layer.get("kind") != "image"]
    base_filters = [publish_cover_base_filter(cover, preset)]
    overlay = overlay_filter({"overlays": non_image_layers}, preset)
    if overlay:
        base_filters.append(overlay)
    parts = [f"[0:v]{','.join(base_filters)}[vbase]"]
    previous = "vbase"
    image_layers = [layer for layer in layers if layer.get("kind") == "image" and str(layer.get("image_file") or "")]
    for index, layer in enumerate(image_layers):
        image_label = f"coverimg{index}"
        output_label = f"vcover{index}"
        parts.append(image_overlay_source_filter(layer, preset, image_label))
        parts.append(image_overlay_compose_filter(layer, preset, previous, image_label, output_label))
        previous = output_label
    parts.append(f"[{previous}]format=yuv420p[vout]")
    return ";".join(parts)


def publish_cover_base_filter(cover: dict[str, object], preset: PlatformPreset) -> str:
    zoom = clamp(float(cover.get("zoom") if cover.get("zoom") is not None else 1.0), 1.0, 1.8)
    crop_x = clamp(float(cover.get("x") if cover.get("x") is not None else 50.0), 0.0, 100.0) / 100.0
    crop_y = clamp(float(cover.get("y") if cover.get("y") is not None else 50.0), 0.0, 100.0) / 100.0
    return ",".join([
        f"scale={int(round(preset.width * zoom))}:{int(round(preset.height * zoom))}:force_original_aspect_ratio=increase",
        f"crop={preset.width}:{preset.height}:x='(iw-ow)*{crop_x:.4f}':y='(ih-oh)*{crop_y:.4f}'",
        "setsar=1",
    ])


def cover_overlay_layers(cover: dict[str, object]) -> list[dict[str, object]]:
    layers = cover.get("layers")
    if not isinstance(layers, list):
        return []
    result = [static_cover_overlay_layer(layer) for layer in layers if isinstance(layer, dict)]
    return [layer for layer in result if layer.get("key") != "none"]


def static_cover_overlay_layer(layer: dict[str, object]) -> dict[str, object]:
    normalized = overlay_layer_from_raw(layer)
    normalized["y"] = lifted_cover_layer_y(float(normalized.get("y") or 0.0))
    normalized["start_seconds"] = 0.0
    normalized["duration_seconds"] = 9999.0
    return normalized


def lifted_cover_layer_y(y: float) -> float:
    return clamp(y - COVER_LAYER_VERTICAL_LIFT, 0.0, 1.0)


def render_platform_clip(
    input_path: Path, output_path: Path, start: float, duration: float,
    preset: PlatformPreset, row: dict[str, object], ffmpeg: str
) -> None:
    filters = post_camera_filters(preset, row)
    base = [
        ffmpeg, "-y", "-ss", fmt_time(start), "-i", str(input_path), "-t", fmt_time(duration),
    ]
    command = render_command(base, output_path, row, preset, filters, duration)
    run_ffmpeg_command(command, row)


def render_command(
    base: list[str], output_path: Path, row: dict[str, object], preset: PlatformPreset,
    filters: list[str], duration: float
) -> list[str]:
    if image_overlay_layers_from_row(row):
        filter_arg = image_overlay_complex_filter(preset, row, duration, filters)
        return [
            *base, *ffmpeg_filter_thread_args(row), "-filter_complex", filter_arg, "-map", "[vout]", "-map", "0:a?",
            *mp4_output_args(row), str(output_path),
        ]
    if camera_is_path(row):
        filter_arg = camera_path_filter(preset, row, duration, filters)
        return [
            *base, *ffmpeg_filter_thread_args(row), "-filter_complex", filter_arg, "-map", "[vout]", "-map", "0:a?",
            *mp4_output_args(row), str(output_path),
        ]
    if camera_is_sequence(row):
        filter_arg = camera_sequence_filter(preset, row, duration, filters)
        return [
            *base, *ffmpeg_filter_thread_args(row), "-filter_complex", filter_arg, "-map", "[vout]", "-map", "0:a?",
            *mp4_output_args(row), str(output_path),
        ]
    filter_arg = ",".join([camera_filter(preset, row), *filters])
    return [
        *base, "-vf", filter_arg,
        *mp4_output_args(row), str(output_path),
    ]


def mp4_output_args(row: dict[str, object]) -> list[str]:
    return [
        "-c:v", "libx264",
        "-preset", "medium",
        "-profile:v", "main",
        "-level", "4.1",
        *ffmpeg_codec_thread_args(row),
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-crf", video_crf(row),
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-movflags", "+faststart",
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
    if camera_is_path(row):
        bounds = camera_path_bounds(row, duration)
        parts.extend(camera_path_split_filters_for_bounds(preset, bounds))
        base = camera_concat_filter(len(bounds), "cp", tail)
        parts.append(f"{base}[vbase]")
    elif camera_is_sequence(row):
        parts.extend(camera_split_filters(preset, camera_from_row(row).get("segments"), duration))
        base = camera_concat_filter(3, "cv", tail)
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
    enable = timed_overlay_enable(overlay)
    return f"[{input_label}][{image_label}]overlay={x}:{y}:format=auto:eof_action=repeat{enable}[{output_label}]"


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


def camera_filter_from_path_frame(preset: PlatformPreset, frame: dict[str, object]) -> str:
    key = str(frame.get("key") or "")
    if key in CAMERA_PRESETS:
        return camera_filter_from_camera(preset, frame)
    zoom = clamp(float(frame.get("zoom") or 1.0), 1.0, 2.0)
    target_w = int(round(preset.width * zoom))
    target_h = int(round(preset.height * zoom))
    x = crop_ratio_expr(float(frame.get("x") or 50.0) / 100.0)
    y = crop_ratio_expr(float(frame.get("y") or 50.0) / 100.0).replace("iw", "ih").replace("ow", "oh")
    return ",".join([
        f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase",
        f"crop={preset.width}:{preset.height}:x='{x}':y='{y}'",
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
        return f"(iw-ow)*{manual_alternate_ratio_expr(0.5 - amplitude, 0.5 + amplitude)}"
    if key == "jump-cut":
        left = 0.22 - strength * 0.0012
        right = 0.78 + strength * 0.0012
        return f"if(lt(mod(t\\,6)\\,3)\\,(iw-ow)*{clamp(left, 0.0, 1.0):.3f}\\,(iw-ow)*{clamp(right, 0.0, 1.0):.3f})"
    return crop_ratio_expr(0.5)


def crop_ratio_expr(ratio: float) -> str:
    return f"(iw-ow)*{clamp(ratio, 0.0, 1.0):.3f}"


def manual_alternate_ratio_expr(left: float, right: float) -> str:
    hold = MANUAL_ALTERNATE_HOLD_SECONDS
    move = MANUAL_ALTERNATE_MOVE_SECONDS
    cycle = (hold + move) * 2.0
    left = clamp(left, 0.0, 1.0)
    right = clamp(right, 0.0, 1.0)
    shift = right - left
    phase = f"mod(t\\,{cycle:.3f})"
    ease_to_right = f"{left:.3f}+{shift:.3f}*(1-cos(PI*({phase}-{hold:.3f})/{move:.3f}))/2"
    ease_to_left = f"{right:.3f}-{shift:.3f}*(1-cos(PI*({phase}-{hold + move + hold:.3f})/{move:.3f}))/2"
    return (
        f"if(lt({phase}\\,{hold:.3f})\\,{left:.3f}\\,"
        f"if(lt({phase}\\,{hold + move:.3f})\\,{ease_to_right}\\,"
        f"if(lt({phase}\\,{hold + move + hold:.3f})\\,{right:.3f}\\,{ease_to_left})))"
    )


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


def camera_x_percent(camera: dict[str, object], elapsed: float = 0.0) -> float:
    key = str(camera.get("key") or "center")
    strength = float(camera.get("strength") or 60.0)
    if key == "face-left":
        return clamp((0.22 - strength * 0.0012) * 100.0, 0.0, 100.0)
    if key == "face-right":
        return clamp((0.78 + strength * 0.0012) * 100.0, 0.0, 100.0)
    if key == "alternate":
        amplitude = 0.12 + (strength / 100.0) * 0.22
        return manual_alternate_x_percent(0.5 - amplitude, 0.5 + amplitude, elapsed)
    if key == "jump-cut":
        left = 0.22 - strength * 0.0012
        right = 0.78 + strength * 0.0012
        return clamp((left if elapsed % 6.0 < 3.0 else right) * 100.0, 0.0, 100.0)
    return 50.0


def manual_alternate_x_percent(left: float, right: float, elapsed: float) -> float:
    hold = MANUAL_ALTERNATE_HOLD_SECONDS
    move = MANUAL_ALTERNATE_MOVE_SECONDS
    cycle = (hold + move) * 2.0
    phase = elapsed % cycle
    if phase < hold:
        ratio = left
    elif phase < hold + move:
        ratio = eased_ratio(left, right, (phase - hold) / move)
    elif phase < hold + move + hold:
        ratio = right
    else:
        ratio = eased_ratio(right, left, (phase - hold - move - hold) / move)
    return clamp(ratio * 100.0, 0.0, 100.0)


def eased_ratio(start: float, end: float, progress: float) -> float:
    amount = (1.0 - math.cos(math.pi * clamp(progress, 0.0, 1.0))) / 2.0
    return start + (end - start) * amount


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


def camera_is_path(row: dict[str, object]) -> bool:
    raw = row.get("camera_path")
    source = raw.get("keyframes") if isinstance(raw, dict) and isinstance(raw.get("keyframes"), list) else raw
    return isinstance(source, list) and bool([item for item in source if isinstance(item, dict)])


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


def camera_path_filter(preset: PlatformPreset, row: dict[str, object], duration: float, filters: list[str]) -> str:
    bounds = camera_path_bounds(row, duration)
    split_filters = camera_path_split_filters_for_bounds(preset, bounds)
    tail = ",".join(filters)
    concat = camera_concat_filter(len(bounds), "cp", tail)
    return ";".join([*split_filters, f"{concat}[vout]"])


def camera_concat_filter(count: int, prefix: str, tail: str = "") -> str:
    concat = "".join(f"[{prefix}{index}]" for index in range(count)) + f"concat=n={count}:v=1:a=0"
    return f"{concat},{tail}" if tail else concat


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


def camera_path_split_filters(preset: PlatformPreset, row: dict[str, object], duration: float) -> list[str]:
    return camera_path_split_filters_for_bounds(preset, camera_path_bounds(row, duration))


def camera_path_split_filters_for_bounds(
    preset: PlatformPreset, bounds: list[tuple[float, float, dict[str, object]]]
) -> list[str]:
    filters = []
    for index, (start, end, frame) in enumerate(bounds):
        if camera_path_frame_uses_group_fit(frame):
            filters.extend(group_fit_camera_path_split_filters(preset, index, start, end))
        else:
            filters.append(
                f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS,"
                f"{camera_filter_from_path_frame(preset, frame)}[cp{index}]"
            )
    return filters


def group_fit_camera_path_split_filters(preset: PlatformPreset, index: int, start: float, end: float) -> list[str]:
    return [
        f"[0:v]trim=start={start:.3f}:end={end:.3f},setpts=PTS-STARTPTS,split=2[cp{index}bgsrc][cp{index}fgsrc]",
        (
            f"[cp{index}bgsrc]scale={preset.width}:{preset.height}:force_original_aspect_ratio=increase,"
            f"crop={preset.width}:{preset.height},boxblur=24:2,eq=brightness=-0.08:saturation=0.85[cp{index}bg]"
        ),
        f"[cp{index}fgsrc]scale={preset.width}:{preset.height}:force_original_aspect_ratio=decrease[cp{index}fg]",
        group_fit_logo_source_filter(preset, index),
        group_fit_logo_overlay_filter(preset, index),
        f"[cp{index}brand][cp{index}fg]overlay=(W-w)/2:(H-h)/2,setsar=1[cp{index}]",
    ]


def group_fit_logo_source_filter(preset: PlatformPreset, index: int) -> str:
    width = max(120, int(round(preset.width * GROUP_FIT_LOGO_WIDTH_RATIO)))
    return (
        f"movie='{ffmpeg_filter_path(brand_logo_path())}',"
        f"scale={width}:-1,format=rgba,colorchannelmixer=aa={GROUP_FIT_LOGO_OPACITY:.2f}[cp{index}logo]"
    )


def group_fit_logo_overlay_filter(preset: PlatformPreset, index: int) -> str:
    top = max(36, int(round(preset.height * GROUP_FIT_LOGO_TOP_RATIO)))
    return f"[cp{index}bg][cp{index}logo]overlay=(W-w)/2:{top}:format=auto:eof_action=repeat[cp{index}brand]"


def camera_path_frame_uses_group_fit(frame: dict[str, object]) -> bool:
    return str(frame.get("fit") or "") == "contain" or "group-fit" in str(frame.get("source") or "")


def camera_path_bounds(row: dict[str, object], duration: float) -> list[tuple[float, float, dict[str, object]]]:
    frames = camera_path_from_row(row, duration)
    safe_duration = max(duration, 0.3)
    if not frames:
        return [(0.0, safe_duration, default_camera_path_frame(default_camera(), 0.0))]
    frames = sorted(frames, key=lambda item: float(item.get("time") or 0.0))
    if float(frames[0].get("time") or 0.0) > 0.001:
        frames.insert(0, {**frames[0], "time": 0.0})
    bounds = []
    for index, frame in enumerate(frames):
        start = clamp(float(frame.get("time") or 0.0), 0.0, safe_duration)
        end = safe_duration
        if index + 1 < len(frames):
            end = clamp(float(frames[index + 1].get("time") or safe_duration), start + 0.001, safe_duration)
        if end > start:
            bounds.append((start, end, frame))
    return bounds or [(0.0, safe_duration, default_camera_path_frame(default_camera(), 0.0))]


def camera_path_from_row(row: dict[str, object], duration: float) -> list[dict[str, object]]:
    raw = row.get("camera_path")
    source = raw.get("keyframes") if isinstance(raw, dict) and isinstance(raw.get("keyframes"), list) else raw
    if isinstance(source, list):
        frames = [camera_path_frame_from_source(item) for item in source if isinstance(item, dict)]
        frames = [frame for frame in frames if frame is not None]
        if frames:
            return sorted(frames, key=lambda item: float(item.get("time") or 0.0))
    return camera_path_from_camera(camera_from_row(row), duration)


def camera_path_from_camera(camera: dict[str, object], duration: float) -> list[dict[str, object]]:
    safe_duration = max(duration, 0.3)
    if camera.get("key") != "sequence":
        return [default_camera_path_frame(camera, 0.0)]
    segments = camera.get("segments") if isinstance(camera.get("segments"), list) else []
    bounds = camera_segment_bounds(safe_duration)
    frames = []
    for index, (start, _end) in enumerate(bounds):
        segment = segments[index] if index < len(segments) and isinstance(segments[index], dict) else default_camera()
        frames.append(default_camera_path_frame(segment, start))
    return frames


def camera_path_frame_from_source(frame: dict[str, object]) -> dict[str, object] | None:
    time = clamp(float(frame.get("time") if frame.get("time") is not None else frame.get("t") or 0.0), 0.0, 86400.0)
    key = str(frame.get("key") or frame.get("camera_key") or "")
    if key in CAMERA_PRESETS:
        camera = {
            "key": key,
            "label": CAMERA_PRESETS[key].label,
            "strength": clamp(float(frame.get("strength") if frame.get("strength") is not None else 60.0), 0.0, 100.0),
        }
        result = default_camera_path_frame(camera, time)
    else:
        result = {
            "time": round(time, 3),
            "x": round(clamp(float(frame.get("x") if frame.get("x") is not None else 50.0), 0.0, 100.0), 2),
            "y": round(clamp(float(frame.get("y") if frame.get("y") is not None else 50.0), 0.0, 100.0), 2),
            "zoom": round(clamp(float(frame.get("zoom") if frame.get("zoom") is not None else 1.0), 1.0, 2.0), 3),
        }
    result["source"] = str(frame.get("source") or result.get("source") or "manual-path")
    result["confidence"] = round(clamp(float(frame.get("confidence") if frame.get("confidence") is not None else 1.0), 0.0, 1.0), 3)
    if str(frame.get("fit") or "") == "contain" or camera_path_frame_uses_group_fit(result):
        result["fit"] = "contain"
    if frame.get("part"):
        result["part"] = str(frame.get("part"))
    return result


def default_camera_path_frame(camera: dict[str, object], time: float) -> dict[str, object]:
    key = str(camera.get("key") or "center")
    strength = clamp(float(camera.get("strength") if camera.get("strength") is not None else 60.0), 0.0, 100.0)
    preset = CAMERA_PRESETS.get(key, CAMERA_PRESETS["center"])
    frame = {
        "time": round(max(time, 0.0), 3),
        "x": round(camera_x_percent({"key": preset.key, "strength": strength}, 0.0), 2),
        "y": 50.0,
        "zoom": round(camera_zoom({"key": preset.key, "strength": strength}), 3),
        "source": "manual-segment",
        "confidence": 1.0,
        "key": preset.key,
        "label": preset.label,
        "strength": strength,
        "part": str(camera.get("part") or ""),
    }
    if preset.key == "fit-blur":
        frame["fit"] = "contain"
    return frame


def camera_segment_bounds(duration: float) -> list[tuple[float, float]]:
    safe_duration = max(duration, 0.3)
    first = safe_duration / 3.0
    second = first * 2.0
    return [(0.0, first), (first, second), (second, safe_duration)]


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


def video_crf(row: dict[str, object]) -> str:
    return FINAL_EFFECT_VIDEO_CRF if effect_from_row(row)["key"] != "none" else FINAL_VIDEO_CRF


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
        "start_seconds": clamp(
            float(raw.get("start_seconds") if raw.get("start_seconds") is not None else 0.0),
            0.0,
            9999.0,
        ),
        "duration_seconds": clamp(
            float(raw.get("duration_seconds") if raw.get("duration_seconds") is not None else 3.0),
            0.3,
            60.0,
        ),
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
        "background_opacity": clamp(
            float(raw.get("background_opacity") if raw.get("background_opacity") is not None else 70.0),
            0.0,
            100.0,
        ),
        "start_seconds": clamp(
            float(raw.get("start_seconds") if raw.get("start_seconds") is not None else 0.0),
            0.0,
            9999.0,
        ),
        "duration_seconds": clamp(
            float(raw.get("duration_seconds") if raw.get("duration_seconds") is not None else 3.0),
            0.3,
            60.0,
        ),
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
    layer["start_seconds"] = clamp(
        float(raw.get("start_seconds") if raw.get("start_seconds") is not None else 0.0),
        0.0,
        9999.0,
    )
    layer["duration_seconds"] = clamp(
        float(raw.get("duration_seconds") if raw.get("duration_seconds") is not None else 3.0),
        0.3,
        60.0,
    )
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


def rendered_row(row: dict[str, object], preset: PlatformPreset, output_path: Path, cover_path: Path | None = None) -> dict[str, object]:
    return {
        "rank": row.get("rank"),
        "platform": preset.key,
        "label": preset.label,
        "width": preset.width,
        "height": preset.height,
        "file": str(output_path),
        "cover_file": str(cover_path) if cover_path else "",
        "adjusted_start": row.get("adjusted_start"),
        "adjusted_end": row.get("adjusted_end"),
        "adjusted_duration": row.get("adjusted_duration"),
        "camera": camera_from_row(row),
        "effect": effect_from_row(row),
        "overlay": overlay_from_row(row),
        "overlays": overlay_layers_from_row(row),
        "bumpers": normalize_bumpers_from_row(row),
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


def prepare_source(args: argparse.Namespace, out_dir: Path, ffmpeg: str, ffprobe: str | None) -> SourceMedia:
    if args.youtube_url:
        return prepare_youtube_source(args, out_dir, ffmpeg, ffprobe)
    if not args.video:
        raise RuntimeError("Provide a local video path or --youtube-url.")
    video = args.video.resolve()
    require_file(video)
    metadata = source_media_metadata("local", video.name, str(video), probe_media_metadata(video, ffprobe), None, None)
    return SourceMedia(str(video), video, video.name, (), metadata)


def prepare_youtube_source(args: argparse.Namespace, out_dir: Path, ffmpeg: str, ffprobe: str | None) -> SourceMedia:
    url = args.youtube_url
    temp_dir = out_dir / "_source"
    temp_dir.mkdir(exist_ok=True)
    label = youtube_title(url)
    transcript = try_youtube_transcript(url, temp_dir, args.language) if args.youtube_captions else None
    transcribe_source = transcript or download_youtube_audio(url, temp_dir / "audio.m4a", ffmpeg)
    download_error: str | None = None
    format_selector = youtube_high_quality_format()
    try:
        render_source_path = download_youtube_render_source(url, temp_dir, ffmpeg, format_selector)
        render_source = str(render_source_path)
        probe = probe_media_metadata(render_source_path, ffprobe)
    except (RuntimeError, subprocess.SubprocessError, OSError) as exc:
        download_error = str(exc)
        render_source = youtube_render_url(url)
        probe = probe_media_metadata(render_source, ffprobe)
    metadata = source_media_metadata("youtube", label, render_source, probe, format_selector, download_error)
    cleanup = (transcribe_source,) if isinstance(transcribe_source, Path) else ()
    return SourceMedia(render_source, transcribe_source, label, cleanup, metadata)


def require_file(path: Path) -> None:
    media_require_file(path)


def find_ffmpeg() -> str:
    return media_find_ffmpeg()


def find_ffprobe() -> str | None:
    return media_find_ffprobe()


def probe_duration(video: Path | str, ffprobe: str | None) -> float:
    return media_probe_duration(video, ffprobe)


def probe_media_metadata(video: Path | str, ffprobe: str | None) -> dict[str, object]:
    return media_probe_media_metadata(video, ffprobe)


def source_media_metadata(
    kind: str, label: str, render_source: str, probe: dict[str, object],
    format_selector: str | None, download_error: str | None
) -> dict[str, object]:
    return media_source_media_metadata(kind, label, render_source, probe, format_selector, download_error)


def write_source_metadata(out_dir: Path, metadata: dict[str, object] | None) -> None:
    media_write_source_metadata(out_dir, metadata)


def yt_dlp_command() -> list[str]:
    return media_yt_dlp_command()


def yt_dlp_runtime_args() -> list[str]:
    return media_yt_dlp_runtime_args()


def bundled_node_path() -> str | None:
    return media_bundled_node_path()


def yt_dlp_extra_args() -> list[str]:
    return media_yt_dlp_extra_args()


def youtube_high_quality_format() -> str:
    return media_youtube_high_quality_format(YOUTUBE_HIGH_QUALITY_FORMAT)


def run_ytdlp(command: list[str]) -> subprocess.CompletedProcess[str]:
    return media_run_ytdlp(command)


def friendly_ytdlp_error(message: str) -> str:
    return media_friendly_ytdlp_error(message)


def youtube_title(url: str) -> str:
    return media_youtube_title(url)


def youtube_render_url(url: str) -> str:
    return media_youtube_render_url(url, YOUTUBE_STREAM_FALLBACK_FORMAT)


def download_youtube_render_source(url: str, temp_dir: Path, ffmpeg: str, format_selector: str) -> Path:
    return media_download_youtube_render_source(url, temp_dir, ffmpeg, format_selector, RANGE_MEDIA_EXTENSIONS)


def resolved_youtube_render_file(temp_dir: Path) -> Path:
    return media_resolved_youtube_render_file(temp_dir, RANGE_MEDIA_EXTENSIONS)


def try_youtube_transcript(url: str, temp_dir: Path, language: str | None) -> Path | None:
    return media_try_youtube_transcript(url, temp_dir, language)


def youtube_caption_lang(language: str | None) -> str:
    return media_youtube_caption_lang(language)


def write_youtube_transcript(caption_path: Path, transcript_path: Path) -> None:
    media_write_youtube_transcript(caption_path, transcript_path)


def caption_event_to_segment(event: dict[str, object]) -> dict[str, object] | None:
    return media_caption_event_to_segment(event)


def download_youtube_audio(url: str, output: Path, ffmpeg: str) -> Path:
    return media_download_youtube_audio(url, output, ffmpeg)


def cleanup_sources(paths: tuple[Path, ...]) -> None:
    media_cleanup_sources(paths)


def load_segments(args: argparse.Namespace, video: Path | str) -> list[Segment]:
    if args.transcript_json:
        return read_transcript_json(args.transcript_json)
    if isinstance(video, Path) and video.suffix.lower() == ".json":
        return read_transcript_json(video)
    if requested_ai_provider(args) == "openai":
        return transcribe_with_openai(video, args.language)
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


def transcribe_with_openai(video: Path | str, language: str | None) -> list[Segment]:
    path = Path(str(video))
    if not path.exists():
        raise RuntimeError("OpenAI transcription requires a local audio/video file.")
    key = openai_api_key()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured in .env.local.")
    files = openai_transcription_files(path)
    segments: list[Segment] = []
    offset = 0.0
    for file_path in files:
        rows = transcribe_openai_file(file_path, key, language)
        segments.extend(Segment(row.start + offset, row.end + offset, row.text) for row in rows)
        record_openai_transcribe_usage(openai_transcribe_model(), transcription_duration(rows))
        offset += openai_chunk_seconds() if len(files) > 1 else 0.0
    return [segment for segment in segments if segment.text and segment.end > segment.start]


def transcribe_openai_file(path: Path, key: str, language: str | None) -> list[Segment]:
    fields: dict[str, str] = {"model": openai_transcribe_model(), "response_format": "verbose_json"}
    if language:
        fields["language"] = language
    data = openai_multipart_request("https://api.openai.com/v1/audio/transcriptions", key, fields, "file", path)
    rows = data.get("segments")
    if not isinstance(rows, list):
        raise RuntimeError("OpenAI transcription did not return timestamped segments. Use CUTED_TRANSCRIBE_MODEL=whisper-1.")
    segments = [Segment(float(row["start"]), float(row["end"]), str(row["text"]).strip()) for row in rows if isinstance(row, dict)]
    return [segment for segment in segments if segment.text and segment.end > segment.start]


def openai_transcription_files(path: Path) -> list[Path]:
    limit = openai_upload_limit_bytes()
    if path.stat().st_size <= limit:
        return [path]
    ffmpeg = find_ffmpeg()
    compact = compressed_audio_path(path)
    compress_audio_for_openai(path, compact, ffmpeg)
    if compact.stat().st_size <= limit:
        return [compact]
    return split_audio_for_openai(compact, ffmpeg)


def openai_upload_limit_bytes() -> int:
    raw = os.environ.get("CUTED_OPENAI_UPLOAD_LIMIT_MB", "").strip()
    if not raw:
        return OPENAI_TRANSCRIBE_LIMIT_BYTES
    return max(1, int(float(raw))) * 1024 * 1024


def openai_chunk_seconds() -> int:
    raw = os.environ.get("CUTED_OPENAI_CHUNK_SECONDS", "").strip()
    if not raw:
        return OPENAI_TRANSCRIBE_CHUNK_SECONDS
    return max(60, int(float(raw)))


def compressed_audio_path(path: Path) -> Path:
    return path.with_name(f"{path.stem}.openai-16k.m4a")


def compress_audio_for_openai(source: Path, output: Path, ffmpeg: str) -> None:
    command = [ffmpeg, "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "32k", str(output)]
    subprocess.run(command, check=True, capture_output=True, text=True)


def split_audio_for_openai(source: Path, ffmpeg: str) -> list[Path]:
    chunk_dir = source.with_suffix("")
    chunk_dir.mkdir(exist_ok=True)
    for stale in chunk_dir.glob("chunk-*.m4a"):
        stale.unlink()
    pattern = chunk_dir / "chunk-%03d.m4a"
    command = [ffmpeg, "-y", "-i", str(source), "-f", "segment", "-segment_time", str(openai_chunk_seconds()), "-c", "copy", str(pattern)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    chunks = sorted(chunk_dir.glob("chunk-*.m4a"))
    if not chunks:
        raise RuntimeError("Could not split audio for OpenAI transcription.")
    too_large = [chunk for chunk in chunks if chunk.stat().st_size > openai_upload_limit_bytes()]
    if too_large:
        raise RuntimeError("Audio chunks are still too large for OpenAI transcription. Lower CUTED_OPENAI_CHUNK_SECONDS.")
    return chunks


def openai_structured_response(
    system: str, user: str, schema_name: str, schema: dict[str, object], operation: str = "clip_selection"
) -> dict[str, object]:
    model = openai_model()
    body = {
        "model": model,
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "strict": True,
                "schema": schema,
            }
        },
    }
    data = openai_json_request("https://api.openai.com/v1/responses", openai_api_key(), body)
    record_openai_text_usage(operation, model, data.get("usage"))
    return parsed_openai_structured_response(data)


def openai_vision_structured_response(
    system: str, user: str, frames: list[dict[str, object]], schema_name: str,
    schema: dict[str, object], operation: str
) -> dict[str, object]:
    model = openai_model()
    content: list[dict[str, object]] = [{"type": "input_text", "text": user}]
    for frame in frames[:8]:
        content.append({"type": "input_image", "image_url": frame["image_url"], "detail": "low"})
    body = {
        "model": model,
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "strict": True,
                "schema": schema,
            }
        },
    }
    data = openai_json_request(
        "https://api.openai.com/v1/responses",
        openai_api_key(),
        body,
        timeout=AI_DIRECTOR_OPENAI_TIMEOUT_SECONDS,
    )
    record_openai_text_usage(operation, model, data.get("usage"))
    return parsed_openai_structured_response(data)


def parsed_openai_structured_response(data: dict[str, object]) -> dict[str, object]:
    text = openai_output_text(data)
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise RuntimeError("OpenAI structured response must be a JSON object.")
    return parsed


def openai_output_text(data: dict[str, object]) -> str:
    direct = data.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    output = data.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    return str(part["text"])
    raise RuntimeError("OpenAI response did not include output text.")


def openai_json_request(
    url: str, api_key: str, payload: dict[str, object], timeout: float = 180.0
) -> dict[str, object]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    return read_openai_json(request, timeout)


def openai_multipart_request(
    url: str,
    api_key: str,
    fields: dict[str, str],
    file_field: str,
    file_path: Path,
    file_content_type: str = "application/octet-stream",
) -> dict[str, object]:
    boundary = f"----cuted{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for key, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode("utf-8"))
    chunks.append(f"--{boundary}\r\n".encode("utf-8"))
    chunks.append(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'
        f"Content-Type: {file_content_type}\r\n\r\n".encode("utf-8")
    )
    chunks.append(file_path.read_bytes())
    chunks.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    request = urllib.request.Request(
        url,
        data=b"".join(chunks),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    return read_openai_json(request, 180.0)


def read_openai_json(request: urllib.request.Request, timeout: float) -> dict[str, object]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        message = error.read().decode("utf-8", errors="replace")[:1200]
        raise RuntimeError(f"OpenAI request failed with HTTP {error.code}: {message}") from error
    except (TimeoutError, socket.timeout) as error:
        raise RuntimeError("OpenAI demorou demais para responder; usei o diretor local como fallback.") from error
    except urllib.error.URLError as error:
        raise RuntimeError("Nao consegui conectar na OpenAI agora; usei o diretor local como fallback.") from error
    if not isinstance(data, dict):
        raise RuntimeError("OpenAI response must be a JSON object.")
    return data


def transcription_duration(rows: list[Segment]) -> float:
    if not rows:
        return 0.0
    return max(0.0, max(row.end for row in rows) - min(row.start for row in rows))


def record_openai_text_usage(operation: str, model: str, usage: object) -> None:
    if not isinstance(usage, dict):
        return
    input_tokens = usage_number(usage, "input_tokens", "prompt_tokens")
    output_tokens = usage_number(usage, "output_tokens", "completion_tokens")
    cached_tokens = cached_input_tokens(usage)
    estimated = estimate_text_cost(model, input_tokens, output_tokens, cached_tokens)
    append_usage_event({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provider": "openai",
        "operation": operation,
        "model": model,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "output_tokens": output_tokens,
        "estimated_usd": round(estimated, 6),
        "pricing_source": OPENAI_PRICING_SOURCE,
    })


def record_openai_transcribe_usage(model: str, duration_seconds: float) -> None:
    if duration_seconds <= 0:
        return
    estimated = estimate_transcribe_cost(model, duration_seconds)
    append_usage_event({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "provider": "openai",
        "operation": "transcription",
        "model": model,
        "audio_seconds": round(duration_seconds, 3),
        "estimated_usd": round(estimated, 6),
        "pricing_source": OPENAI_PRICING_SOURCE,
    })


def usage_number(usage: dict[str, object], *keys: str) -> int:
    for key in keys:
        value = usage.get(key)
        if isinstance(value, (int, float)):
            return max(0, int(value))
    return 0


def cached_input_tokens(usage: dict[str, object]) -> int:
    details = usage.get("input_tokens_details") or usage.get("prompt_tokens_details")
    if not isinstance(details, dict):
        return 0
    value = details.get("cached_tokens")
    return max(0, int(value)) if isinstance(value, (int, float)) else 0


def estimate_text_cost(model: str, input_tokens: int, output_tokens: int, cached_tokens: int) -> float:
    prices = OPENAI_TEXT_PRICES_USD_PER_1M.get(model, OPENAI_TEXT_PRICES_USD_PER_1M["gpt-5-mini"])
    billable_input = max(0, input_tokens - cached_tokens)
    return (
        billable_input * float(prices["input"]) / 1_000_000
        + cached_tokens * float(prices["cached_input"]) / 1_000_000
        + max(0, output_tokens) * float(prices["output"]) / 1_000_000
    )


def estimate_transcribe_cost(model: str, duration_seconds: float) -> float:
    price = OPENAI_TRANSCRIBE_PRICES_USD_PER_MINUTE.get(model, OPENAI_TRANSCRIBE_PRICES_USD_PER_MINUTE["whisper-1"])
    return max(0.0, duration_seconds) / 60.0 * price


def pick_moments(segments: list[Segment], config: CuttedConfig, video_duration: float) -> list[Moment]:
    if not segments:
        raise RuntimeError("No transcript segments found.")
    candidates = build_candidates(segments, config, video_duration)
    ranked = sorted(candidates, key=lambda item: item.score, reverse=True)
    selected = suppress_overlaps(ranked, config.clips)
    return [with_rank(moment, index + 1) for index, moment in enumerate(sorted(selected, key=lambda item: item.start))]


def pick_moments_for_import(args: argparse.Namespace, segments: list[Segment], config: CuttedConfig, video_duration: float) -> list[Moment]:
    provider = requested_ai_provider(args)
    if provider == "local":
        return pick_moments(segments, config, video_duration)
    if provider == "openai":
        return pick_moments_with_openai(args, segments, config, video_duration)
    if openai_api_key():
        try:
            return pick_moments_with_openai(args, segments, config, video_duration)
        except Exception as error:
            print(f"[cutted] OpenAI selection failed, falling back to local heuristics: {error}")
    return pick_moments(segments, config, video_duration)


def pick_moments_with_openai(args: argparse.Namespace, segments: list[Segment], config: CuttedConfig, video_duration: float) -> list[Moment]:
    if not openai_api_key():
        raise RuntimeError("OPENAI_API_KEY is not configured in .env.local.")
    ranked = sorted(build_candidates(segments, config, video_duration), key=lambda item: item.score, reverse=True)
    candidates = diverse_candidate_pool(ranked, config.clips, 90)
    if not candidates:
        raise RuntimeError("No transcript candidates found.")
    requested = min(max(config.clips, 1), len(candidates))
    payload = openai_select_candidates(args, candidates, requested)
    selected = openai_selected_moments(payload, candidates, requested)
    return [with_rank(moment, index + 1) for index, moment in enumerate(sorted(selected, key=lambda item: item.start))]


def openai_select_candidates(args: argparse.Namespace, candidates: list[Moment], requested: int) -> dict[str, object]:
    context = clean_optional_text(getattr(args, "context_prompt", ""), 5000)
    candidate_rows = [
        {
            "id": index,
            "start": round(item.start, 3),
            "end": round(item.end, 3),
            "duration": round(item.end - item.start, 3),
            "score": item.score,
            "cluster_id": selection_cluster_id(item),
            "title": item.title,
            "text": item.transcript[:1600],
        }
        for index, item in enumerate(candidates)
    ]
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "clips": {
                "type": "array",
                "minItems": 1,
                "maxItems": requested,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "integer"},
                        "title": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["id", "title", "reason"],
                },
            }
        },
        "required": ["clips"],
    }
    system = (
        "Voce e o analista editorial do CUTED e deve imitar o criterio da skill local. "
        "Escolha apenas IDs existentes; nunca invente timestamps. Priorize cortes com gancho forte, "
        "frase completa, contexto suficiente, comeco natural e fechamento claro. Penalize trechos que "
        "parecem comecar no meio de uma frase ou terminar em conectivos como porque, entao, mas, so que, "
        "ou seja e tipo. Favoreca surpresa, conflito, opiniao forte, aprendizado, dinheiro, erro, segredo "
        "ou insight especifico. Evite filler generico, repeticao, sobreposicao e trechos que dependem de "
        "contexto externo demais. Evite escolher mais de um corte do mesmo cluster_id, exceto se forem "
        "momentos claramente diferentes. Use o contexto editorial do usuario para desempatar. "
        "Responda apenas no JSON estruturado solicitado."
    )
    user = json.dumps(
        {
            "desired_suggestion_count": requested,
            "editorial_context": context or "Use o criterio editorial padrao do CUTED.",
            "candidates": candidate_rows,
        },
        ensure_ascii=False,
    )
    return openai_structured_response(system, user, "cuted_clip_selection", schema)


def openai_selected_moments(payload: dict[str, object], candidates: list[Moment], requested: int) -> list[Moment]:
    selected: list[Moment] = []
    used: set[int] = set()
    rows = payload.get("clips")
    if not isinstance(rows, list):
        raise RuntimeError("OpenAI response did not include clips.")
    for row in rows:
        if not isinstance(row, dict):
            continue
        index = int(row.get("id", -1))
        if index < 0 or index >= len(candidates) or index in used:
            continue
        used.add(index)
        candidate = candidates[index]
        if not is_diverse_candidate(candidate, selected):
            continue
        title = clean_optional_text(row.get("title"), 80) or candidate.title
        reason_text = clean_optional_text(row.get("reason"), 160) or candidate.reason
        selected.append(Moment(0, candidate.start, candidate.end, candidate.peak, candidate.score, title, reason_text, candidate.transcript, candidate.peak_text, candidate.clip_file, candidate.frame_file, candidate.caption_segments))
        if len(selected) >= requested:
            break
    if not selected:
        raise RuntimeError("OpenAI did not select usable clips.")
    if len(selected) < requested:
        selected.extend(fill_missing_moments(selected, candidates, requested - len(selected)))
    return selected[:requested]


def diverse_candidate_pool(candidates: list[Moment], requested: int, limit: int) -> list[Moment]:
    selected: list[Moment] = []
    target = min(limit, max(requested * 6, requested))
    for candidate in candidates:
        if is_diverse_candidate(candidate, selected):
            selected.append(candidate)
        if len(selected) >= target:
            break
    if len(selected) < requested:
        selected.extend(fill_missing_without_duplicates(selected, candidates, requested - len(selected)))
    return selected[:limit]


def fill_missing_without_duplicates(selected: list[Moment], candidates: list[Moment], count: int) -> list[Moment]:
    filled: list[Moment] = []
    for candidate in candidates:
        if any(same_window(candidate, item) for item in [*selected, *filled]):
            continue
        filled.append(candidate)
        if len(filled) >= count:
            break
    return filled


def same_window(left: Moment, right: Moment) -> bool:
    return abs(left.start - right.start) < 0.01 and abs(left.end - right.end) < 0.01


def is_diverse_candidate(candidate: Moment, selected: list[Moment]) -> bool:
    return all(not selection_conflict(candidate, item) for item in selected)


def selection_conflict(left: Moment, right: Moment) -> bool:
    return overlap_ratio(left, right) >= MAX_SELECTION_OVERLAP or transcript_similarity(left, right) >= MAX_SELECTION_TEXT_SIMILARITY


def transcript_similarity(left: Moment, right: Moment) -> float:
    left_tokens = meaningful_tokens(left.transcript)
    right_tokens = meaningful_tokens(right.transcript)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(1, min(len(left_tokens), len(right_tokens)))


def meaningful_tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"\w{3,}", normalize_text(text)) if token not in COMMON_TOKENS}


def selection_cluster_id(moment: Moment) -> int:
    return int(moment.start // SELECTION_CLUSTER_SECONDS)


def fill_missing_moments(selected: list[Moment], candidates: list[Moment], count: int) -> list[Moment]:
    filled: list[Moment] = []
    for candidate in candidates:
        if not is_diverse_candidate(candidate, [*selected, *filled]):
            continue
        filled.append(candidate)
        if len(filled) >= count:
            break
    return filled


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
                  moment.transcript, moment.peak_text, moment.clip_file, moment.frame_file, moment.caption_segments,
                  moment.waveform_file)


def render_outputs(
    video: Path | str, out_dir: Path, moments: list[Moment], ffmpeg: str, skip_render: bool,
    progress_callback: object | None = None,
) -> list[Moment]:
    clips_dir = out_dir / "clips"
    frames_dir = out_dir / "frames"
    waveforms_dir = out_dir / "waveforms"
    clips_dir.mkdir(exist_ok=True)
    frames_dir.mkdir(exist_ok=True)
    waveforms_dir.mkdir(exist_ok=True)
    rendered = []
    total = len(moments)
    for index, moment in enumerate(moments, start=1):
        rendered.append(render_one(video, clips_dir, frames_dir, waveforms_dir, moment, ffmpeg, skip_render))
        if callable(progress_callback):
            progress_callback(index, total)
    return rendered


def render_one(video: Path | str, clips_dir: Path, frames_dir: Path, waveforms_dir: Path, moment: Moment, ffmpeg: str, skip_render: bool) -> Moment:
    stem = f"clip-{moment.rank:03d}"
    clip_path = clips_dir / f"{stem}.mp4"
    frame_path = frames_dir / f"{stem}.jpg"
    waveform_path = waveforms_dir / f"{stem}.json"
    if not skip_render:
        cut_clip(video, clip_path, moment.start, moment.end, ffmpeg)
        extract_frame(video, frame_path, moment.peak, ffmpeg)
        cover_candidates = extract_cover_candidates(video, frames_dir, stem, frame_path, moment, ffmpeg)
    else:
        return Moment(moment.rank, moment.start, moment.end, moment.peak, moment.score, moment.title, moment.reason,
                      moment.transcript, moment.peak_text, None, None, moment.caption_segments, None)
    waveform_file = write_audio_waveform_file(clip_path, waveform_path, ffmpeg)
    return Moment(moment.rank, moment.start, moment.end, moment.peak, moment.score, moment.title, moment.reason,
                  moment.transcript, moment.peak_text, rel(clip_path, clips_dir.parent), rel(frame_path, frames_dir.parent),
                  moment.caption_segments, rel(waveform_path, waveforms_dir.parent) if waveform_file else None,
                  None, tuple(rel(path, frames_dir.parent) for path in cover_candidates))


def extract_cover_candidates(
    video: Path | str, frames_dir: Path, stem: str, peak_frame: Path, moment: Moment, ffmpeg: str
) -> list[Path]:
    candidates = [peak_frame]
    for label, timestamp in cover_candidate_timestamps(moment):
        output = frames_dir / f"{stem}-cover-{label}.jpg"
        try:
            extract_frame(video, output, timestamp, ffmpeg)
            candidates.append(output)
        except subprocess.CalledProcessError as error:
            print(f"Warning: could not extract cover candidate {output}: {error}", file=sys.stderr)
    return unique_paths(candidates)


def cover_candidate_timestamps(moment: Moment) -> list[tuple[str, float]]:
    duration = max(moment.end - moment.start, 0.1)
    return [
        ("inicio", moment.start + duration * 0.22),
        ("fim", moment.start + duration * 0.78),
    ]


def unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = path.as_posix()
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def write_audio_waveform_file(media: Path, output: Path, ffmpeg: str, buckets: int = 120) -> bool:
    if not media.exists() or not media_has_audio(media, ffmpeg):
        return False
    samples = audio_waveform_samples(media, ffmpeg)
    if not samples:
        return False
    peaks = normalized_audio_peaks(samples, buckets)
    if not peaks:
        return False
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({"peaks": peaks}, separators=(",", ":")), encoding="utf-8")
    return True


def audio_waveform_samples(media: Path, ffmpeg: str, sample_rate: int = 8000) -> list[float]:
    command = [ffmpeg, "-v", "error", "-i", str(media), "-vn", "-ac", "1", "-ar", str(sample_rate), "-f", "f32le", "pipe:1"]
    try:
        result = subprocess.run(command, check=True, capture_output=True)
    except subprocess.CalledProcessError as error:
        print(f"Warning: could not extract audio waveform for {media}: {error}", file=sys.stderr)
        return []
    if not result.stdout:
        return []
    values = array_from_float32le(result.stdout)
    return [float(item) for item in values]


def array_from_float32le(data: bytes):
    import array

    values = array.array("f")
    values.frombytes(data[: len(data) - (len(data) % 4)])
    if sys.byteorder != "little":
        values.byteswap()
    return values


def normalized_audio_peaks(samples: list[float], buckets: int) -> list[float]:
    count = max(1, int(buckets))
    width = max(1, math.ceil(len(samples) / count))
    levels = [audio_bucket_level(samples[index:index + width]) for index in range(0, len(samples), width)]
    peak = max(levels) if levels else 0.0
    if peak <= 0:
        return []
    return [round(clampNumberPy(level / peak, 0.03, 1.0), 3) for level in levels[:count]]


def audio_bucket_level(samples: list[float]) -> float:
    if not samples:
        return 0.0
    energy = sum(float(item) * float(item) for item in samples) / len(samples)
    return math.sqrt(max(energy, 0.0))


def clampNumberPy(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def cut_clip(video: Path | str, output: Path, start: float, end: float, ffmpeg: str) -> None:
    command = [ffmpeg, "-y", "-ss", fmt_time(start), "-i", str(video), "-t", fmt_time(end - start),
               "-c:v", "libx264", "-preset", "ultrafast", "-profile:v", "main", "-level", "4.1",
               "-pix_fmt", "yuv420p", "-r", "30", "-crf", PREVIEW_DRAFT_VIDEO_CRF, "-c:a", "aac", "-b:a", "128k",
               "-ar", "44100", "-movflags", "+faststart", str(output)]
    subprocess.run(command, check=True, capture_output=True, text=True)


def extract_frame(video: Path | str, output: Path, timestamp: float, ffmpeg: str) -> None:
    command = [ffmpeg, "-y", "-ss", fmt_time(timestamp), "-i", str(video), "-frames:v", "1",
               "-q:v", "2", str(output)]
    subprocess.run(command, check=True, capture_output=True, text=True)


def fmt_time(value: float) -> str:
    return f"{max(value, 0.0):.3f}"


def rel(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def apply_publish_intelligence(
    moments: list[Moment], source_label: str, config: CuttedConfig,
    args: argparse.Namespace, source_metadata: dict[str, object] | None = None
) -> list[Moment]:
    if not moments:
        return moments
    context = publish_source_context(source_label, args, source_metadata)
    provider = requested_ai_provider(args)
    if provider in {"openai", "auto"} and openai_api_key():
        try:
            payload = openai_publish_intelligence(context, config, moments)
            return merge_publish_intelligence(moments, payload, "openai-web")
        except Exception as error:
            print(f"[cutted] Publish intelligence fallback: {error}", file=sys.stderr)
    return fallback_publish_intelligence(moments, context, "local-fallback")


def openai_publish_intelligence(
    context: PublishSourceContext, config: CuttedConfig, moments: list[Moment]
) -> dict[str, object]:
    model = openai_model()
    body = {
        "model": model,
        "tools": [{"type": "web_search", "search_context_size": "low"}],
        "input": [
            {"role": "system", "content": publish_intelligence_system_prompt()},
            {"role": "user", "content": publish_intelligence_user_prompt(context, config, moments)},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "cuted_publish_intelligence",
                "strict": True,
                "schema": publish_intelligence_schema(),
            }
        },
    }
    data = openai_json_request(
        "https://api.openai.com/v1/responses",
        openai_api_key(),
        body,
        timeout=PUBLISH_INTELLIGENCE_TIMEOUT_SECONDS,
    )
    record_openai_text_usage("publish_intelligence", model, data.get("usage"))
    return parsed_openai_structured_response(data)


def publish_intelligence_system_prompt() -> str:
    return (
        "Voce e o estrategista de publicacao do CUTED para clips curtos. "
        "Use no maximo uma busca web para entender SEO e tendencias atuais. "
        "O titulo original do video ou nome do arquivo e contexto, nao copy final. "
        "Reescreva tudo em portugues natural do Brasil, com acentuacao, pontuacao "
        "e frases completas. Nunca copie marcas cruas da transcricao como >>, "
        "timestamps, falas cortadas ou pontuacao quebrada. Hashtags devem vir "
        "principalmente do transcript e peak_text do corte; use o titulo original "
        "so para identificar tema, convidado ou evento. Relacione trends apenas "
        "quando houver encaixe claro com o que foi falado. Escolha capa apenas "
        "entre os frames candidatos do corte; nao redesenhe."
    )


def publish_intelligence_user_prompt(
    context: PublishSourceContext, config: CuttedConfig, moments: list[Moment]
) -> str:
    payload = {
        "source_context": publish_source_context_payload(context),
        "preset": config.preset or "default",
        "one_search_budget": True,
        "style_rules": [
            "title: curto, publicavel, sem copiar transcricao crua",
            "hook: uma chamada forte para os 2 primeiros segundos",
            "description: 1 ou 2 frases limpas explicando o corte",
            "hashtags: 4 a 6 tags relevantes baseadas no que foi falado",
            "cover: escolha somente um arquivo existente em cover_candidates",
        ],
        "clips": publish_clip_rows(moments),
    }
    return json.dumps(payload, ensure_ascii=False)


def publish_clip_rows(moments: list[Moment]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for moment in moments:
        rows.append({
            "rank": moment.rank,
            "title": clean_publish_line(moment.title, "", 140),
            "peak_text": trim_publish_text(clean_transcript_artifacts(moment.peak_text), 260),
            "transcript": trim_publish_text(clean_transcript_artifacts(moment.transcript), PUBLISH_CLIP_TEXT_LIMIT),
            "frame_file": moment.frame_file or "",
            "cover_candidates": list(publish_cover_candidates_for_moment(moment)),
        })
    return rows


def publish_source_context(
    source_label: str, args: argparse.Namespace, metadata: dict[str, object] | None
) -> PublishSourceContext:
    data = metadata if isinstance(metadata, dict) else {}
    kind = clean_publish_line(data.get("kind"), "local", 40)
    title = clean_publish_line(data.get("label") or source_label, source_label, 180)
    return PublishSourceContext(
        label=clean_publish_line(source_label, title, 180),
        kind=kind,
        title=title,
        user_context=clean_publish_line(getattr(args, "context_prompt", ""), "", PUBLISH_SOURCE_TEXT_LIMIT),
        source_url=clean_publish_line(getattr(args, "youtube_url", ""), "", 320),
    )


def publish_source_context_payload(context: PublishSourceContext) -> dict[str, object]:
    return {
        "kind": context.kind,
        "title": context.title,
        "label": context.label,
        "user_context": context.user_context,
        "source_url": context.source_url,
        "priority": (
            "Use this origin context to identify people, topic and event. "
            "Do not copy it as the clip title unless the clip transcript supports it."
        ),
    }


def publish_intelligence_schema() -> dict[str, object]:
    clip_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["rank", "hook", "title", "description", "hashtags", "cover", "confidence"],
        "properties": {
            "rank": {"type": "integer"},
            "hook": {"type": "string"},
            "title": {"type": "string"},
            "description": {"type": "string"},
            "hashtags": {"type": "array", "items": {"type": "string"}},
            "cover": publish_cover_schema(),
            "confidence": {"type": "number"},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["trend_context", "clips"],
        "properties": {
            "trend_context": publish_trend_schema(),
            "clips": {"type": "array", "items": clip_schema},
        },
    }


def publish_trend_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["query", "summary", "matched_terms", "source_urls", "confidence"],
        "properties": {
            "query": {"type": "string"},
            "summary": {"type": "string"},
            "matched_terms": {"type": "array", "items": {"type": "string"}},
            "source_urls": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number"},
        },
    }


def publish_cover_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["selected_frame", "candidates", "reason"],
        "properties": {
            "selected_frame": {"type": "string"},
            "candidates": {"type": "array", "items": {"type": "string"}},
            "zoom": {"type": "number"},
            "x": {"type": "number"},
            "y": {"type": "number"},
            "reason": {"type": "string"},
        },
    }


def merge_publish_intelligence(
    moments: list[Moment], payload: dict[str, object], source: str
) -> list[Moment]:
    trend = normalize_publish_trend(payload.get("trend_context"), source)
    rows = publish_rows_by_rank(payload.get("clips"))
    return [
        replace(moment, publish_metadata=publish_metadata_for_moment(moment, rows.get(moment.rank), trend))
        for moment in moments
    ]


def publish_rows_by_rank(value: object) -> dict[int, dict[str, object]]:
    if not isinstance(value, list):
        return {}
    rows: dict[int, dict[str, object]] = {}
    for item in value:
        if not isinstance(item, dict):
            continue
        rank = int(item.get("rank")) if isinstance(item.get("rank"), (int, float)) else 0
        if rank > 0:
            rows[rank] = item
    return rows


def publish_metadata_for_moment(
    moment: Moment, row: dict[str, object] | None, trend: dict[str, object]
) -> dict[str, object]:
    context = trend_source_context(trend)
    fallback = fallback_publish_for_moment(moment, trend, context)
    if not row:
        return fallback
    hashtags = normalize_hashtags(row.get("hashtags"), fallback["hashtags"])
    hook = clean_publish_line(row.get("hook"), str(fallback["hook"]), 96)
    title = clean_publish_line(row.get("title"), str(fallback["title"]), 90)
    description = clean_publish_line(row.get("description"), str(fallback["description"]), 260)
    cover = normalize_publish_cover(row.get("cover"), moment)
    return build_publish_metadata(hook, title, description, hashtags, cover, trend, row.get("confidence"))


def normalize_publish_trend(value: object, source: str) -> dict[str, object]:
    if not isinstance(value, dict):
        return fallback_publish_trend(coerce_publish_source_context(""), source)
    return {
        "query": clean_publish_line(value.get("query"), "", 160),
        "summary": clean_publish_line(value.get("summary"), "Contexto atual aplicado com baixa confianca.", 280),
        "matched_terms": clean_string_list(value.get("matched_terms"), 8),
        "source_urls": clean_url_list(value.get("source_urls"), 5),
        "confidence": clamp_float(value.get("confidence"), 0.0, 1.0, 0.45),
        "source": source,
        "origin_title": clean_publish_line(value.get("origin_title"), "", 180),
        "origin_kind": clean_publish_line(value.get("origin_kind"), "", 40),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "search_budget": "single",
    }


def trend_source_context(trend: dict[str, object]) -> PublishSourceContext:
    title = clean_publish_line(trend.get("origin_title"), "", 180)
    kind = clean_publish_line(trend.get("origin_kind"), "local", 40)
    return PublishSourceContext(label=title, kind=kind, title=title, user_context="", source_url="")


def fallback_publish_intelligence(
    moments: list[Moment], context: PublishSourceContext | str, source: str
) -> list[Moment]:
    source_context = coerce_publish_source_context(context)
    trend = fallback_publish_trend(source_context, source)
    return [
        replace(moment, publish_metadata=fallback_publish_for_moment(moment, trend, source_context))
        for moment in moments
    ]


def coerce_publish_source_context(value: PublishSourceContext | str) -> PublishSourceContext:
    if isinstance(value, PublishSourceContext):
        return value
    title = clean_publish_line(value, "video curto", 180)
    return PublishSourceContext(label=title, kind="local", title=title, user_context="", source_url="")


def fallback_publish_trend(context: PublishSourceContext, source: str) -> dict[str, object]:
    topic = clean_publish_line(context.title or context.label, "video curto", 120)
    return {
        "query": f"trends reels shorts tiktok {topic}".strip(),
        "summary": "Sugestoes geradas pelo transcript local; sem busca web aplicada neste import.",
        "matched_terms": [],
        "source_urls": [],
        "confidence": 0.25,
        "source": source,
        "origin_title": context.title,
        "origin_kind": context.kind,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "search_budget": "single",
    }


def fallback_publish_for_moment(
    moment: Moment, trend: dict[str, object], context: PublishSourceContext
) -> dict[str, object]:
    base = publish_core_sentence(moment)
    title = fallback_publish_title(moment, context, base)
    hook = fallback_publish_hook(base, title)
    description = fallback_publish_description(moment, title)
    hashtags = fallback_hashtags_for_moment(moment, context)
    cover = normalize_publish_cover(None, moment)
    return build_publish_metadata(hook, title, description, hashtags, cover, trend, 0.25)


def publish_core_sentence(moment: Moment) -> str:
    peak = clean_publish_line(moment.peak_text, "", 120)
    transcript = first_publish_sentence(moment.transcript, 140)
    return peak or transcript or clean_publish_line(moment.title, "O ponto mais forte do corte", 92)


def fallback_publish_title(moment: Moment, context: PublishSourceContext, base: str) -> str:
    source_hint = best_source_entity(context.title)
    text = first_publish_sentence(moment.transcript or moment.peak_text, 86)
    if source_hint and source_hint.lower() in strip_accents(f"{moment.transcript} {moment.peak_text}").lower():
        return clean_publish_line(f"{source_hint}: {text or base}", base, 82)
    return clean_publish_line(text or base, base, 82)


def fallback_publish_hook(base: str, title: str) -> str:
    hook = clean_publish_line(base, title, 96).rstrip(".,;:")
    if publish_line_has_weak_ending(hook):
        hook = clean_publish_line(title, "O que aconteceu nesse corte", 80).rstrip(".,;:")
    return hook if hook.endswith(("?", "!")) else f"{hook}?"


def fallback_publish_description(moment: Moment, title: str) -> str:
    sentence = first_publish_sentence(moment.transcript, 180)
    if sentence and sentence.lower() != title.lower():
        return sentence
    topic = title.rstrip(".,;:!?")
    return f"Corte rapido sobre {topic}."


def publish_line_has_weak_ending(value: str) -> bool:
    normalized = strip_accents(value).lower().strip(" .,;:!?")
    weak = ("porque", "por que", "mas", "so que", "tem que", "vai", "assim", "tipo")
    return any(normalized.endswith(item) for item in weak)


def build_publish_metadata(
    hook: str, title: str, description: str, hashtags: list[str],
    cover: dict[str, object], trend: dict[str, object], confidence: object
) -> dict[str, object]:
    return {
        "version": PUBLISH_INTELLIGENCE_VERSION,
        "hook": hook,
        "title": title,
        "description": description,
        "hashtags": hashtags,
        "caption_hint": publish_caption_hint(hook, description, hashtags),
        "strategy": "Usar o hook nos 2 primeiros segundos e validar hashtags antes de publicar.",
        "cover": cover,
        "trend_context": trend,
        "confidence": clamp_float(confidence, 0.0, 1.0, 0.25),
    }


def normalize_publish_cover(value: object, moment: Moment) -> dict[str, object]:
    frame = moment.frame_file or ""
    fallback_candidates = list(publish_cover_candidates_for_moment(moment))
    if isinstance(value, dict):
        selected = str(value.get("selected_frame") or frame)
        candidates = clean_string_list(value.get("candidates"), 4) or fallback_candidates
        zoom = clamp_float(value.get("zoom"), 1.0, 1.8, 1.0)
        x = clamp_float(value.get("x"), 0.0, 100.0, 50.0)
        y = clamp_float(value.get("y"), 0.0, 100.0, 50.0)
        reason = clean_publish_line(value.get("reason"), "Frame de pico extraido do corte.", 140)
    else:
        selected = frame
        candidates = fallback_candidates
        zoom = 1.0
        x = 50.0
        y = 50.0
        reason = "Frame de pico extraido do corte."
    if selected and selected not in candidates:
        candidates = [selected, *candidates]
    return {"selected_frame": selected, "candidates": candidates, "zoom": zoom, "x": x, "y": y, "reason": reason}


def publish_cover_candidates_for_moment(moment: Moment) -> tuple[str, ...]:
    candidates = [item for item in moment.cover_candidates if str(item).strip()]
    if moment.frame_file and moment.frame_file not in candidates:
        candidates.insert(0, moment.frame_file)
    return tuple(candidates[:4])


def publish_caption_hint(hook: str, description: str, hashtags: list[str]) -> str:
    return "\n\n".join(part for part in [hook, description, " ".join(hashtags)] if part).strip()


def fallback_hashtags(text: str) -> list[str]:
    topics = [f"#{word}" for word in publish_topic_words(text, 5)]
    defaults = contextual_default_hashtags(text)
    return normalize_hashtags(topics + defaults, defaults)


def fallback_hashtags_for_moment(moment: Moment, context: PublishSourceContext) -> list[str]:
    transcript_text = f"{moment.transcript} {moment.peak_text}"
    transcript_tags = [f"#{word}" for word in publish_topic_words(transcript_text, 5)]
    source_tags = source_title_hashtags(context.title, 5)
    defaults = contextual_default_hashtags(transcript_text + " " + context.title)
    if len(source_tags) >= 5:
        return normalize_hashtags(source_tags, defaults)
    return normalize_hashtags(source_tags + transcript_tags + defaults, defaults)


def source_title_hashtags(title: str, limit: int) -> list[str]:
    cleaned = strip_accents(clean_transcript_artifacts(title)).lower()
    words = re.findall(r"[a-z0-9]{3,}", cleaned)
    tags: list[str] = []
    index = 0
    while index < len(words) and len(tags) < limit:
        word = words[index]
        if word == "clima" and index + 1 < len(words) and words[index + 1] == "esquentou":
            append_unique_tag(tags, "#ClimaEsquentou")
            index += 2
            continue
        if valid_source_title_word(word):
            append_unique_tag(tags, f"#{publish_hashtag_word(word)}")
        index += 1
    return tags


def valid_source_title_word(word: str) -> bool:
    return word not in publish_stop_words() and word not in {"cobrou", "clima", "esquentou"}


def append_unique_tag(tags: list[str], tag: str) -> None:
    if tag not in tags:
        tags.append(tag)


def contextual_default_hashtags(text: str) -> list[str]:
    normalized = strip_accents(text).lower()
    tags = ["#Podcast", "#Cortes"]
    if re.search(r"\bia\b|inteligencia artificial|artificial intelligence", normalized):
        tags.insert(0, "#IA")
    if "youtube" in normalized:
        tags.append("#YouTube")
    return tags


def publish_topic_words(text: str, limit: int) -> list[str]:
    normalized = strip_accents(text).lower()
    words = re.findall(r"[a-z0-9]{3,}", normalized)
    stop = publish_stop_words()
    counts: dict[str, int] = {}
    for word in words:
        if word not in stop:
            counts[word] = counts.get(word, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [publish_hashtag_word(word) for word, _count in ranked[:limit]]


def publish_stop_words() -> set[str]:
    return {
        "aqui", "acho", "agora", "ainda", "assim", "cada", "cara", "como", "coisa", "com",
        "dela", "dele", "deles", "dessa", "desse", "disso", "entao", "essa", "esse", "esta",
        "falar", "fala", "falando", "gente", "isso", "mais", "menos", "muito", "nao", "para",
        "pela", "pelo", "porque", "qual", "quando", "que", "sobre", "tambem", "tem", "tipo",
        "tia", "verdade", "video", "voce",
    }


def publish_hashtag_word(word: str) -> str:
    aliases = {"inteligencia": "InteligenciaArtificial", "artificial": "InteligenciaArtificial"}
    return aliases.get(word, word[:1].upper() + word[1:])


def first_publish_sentence(value: object, limit: int) -> str:
    text = clean_transcript_artifacts(value)
    parts = re.split(r"(?<=[.!?])\s+", text)
    for part in parts:
        cleaned = clean_publish_line(part, "", limit)
        if len(cleaned) >= 18:
            return cleaned
    return clean_publish_line(text, "", limit)


def clean_transcript_artifacts(value: object) -> str:
    text = str(value or "")
    text = re.sub(r"(^|\s)>+\s*", " ", text)
    text = re.sub(r"\[[^\]]{1,32}\]", " ", text)
    text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def best_source_entity(source_title: str) -> str:
    cleaned = clean_transcript_artifacts(source_title)
    words = re.findall(r"[A-Za-zÀ-ÿ0-9]{3,}", cleaned)
    candidates = [word.title() for word in words if strip_accents(word).lower() not in publish_stop_words()]
    return " ".join(candidates[:2]) if candidates else ""


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFD", str(value or ""))
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def normalize_hashtags(value: object, fallback: object) -> list[str]:
    raw = value if isinstance(value, list) else fallback
    tags: list[str] = []
    for item in raw if isinstance(raw, list) else []:
        cleaned = re.sub(r"[^0-9A-Za-z_À-ÿ]", "", str(item).lstrip("#")).strip()
        if valid_publish_hashtag(cleaned) and f"#{cleaned}" not in tags:
            tags.append(f"#{cleaned}")
    return tags[:PUBLISH_MAX_HASHTAGS] or list(PUBLISH_DEFAULT_HASHTAGS)


def valid_publish_hashtag(value: str) -> bool:
    normalized = strip_accents(value).lower()
    if normalized.isdigit():
        return False
    if len(normalized) < 3:
        return normalized in {"ia"}
    return normalized not in publish_stop_words()


def clean_string_list(value: object, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value[:limit] if str(item).strip()]


def clean_url_list(value: object, limit: int) -> list[str]:
    return [url for url in clean_string_list(value, limit) if url.startswith(("http://", "https://"))]


def clean_publish_line(value: object, fallback: str, limit: int) -> str:
    cleaned = clean_transcript_artifacts(value)
    cleaned = re.sub(r"^(ah|ai|aí|entao|então|né|ne)[,.\s]+", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.lstrip(" ,.!?;:")
    cleaned = re.sub(r"\s+([,.!?;:])", r"\1", cleaned)
    cleaned = re.sub(r"([!?.,;:]){2,}", r"\1", cleaned)
    cleaned = re.sub(r",\s*([!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -–—")
    if not cleaned:
        cleaned = fallback
    return sentence_case_publish(trim_publish_text(cleaned, limit))


def sentence_case_publish(value: str) -> str:
    if not value:
        return value
    for index, char in enumerate(value):
        if char.isalpha():
            return value[:index] + char.upper() + value[index + 1:]
    return value


def trim_publish_text(value: object, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return text if len(text) <= limit else text[: max(0, limit - 1)].rstrip() + "…"


def clamp_float(value: object, minimum: float, maximum: float, fallback: float) -> float:
    number = float(value) if isinstance(value, (int, float)) else fallback
    return min(max(number, minimum), maximum)


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
        "waveform_file": moment.waveform_file,
        "publish_metadata": moment.publish_metadata or {},
        "cover_candidates": list(moment.cover_candidates),
        "caption_segments": [segment_to_dict(item) for item in moment.caption_segments],
    }


def segment_to_dict(segment: Segment) -> dict[str, object]:
    return {"start": segment.start, "end": segment.end, "text": segment.text}


def write_html(path: Path, moments: list[Moment], source_label: str) -> None:
    cards = "\n".join(card_html(moment) for moment in moments)
    data = json.dumps({"moments": [moment_to_dict(item) for item in moments]}, ensure_ascii=False)
    logo_src = write_brand_logo_asset(path.parent)
    live_timeline_assets = write_live_timeline_assets(path.parent)
    control_bar_assets = write_control_bar_assets(path.parent)
    path.write_text(page_html(source_label, cards, data, logo_src, live_timeline_assets, control_bar_assets), encoding="utf-8")


def write_project_home(path: Path, workspace: Path) -> None:
    logo_src = write_brand_logo_asset(path.parent)
    recent = project_catalog_recent(workspace)
    path.write_text(project_home_html(workspace, logo_src, recent), encoding="utf-8")


def project_home_html(workspace: Path, logo_src: str, recent: list[dict[str, object]]) -> str:
    project_rows = "\n".join(project_home_card_html(project) for project in recent) if recent else project_home_empty_state_html()
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CUTED</title>
  <style>{css()}{project_home_css()}{project_home_compact_import_css()}</style>
</head>
<body data-project-home>
  <main class="project-home">
    <button id="open-settings" class="home-settings-button icon-button" type="button" aria-label="OpenAI settings" title="OpenAI settings">{gear_icon_svg()}</button>
    <section class="home-brand-stage" aria-label="CUTED">
      <div class="home-logo-orbit">
        <img class="home-brand-logo" src="{html.escape(logo_src)}" alt="CUTED">
      </div>
    </section>
    <section class="project-library" data-project-library aria-label="Recent projects">
      <div class="project-section-head">
        <strong>Recent projects</strong>
        <div class="project-toolbar" aria-label="Project actions">
          <button type="button" class="project-icon-button project-primary" data-new-project aria-label="New project" title="New project">+</button>
          <button type="button" class="project-icon-button" data-refresh-projects aria-label="Refresh" title="Refresh">↻</button>
          <button type="button" data-open-workspace title="Local projects">Workspace</button>
        </div>
      </div>
        <div class="project-table" data-project-list>
          <div class="project-table-head" aria-hidden="true">
          <span>Project</span>
          <span>Status</span>
          <span>Updated</span>
          <span>Actions</span>
        </div>
        {project_rows}
      </div>
    </section>
    <section class="project-import" data-home-import hidden>
      {project_import_form_html()}
    </section>
  </main>
  {project_home_import_loading_html(logo_src)}
  {settings_modal_html()}
  <script>{project_home_js(workspace)}</script>
</body>
</html>"""


def project_home_card_html(project: dict[str, object]) -> str:
    title = html.escape(str(project.get("title") or "Untitled project"))
    source = html.escape(str(project.get("source_label") or ""))
    url = html.escape(str(project.get("url") or ""))
    project_id = html.escape(str(project.get("id") or ""))
    path = html.escape(str(project.get("path") or ""))
    clip_count = int(project.get("clip_count") or 0)
    render_count = int(project.get("render_count") or 0)
    size_label = file_size_label(int(project.get("size_bytes") or 0))
    open_action = f'<a href="{url}">Open</a>' if url else '<button type="button" disabled>Open</button>'
    updated = html.escape(str(project.get("last_opened_at") or ""))
    return f"""
        <article class="project-row" data-project-id="{project_id}" data-project-title="{title}" data-project-path="{path}" data-project-size="{size_label}">
          <div class="project-name-cell">
            <strong>{title}</strong>
            <p>{source}</p>
            <small>{html.escape(path)}</small>
          </div>
          <dl class="project-meta-cell">
            <div><dt>Clips</dt><dd>{clip_count}</dd></div>
            <div><dt>Renders</dt><dd>{render_count}</dd></div>
            <div><dt>Size</dt><dd>{size_label}</dd></div>
          </dl>
          <time class="project-updated-cell">{updated}</time>
          <div class="project-row-actions">
            {open_action}
            <button type="button" data-forget-project>Remove recent</button>
            <button type="button" data-delete-project>Delete project</button>
          </div>
        </article>"""


def project_home_empty_state_html() -> str:
    return """
        <article class="project-empty-state" data-project-empty-state>
          <strong>No recent projects</strong>
          <p>Create a new project to start.</p>
        </article>"""


def project_import_form_html() -> str:
    return f"""
      <form class="import-panel new-project-panel" data-import-form data-source-mode="local">
        <div class="new-project-head">
          <strong>New project</strong>
          <button type="button" data-show-projects>Recent projects</button>
        </div>
        <div class="import-key-banner" data-import-key-banner hidden>
          <span>Add your OpenAI key in Settings before importing with AI.</span>
          <button type="button" data-import-key-open>Settings</button>
        </div>
        <div class="new-project-config-grid">
          <section class="new-project-config-block source-config-block" aria-label="Source media">
            <div class="new-project-block-title"><strong>Media</strong><span>File or link</span></div>
            <div class="source-toggle icon-source-toggle" role="group" aria-label="Project source">
              <label title="Local video"><input name="source_mode" type="radio" value="local" aria-label="Local video" checked><span>{project_home_icon_svg("local-video")}<strong>Local</strong></span></label>
              <label title="YouTube"><input name="source_mode" type="radio" value="youtube" aria-label="YouTube"><span>{project_home_icon_svg("youtube")}<strong>YouTube</strong></span></label>
            </div>
            <div class="source-panel" data-source-panel="local">
              <input name="source_path" type="text" value="" placeholder="No video selected" autocomplete="off" readonly>
              <button class="icon-action-button" type="button" data-select-video-file aria-label="Select video" title="Select video">{project_home_icon_svg("folder-video")}</button>
            </div>
            <div class="source-panel" data-source-panel="youtube" hidden>
              <input name="source_url" type="url" placeholder="Paste a YouTube link" autocomplete="off">
            </div>
          </section>
          <section class="new-project-config-block tuning-config-block" aria-label="Project tuning">
            <div class="new-project-block-title"><strong>Clips</strong><span>Suggestions and duration</span></div>
            <div class="cuts-control-grid">
              <label class="cut-count-field" title="Clip count">
                <span class="tuning-copy">Count</span>
                <select name="preview_count" aria-label="Clip count">
                  {suggestion_count_options()}
                </select>
              </label>
              <fieldset class="duration-profile duration-size-toggle duration-tile-grid" aria-label="Clip duration">
                <legend class="sr-only">Clip duration</legend>
                <label class="duration-option-short" title="Short: 20 to 45 seconds"><input name="duration_profile" type="radio" value="short" aria-label="Short"><span><strong>S</strong><small>20-45s</small></span></label>
                <label class="duration-option-medium" title="Medium: 30 to 70 seconds"><input name="duration_profile" type="radio" value="medium" aria-label="Medium" checked><span><strong>M</strong><small>30-70s</small></span></label>
                <label class="duration-option-long" title="Long: 60 to 120 seconds"><input name="duration_profile" type="radio" value="long" aria-label="Long"><span><strong>L</strong><small>60-120s</small></span></label>
              </fieldset>
            </div>
          </section>
        </div>
        <input name="language" type="hidden" value="en">
        <input name="preset" type="hidden" value="tiktok">
        <section class="ai-context-box" aria-label="AI briefing" data-ai-context-box>
          <div class="ai-context-head">
            <div class="ai-context-title">
              <strong>AI Briefing</strong>
              <small>Speak or write what the AI should prioritize.</small>
            </div>
            <button class="icon-action-button context-audio-button" type="button" data-context-audio aria-label="Record voice briefing" title="Record voice briefing">{project_home_icon_svg("mic")}</button>
          </div>
          <div class="ai-context-device-row">
            <select data-context-audio-device aria-label="Microphone input">
              <option value="">Default microphone</option>
            </select>
            <div class="ai-context-level" aria-hidden="true"><span data-context-audio-level></span></div>
          </div>
          <textarea name="context_prompt" rows="5" placeholder="Example: prioritize sharp hooks, practical advice, complete thoughts, and moments that will work as short-form clips."></textarea>
          <div class="ai-context-status" data-context-audio-status>Ready for a typed or spoken briefing.</div>
        </section>
        <div class="import-status" data-import-status>Ready.</div>
        <div class="import-result" data-import-result></div>
        <footer class="new-project-footer">
          <span>Renders are saved automatically inside the project.</span>
          <button class="import-submit-button" type="submit">Import</button>
        </footer>
      </form>"""


def project_home_import_loading_html(logo_src: str) -> str:
    return f"""
  <section class="home-import-loading" data-import-loading hidden aria-live="polite" aria-label="Importing project">
    <div class="home-import-loading-inner">
      <img src="{html.escape(logo_src)}" alt="CUTED">
      <div class="home-import-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="8">
        <span data-import-loading-bar></span>
        <strong data-import-loading-message>Preparing project...</strong>
      </div>
      <small data-import-loading-label>Import</small>
      <p class="home-import-detail" data-import-loading-detail>Organizing local files.</p>
      <ol class="home-import-steps" data-import-loading-steps aria-label="Import steps">
        <li data-import-step="prepare" data-state="active"><span></span>Project</li>
        <li data-import-step="media"><span></span>Media</li>
        <li data-import-step="audio"><span></span>Audio</li>
        <li data-import-step="analysis"><span></span>AI</li>
        <li data-import-step="suggestions"><span></span>Clips</li>
        <li data-import-step="previews"><span></span>Previews</li>
        <li data-import-step="publish"><span></span>Post</li>
        <li data-import-step="editor"><span></span>Edit</li>
      </ol>
      <button type="button" data-import-loading-back hidden>Back</button>
    </div>
  </section>"""


def settings_modal_html() -> str:
    return f"""
  <div class="settings-backdrop" data-settings-modal hidden>
    <section class="settings-panel" data-settings-panel role="dialog" aria-modal="true" aria-labelledby="settings-title" aria-describedby="settings-description" tabindex="-1">
      <div class="settings-aura" aria-hidden="true"></div>
      <div class="settings-head">
        <div class="settings-title-row">
          <span class="settings-orb" aria-hidden="true">{gear_icon_svg()}</span>
          <div>
            <strong id="settings-title">OpenAI</strong>
            <p id="settings-description">Key, models, and CUTED connection test.</p>
          </div>
        </div>
        <button class="settings-close-button" type="button" data-settings-close aria-label="Close settings">X</button>
      </div>
      <form data-settings-form class="settings-form">
        <div class="settings-status" data-settings-status>Loading...</div>
        <label class="settings-field settings-token-field">Token OpenAI
          <input name="api_key" type="password" autocomplete="off" placeholder="Paste only when you want to replace the token">
        </label>
        <div class="settings-grid">
          <label class="settings-field">AI provider
            <select name="ai_provider">
              <option value="openai">OpenAI</option>
              <option value="auto">Auto</option>
              <option value="local">Local</option>
            </select>
          </label>
          <label class="settings-field">Analysis model
            <select name="openai_model">
              {openai_model_options()}
            </select>
          </label>
          <label class="settings-field">Transcription
            <select name="transcribe_model">
              {transcribe_model_options()}
            </select>
          </label>
        </div>
        <div class="settings-usage" data-settings-usage>No local usage recorded on this machine.</div>
        <div class="settings-actions">
          <button type="button" data-settings-test>Test connection</button>
          <button type="submit">Save</button>
        </div>
        <small>Local estimate. Check the official amount in the OpenAI dashboard.</small>
      </form>
    </section>
  </div>"""


def file_size_label(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "0 MB"
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} GB"


def write_brand_logo_asset(output_dir: Path) -> str:
    source = brand_logo_path()
    destination = output_dir / "assets" / "brand" / BRAND_LOGO_FILE
    if source.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists() or source.read_bytes() != destination.read_bytes():
            shutil.copyfile(source, destination)
    return f"assets/brand/{BRAND_LOGO_FILE}"


def write_live_timeline_assets(output_dir: Path) -> dict[str, str]:
    return write_static_asset_group(
        output_dir,
        live_timeline_asset_source_dir(),
        "live-timeline",
        LIVE_TIMELINE_ASSET_FILES,
    )


def write_control_bar_assets(output_dir: Path) -> dict[str, str]:
    return write_static_asset_group(
        output_dir,
        control_bar_asset_source_dir(),
        "control-bar",
        CONTROL_BAR_ASSET_FILES,
    )


def write_static_asset_group(output_dir: Path, source_dir: Path, asset_group: str, filenames: tuple[str, ...]) -> dict[str, str]:
    destination_dir = output_dir / "assets" / asset_group
    assets: dict[str, str] = {}
    for filename in filenames:
        source = source_dir / filename
        if not source.exists():
            continue
        source_bytes = source.read_bytes()
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / filename
        if not destination.exists() or source_bytes != destination.read_bytes():
            destination.write_bytes(source_bytes)
        digest = hashlib.sha1(source_bytes).hexdigest()[:10]
        assets[filename.rsplit(".", 1)[-1]] = f"assets/{asset_group}/{filename}?v={digest}"
    return assets


def live_timeline_asset_source_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "live-timeline"


def control_bar_asset_source_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "control-bar"


def brand_logo_path() -> Path:
    return Path(__file__).resolve().parents[3] / "assets" / "brand" / BRAND_LOGO_FILE


def project_home_icon_svg(name: str) -> str:
    icons = {
        "clock": '<svg data-cuted-icon="clock" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="8"/><path d="M12 7v5l3 2"/></svg>',
        "folder-video": '<svg data-cuted-icon="folder-video" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H9l2 2h7.5A2.5 2.5 0 0 1 21 9.5v7A2.5 2.5 0 0 1 18.5 19h-13A2.5 2.5 0 0 1 3 16.5Z"/><path d="m10 11 5 3-5 3Z"/></svg>',
        "local-video": '<svg data-cuted-icon="local-video" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="4" y="5" width="12" height="14" rx="2"/><path d="m16 10 4-2v8l-4-2M8 9h4M8 13h3"/></svg>',
        "mic": '<svg data-cuted-icon="mic" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6"/></svg>',
        "sparkles": '<svg data-cuted-icon="sparkles" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m12 3 1.4 4.1L17 9l-3.6 1.9L12 15l-1.4-4.1L7 9l3.6-1.9Z"/><path d="m5 14 .9 2.6L8 18l-2.1 1.4L5 22l-.9-2.6L2 18l2.1-1.4ZM19 13l.8 2.2L22 16l-2.2.8L19 19l-.8-2.2L16 16l2.2-.8Z"/></svg>',
        "youtube": '<svg data-cuted-icon="youtube" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3" y="6" width="18" height="12" rx="4"/><path d="m10 9 5 3-5 3Z"/></svg>',
    }
    return icons.get(name, "")


def suggestion_count_options() -> str:
    return "\n".join(f'<option value="{value}"{" selected" if value == 10 else ""}>{value}</option>' for value in range(1, 11))


def openai_model_options() -> str:
    labels = {"gpt-5": "GPT-5", "gpt-5-mini": "GPT-5 mini", "gpt-5-nano": "GPT-5 nano"}
    return "\n".join(option_html(key, labels.get(key, key), key == "gpt-5-mini") for key in OPENAI_TEXT_PRICES_USD_PER_1M)


def transcribe_model_options() -> str:
    return option_html("whisper-1", "Whisper 1", True)


def option_html(value: str, label: str, selected: bool) -> str:
    marker = " selected" if selected else ""
    return f'<option value="{html.escape(value)}"{marker}>{html.escape(label)}</option>'


def gear_icon_svg() -> str:
    return (
        '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
        '<path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/>'
        '<path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.04.04a2 2 0 1 1-2.83 2.83l-.04-.04A1.7 1.7 0 0 0 15 19.37a1.7 1.7 0 0 0-1 1.56V21a2 2 0 1 1-4 0v-.07a1.7 1.7 0 0 0-1-1.56 1.7 1.7 0 0 0-1.88.34l-.04.04a2 2 0 1 1-2.83-2.83l.04-.04A1.7 1.7 0 0 0 4.63 15a1.7 1.7 0 0 0-1.56-1H3a2 2 0 1 1 0-4h.07a1.7 1.7 0 0 0 1.56-1 1.7 1.7 0 0 0-.34-1.88l-.04-.04a2 2 0 1 1 2.83-2.83l.04.04A1.7 1.7 0 0 0 9 4.63a1.7 1.7 0 0 0 1-1.56V3a2 2 0 1 1 4 0v.07a1.7 1.7 0 0 0 1 1.56 1.7 1.7 0 0 0 1.88-.34l.04-.04a2 2 0 1 1 2.83 2.83l-.04.04A1.7 1.7 0 0 0 19.37 9a1.7 1.7 0 0 0 1.56 1H21a2 2 0 1 1 0 4h-.07A1.7 1.7 0 0 0 19.4 15Z"/>'
        '</svg>'
    )


def header_action_icon_svg(name: str) -> str:
    icons = {
        "new-project": (
            '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            '<rect x="4" y="5" width="13" height="14" rx="2.4"/>'
            '<path d="m17 10 3-1.8v7.6L17 14"/>'
            '<path d="M10.5 8.8v6.4M7.3 12h6.4"/>'
            '</svg>'
        ),
        "render": (
            '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            '<rect x="3.5" y="5.5" width="13" height="13" rx="2.6"/>'
            '<path d="m9.2 9.2 4.6 2.8-4.6 2.8Z"/>'
            '<path d="M17.5 7.5h2.8M18.9 6.1v2.8"/>'
            '<path d="m17.8 15.7 2.7 2.7M20.5 15.7l-2.7 2.7"/>'
            '<path d="M5.8 3.8 4.6 2.5M7.9 3.2 8.4 1.5"/>'
            '</svg>'
        ),
    }
    return icons.get(name, gear_icon_svg())


def clean_clip_title(value: str) -> str:
    cleaned = re.sub(r"^[\s>»:\-]+", "", str(value or "")).strip()
    return cleaned or str(value or "").strip() or "Corte sem titulo"


def card_html(moment: Moment) -> str:
    video_tag = media_html(moment)
    cover_panel, copy_panel = publish_panels_html(moment)
    duration = max(0.0, moment.end - moment.start)
    title = html.escape(clean_clip_title(moment.title))
    summary = f"{moment.start:.1f}s - {moment.end:.1f}s ({duration:.1f}s)"
    return f"""
    <details class="card" data-rank="{moment.rank}" data-clip-title="{title}" data-clip-summary="{html.escape(summary)}" data-start="{moment.start:.3f}" data-end="{moment.end:.3f}" data-duration="{duration:.3f}" data-preview-format="tiktok">
      <summary class="clip-summary">
        <span class="clip-control-surface cuted-control-surface-slot" data-cuted-control-surface aria-label="Control surface do corte"></span>
        <span data-card-summary hidden>{html.escape(summary)}</span>
        <span class="clip-row-timeline preview-camera-timeline" data-card-row-timeline data-preview-camera-timeline aria-label="Timeline do corte"></span>
      </summary>
      <div class="editor-shell">
        {cover_panel}
        <div class="editor-preview">
          <div class="preview-frame">
            <div class="media camera-surface" data-overlay-surface>
              {video_tag}
              <video class="camera-fit-bg" data-camera-fit-bg playsinline muted preload="none" aria-hidden="true" tabindex="-1"></video>
              <img class="camera-fit-logo" src="{html.escape('assets/brand/' + BRAND_LOGO_FILE)}" alt="" aria-hidden="true">
              <div class="camera-reticle"></div>
              <div class="preview-caption-layer" data-preview-caption-layer aria-live="off"></div>
              <div data-overlay-layer-list></div>
              <div class="overlay-menu" data-overlay-menu hidden></div>
              <input data-overlay-image type="file" accept="image/png,image/webp,image/jpeg" hidden>
            </div>
            <div class="layer-strip" data-layer-strip></div>
            <div class="bumper-sequence" data-bumper-sequence></div>
            <div class="edit-hidden-hooks" aria-hidden="true">
              <input data-bumper-video="intro" type="file" accept="video/mp4,video/quicktime,video/webm,video/x-m4v" hidden tabindex="-1">
              <input data-bumper-video="outro" type="file" accept="video/mp4,video/quicktime,video/webm,video/x-m4v" hidden tabindex="-1">
            </div>
          </div>
        </div>
        {copy_panel}
      </div>
    </details>"""


def publish_panels_html(moment: Moment) -> tuple[str, str]:
    metadata = moment.publish_metadata or {}
    cover = metadata.get("cover") if isinstance(metadata.get("cover"), dict) else {}
    frame_value = cover.get("selected_frame") if isinstance(cover, dict) else ""
    frame = str(frame_value or moment.frame_file or "")
    poster = html.escape(cache_busted_url(frame, preview_cache_token(moment))) if frame else ""
    reason_value = cover.get("reason") if isinstance(cover, dict) else ""
    reason = html.escape(str(reason_value or "Frame de pico do corte."))
    hook = html.escape(str(metadata.get("hook") or moment.peak_text or moment.title))
    title = html.escape(str(metadata.get("title") or clean_clip_title(moment.title)))
    description = html.escape(str(metadata.get("description") or moment.reason or moment.transcript))
    trend = metadata.get("trend_context") if isinstance(metadata.get("trend_context"), dict) else {}
    trend_summary = html.escape(str(trend.get("summary") if isinstance(trend, dict) else "" or "Sugestao local do corte."))
    tags = publish_hashtags_html(metadata.get("hashtags"))
    tag_value = html.escape(" ".join(publish_hashtags_list(metadata.get("hashtags"))), quote=True)
    cover_img = f'<img src="{poster}" alt="Capa sugerida do corte {moment.rank}">' if poster else "<span></span>"
    cover_zoom = int(round(clamp_float(cover.get("zoom") if isinstance(cover, dict) else None, 1.0, 1.8, 1.0) * 100))
    cover_options = publish_cover_options_html(moment, cover, frame)
    return (
        f"""<aside class="publish-panel publish-cover-panel" data-publish-panel="cover">
          <strong>Capa IA</strong>
          <div class="publish-cover-stage" data-publish-cover-stage>
            <div class="publish-cover-frame" data-publish-cover-preview>{cover_img}<div class="publish-cover-layer-list" data-publish-cover-layer-list></div></div>
            <div class="overlay-menu publish-cover-menu" data-publish-cover-menu hidden></div>
          </div>
          <div class="publish-cover-adjust">
            <label>Zoom <output data-publish-cover-zoom-value>{cover_zoom}%</output>
              <input data-publish-cover-zoom type="range" min="100" max="180" step="5" value="{cover_zoom}">
            </label>
            <button type="button" data-publish-cover-zoom-reset title="Restaurar zoom">Reset</button>
          </div>
          <input data-publish-cover-image type="file" accept="image/png,image/webp,image/jpeg" hidden>
          {cover_options}
          <p>{reason}</p>
        </aside>""",
        f"""<aside class="publish-panel publish-copy-panel" data-publish-panel="copy">
          <div class="publish-panel-head">
            <strong>Publicacao IA</strong>
            <button type="button" data-publish-reset title="Restaurar sugestao">Reset</button>
          </div>
          <label class="publish-field">Titulo
            <input data-publish-field="title" type="text" value="{title}">
          </label>
          <label class="publish-field">Hook
            <input data-publish-field="hook" type="text" value="{hook}">
          </label>
          <label class="publish-field">Descricao
            <textarea data-publish-field="description" rows="3">{description}</textarea>
          </label>
          <label class="publish-field">Hashtags
            <input data-publish-field="hashtags" type="text" value="{tag_value}">
          </label>
          <div class="publish-tags">{tags}</div>
          <small>{trend_summary}</small>
        </aside>""",
    )


def publish_cover_options_html(moment: Moment, cover: object, selected: str) -> str:
    cover_data = cover if isinstance(cover, dict) else {}
    raw = cover_data.get("candidates") if isinstance(cover_data, dict) else []
    candidates = publish_hashtags_list(raw) or list(publish_cover_candidates_for_moment(moment))
    buttons = []
    for index, frame in enumerate(unique_strings(candidates)[:4], start=1):
        src = html.escape(cache_busted_url(frame, preview_cache_token(moment)), quote=True)
        value = html.escape(frame, quote=True)
        active = " active" if frame == selected else ""
        buttons.append(
            f'<button type="button" class="{active}" data-publish-cover-option="{value}" '
            f'aria-label="Escolher capa {index}"><img src="{src}" alt=""></button>'
        )
    return f'<div class="publish-cover-options">{"".join(buttons)}</div>' if buttons else ""


def publish_hashtags_html(value: object) -> str:
    cleaned = [html.escape(str(tag)) for tag in publish_hashtags_list(value)]
    if not cleaned:
        cleaned = ["#IA", "#Podcast"]
    return "".join(f"<span>{tag}</span>" for tag in cleaned[:PUBLISH_MAX_HASHTAGS])


def publish_hashtags_list(value: object) -> list[str]:
    tags = value if isinstance(value, list) else []
    return [str(tag).strip() for tag in tags if str(tag).strip()]


def unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        key = value.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(key)
    return result


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


def page_html(
    source_label: str,
    cards: str,
    data: str,
    logo_src: str,
    live_timeline_assets: dict[str, str] | None = None,
    control_bar_assets: dict[str, str] | None = None,
) -> str:
    live_timeline_css = live_timeline_assets_html(live_timeline_assets or {}, "css")
    live_timeline_js = live_timeline_assets_html(live_timeline_assets or {}, "js")
    control_bar_css = static_assets_html(control_bar_assets or {}, "css")
    control_bar_js = static_assets_html(control_bar_assets or {}, "js")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CUTED Review</title>
{live_timeline_css}
{control_bar_css}
  <style>{css()}</style>
</head>
<body data-format="tiktok" data-tab="edit">
  <header>
    <div></div>
    <div class="brand-lockup" aria-label="CUTED">
      <img class="brand-logo" src="{html.escape(logo_src)}" alt="CUTED">
      <p>{html.escape(source_label)}</p>
    </div>
    <div class="header-actions">
      <button id="reset-ui" class="header-icon-button header-new-project" type="button" aria-label="Novo projeto" title="Novo projeto">{header_action_icon_svg("new-project")}</button>
      <button id="finalize-videos" class="header-icon-button header-render-button" type="button" aria-label="Renderizar" title="Renderizar">{header_action_icon_svg("render")}</button>
      <button id="open-settings" class="header-icon-button header-settings-button" type="button" aria-label="Configuracoes OpenAI" title="Configuracoes OpenAI">{gear_icon_svg()}</button>
    </div>
  </header>
  <section class="import-stage" aria-label="Importar projeto">
    <form class="import-panel" data-import-form>
      <div class="stage-head">
        <div>
          <strong>Importar projeto</strong>
          <p>Link, contexto e destino local.</p>
        </div>
        <button type="submit">Importar</button>
      </div>
      <div class="import-key-banner" data-import-key-banner hidden>
        <span>Adicione sua chave OpenAI aqui para importar com IA.</span>
        <button type="button" data-import-key-open>Abrir configuracoes</button>
      </div>
      <div class="import-grid">
        <label>Video local
          <span class="import-path-row">
            <input name="source_path" type="text" value="" placeholder="Selecione um MP4, MOV, M4V ou WebM" autocomplete="off">
            <button type="button" data-select-video-file>Video</button>
          </span>
          <small>Fluxo principal: use o arquivo inteiro para mapa visual, camera e render local.</small>
        </label>
        <label>Link do YouTube (experimental)
          <input name="source_url" type="url" placeholder="Cole um link apenas para teste rapido" autocomplete="off">
          <small>Se o YouTube bloquear, baixe com sua ferramenta preferida e importe o video local.</small>
        </label>
        <label>Destino dos renders
          <span class="import-path-row">
            <input name="output_path" type="text" value="" placeholder="Selecione a pasta dos videos finais" autocomplete="off">
            <button type="button" data-select-folder>Pasta</button>
          </span>
        </label>
        <label>Quantidade de sugestoes
          <select name="preview_count">
            {suggestion_count_options()}
          </select>
        </label>
      </div>
      <input name="language" type="hidden" value="pt">
      <input name="preset" type="hidden" value="tiktok">
      <fieldset class="duration-profile">
        <legend>Duracao dos cortes</legend>
        <label>
          <input name="duration_profile" type="radio" value="short">
          <span><strong>Curto</strong><small>20-45s</small></span>
        </label>
        <label>
          <input name="duration_profile" type="radio" value="medium" checked>
          <span><strong>Medio</strong><small>30-70s</small></span>
        </label>
        <label>
          <input name="duration_profile" type="radio" value="long">
          <span><strong>Longo</strong><small>60-120s</small></span>
        </label>
      </fieldset>
      <label class="import-context">Contexto para a IA
        <textarea name="context_prompt" rows="5" placeholder="Opcional. Ex.: priorize momentos polemicos, engracados, com frase completa e gancho forte."></textarea>
      </label>
      <div class="import-status" data-import-status>Pronto.</div>
      <div class="import-result" data-import-result></div>
    </form>
  </section>
  <section class="final-stage">
    <div class="stage-head">
      <div>
        <strong>Fila</strong>
        <p data-final-summary>Nada na fila.</p>
      </div>
    </div>
    <div class="render-status" data-render-status></div>
    <div class="render-results" data-render-results></div>
  </section>
  <section class="empty-project-stage" aria-label="Projeto em branco">
    <div class="empty-project-panel">
      <strong>Novo projeto em branco</strong>
      <p>Importe um link ou arquivo local para carregar novos cortes.</p>
      <button type="button" data-empty-import>Importar projeto</button>
    </div>
  </section>
  <div class="settings-backdrop" data-settings-modal hidden>
    <section class="settings-panel" data-settings-panel role="dialog" aria-modal="true" aria-labelledby="settings-title" aria-describedby="settings-description" tabindex="-1">
      <div class="settings-aura" aria-hidden="true"></div>
      <div class="settings-head">
        <div class="settings-title-row">
          <span class="settings-orb" aria-hidden="true">{gear_icon_svg()}</span>
          <div>
            <strong id="settings-title">OpenAI</strong>
            <p id="settings-description">Chave, modelos e teste de conexao do CUTED.</p>
          </div>
        </div>
        <button class="settings-close-button" type="button" data-settings-close aria-label="Fechar configuracoes">X</button>
      </div>
      <form data-settings-form class="settings-form">
        <div class="settings-status" data-settings-status>Carregando...</div>
        <label class="settings-field settings-token-field">Token OpenAI
          <input name="api_key" type="password" autocomplete="off" placeholder="Cole aqui apenas se quiser trocar o token">
        </label>
        <div class="settings-grid">
          <label class="settings-field">Provedor IA
            <select name="ai_provider">
              <option value="openai">OpenAI</option>
              <option value="auto">Auto</option>
              <option value="local">Local</option>
            </select>
          </label>
          <label class="settings-field">Modelo de analise
            <select name="openai_model">
              {openai_model_options()}
            </select>
          </label>
          <label class="settings-field">Transcricao
            <select name="transcribe_model">
              {transcribe_model_options()}
            </select>
          </label>
        </div>
        <div class="settings-usage" data-settings-usage>Sem uso registrado nesta maquina.</div>
        <div class="settings-actions">
          <button type="button" data-settings-test>Testar conexao</button>
          <button type="submit">Salvar</button>
        </div>
        <small>Estimativa local. Confira o valor oficial no painel da OpenAI.</small>
      </form>
    </section>
  </div>
  <div class="render-queue-backdrop" data-render-queue-modal hidden>
    <section class="render-queue-panel" data-render-queue-panel role="dialog" aria-modal="true" aria-labelledby="render-queue-title" tabindex="-1">
      <div class="render-queue-aura" aria-hidden="true"></div>
      <div class="render-queue-head">
        <div>
          <strong id="render-queue-title">Render</strong>
          <p>Fila local, cache e arquivos prontos.</p>
        </div>
        <button class="render-queue-close" type="button" data-render-queue-close aria-label="Fechar render">X</button>
      </div>
      <div class="render-resource-switch" role="group" aria-label="Uso da maquina">
        <button type="button" data-render-profile="eco">Eco</button>
        <button type="button" data-render-profile="medium" class="active">Medio</button>
        <button type="button" data-render-profile="high">Alto</button>
      </div>
      <label class="render-cover-frame-toggle">
        <input type="checkbox" data-render-cover-frame>
        <span><strong>Capa TikTok</strong><small>Cria uma copia com a capa no ultimo frame.</small></span>
      </label>
      <div class="render-queue-status" data-render-queue-status>Nenhum render em andamento.</div>
      <div class="render-queue-list" data-render-queue-list></div>
    </section>
  </div>
  <div class="workspace-exit-backdrop" data-workspace-exit-modal hidden>
    <section class="workspace-exit-panel" data-workspace-exit-panel role="dialog" aria-modal="true" aria-labelledby="workspace-exit-title" aria-describedby="workspace-exit-description" tabindex="-1">
      <div class="workspace-exit-aura" aria-hidden="true"></div>
      <div class="workspace-exit-head">
        <div>
          <strong id="workspace-exit-title">Sair deste projeto?</strong>
          <p id="workspace-exit-description">Voce vai voltar para Projetos recentes. Renders e arquivos do projeto continuam salvos.</p>
        </div>
        <button class="workspace-exit-close" type="button" data-workspace-exit-cancel aria-label="Continuar editando">X</button>
      </div>
      <div class="workspace-exit-body">
        <p>As edicoes locais deste navegador serao preservadas enquanto este projeto continuar neste browser.</p>
        <p>Para criar outro video, volte para a Home e use Novo projeto.</p>
      </div>
      <div class="workspace-exit-actions">
        <button type="button" data-workspace-exit-cancel>Cancelar</button>
        <button class="primary" type="button" data-workspace-exit-confirm>Voltar para recentes</button>
      </div>
    </section>
  </div>
  <main>{cards}</main>
{live_timeline_js}
{control_bar_js}
  <script>window.CUTTED_DATA = {data}; window.CUTTED_SCRIPT = {json.dumps(str(Path(__file__).resolve()))};</script>
  <script>{js()}</script>
</body>
</html>"""


def live_timeline_assets_html(assets: dict[str, str], kind: str) -> str:
    return static_assets_html(assets, kind)


def static_assets_html(assets: dict[str, str], kind: str) -> str:
    value = assets.get(kind)
    if not value:
        return ""
    escaped = html.escape(value)
    if kind == "css":
        return f'  <link rel="stylesheet" href="{escaped}">'
    if kind == "js":
        return f'  <script src="{escaped}"></script>'
    return ""


def project_home_css() -> str:
    return """
body[data-project-home]{overflow-x:hidden}body[data-project-home] header{display:none}.project-home{width:min(1080px,calc(100vw - 36px));max-width:none;min-height:100vh;padding:30px 0 34px;align-content:start;gap:12px}.home-brand-stage{display:grid;place-items:center;min-height:164px;padding:4px 0 0}.home-logo-orbit{position:relative;display:grid;place-items:center;width:min(620px,84vw);isolation:isolate}.home-logo-orbit:before{position:absolute;inset:18% 12%;z-index:-1;border-radius:999px;background:radial-gradient(circle at 26% 50%,rgba(17,162,207,.28),transparent 34%),radial-gradient(circle at 74% 50%,rgba(175,207,42,.24),transparent 34%);filter:blur(24px);content:"";animation:home-logo-aura 5.2s ease-in-out infinite}.home-brand-logo{display:block;width:min(520px,80vw);height:104px;object-fit:contain;filter:drop-shadow(0 0 12px rgba(17,162,207,.18)) drop-shadow(0 0 12px rgba(175,207,42,.12));animation:home-logo-breathe 5.8s ease-in-out infinite}.project-library{display:grid;align-content:start;gap:0;border:1px solid var(--glass-border);border-radius:8px;background:linear-gradient(180deg,rgba(255,255,255,.052),rgba(255,255,255,.016)),rgba(7,7,7,.76);box-shadow:0 18px 46px rgba(0,0,0,.42),inset 0 1px 0 var(--glass-edge);backdrop-filter:blur(22px) saturate(1.22);overflow:hidden}.project-section-head{display:flex;justify-content:space-between;gap:12px;align-items:center;min-height:52px;padding:9px 16px;border-bottom:1px solid rgba(231,231,232,.1)}.project-section-head strong{font-size:17px;letter-spacing:0}.project-toolbar{display:flex;gap:8px;align-items:center;justify-content:flex-end;flex-wrap:wrap}.project-toolbar button,.project-row-actions button,.project-row-actions a{min-height:32px;padding:6px 11px}.project-icon-button{display:inline-grid!important;place-items:center;width:36px;min-width:36px;padding:0!important;font-size:17px;font-weight:900}.project-primary{border-color:rgba(175,207,42,.58)!important;background:linear-gradient(180deg,rgba(175,207,42,.26),rgba(17,162,207,.1)),rgba(23,32,14,.78)!important;color:var(--color-text)!important}.project-table{display:grid;max-height:min(456px,calc(100vh - 304px));overflow:auto;scrollbar-width:thin;scrollbar-color:rgba(175,207,42,.55) rgba(255,255,255,.055)}.project-table::-webkit-scrollbar{width:10px}.project-table::-webkit-scrollbar-track{background:rgba(255,255,255,.04);border-left:1px solid rgba(231,231,232,.06)}.project-table::-webkit-scrollbar-thumb{border:2px solid rgba(7,7,7,.76);border-radius:999px;background:linear-gradient(180deg,rgba(17,162,207,.72),rgba(175,207,42,.72));box-shadow:0 0 12px rgba(17,162,207,.22)}.project-table::-webkit-scrollbar-thumb:hover{background:linear-gradient(180deg,var(--color-brand-blue),var(--color-brand-green))}.project-table-head,.project-row{display:grid;grid-template-columns:minmax(230px,1fr) minmax(245px,.82fr) 100px minmax(214px,.58fr);gap:14px;align-items:center}.project-table-head{position:sticky;top:0;z-index:2;min-height:34px;padding:0 16px;border-bottom:1px solid rgba(231,231,232,.08);background:rgba(11,11,11,.92);color:var(--color-text-muted);font-size:11px;text-transform:uppercase;backdrop-filter:blur(12px)}.project-row{min-height:76px;padding:12px 16px;border-bottom:1px solid rgba(231,231,232,.075);animation:home-row-in .42s ease both}.project-row:last-child{border-bottom:0}.project-row:nth-child(2){animation-delay:.03s}.project-row:nth-child(3){animation-delay:.08s}.project-row:nth-child(4){animation-delay:.13s}.project-row:nth-child(5){animation-delay:.18s}.project-row:hover{background:linear-gradient(90deg,rgba(17,162,207,.085),rgba(175,207,42,.045),transparent)}.project-name-cell{display:grid;gap:3px;min-width:0}.project-name-cell strong{font-size:15px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.project-name-cell p{margin:0;color:rgba(175,207,42,.82);font-size:12px}.project-name-cell small{display:block;color:#777;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.project-meta-cell{display:flex;gap:10px;margin:0}.project-meta-cell div{display:grid;gap:2px;min-width:62px}.project-meta-cell dt{color:var(--color-text-muted);font-size:11px}.project-meta-cell dd{margin:0;color:var(--color-text);font-weight:800}.project-updated-cell{color:var(--color-text-muted);font-size:12px}.project-row-actions{display:flex;gap:7px;justify-content:flex-end;flex-wrap:wrap}.project-row-actions a{display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--glass-border);border-radius:999px;background:var(--color-brand-white);color:var(--color-brand-black);text-decoration:none}.project-row-actions button[data-delete-project]{color:var(--color-danger)}.project-row-actions button:disabled{opacity:.38;cursor:not-allowed}.project-import{margin-top:12px}.project-import[hidden],.project-library[hidden]{display:none}.project-import .import-panel{animation:home-row-in .28s ease both}.new-project-panel{gap:14px;border-color:var(--glass-border);background:linear-gradient(180deg,rgba(255,255,255,.052),rgba(255,255,255,.016)),rgba(7,7,7,.76);box-shadow:0 18px 46px rgba(0,0,0,.42),inset 0 1px 0 var(--glass-edge);backdrop-filter:blur(22px) saturate(1.22)}.new-project-head,.new-project-footer,.ai-context-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.new-project-head{min-height:38px;padding-bottom:10px;border-bottom:1px solid rgba(231,231,232,.1)}.new-project-head strong{font-size:17px}.source-toggle{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.source-toggle label,.duration-size-toggle label{position:relative;display:grid}.source-toggle input,.duration-size-toggle input{position:absolute;opacity:0;pointer-events:none}.source-toggle span,.duration-size-toggle span{display:grid;place-items:center;min-height:48px;padding:8px 12px;border:1px solid var(--glass-border);border-radius:8px;background:rgba(231,231,232,.055);box-shadow:inset 0 1px rgba(255,255,255,.14);color:var(--color-text-soft);font-weight:800}.source-toggle input:checked+span,.duration-size-toggle input:checked+span{border-color:rgba(175,207,42,.72);background:linear-gradient(180deg,rgba(175,207,42,.2),rgba(17,162,207,.08)),rgba(13,18,12,.84);color:var(--color-text);box-shadow:inset 0 1px rgba(255,255,255,.18),0 0 22px rgba(175,207,42,.12)}.source-panel{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px}.source-panel[hidden]{display:none}.new-project-grid{display:grid;grid-template-columns:minmax(140px,.32fr) minmax(0,1fr);gap:12px;align-items:end}.suggestion-field{display:grid;gap:6px;color:var(--color-text-muted);font-size:12px}.duration-size-toggle{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:0;padding:0;border:0}.duration-size-toggle legend{grid-column:1/-1;color:var(--color-text-muted);font-size:12px}.duration-size-toggle span{min-height:58px}.duration-size-toggle strong{font-size:22px;line-height:1}.duration-size-toggle small{color:var(--color-text-muted);font-size:11px}.ai-context-box{display:grid;gap:8px;padding:12px;border:1px solid rgba(17,162,207,.28);border-radius:8px;background:linear-gradient(135deg,rgba(17,162,207,.09),rgba(175,207,42,.035)),rgba(0,0,0,.18)}.ai-context-box textarea{min-height:126px;border-color:rgba(17,162,207,.28);background:rgba(0,0,0,.44)}.new-project-footer{padding-top:4px}.new-project-footer span{color:var(--color-text-muted);font-size:12px}@keyframes home-logo-aura{0%,100%{opacity:.56;transform:scale(.98)}50%{opacity:.84;transform:scale(1.03)}}@keyframes home-logo-breathe{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-1px) scale(1.006)}}@keyframes home-row-in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}@media(max-width:900px){.project-home{width:min(100vw - 20px,760px);padding-top:26px}.home-brand-stage{min-height:138px}.home-brand-logo{height:78px}.project-section-head{align-items:flex-start;flex-direction:column}.project-toolbar{justify-content:flex-start}.project-table{max-height:none}.project-table-head{display:none}.project-row,.new-project-grid,.source-panel{grid-template-columns:1fr;gap:10px}.project-meta-cell{justify-content:space-between}.project-row-actions{justify-content:flex-start}.project-updated-cell{display:none}}
.project-empty-state{display:grid;justify-items:center;gap:6px;min-height:116px;padding:30px 18px;border-top:1px solid rgba(231,231,232,.075);color:rgba(231,231,232,.64);text-align:center;animation:home-row-in .3s ease both}.project-empty-state strong{color:var(--color-text);font-size:15px}.project-empty-state p{margin:0;color:var(--color-text-muted);font-size:12px}
"""


def project_home_compact_import_css() -> str:
    return """
.sr-only{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}
.home-settings-button{position:fixed;top:18px;right:22px;z-index:20;border-color:var(--glass-border);background:rgba(231,231,232,.055);color:var(--color-text-soft);box-shadow:inset 0 1px rgba(255,255,255,.14)}
.home-settings-button:hover{border-color:rgba(17,162,207,.5);color:var(--color-text);background:rgba(17,162,207,.1)}
.home-settings-button svg{display:block;width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.new-project-config-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;align-items:start}
.new-project-config-block{display:grid;gap:8px;justify-self:stretch;width:100%;min-height:170px;padding:10px;border:1px solid rgba(231,231,232,.08);border-radius:8px;background:rgba(255,255,255,.018)}
.new-project-block-title{display:flex;align-items:baseline;justify-content:space-between;gap:10px;min-height:18px}
.new-project-block-title strong{color:var(--color-text);font-size:12px;text-transform:uppercase}
.new-project-block-title span,.tuning-copy{color:var(--color-text-muted);font-size:11px}
.icon-source-toggle{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;width:100%}
.icon-source-toggle span,.duration-size-toggle label span,.icon-action-button,.field-icon{display:grid;place-items:center;border:1px solid var(--glass-border);border-radius:8px;background:rgba(231,231,232,.055);box-shadow:inset 0 1px rgba(255,255,255,.14);color:var(--color-text-soft)}
.icon-source-toggle span{grid-template-rows:auto auto;gap:4px;min-height:68px;padding:9px 8px}
.icon-source-toggle span strong{font-size:11px;letter-spacing:0;text-transform:uppercase}
.icon-source-toggle input:checked+span,.duration-size-toggle input:checked+span{border-color:rgba(175,207,42,.72);background:rgba(25,33,18,.9);color:var(--color-text);box-shadow:inset 0 1px rgba(255,255,255,.18),0 0 18px rgba(175,207,42,.13)}
.icon-source-toggle svg,.duration-size-toggle svg,.icon-action-button svg,.field-icon svg{display:block;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.icon-source-toggle svg{width:30px;height:30px}
.source-panel{grid-template-columns:minmax(0,1fr) 52px;gap:8px;width:100%}
.source-panel[data-source-panel=youtube]{grid-template-columns:minmax(0,1fr)}
.source-panel input,.suggestion-field select{min-height:44px}
.icon-action-button{width:52px;min-width:52px;min-height:44px;padding:0!important}
.icon-action-button svg,.field-icon svg{width:19px;height:19px}
.icon-action-button:hover{border-color:rgba(17,162,207,.52);color:var(--color-text);background:rgba(17,162,207,.1)}
.cuts-control-grid{display:grid;grid-template-columns:minmax(128px,.42fr) minmax(0,.58fr);gap:10px;align-items:stretch}
.cut-count-field{display:grid!important;grid-template-rows:auto 1fr;gap:8px;min-width:0;color:inherit;font-size:inherit}
.cut-count-field .tuning-copy{align-self:end;font-weight:800;text-transform:uppercase}
.cut-count-field select{width:100%;min-height:96px;padding:0 14px;border:1px solid var(--glass-border);border-radius:8px;background:#202020;color:var(--color-text);font-weight:900;text-align:center}
.cut-count-field select option{background:#111;color:var(--color-text)}
.duration-size-toggle{display:grid;grid-template-columns:minmax(0,1fr) repeat(3,62px);gap:8px;align-items:center;margin:0;padding:0;border:0}
.duration-size-toggle legend.sr-only{position:absolute;grid-column:auto;color:inherit;font-size:inherit}
.duration-size-toggle>.tuning-copy{display:flex!important;align-items:center;min-height:auto!important;padding:0!important;border:0!important;background:transparent!important;box-shadow:none!important;color:var(--color-text-muted)!important;font-weight:600}
.duration-size-toggle label span{gap:2px;min-width:62px;min-height:44px;padding:6px 8px}
.duration-size-toggle label small{color:var(--color-text-muted);font-size:10px;line-height:1}
.duration-tile-grid{grid-template-columns:repeat(2,minmax(0,1fr));grid-template-rows:repeat(2,minmax(0,1fr));align-items:stretch}
.duration-tile-grid label span{width:100%;min-width:0;min-height:44px}
.duration-option-long{grid-column:1/-1}
.duration-size-toggle svg{width:14px;height:14px;opacity:.72}
.duration-size-toggle strong{font-size:17px;line-height:1}
.ai-context-title{display:grid;gap:2px}.ai-context-title small{color:var(--color-text-muted);font-size:11px;line-height:1.25}.ai-context-device-row{display:grid;grid-template-columns:minmax(160px,240px) minmax(120px,1fr);gap:8px;align-items:center}.ai-context-device-row select{min-height:32px;padding:5px 8px;border-color:rgba(231,231,232,.12);font-size:12px}.ai-context-level{height:8px;overflow:hidden;border:1px solid rgba(231,231,232,.12);border-radius:999px;background:rgba(0,0,0,.32)}.ai-context-level span{display:block;width:0%;height:100%;border-radius:999px;background:linear-gradient(90deg,var(--color-brand-blue),var(--color-brand-green));transition:width .16s ease}.ai-context-status{min-height:18px;color:rgba(231,231,232,.68);font-size:12px}.ai-context-box[data-audio-state=recording]{border-color:rgba(17,162,207,.72);box-shadow:0 0 0 1px rgba(17,162,207,.22),0 0 28px rgba(17,162,207,.12)}.ai-context-box[data-audio-state=recording] .context-audio-button{border-color:rgba(17,162,207,.8);background:rgba(17,162,207,.18);color:var(--color-text);animation:context-mic-pulse 1.1s ease-in-out infinite}.ai-context-box[data-audio-state=transcribing] .context-audio-button{border-color:rgba(175,207,42,.7);background:rgba(175,207,42,.14);color:var(--color-text)}.ai-context-box[data-audio-state=applied]{border-color:rgba(175,207,42,.52)}.ai-context-box[data-audio-state=error]{border-color:rgba(255,111,111,.52)}
.context-audio-button{border-radius:999px}
@keyframes context-mic-pulse{0%,100%{box-shadow:0 0 0 0 rgba(17,162,207,.18)}50%{box-shadow:0 0 0 7px rgba(17,162,207,.08)}}
.import-submit-button{min-width:116px;min-height:42px!important;border-color:var(--color-brand-white)!important;background:var(--color-brand-white)!important;color:var(--color-brand-black)!important;font-weight:900;box-shadow:0 10px 24px rgba(0,0,0,.32)}
.import-submit-button:hover{transform:translateY(-1px);border-color:var(--color-brand-green)!important;background:var(--color-brand-green)!important;color:var(--color-brand-black)!important;box-shadow:0 12px 26px rgba(0,0,0,.36),0 0 16px rgba(175,207,42,.16)}
.home-import-loading{position:fixed;inset:0;z-index:60;display:grid;place-items:center;background:radial-gradient(circle at 50% 42%,rgba(17,162,207,.12),transparent 30%),radial-gradient(circle at 56% 52%,rgba(175,207,42,.09),transparent 34%),rgba(5,5,5,.88);backdrop-filter:blur(18px) saturate(1.25)}
.home-import-loading[hidden]{display:none}
.home-import-loading-inner{display:grid;justify-items:center;gap:14px;width:min(520px,calc(100vw - 44px));animation:home-row-in .28s ease both}
.home-import-loading img{display:block;width:min(360px,76vw);height:96px;object-fit:contain;filter:drop-shadow(0 0 14px rgba(17,162,207,.16)) drop-shadow(0 0 12px rgba(175,207,42,.12))}
.home-import-progress{position:relative;width:100%;height:42px;border:1px solid var(--glass-border);border-radius:999px;background:rgba(231,231,232,.055);box-shadow:inset 0 1px rgba(255,255,255,.14),0 18px 44px rgba(0,0,0,.34);overflow:hidden}
.home-import-progress span{position:absolute;inset:0 auto 0 0;width:8%;border-radius:999px;background:linear-gradient(90deg,var(--color-brand-blue),var(--color-brand-green));transition:width .5s ease}
.home-import-progress strong{position:relative;z-index:1;display:grid;place-items:center;height:100%;padding:0 18px;color:var(--color-text);font-size:13px;text-align:center;text-shadow:0 1px 8px rgba(0,0,0,.6)}
.home-import-loading small{color:var(--color-text-muted);font-size:12px;text-transform:uppercase}
.home-import-detail{min-height:18px;margin:-4px 0 0;color:rgba(231,231,232,.7);font-size:12px;text-align:center}
.home-import-steps{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:6px;width:100%;margin:2px 0 0;padding:0;list-style:none}
.home-import-steps li{display:grid;justify-items:center;gap:6px;min-width:0;color:rgba(231,231,232,.48);font-size:10px;font-weight:800;text-transform:uppercase}
.home-import-steps li span{display:block;width:10px;height:10px;border:1px solid rgba(231,231,232,.18);border-radius:999px;background:rgba(231,231,232,.08);box-shadow:inset 0 1px rgba(255,255,255,.12)}
.home-import-steps li[data-state=done]{color:rgba(175,207,42,.86)}.home-import-steps li[data-state=done] span{border-color:rgba(175,207,42,.62);background:var(--color-brand-green);box-shadow:0 0 14px rgba(175,207,42,.3)}
.home-import-steps li[data-state=active]{color:var(--color-text)}.home-import-steps li[data-state=active] span{border-color:rgba(17,162,207,.72);background:var(--color-brand-blue);box-shadow:0 0 16px rgba(17,162,207,.38);animation:home-import-step-pulse 1.2s ease-in-out infinite}
.home-import-loading[data-state=failed] .home-import-progress span{background:linear-gradient(90deg,#7f1d1d,var(--color-danger))}
.home-import-loading[data-state=failed] .home-import-steps li[data-state=active] span{border-color:rgba(255,111,111,.68);background:var(--color-danger);box-shadow:0 0 16px rgba(255,111,111,.32);animation:none}
.home-import-loading button{min-height:38px;padding:8px 14px;border-color:var(--glass-border);background:var(--color-brand-white);color:var(--color-brand-black)}
body[data-importing=true] .project-home{opacity:0;pointer-events:none;transition:opacity .24s ease}
@keyframes home-import-step-pulse{0%,100%{transform:scale(1);opacity:.72}50%{transform:scale(1.2);opacity:1}}
@media(max-width:680px){.home-import-steps{grid-template-columns:repeat(4,minmax(0,1fr))}.home-import-steps li{font-size:9px}}
@media(max-width:900px){.new-project-config-grid{grid-template-columns:1fr}.new-project-config-block{width:100%}.source-panel,.source-panel[data-source-panel=youtube]{grid-template-columns:minmax(0,1fr) 52px}.source-panel[data-source-panel=youtube]{grid-template-columns:minmax(0,1fr)}.cuts-control-grid{grid-template-columns:1fr}.cut-count-field select{min-height:54px}.duration-tile-grid{grid-template-columns:repeat(2,minmax(54px,1fr))}.duration-size-toggle span{min-width:0}}
"""


def project_home_js(workspace: Path) -> str:
    script = r"""
const workspacePath = __WORKSPACE_PATH__;
const homeImport = document.querySelector("[data-home-import]");
const projectLibrary = document.querySelector("[data-project-library]");
const projectList = document.querySelector("[data-project-list]");
function escapeHtml(value){
  return String(value || "").replace(/[&<>"']/g, char => {
    if (char === "&") return "&amp;";
    if (char === "<") return "&lt;";
    if (char === ">") return "&gt;";
    if (char === '"') return "&quot;";
    return "&#39;";
  });
}
function escapeAttr(value){ return escapeHtml(value); }
function projectPayload(form){
  const data = new FormData(form);
  const sourceMode = String(data.get("source_mode") || form.dataset.sourceMode || "local");
  return {
    source_path: sourceMode === "local" ? String(data.get("source_path") || "").trim() : "",
    source_url: sourceMode === "youtube" ? String(data.get("source_url") || "").trim() : "",
    output_path: String(data.get("output_path") || "").trim(),
    preview_count: Number(data.get("preview_count") || 10),
    language: String(data.get("language") || "pt"),
    preset: String(data.get("preset") || "tiktok"),
    duration_profile: String(data.get("duration_profile") || "medium"),
    context_prompt: String(data.get("context_prompt") || ""),
    render_previews: true
  };
}
function setStatus(text){
  const status = document.querySelector("[data-import-status]");
  if (status) status.textContent = text;
}
function setResult(html){
  const result = document.querySelector("[data-import-result]");
  if (result) result.innerHTML = html;
}
async function postJson(url, payload){
  const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload || {}) });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || !data.ok) throw new Error(data.error || "Local operation failed.");
  return data;
}
let importOpenaiState = { provider: "local", keyConfigured: true };
function importNeedsOpenaiKey(){
  return importOpenaiState.provider === "openai" && !importOpenaiState.keyConfigured;
}
const importStageOrder = ["prepare", "media", "audio", "analysis", "suggestions", "previews", "publish", "editor"];
function setImportLoading(message, label = "Import", percent = 8, progress = {}){
  const loading = document.querySelector("[data-import-loading]");
  if (!loading) return;
  const value = Math.max(0, Math.min(100, Number(percent || 0)));
  const stage = String(progress.stage || "prepare");
  loading.hidden = false;
  loading.dataset.state = "running";
  document.body.dataset.importing = "true";
  loading.querySelector("[data-import-loading-message]").textContent = message || "Processing...";
  loading.querySelector("[data-import-loading-label]").textContent = label || "Import";
  loading.querySelector("[data-import-loading-detail]").textContent = importProgressDetail(progress);
  loading.querySelector("[data-import-loading-bar]").style.width = `${value}%`;
  loading.querySelector("[role=progressbar]").setAttribute("aria-valuenow", String(value));
  loading.querySelector("[data-import-loading-back]").hidden = true;
  updateImportSteps(stage);
}
function importProgressDetail(progress){
  if (progress.detail) return String(progress.detail);
  const step = Number(progress.step || 0);
  const steps = Number(progress.steps || 0);
  if (step && steps) return `${step} of ${steps}`;
  if (progress.stage === "media") return "Preparing the video source.";
  if (progress.stage === "audio") return "Converting and transcribing audio.";
  if (progress.stage === "analysis") return "Finding strong hooks and complete thoughts.";
  if (progress.stage === "previews") return "Generating samples for editor review.";
  return "Follow the steps while the project is created.";
}
function updateImportSteps(stage){
  const currentIndex = importStageOrder.includes(stage) ? importStageOrder.indexOf(stage) : 0;
  document.querySelectorAll("[data-import-step]").forEach(item => {
    const index = importStageOrder.indexOf(item.dataset.importStep || "");
    item.dataset.state = index < currentIndex ? "done" : index === currentIndex ? "active" : "";
  });
}
function updateImportLoading(job){
  const progress = job.progress || {};
  setImportLoading(progress.message || job.message || "Processing import...", progress.label || job.status || "Import", progress.percent || 35, progress);
}
function failImportLoading(message){
  const loading = document.querySelector("[data-import-loading]");
  if (!loading) return;
  loading.hidden = false;
  loading.dataset.state = "failed";
  loading.querySelector("[data-import-loading-message]").textContent = message || "Could not import this project.";
  loading.querySelector("[data-import-loading-label]").textContent = "Import stopped";
  loading.querySelector("[data-import-loading-detail]").textContent = "Check the message below and try again.";
  loading.querySelector("[data-import-loading-bar]").style.width = "100%";
  loading.querySelector("[role=progressbar]").setAttribute("aria-valuenow", "100");
  loading.querySelector("[data-import-loading-back]").hidden = false;
}
function hideImportLoading(){
  const loading = document.querySelector("[data-import-loading]");
  if (loading) loading.hidden = true;
  delete document.body.dataset.importing;
}
const activeImportJobStorageKey = "cuted-active-import-job";
let activeImportPollJobId = "";
function importJobStorage(){
  try {
    return window.sessionStorage;
  } catch (error) {
    console.warn("Could not access sessionStorage for import recovery.", error);
    return null;
  }
}
function saveActiveImportJob(job){
  if (!job?.id) return;
  const storage = importJobStorage();
  if (!storage) return;
  storage.setItem(activeImportJobStorageKey, JSON.stringify({
    id: job.id,
    output_url: job.output_url || "",
    updated_at: Date.now()
  }));
}
function storedActiveImportJob(){
  const storage = importJobStorage();
  if (!storage) return null;
  try {
    const data = JSON.parse(storage.getItem(activeImportJobStorageKey) || "null");
    return data && data.id ? data : null;
  } catch (error) {
    storage.removeItem(activeImportJobStorageKey);
    return null;
  }
}
function clearActiveImportJob(jobId){
  const storage = importJobStorage();
  if (!storage) return;
  const active = storedActiveImportJob();
  if (!jobId || !active || active.id === jobId) storage.removeItem(activeImportJobStorageKey);
}
async function completeImportJob(job, button, options = {}){
  activeImportPollJobId = "";
  clearActiveImportJob(job.id || options.jobId);
  if (button) button.disabled = false;
  setImportLoading("Project ready. Opening editor...", "Done", 100, { stage: "editor", detail: "Updating recent projects." });
  if (job.output_url) setResult(`<a href="${escapeAttr(job.output_url)}">Open imported project</a>`);
  await refreshProjects().catch(error => console.warn("Could not refresh projects after import.", error));
  if (job.output_url && options.open !== false) {
    window.setTimeout(() => window.location.assign(job.output_url), 450);
  }
}
async function importOutputIsReady(outputUrl){
  if (!outputUrl) return false;
  try {
    const response = await fetch(outputUrl, { cache: "no-store" });
    return response.ok;
  } catch (error) {
    return false;
  }
}
function recoverActiveImportJob(options = {}){
  const active = storedActiveImportJob();
  if (!active?.id || activeImportPollJobId === active.id) return;
  setImportLoading("Resuming import...", "Tracking", 35, { stage: "analysis", detail: "Reconnecting to the active job." });
  pollImport(active.id, document.querySelector("[data-import-form] button[type=submit]"), options);
}
function setupImportRecovery(){
  refreshProjects().catch(error => console.warn("Could not refresh projects on Home load.", error));
  recoverActiveImportJob();
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState !== "visible") return;
    refreshProjects().catch(error => console.warn("Could not refresh projects when the tab returned.", error));
    recoverActiveImportJob();
  });
  window.addEventListener("focus", () => {
    refreshProjects().catch(error => console.warn("Could not refresh projects on focus.", error));
    recoverActiveImportJob();
  });
}
async function startImport(form){
  const button = form.querySelector("button[type=submit]");
  const payload = projectPayload(form);
  if (!payload.source_path && !payload.source_url) {
    setStatus(form.dataset.sourceMode === "youtube" ? "Paste a YouTube link." : "Select a local video.");
    form.querySelector(form.dataset.sourceMode === "youtube" ? "[name=source_url]" : "[name=source_path]")?.focus();
    return;
  }
  if (importNeedsOpenaiKey()) {
    setStatus("Add your OpenAI key in Settings to import with AI.");
    openSettingsPanel();
    return;
  }
  setResult("");
  setImportLoading("Preparing project...", "Preparing", 8, { stage: "prepare", detail: "Organizing local files." });
  setStatus("Creating import job...");
  if (button) button.disabled = true;
  try {
    const data = await postJson("/api/import-jobs", payload);
    setStatus(data.job?.message || "Import started.");
    updateImportLoading(data.job || {});
    saveActiveImportJob(data.job || {});
    pollImport(data.job.id, button);
  } catch (error) {
    if (button) button.disabled = false;
    failImportLoading(error.message || "Could not start the import.");
    setStatus("Could not start the import.");
    setResult(`<code>${escapeHtml(error.message || String(error))}</code>`);
  }
}
async function pollImport(jobId, button, options = {}){
  if (!jobId) return;
  activeImportPollJobId = jobId;
  try {
    const response = await fetch(`/api/import-jobs/${encodeURIComponent(jobId)}`);
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || "Job not found.");
    const job = data.job || {};
    setStatus(`${job.message || "Processing..."} (${job.status || "running"})`);
    updateImportLoading(job);
    if (job.status === "ready") {
      await completeImportJob(job, button, { jobId, open: options.open !== false });
      return;
    }
    if (job.status === "failed" || job.status === "cancelled") {
      activeImportPollJobId = "";
      clearActiveImportJob(jobId);
      if (button) button.disabled = false;
      failImportLoading(job.stderr || job.message || "Import ended.");
      setResult(`<code>${escapeHtml(job.stderr || job.message || "Import ended.")}</code>`);
      return;
    }
    window.setTimeout(() => pollImport(jobId, button), 1200);
  } catch (error) {
    activeImportPollJobId = "";
    const active = storedActiveImportJob();
    if (active?.id === jobId && await importOutputIsReady(active.output_url)) {
      await completeImportJob({ id: jobId, output_url: active.output_url }, button, { jobId, open: options.open !== false });
      return;
    }
    if (button) button.disabled = false;
    setImportLoading("Reconnecting import...", "Tracking", 35, { stage: "analysis", detail: "The tab lost the job stream; retrying." });
    setStatus("Could not track the import. I will retry when the tab comes back.");
    setResult(`<code>${escapeHtml(error.message || String(error))}</code>`);
    refreshProjects().catch(() => {});
  }
}
let contextAudio = { recorder: null, stream: null, chunks: [], startedAt: 0, audioContext: null, analyser: null, levelTimer: 0, maxLevel: 0, deviceLabel: "" };
function setContextAudioState(form, state, message){
  const box = form.querySelector("[data-ai-context-box]");
  const status = form.querySelector("[data-context-audio-status]");
  const button = form.querySelector("[data-context-audio]");
  if (box) box.dataset.audioState = state || "ready";
  if (status) status.textContent = message || "";
  if (button) button.disabled = state === "transcribing";
  if (button) button.title = state === "recording" ? "Stop recording" : "Record voice briefing";
}
function contextAudioMimeType(){
  if (!window.MediaRecorder) return "";
  const types = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"];
  return types.find(type => MediaRecorder.isTypeSupported(type)) || "";
}
function selectedContextAudioDeviceId(form){
  return String(form.querySelector("[data-context-audio-device]")?.value || "");
}
function contextAudioConstraints(form){
  const deviceId = selectedContextAudioDeviceId(form);
  const audio = { echoCancellation: false, noiseSuppression: false, autoGainControl: true };
  if (deviceId) audio.deviceId = { exact: deviceId };
  return { audio };
}
async function refreshContextAudioDevices(form){
  const select = form.querySelector("[data-context-audio-device]");
  if (!select || !navigator.mediaDevices?.enumerateDevices) return;
  const current = select.value;
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const audioInputs = devices.filter(device => device.kind === "audioinput");
    select.innerHTML = '<option value="">Default microphone</option>';
    audioInputs.forEach((device, index) => {
      const option = document.createElement("option");
      option.value = device.deviceId;
      option.textContent = device.label || `Microphone ${index + 1}`;
      select.appendChild(option);
    });
    if (current && Array.from(select.options).some(option => option.value === current)) select.value = current;
  } catch (error) {
    console.warn("Could not list microphones:", error);
  }
}
async function toggleContextAudio(form){
  if (contextAudio.recorder?.state === "recording") {
    contextAudio.recorder.requestData?.();
    contextAudio.recorder.stop();
    return;
  }
  await startContextAudio(form);
}
async function startContextAudio(form){
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    throw new Error("Microphone recording is not available in this browser.");
  }
  const stream = await navigator.mediaDevices.getUserMedia(contextAudioConstraints(form));
  await refreshContextAudioDevices(form);
  const mimeType = contextAudioMimeType();
  const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
  const track = stream.getAudioTracks()[0];
  contextAudio = { recorder, stream, chunks: [], startedAt: Date.now(), audioContext: null, analyser: null, levelTimer: 0, maxLevel: 0, deviceLabel: track?.label || "microphone" };
  const activeDeviceId = track?.getSettings?.().deviceId || "";
  const deviceSelect = form.querySelector("[data-context-audio-device]");
  if (activeDeviceId && deviceSelect && !deviceSelect.value) deviceSelect.value = activeDeviceId;
  recorder.addEventListener("dataavailable", event => {
    if (event.data?.size) contextAudio.chunks.push(event.data);
  });
  recorder.addEventListener("stop", () => finishContextAudio(form, mimeType));
  recorder.start(250);
  startContextAudioLevelMonitor(form, stream);
  setContextAudioState(form, "recording", `Recording from ${contextAudio.deviceLabel} - input 0%... click the mic again to stop.`);
}
async function finishContextAudio(form, mimeType){
  const maxLevel = contextAudio.maxLevel || 0;
  const deviceLabel = contextAudio.deviceLabel || "microphone";
  stopContextAudioLevelMonitor(form);
  contextAudio.stream?.getTracks().forEach(track => track.stop());
  const seconds = Math.max(0, (Date.now() - contextAudio.startedAt) / 1000);
  const blob = new Blob(contextAudio.chunks, { type: mimeType || "audio/webm" });
  contextAudio = { recorder: null, stream: null, chunks: [], startedAt: 0, audioContext: null, analyser: null, levelTimer: 0, maxLevel: 0, deviceLabel: "" };
  if (!blob.size || seconds < .35) {
    setContextAudioState(form, "ready", "No briefing was recorded.");
    return;
  }
  if (seconds >= 2 && maxLevel < .006) {
    setContextAudioState(form, "error", `Microphone input stayed very low from ${deviceLabel}. Pick another microphone or check Windows input settings.`);
    return;
  }
  await transcribeContextAudio(form, blob, seconds, maxLevel);
}
function startContextAudioLevelMonitor(form, stream){
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) return;
  const meter = form.querySelector("[data-context-audio-level]");
  try {
    const audioContext = new AudioContextClass();
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 1024;
    const source = audioContext.createMediaStreamSource(stream);
    const data = new Uint8Array(analyser.fftSize);
    source.connect(analyser);
    contextAudio.audioContext = audioContext;
    contextAudio.analyser = analyser;
    const tick = () => {
      analyser.getByteTimeDomainData(data);
      const level = contextAudioInputLevel(data);
      contextAudio.maxLevel = Math.max(contextAudio.maxLevel || 0, level);
      const percent = contextAudioLevelPercent(level);
      if (meter) meter.style.width = `${percent}%`;
      setContextAudioState(form, "recording", `Recording from ${contextAudio.deviceLabel || "microphone"} - input ${percent}%... click the mic again to stop.`);
    };
    contextAudio.levelTimer = window.setInterval(tick, 250);
    tick();
  } catch (error) {
    console.warn("Could not monitor microphone level:", error);
  }
}
function stopContextAudioLevelMonitor(form){
  if (contextAudio.levelTimer) window.clearInterval(contextAudio.levelTimer);
  contextAudio.audioContext?.close?.().catch?.(() => {});
  const meter = form.querySelector("[data-context-audio-level]");
  if (meter) meter.style.width = "0%";
}
function contextAudioInputLevel(data){
  let sum = 0;
  for (const value of data) {
    const centered = (value - 128) / 128;
    sum += centered * centered;
  }
  return Math.sqrt(sum / Math.max(1, data.length));
}
function contextAudioLevelPercent(level){
  return Math.max(0, Math.min(100, Math.round(Number(level || 0) * 420)));
}
async function transcribeContextAudio(form, blob, seconds, maxLevel){
  const sizeKb = Math.max(1, Math.round(blob.size / 1024));
  setContextAudioState(form, "transcribing", `Transcribing ${seconds.toFixed(1)}s / ${sizeKb} KB, peak input ${contextAudioLevelPercent(maxLevel)}%...`);
  try {
    const language = "auto";
    const response = await fetch(`/api/ai-context/audio?language=${encodeURIComponent(language)}`, {
      method: "POST",
      headers: { "Content-Type": blob.type || "audio/webm" },
      body: blob
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || !data.ok) throw new Error(data.error || "Transcription failed.");
    const transcript = String(data.context?.text || "").trim();
    if (isWeakContextTranscript(transcript, seconds)) {
      throw new Error(weakContextTranscriptMessage(transcript, seconds, sizeKb, maxLevel));
    }
    applyContextTranscript(form, transcript);
    setContextAudioState(form, "applied", `Voice briefing applied (${seconds.toFixed(1)}s / ${sizeKb} KB). Review it before importing.`);
  } catch (error) {
    setContextAudioState(form, "error", error.message || "Could not transcribe the briefing.");
  }
}
function isWeakContextTranscript(text, seconds){
  const clean = String(text || "").trim().toLowerCase();
  if (!clean) return true;
  if (seconds < 1.2) return clean.length <= 3;
  return clean.length <= 4 || ["you", "you.", "yeah", "ok", "okay"].includes(clean);
}
function weakContextTranscriptMessage(text, seconds, sizeKb, maxLevel){
  const detected = String(text || "").trim() || "no speech";
  return `Only "${detected}" was detected from ${seconds.toFixed(1)}s / ${sizeKb} KB, peak input ${contextAudioLevelPercent(maxLevel)}%. Pick another microphone or record closer to the input.`;
}
function applyContextTranscript(form, text){
  const textarea = form.querySelector("[name=context_prompt]");
  const transcript = String(text || "").trim();
  if (!textarea || !transcript) return;
  const current = textarea.value.trim();
  textarea.value = current ? `${current}\n\n${transcript}` : transcript;
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
}
function bindImportForm(){
  const form = document.querySelector("[data-import-form]");
  if (!form) return;
  bindSourceMode(form);
  form.addEventListener("submit", event => {
    event.preventDefault();
    startImport(form);
  });
  form.querySelector("[data-select-video-file]")?.addEventListener("click", () => selectPath("/api/select-video-file", "[name=source_path]", "Local video selected."));
  form.querySelector("[data-context-audio]")?.addEventListener("click", () => {
    toggleContextAudio(form).catch(error => setContextAudioState(form, "error", error.message || "Microphone unavailable."));
  });
  document.querySelector("[data-import-loading-back]")?.addEventListener("click", () => hideImportLoading());
}
function bindSourceMode(form){
  const inputs = form.querySelectorAll("[name=source_mode]");
  const sync = () => {
    const mode = String(new FormData(form).get("source_mode") || "local");
    form.dataset.sourceMode = mode;
    form.querySelectorAll("[data-source-panel]").forEach(panel => {
      panel.hidden = panel.dataset.sourcePanel !== mode;
    });
  };
  inputs.forEach(input => input.addEventListener("change", sync));
  sync();
}
async function selectPath(url, selector, message){
  setStatus("Opening local picker...");
  try {
    const data = await postJson(url);
    const input = document.querySelector(selector);
    if (input) input.value = data.path || input.value;
    setStatus(message);
  } catch (error) {
    setStatus(error.message || "Local picker unavailable.");
  }
}
let settingsLastFocus = null;
function setupHomeSettingsPanel(){
  const modal = document.querySelector("[data-settings-modal]");
  const form = document.querySelector("[data-settings-form]");
  const open = document.getElementById("open-settings");
  const close = document.querySelector("[data-settings-close]");
  const test = document.querySelector("[data-settings-test]");
  if (!modal || !form || !open) return;
  open.addEventListener("click", () => openSettingsPanel());
  close?.addEventListener("click", () => closeSettingsPanel());
  modal.addEventListener("click", event => { if (event.target === modal) closeSettingsPanel(); });
  document.addEventListener("keydown", event => {
    if (modal.hidden) return;
    if (event.key === "Escape") closeSettingsPanel();
    if (event.key === "Tab") trapSettingsFocus(event);
  });
  form.addEventListener("submit", event => {
    event.preventDefault();
    saveSettingsForm(form);
  });
  test?.addEventListener("click", () => testSettingsConnection(form));
  loadOpenaiSettings();
}
function openSettingsPanel(){
  const modal = document.querySelector("[data-settings-modal]");
  if (!modal) return;
  settingsLastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  modal.hidden = false;
  modal.classList.remove("is-closing");
  requestAnimationFrame(() => modal.classList.add("is-open"));
  loadOpenaiSettings();
  modal.querySelector("[data-settings-panel]")?.focus();
}
function closeSettingsPanel(){
  const modal = document.querySelector("[data-settings-modal]");
  if (!modal || modal.hidden) return;
  modal.classList.remove("is-open");
  modal.classList.add("is-closing");
  window.setTimeout(() => {
    modal.hidden = true;
    modal.classList.remove("is-closing");
    settingsLastFocus?.focus?.();
    settingsLastFocus = null;
  }, 190);
}
function settingsFocusableElements(modal){
  return Array.from(modal.querySelectorAll("button,input,select,textarea,a[href],[tabindex]:not([tabindex='-1'])"))
    .filter(element => !element.disabled && !element.hidden && element.offsetParent !== null);
}
function trapSettingsFocus(event){
  const modal = document.querySelector("[data-settings-modal]");
  if (!modal || modal.hidden) return;
  const focusable = settingsFocusableElements(modal);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
async function loadOpenaiSettings(){
  const form = document.querySelector("[data-settings-form]");
  const status = document.querySelector("[data-settings-status]");
  if (!form) return;
  try {
    const response = await fetch("/api/settings/openai");
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Could not load settings.");
    applySettingsPayload(form, payload.settings || {}, payload.usage || {});
  } catch (error) {
    if (status) status.textContent = error.message || "Could not load settings.";
  }
}
function applySettingsPayload(form, settings, usage){
  form.elements.ai_provider.value = settings.ai_provider || "local";
  form.elements.openai_model.value = settings.openai_model || "gpt-5-mini";
  form.elements.transcribe_model.value = settings.transcribe_model || "whisper-1";
  form.elements.api_key.value = "";
  importOpenaiState = {
    provider: String(settings.ai_provider || "local"),
    keyConfigured: Boolean(settings.key_configured)
  };
  const status = document.querySelector("[data-settings-status]");
  if (status) {
    const key = settings.key_configured ? "Token configured" : "Token not configured";
    status.textContent = `${key} - ${settings.openai_model || "gpt-5-mini"} / ${settings.transcribe_model || "whisper-1"}`;
  }
  renderSettingsUsage(usage);
  refreshImportKeyBannerFromState();
}
function settingsPayloadFromForm(form){
  const data = new FormData(form);
  const payload = {
    ai_provider: String(data.get("ai_provider") || "local"),
    openai_model: String(data.get("openai_model") || "gpt-5-mini"),
    transcribe_model: String(data.get("transcribe_model") || "whisper-1")
  };
  const apiKey = String(data.get("api_key") || "").trim();
  if (apiKey) payload.api_key = apiKey;
  return payload;
}
async function saveSettingsForm(form){
  const status = document.querySelector("[data-settings-status]");
  if (status) status.textContent = "Saving...";
  try {
    const response = await fetch("/api/settings/openai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settingsPayloadFromForm(form))
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Could not save settings.");
    applySettingsPayload(form, payload.settings || {}, payload.usage || {});
    if (status) status.textContent = `Saved. ${status.textContent}`;
  } catch (error) {
    if (status) status.textContent = error.message || "Could not save.";
  }
}
async function testSettingsConnection(form){
  const status = document.querySelector("[data-settings-status]");
  const button = document.querySelector("[data-settings-test]");
  if (status) status.textContent = "Testing connection...";
  if (button) button.disabled = true;
  try {
    const response = await fetch("/api/settings/openai/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settingsPayloadFromForm(form))
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || "Could not test connection.");
    if (status) status.textContent = data.message || "OpenAI connection validated.";
  } catch (error) {
    if (status) status.textContent = error.message || "Could not validate the connection.";
  } finally {
    if (button) button.disabled = false;
  }
}
function renderSettingsUsage(usage){
  const target = document.querySelector("[data-settings-usage]");
  if (!target) return;
  const total = Number(usage?.estimated_total_usd || 0);
  const count = Number(usage?.event_count || 0);
  const last = usage?.last_event || {};
  const lastText = last.operation
    ? `Last: ${escapeHtml(last.operation)} on ${escapeHtml(last.model || "-")} - ${formatUsd(last.estimated_usd || 0)}`
    : "Last: no record.";
  target.innerHTML = `<strong>Estimated local total: ${formatUsd(total)}</strong><span>${count} event(s) recorded.</span><span>${lastText}</span>`;
}
function formatUsd(value){
  return `$${Number(value || 0).toFixed(4)}`;
}
async function refreshImportKeyBanner(){
  const banner = document.querySelector("[data-import-key-banner]");
  if (!banner) return;
  try {
    const response = await fetch("/api/settings/openai");
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Could not load settings.");
    const settings = payload.settings || {};
    importOpenaiState = {
      provider: String(settings.ai_provider || "local"),
      keyConfigured: Boolean(settings.key_configured)
    };
  } catch (error) {
    console.warn("Could not check the OpenAI key:", error);
    importOpenaiState = { provider: "local", keyConfigured: true };
  }
  refreshImportKeyBannerFromState();
}
function refreshImportKeyBannerFromState(){
  const banner = document.querySelector("[data-import-key-banner]");
  if (banner) banner.hidden = !importNeedsOpenaiKey();
}
function setupImportKeyBanner(){
  const banner = document.querySelector("[data-import-key-banner]");
  if (!banner) return;
  banner.querySelector("[data-import-key-open]")?.addEventListener("click", () => openSettingsPanel());
  refreshImportKeyBanner();
}
function projectCard(project){
  const open = project.url ? `<a href="${escapeAttr(project.url)}">Open</a>` : `<button type="button" disabled>Open</button>`;
  const size = sizeLabel(project.size_bytes || 0);
  return `<article class="project-row" data-project-id="${escapeAttr(project.id)}" data-project-title="${escapeAttr(project.title || "Untitled project")}" data-project-path="${escapeAttr(project.path || "")}" data-project-size="${escapeAttr(size)}">
    <div class="project-name-cell"><strong>${escapeHtml(project.title || "Untitled project")}</strong><p>${escapeHtml(project.source_label || "")}</p><small>${escapeHtml(project.path || "")}</small></div>
    <dl class="project-meta-cell"><div><dt>Clips</dt><dd>${Number(project.clip_count || 0)}</dd></div><div><dt>Renders</dt><dd>${Number(project.render_count || 0)}</dd></div><div><dt>Size</dt><dd>${escapeHtml(size)}</dd></div></dl>
    <time class="project-updated-cell">${escapeHtml(project.last_opened_at || "")}</time>
    <div class="project-row-actions">${open}<button type="button" data-forget-project>Remove recent</button><button type="button" data-delete-project>Delete project</button></div>
  </article>`;
}
function emptyProjectState(){
  return `<article class="project-empty-state" data-project-empty-state><strong>No recent projects</strong><p>Create a new project to start.</p></article>`;
}
function sizeLabel(bytes){
  let value = Number(bytes || 0);
  for (const unit of ["B", "KB", "MB", "GB"]) {
    if (value < 1024 || unit === "GB") return unit === "B" ? `${Math.round(value)} B` : `${value.toFixed(1)} ${unit}`;
    value /= 1024;
  }
  return "0 MB";
}
async function refreshProjects(){
  if (!projectList) return;
  const response = await fetch("/api/projects");
  const data = await response.json();
  if (!response.ok || !data.ok) throw new Error(data.error || "Could not load projects.");
  const projects = Array.isArray(data.projects) ? data.projects : [];
  const content = projects.length ? projects.map(projectCard).join("") : emptyProjectState();
  projectList.innerHTML = `<div class="project-table-head" aria-hidden="true"><span>Project</span><span>Status</span><span>Updated</span><span>Actions</span></div>${content}`;
}
async function deleteProject(card, deleteFiles){
  const projectId = card?.dataset.projectId || "";
  const title = card?.dataset.projectTitle || "Untitled project";
  const path = card?.dataset.projectPath || "";
  const size = card?.dataset.projectSize || "unknown size";
  const message = projectDeleteMessage(title, path, size, deleteFiles);
  if (!projectId || !window.confirm(message)) return;
  const result = await postJson(`/api/projects/${encodeURIComponent(projectId)}/delete`, { delete_files: deleteFiles });
  await refreshProjects();
  if (deleteFiles) {
    const method = result.delete_method === "recycle-bin" ? "Project moved to the Recycle Bin." : "Project deleted locally.";
    setStatus(method);
  } else {
    setStatus("Project removed from recents. Files remain on disk.");
  }
}
function projectDeleteMessage(title, path, size, deleteFiles){
  if (!deleteFiles) {
    return `Remove "${title}" from recents?\n\nFiles remain on disk:\n${path}`;
  }
  return [
    `Delete project "${title}"?`,
    "",
    `Approximate size: ${size}`,
    `Folder: ${path}`,
    "",
    "The project folder will be moved to the Recycle Bin when available.",
    "If the Recycle Bin is unavailable, local files will be removed.",
    "Final renders outside the project folder are not deleted by this action."
  ].join("\n");
}
document.querySelectorAll("[data-new-project]").forEach(button => {
  button.addEventListener("click", () => {
    if (projectLibrary) projectLibrary.hidden = true;
    if (homeImport) homeImport.hidden = false;
    document.querySelector("[data-import-form]")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});
document.querySelector("[data-show-projects]")?.addEventListener("click", () => {
  if (homeImport) homeImport.hidden = true;
  if (projectLibrary) projectLibrary.hidden = false;
});
document.querySelectorAll("[data-open-workspace]").forEach(button => {
  button.addEventListener("click", () => postJson("/api/open-folder", { path: workspacePath }).catch(error => setStatus(error.message || "Could not open the folder.")));
});
document.querySelector("[data-refresh-projects]")?.addEventListener("click", () => refreshProjects().catch(error => setStatus(error.message || "Could not refresh projects.")));
projectList?.addEventListener("click", event => {
  const card = event.target.closest("[data-project-id]");
  if (event.target.closest("[data-forget-project]")) deleteProject(card, false);
  if (event.target.closest("[data-delete-project]")) deleteProject(card, true);
});
setupHomeSettingsPanel();
setupImportKeyBanner();
bindImportForm();
setupImportRecovery();
"""
    return script.replace("__WORKSPACE_PATH__", json.dumps(str(workspace)))


def css() -> str:
    return base_css() + liquid_ui_css()


def base_css() -> str:
    return """
*{box-sizing:border-box}:root{--color-brand-blue:#11A2CF;--color-brand-green:#AFCF2A;--color-brand-white:#E7E7E8;--color-brand-black:#050505;--color-metal-gray:#68686A;--color-surface:#0D0D0D;--color-surface-raised:#111;--color-surface-muted:#151515;--color-surface-control:#191919;--color-border:#272727;--color-border-strong:#333;--color-text:#f4f4f4;--color-text-soft:#ddd;--color-text-muted:#9a9a9a;--color-focus:#11A2CF;--color-danger:#ffb3b3;--shadow-panel:0 14px 42px rgba(0,0,0,.5)}body{margin:0;background:var(--color-brand-black);color:var(--color-text);font:14px/1.45 Arial,sans-serif}
header{position:sticky;top:0;z-index:5;display:grid;grid-template-columns:minmax(90px,1fr) auto minmax(90px,1fr);gap:16px;align-items:center;padding:10px 22px 12px;background:var(--color-brand-black);border-bottom:1px solid var(--color-border)}.header-actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}.icon-button{display:inline-grid;place-items:center;width:38px;min-width:38px;padding:0}.icon-button svg{display:block;width:17px;height:17px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}.brand-lockup{display:grid;justify-items:center;gap:8px;min-width:0}.brand-logo{display:block;width:min(540px,54vw);height:78px;object-fit:contain;object-position:center;border:0;border-radius:0;filter:none}.brand-lockup p{margin:2px 0 0;color:var(--color-text-muted);font-size:11px;line-height:1.1;text-align:center;max-width:min(520px,56vw);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.tabs{position:sticky;top:119px;z-index:4;display:flex;gap:8px;padding:10px 22px;background:#060606;border-bottom:1px solid #1f1f1f}.tabs button{background:var(--color-surface-control);color:var(--color-text-soft);border:1px solid #303030;padding:8px 12px}.tabs button.active{background:var(--color-brand-white);color:var(--color-brand-black);border-color:var(--color-brand-white)}
main{display:grid;gap:12px;max-width:1440px;margin:0 auto;padding:16px 18px 28px}.card{border:1px solid var(--color-border);border-radius:8px;background:var(--color-surface);overflow:hidden}.card[open]{border-color:var(--color-metal-gray);background:var(--color-surface-raised)}.card.liked{border-color:var(--color-brand-green)}.card.discarded{opacity:.46}.clip-summary{display:grid;grid-template-columns:auto minmax(0,1fr) minmax(180px,.55fr) auto;gap:12px;align-items:center;min-height:62px;padding:12px 14px;cursor:pointer;list-style:none}.clip-summary::-webkit-details-marker{display:none}.clip-rank{color:var(--color-metal-gray);font-weight:700}.clip-title{display:grid;gap:2px;min-width:0}.clip-title strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:15px}.clip-title small{color:var(--color-text-muted)}.clip-row-timeline{position:relative;display:block;min-width:160px;height:30px;border:1px solid rgba(17,162,207,.22);border-radius:4px;background:linear-gradient(180deg,rgba(17,162,207,.08),rgba(255,255,255,.02)),rgba(5,5,5,.28);overflow:hidden}.clip-row-timeline-track{position:absolute;left:8px;right:8px;top:50%;height:3px;border-radius:999px;background:rgba(231,231,232,.12);transform:translateY(-50%)}.clip-row-timeline-window{position:absolute;top:7px;bottom:7px;border:1px solid rgba(175,207,42,.5);border-radius:3px;background:rgba(175,207,42,.08)}.clip-row-timeline-marker{position:absolute;top:6px;width:7px;height:18px;border:1px solid rgba(17,162,207,.8);border-radius:3px;background:rgba(17,162,207,.22);transform:translateX(-50%)}.clip-row-timeline-playhead{position:absolute;top:5px;width:2px;height:20px;border-radius:999px;background:var(--color-brand-white);transform:translateX(-50%);opacity:.72}.clip-status{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}.clip-status span,.format-previews span{display:inline-flex;align-items:center;min-height:26px;padding:4px 8px;border-radius:999px;background:#242424;color:var(--color-text-soft);font-size:12px}
.app-notice{position:sticky;top:0;z-index:30;margin:0;padding:10px 14px;background:#2b1717;color:#ffd7d7;border-bottom:1px solid #6d2b2b;font-size:13px;text-align:center}.app-notice[hidden]{display:none}
.import-stage{display:none;max-width:1080px;margin:18px auto;padding:0 18px}.import-panel{display:grid;gap:14px;padding:18px;border:1px solid var(--color-border);border-radius:8px;background:var(--color-surface-raised)}.import-panel p{margin:4px 0 0;color:var(--color-text-muted)}.import-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.import-panel label{display:grid;gap:6px;color:var(--color-text-muted);font-size:12px}.import-panel input,.import-panel select,.import-panel textarea{width:100%;border:1px solid var(--color-border-strong);border-radius:6px;background:var(--color-brand-black);color:var(--color-text);padding:9px 10px;font:inherit}.import-panel textarea{resize:vertical;min-height:112px}.import-panel small{color:var(--color-text-muted);line-height:1.35}.import-path-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:6px}.import-key-banner{display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap;padding:10px 12px;border:1px solid rgba(17,162,207,.4);border-radius:8px;background:rgba(17,162,207,.1);color:var(--color-text)}.import-key-banner[hidden]{display:none}.import-key-banner button{min-height:34px}.import-path-row button{min-height:38px;background:var(--color-surface-control);color:var(--color-text-soft);border:1px solid var(--color-border-strong)}.duration-profile{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:0;padding:0;border:0}.duration-profile legend{grid-column:1/-1;color:var(--color-text-muted);font-size:12px}.duration-profile label{position:relative;display:grid!important}.duration-profile input{position:absolute;opacity:0;pointer-events:none}.duration-profile span{display:grid;gap:2px;min-height:54px;padding:10px 12px;border:1px solid var(--color-border-strong);border-radius:8px;background:var(--color-surface-muted);color:var(--color-text-soft)}.duration-profile input:checked+span{border-color:var(--color-brand-green);background:#182011;color:var(--color-text)}.duration-profile small{color:var(--color-text-muted)}.import-context{display:grid}.import-status{min-height:20px;color:var(--color-text-muted)}.import-result{display:flex;gap:8px;flex-wrap:wrap}.import-result a{display:inline-flex;align-items:center;justify-content:center;min-height:38px;padding:9px 12px;border-radius:6px;background:var(--color-brand-white);color:var(--color-brand-black);text-decoration:none}.import-result code{display:block;width:100%;padding:10px;border:1px solid #3a2525;border-radius:6px;background:#180d0d;color:#ffcccc;white-space:pre-wrap}
.layer-strip{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;width:100%;min-height:0}.layer-strip:empty{display:none}.bumper-sequence{display:flex;gap:6px;align-items:center;justify-content:center;flex-wrap:wrap;min-height:24px;color:var(--color-text-muted);font-size:12px}.bumper-sequence:empty{display:none}.bumper-sequence span{max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bumper-sequence b{color:var(--color-brand-green);font-weight:800}.layer-chip{display:inline-flex;gap:6px;align-items:center;max-width:100%;min-height:30px;padding:4px 5px 4px 9px;border:1px solid #303030;border-radius:999px;background:var(--color-surface-muted);color:var(--color-text-soft);font-size:12px}.layer-chip.is-selected{border-color:var(--color-focus);background:#182011;color:var(--color-text)}.layer-chip span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.layer-chip button{display:inline-grid;place-items:center;width:22px;height:22px;min-width:22px;padding:0;border:1px solid #3a3a3a;border-radius:999px;background:#242424;color:var(--color-text-soft);font-size:14px;line-height:1}
.cuted-control-surface-slot{display:none;position:relative;z-index:90;margin:-34px 14px 8px;justify-content:center}.cuted-control-surface-slot:empty{display:none}.card[open]>.cuted-control-surface-slot:not(:empty){display:flex}.cuted-control-surface-slot .cuted-control-bar{width:min(66%,930px);min-width:min(100%,820px);min-height:98px;padding:9px 16px;border-radius:18px}.cuted-control-surface-slot .cuted-render-zone{justify-content:flex-end;overflow:visible;min-height:74px}.cuted-control-surface-slot .cuted-tool-group{flex:0 0 408px;min-height:74px}.cuted-control-surface-slot .cuted-tile-button{flex:0 0 68px;width:68px;height:62px;font-size:30px}.cuted-control-surface-slot .cuted-insert-button span{font-size:20px}.cuted-control-surface-slot .cuted-format-trigger{flex:0 0 118px;width:118px;height:62px;grid-template-columns:auto 1fr auto;gap:8px;padding:7px 9px}.cuted-control-surface-slot .cuted-format-copy small{display:none}.cuted-control-surface-slot .cuted-format-copy strong{font-size:20px}.cuted-control-surface-slot .cuted-ratio-icon{border-width:2px;border-radius:3px}.cuted-control-surface-slot .cuted-ratio-vertical{width:16px;height:34px}.cuted-control-surface-slot .cuted-ratio-feed{width:22px;height:28px}.cuted-control-surface-slot .cuted-ratio-wide{width:32px;height:17px}.cuted-control-surface-slot .cuted-divider{flex:0 0 1px;height:48px;margin:0 8px}.cuted-control-surface-slot .cuted-audio-group{flex:0 0 58px;min-width:58px}.cuted-control-surface-slot .cuted-ready-region{flex:0 0 132px;width:132px;min-height:62px;margin-left:auto}.cuted-control-surface-slot .cuted-approve-button{width:60px;height:60px}.cuted-control-surface-slot .cuted-approve-button svg{width:36px;height:36px}.cuted-control-surface-slot .cuted-discard-button{width:46px;height:46px}.cuted-control-surface-slot .cuted-discard-button svg{width:25px;height:25px}
.editor-shell{display:grid;grid-template-columns:minmax(280px,520px) minmax(360px,1fr);gap:14px;padding:0 14px 14px}.editor-preview{display:grid;align-content:start;justify-items:center;gap:10px}.preview-frame{display:grid;gap:10px;width:100%;max-width:520px}.media{position:relative;container-type:inline-size;aspect-ratio:16/9;background:#000;max-height:72vh;overflow:hidden;border-radius:6px}.media video,.media img{width:100%;height:100%;object-fit:cover;display:block;background:#000;pointer-events:none}.placeholder{display:grid;place-items:center;height:100%;color:#777}.preview-bar{display:grid;grid-template-columns:1fr;gap:8px;justify-items:center;width:100%;padding:8px;border:1px solid #252525;border-radius:8px;background:#0a0a0a}.preview-controls,.preview-volume-group{display:flex;gap:6px;align-items:center}.preview-controls{justify-content:center;padding:4px;border:1px solid #202020;border-radius:999px;background:var(--color-surface-raised)}.preview-volume-group{padding-left:4px;border-left:1px solid #2d2d2d}.preview-icon,.preview-step{display:inline-grid;place-items:center;width:32px;height:32px;min-width:32px;padding:0;border:1px solid var(--color-border-strong);border-radius:999px;background:var(--color-surface-control);color:var(--color-text-soft)}.preview-play{background:var(--color-brand-white);color:var(--color-brand-black);border-color:var(--color-brand-white)}.preview-icon svg{width:16px;height:16px;display:block;stroke:currentColor}.preview-step{width:26px;height:26px;min-width:26px;font-weight:700}.preview-volume-group output{min-width:32px;color:#d8d8d8;font-size:12px;text-align:center}.card[data-preview-format=tiktok] .preview-frame,.card[data-preview-format=shorts] .preview-frame,.card[data-preview-format=instagram] .preview-frame{max-width:min(100%,calc(72vh * 9 / 16))}.card[data-preview-format=facebook] .preview-frame{max-width:min(100%,calc(72vh * 4 / 5))}.card[data-preview-format=youtube] .preview-frame{max-width:min(100%,520px)}.card[data-preview-format=tiktok] .media,.card[data-preview-format=shorts] .media,.card[data-preview-format=instagram] .media{aspect-ratio:9/16}.card[data-preview-format=facebook] .media{aspect-ratio:4/5}.card[data-preview-format=youtube] .media{aspect-ratio:16/9}.preview-strip{display:flex;gap:6px;flex-wrap:wrap;justify-content:center;overflow:visible;padding-bottom:1px}.preview-strip button{background:var(--color-surface-control);color:var(--color-text-soft);border:1px solid #303030;padding:8px 10px;min-height:34px;border-radius:999px;white-space:nowrap}.preview-strip button.active{background:var(--color-brand-white);color:var(--color-brand-black);border-color:var(--color-brand-white)}
.preview-camera-timeline--live{position:relative;display:block!important;width:100%;min-height:152px;padding:0!important;border-color:rgba(17,162,207,.34)!important;overflow:hidden}.preview-camera-timeline--live .timeline-shell{min-height:150px;border:0;border-radius:4px;background:linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px) 0 0/28px 100%,linear-gradient(180deg,rgba(17,162,207,.08),transparent 34%),#070707}.preview-camera-timeline--live .volume-popover[data-disabled=true]{display:none!important}.preview-live-timeline-loading{display:grid;place-items:center;min-height:86px;color:var(--color-text-muted);font-size:12px}.overlay-timeline{position:absolute;left:76px;right:76px;bottom:44px;z-index:18;height:34px;pointer-events:none}.overlay-timeline[hidden]{display:none}.overlay-timeline-item{position:absolute;left:var(--overlay-time-left);top:0;display:grid;place-items:center;width:clamp(16px,var(--overlay-time-width),24px);height:26px;min-width:16px;min-height:26px;padding:0;border:2px solid rgba(175,207,42,.86);border-radius:7px;background:linear-gradient(180deg,rgba(175,207,42,.16),rgba(5,5,5,.9));color:transparent;box-shadow:0 0 0 2px rgba(175,207,42,.12),0 0 18px rgba(175,207,42,.22);font-size:0;line-height:1;cursor:grab;overflow:visible;pointer-events:auto;transform:translateY(0);transition:border-color .14s ease,box-shadow .14s ease,background .14s ease}.overlay-timeline-item:before{content:"";position:absolute;left:50%;top:-9px;width:5px;height:5px;border-radius:999px;background:var(--color-brand-green);box-shadow:0 0 10px rgba(175,207,42,.7);transform:translateX(-50%)}.overlay-timeline-item:after{content:"";position:absolute;inset:5px 4px;border:1px solid rgba(175,207,42,.38);border-radius:3px;background:rgba(0,0,0,.42)}.overlay-timeline-item span{position:absolute;inset:0;overflow:hidden;opacity:0;pointer-events:none}.overlay-timeline-item i{position:absolute;right:-3px;top:4px;bottom:4px;z-index:2;display:block;width:7px;border:0;border-radius:999px;background:rgba(231,231,232,.2);cursor:ew-resize}.overlay-timeline-item[data-overlay-kind=speech]{border-color:rgba(231,231,232,.88);background:linear-gradient(180deg,rgba(175,207,42,.28),rgba(5,5,5,.9));box-shadow:0 0 0 2px rgba(231,231,232,.08),0 0 20px rgba(175,207,42,.28)}.overlay-timeline-item[data-overlay-kind=image]{border-style:dashed}.overlay-timeline-item.is-active,.overlay-timeline-item.is-selected{border-color:rgba(231,231,232,.98);box-shadow:0 0 0 3px rgba(175,207,42,.18),0 0 24px rgba(175,207,42,.36)}
.editor-tools{display:grid;align-content:start;gap:12px}.tool-stack{display:grid;gap:10px}.tool-section{border:1px solid #242424;border-radius:8px;background:#0a0a0a;padding:0;overflow:hidden}.tool-section>summary{display:flex;align-items:center;justify-content:space-between;gap:12px;min-height:44px;padding:10px 12px;cursor:pointer;list-style:none;color:var(--color-text);font-weight:800}.tool-section>summary::-webkit-details-marker{display:none}.tool-section>summary:after{content:"";width:8px;height:8px;border-right:1px solid currentColor;border-bottom:1px solid currentColor;transform:rotate(45deg);opacity:.62;transition:transform .16s ease}.tool-section[open]>summary:after{transform:rotate(225deg)}.tool-section>summary small{color:var(--color-text-muted);font-size:12px;font-weight:600;text-align:right}.tool-section[open]>summary{border-bottom:1px solid rgba(231,231,232,.08)}.tool-section>*:not(summary){margin:12px}.timeline-editor{padding:0}.timeline-head,.timeline-timebar,.timeline-values{display:flex;justify-content:space-between;gap:12px;color:var(--color-text-muted);font-size:12px}.timeline-head output,.timeline-timebar output{color:var(--color-text);text-align:right}.timeline-timebar{margin-top:10px}.timeline-timebar span:last-child{color:#777;text-align:right}.timeline-scrub{position:relative;height:42px;margin-top:8px}.timeline-scrub-track{position:absolute;left:0;right:0;top:17px;height:8px;border:1px solid #343434;border-radius:999px;background:linear-gradient(90deg,var(--color-surface-muted),#252525);overflow:hidden}.timeline-selected{position:absolute;top:0;bottom:0;background:rgba(175,207,42,.22);border-left:1px solid var(--color-brand-green);border-right:1px solid var(--color-brand-green)}.timeline-playhead{position:absolute;top:-8px;bottom:-8px;width:2px;background:var(--color-brand-white);box-shadow:0 0 0 1px rgba(0,0,0,.7)}.timeline-playhead:before{content:"";position:absolute;left:50%;top:-4px;width:10px;height:10px;border-radius:50%;background:var(--color-brand-white);transform:translateX(-50%)}.timeline-scrub input{position:absolute;inset:0;width:100%;height:42px;margin:0;background:transparent;opacity:0;cursor:pointer}.timeline{position:relative;height:38px;margin-top:6px}.timeline-track{position:absolute;left:0;right:0;top:16px;height:6px;background:#292929;border-radius:999px;overflow:hidden}.timeline-fill{position:absolute;top:0;bottom:0;background:var(--color-brand-white);border-radius:999px}.timeline input{position:absolute;inset:0;width:100%;height:38px;margin:0;background:transparent;pointer-events:none;-webkit-appearance:none;appearance:none}.timeline input::-webkit-slider-thumb{width:18px;height:18px;border-radius:50%;background:var(--color-brand-white);border:2px solid var(--color-brand-black);pointer-events:auto;-webkit-appearance:none;appearance:none}.timeline input::-webkit-slider-runnable-track{background:transparent}.timeline input::-moz-range-thumb{width:18px;height:18px;border-radius:50%;background:var(--color-brand-white);border:2px solid var(--color-brand-black);pointer-events:auto}.timeline input::-moz-range-track{background:transparent}.timeline-values{margin-top:6px}.actions,.platform-tags{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.export-dock{display:grid;gap:8px;margin-top:2px;padding:12px;border:1px solid #303030;border-radius:8px;background:#111}.export-dock strong{display:block;font-size:13px}.export-dock span{color:#a8a8a8;font-size:12px}
.platform-tags button,.camera-card-buttons button,.effect-card-buttons button,.overlay-card-buttons button{background:var(--color-surface-control);color:var(--color-text-soft);border:1px solid var(--color-border-strong);text-align:left}.platform-tags button.active,.camera-card-buttons button.active,.effect-card-buttons button.active,.overlay-card-buttons button.active{background:#102018;color:var(--color-text);border-color:var(--color-brand-green)}.camera-card-controls,.effect-card-controls,.overlay-card-controls{display:grid;gap:10px}.effect-split{display:grid;grid-template-columns:minmax(0,1fr) minmax(220px,.75fr);gap:10px}.effect-subpanel{display:grid;gap:10px;padding:10px;border:1px solid #2a2a2a;border-radius:8px;background:#101010}.effect-subpanel strong{font-size:12px}.bumper-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.bumper-upload{display:grid;gap:6px;align-content:start;min-height:64px;padding:9px;border:1px dashed var(--color-border-strong);border-radius:8px;background:var(--color-surface-control);cursor:pointer}.bumper-upload input{font-size:11px}.bumper-strip{display:flex;gap:6px;flex-wrap:wrap;min-height:28px}.bumper-empty{color:var(--color-text-muted);font-size:12px}.camera-card-buttons,.effect-card-buttons,.overlay-card-buttons{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.camera-card-controls label,.effect-card-controls label,.overlay-card-controls label,.caption-settings label{display:grid;gap:6px;color:var(--color-text-muted);font-size:12px}.camera-card-controls input,.effect-card-controls input,.overlay-card-controls input{width:100%;accent-color:var(--color-brand-blue)}.camera-card-controls select,.caption-settings select,.caption-settings input{width:100%;background:var(--color-brand-black);color:var(--color-text);border:1px solid var(--color-border-strong);border-radius:6px;padding:8px}.camera-path-editor,.camera-manual-panel{display:grid;gap:10px;padding:10px;border:1px solid #2a2a2a;border-radius:8px;background:#101010}.camera-path-head,.camera-panel-title{display:flex;justify-content:space-between;gap:10px;align-items:center}.camera-path-head strong,.camera-panel-title strong{font-size:12px}.camera-path-head span,.camera-panel-title span{color:var(--color-text-muted);font-size:12px}.camera-smart-panel{display:grid;gap:9px;padding:10px;border:1px solid rgba(17,162,207,.28);border-radius:8px;background:linear-gradient(135deg,rgba(17,162,207,.12),rgba(175,207,42,.06))}.camera-smart-row,.camera-smart-ai{display:grid;gap:8px}.camera-smart-row{grid-template-columns:repeat(3,minmax(0,1fr))}.camera-smart-ai{grid-template-columns:repeat(5,minmax(0,1fr))}.camera-smart-panel button{display:grid;gap:3px;justify-items:center;background:rgba(17,162,207,.1);color:var(--color-text);border:1px solid rgba(17,162,207,.34);text-align:center}.camera-smart-panel button:hover{border-color:var(--color-brand-blue);box-shadow:0 0 0 3px rgba(17,162,207,.14)}.camera-path-track{position:relative;height:34px}.camera-path-rail{position:absolute;left:0;right:0;top:15px;height:5px;border-radius:999px;background:#292929}.camera-path-marker{position:absolute;top:7px;width:20px;height:20px;min-width:20px;padding:0;border-radius:999px;transform:translateX(-50%);background:var(--color-surface-control);border:1px solid var(--color-border-strong)}.camera-path-marker.active{background:var(--color-brand-blue);border-color:var(--color-brand-blue);box-shadow:0 0 0 4px rgba(17,162,207,.18)}.camera-path-actions{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.camera-keyframe-panel{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;align-items:end}.camera-auto-status{min-height:18px;color:var(--color-text-muted);font-size:12px}.camera-path-delete{color:var(--color-danger)!important}.camera-segments{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.camera-segment{display:grid;gap:8px;padding:10px;border:1px solid #2a2a2a;border-radius:8px;background:#101010}.camera-segment strong{font-size:12px}.caption-settings{display:grid;grid-template-columns:minmax(160px,1fr) 120px 150px;gap:12px;max-width:none}.caption-toggle{align-content:center}.caption-toggle input{justify-self:start;width:auto;min-height:20px;accent-color:var(--color-brand-blue)}
.camera-smart-panel p{margin:0;color:var(--color-text-muted);font-size:12px}.camera-smart-panel button span{color:var(--color-text-muted);font-size:11px}.camera-director-action{min-height:72px;background:linear-gradient(135deg,rgba(17,162,207,.32),rgba(231,231,232,.08))!important;border-color:rgba(17,162,207,.72)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.16),0 16px 34px rgba(17,162,207,.1)}.camera-director-action strong{font-size:15px}.camera-smart-row button{min-height:54px}.camera-smart-ai button{min-height:50px}.camera-advanced{display:grid;gap:10px;padding:10px;border:1px solid rgba(231,231,232,.08);border-radius:8px;background:rgba(255,255,255,.025)}.camera-advanced summary{display:flex;justify-content:space-between;gap:10px;align-items:center;cursor:pointer;color:var(--color-text-soft)}.camera-advanced summary small{color:var(--color-text-muted);font-size:12px}.camera-advanced[open] summary{padding-bottom:8px;border-bottom:1px solid rgba(231,231,232,.08)}.camera-advanced .camera-manual-panel{padding:0;border:0;background:transparent}.camera-surface video{position:relative;z-index:1;object-position:var(--camera-x,50%) 50%;transform:scale(var(--camera-scale,1));transform-origin:var(--camera-x,50%) 50%;transition:object-position var(--camera-transition-ms,700ms) cubic-bezier(.22,.61,.36,1),transform var(--camera-transition-ms,700ms) cubic-bezier(.22,.61,.36,1)}.camera-surface[data-camera-cut=hard] video:not(.camera-fit-bg){transition:none}.camera-surface .camera-fit-bg{position:absolute!important;inset:-7%;z-index:0!important;width:114%!important;height:114%!important;display:none!important;object-fit:cover!important;object-position:center!important;transform:none!important;filter:blur(22px) saturate(.88) brightness(.62)!important;pointer-events:none}.camera-surface .camera-fit-logo{position:absolute;top:11%;left:50%;z-index:1;width:38%!important;max-width:240px;height:auto!important;display:none!important;object-fit:contain!important;object-position:center;background:transparent!important;transform:translateX(-50%);opacity:.9;pointer-events:none}.camera-surface[data-camera-fit=contain]{background:#050505}.camera-surface[data-camera-fit=contain] .camera-fit-bg{display:block!important}.camera-surface[data-camera-fit=contain] .camera-fit-logo{display:block!important}.camera-surface[data-camera-fit=contain] video:not(.camera-fit-bg){z-index:2;object-fit:contain;transform:none;transform-origin:center;background:transparent}.camera-reticle{position:absolute;inset:14% 22%;z-index:3;border:1px solid rgba(36,209,126,.58);border-radius:8px;box-shadow:0 0 0 999px rgba(0,0,0,.1);pointer-events:none}.preview-caption-layer{position:absolute;left:7.4%;right:7.4%;bottom:16.25%;z-index:4;display:grid;justify-items:center;pointer-events:none;opacity:0;transform:translateY(8px);transition:opacity 120ms ease,transform 120ms ease}.preview-caption-layer[data-visible=true]{opacity:1;transform:translateY(0)}.preview-caption-layer span{display:block;max-width:100%;color:#fff;font-family:Arial,sans-serif;font-size:clamp(18px,6.67cqw,36px);font-weight:900;line-height:1.08;text-align:center;text-shadow:0 2px 0 #000,0 -2px 0 #000,2px 0 0 #000,-2px 0 0 #000,0 0 12px rgba(0,0,0,.9),0 8px 22px rgba(0,0,0,.66);-webkit-text-stroke:clamp(1.2px,.44cqw,2.4px) rgba(0,0,0,.88);paint-order:stroke fill;text-transform:none;white-space:normal}.card[data-preview-format=facebook] .preview-caption-layer{bottom:8.8%}.card[data-preview-format=facebook] .preview-caption-layer span{font-size:clamp(18px,5cqw,34px);-webkit-text-stroke:clamp(1.1px,.38cqw,2px) rgba(0,0,0,.88)}.card[data-preview-format=youtube] .preview-caption-layer{bottom:11%}.card[data-preview-format=youtube] .preview-caption-layer span{font-size:clamp(18px,2.82cqw,32px);-webkit-text-stroke:clamp(1px,.26cqw,1.8px) rgba(0,0,0,.88)}
.card[data-effect=light-grain] .media video,.card[data-effect=light-grain] .media img{filter:contrast(1.08) brightness(1.02)}.card[data-effect=old-film] .media video,.card[data-effect=old-film] .media img{filter:sepia(.48) contrast(1.2) saturate(.62) brightness(.92)}.card[data-effect=vhs] .media video,.card[data-effect=vhs] .media img{filter:saturate(.62) contrast(1.22) brightness(.9) hue-rotate(-7deg)}.card[data-effect=bw-old] .media video,.card[data-effect=bw-old] .media img{filter:grayscale(1) contrast(1.22) brightness(.9)}.card[data-effect=light-grain] .media:after,.card[data-effect=old-film] .media:after,.card[data-effect=vhs] .media:after,.card[data-effect=bw-old] .media:after{content:"";position:absolute;inset:0;pointer-events:none;opacity:var(--effect-opacity,.24);background-image:radial-gradient(circle at 20% 30%,rgba(255,255,255,.95) 0 1px,transparent 1.6px),radial-gradient(circle at 70% 65%,rgba(0,0,0,.95) 0 1px,transparent 1.8px);background-size:4px 4px,6px 6px;mix-blend-mode:overlay}.card[data-effect=old-film] .media:before,.card[data-effect=bw-old] .media:before{content:"";position:absolute;inset:0;pointer-events:none;z-index:1;background:radial-gradient(circle at center,transparent 44%,rgba(0,0,0,.46) 100%)}.card[data-effect=vhs] .media:before{content:"";position:absolute;inset:0;pointer-events:none;z-index:1;background:repeating-linear-gradient(0deg,rgba(255,255,255,.08) 0 1px,transparent 1px 4px);mix-blend-mode:overlay}
.camera-surface[data-camera-fit=contain] video:not(.camera-fit-bg){object-position:center}
.preview-caption-layer span{padding:var(--preview-caption-padding,0);border-radius:.16em;background:var(--preview-caption-bg,transparent);color:var(--preview-caption-color,#fff);font-size:var(--preview-caption-size,clamp(18px,6.67cqw,36px));box-decoration-break:clone;-webkit-box-decoration-break:clone}
.overlay-tools{display:grid;grid-template-columns:1fr auto;gap:10px;align-items:end}.overlay-box{position:absolute;z-index:3;left:calc(var(--overlay-x)*100%);top:calc(var(--overlay-y)*100%);width:calc(var(--overlay-width)*100%);min-width:120px;padding:10px 14px 11px 18px;border-left:6px solid var(--overlay-accent,var(--color-brand-green));border-radius:8px;background:rgba(0,0,0,var(--overlay-opacity,.92));box-shadow:0 10px 30px rgba(0,0,0,.35);cursor:move;touch-action:none;user-select:none;pointer-events:auto;opacity:1;transform:translateY(0);transition:opacity 170ms ease,transform 170ms ease,outline-color .14s ease}.overlay-box[data-overlay-visible=false]{opacity:0;transform:translateY(5px);pointer-events:none}.overlay-box[data-overlay-key=none]{display:none}.overlay-box strong{font-size:clamp(13px,4vw,20px);line-height:1.05}.overlay-box em{display:block;margin-top:3px;color:rgba(255,255,255,.75);font-style:normal;font-size:clamp(10px,2.4vw,13px);line-height:1.2}.overlay-text-box{display:grid;align-items:center;min-width:96px;min-height:34px;padding:8px 12px;border-left:0;background:rgba(var(--overlay-bg-rgb,0,0,0),var(--overlay-bg-opacity,.7));box-shadow:none;color:var(--overlay-color,#fff);font-weight:700;font-size:clamp(13px,var(--overlay-font-size,20px),36px);line-height:1.05;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.overlay-text-box[data-overlay-bg=off]{background:transparent;box-shadow:none}.overlay-text-box span{opacity:var(--overlay-opacity,1);overflow:hidden;text-overflow:ellipsis}.overlay-speech-box{display:grid;align-items:center;min-width:112px;min-height:42px;padding:10px 15px;border:0;border-radius:18px;background:rgba(var(--overlay-bg-rgb,255,255,255),var(--overlay-bg-opacity,.94));box-shadow:0 10px 24px rgba(0,0,0,.22);color:var(--overlay-color,#050505);font-weight:900;font-size:clamp(14px,var(--overlay-font-size,22px),30px);line-height:1.08;white-space:normal;overflow:visible}.overlay-speech-box:after{position:absolute;left:18%;bottom:-12px;width:24px;height:20px;border-radius:0 0 22px 0;background:inherit;content:"";transform:skewX(-18deg);box-shadow:8px 9px 16px rgba(0,0,0,.12)}.overlay-speech-box span{position:relative;z-index:1;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;opacity:var(--overlay-opacity,1);overflow:hidden;text-overflow:ellipsis;overflow-wrap:anywhere}.overlay-box.is-selected{outline:2px solid var(--color-focus);outline-offset:2px}.overlay-image-box{display:grid;place-items:center;min-width:72px;min-height:72px;padding:6px;border:1px dashed rgba(255,255,255,.42);background:rgba(0,0,0,.12);box-shadow:0 8px 24px rgba(0,0,0,.22)}.overlay-image-box img{display:block;width:100%;height:auto;max-height:100%;object-fit:contain;opacity:var(--overlay-opacity,1);pointer-events:none;background:transparent}.overlay-resize{position:absolute;right:3px;bottom:3px;z-index:4;width:22px;height:22px;padding:0;border:1px solid rgba(255,255,255,.52);border-radius:5px;background:rgba(255,255,255,.2);cursor:nwse-resize;touch-action:none;pointer-events:auto}.overlay-menu{position:absolute;z-index:6;display:grid;gap:8px;width:min(360px,94%);max-height:min(420px,calc(100vh - 24px));overflow:auto;padding:8px;border:1px solid var(--color-border-strong);border-radius:8px;background:#101010;box-shadow:var(--shadow-panel);touch-action:none;scrollbar-width:thin;scrollbar-color:rgba(175,207,42,.5) rgba(255,255,255,.06)}.overlay-menu[hidden]{display:none}.overlay-menu-head{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:2px 2px 4px;cursor:move}.overlay-menu-head strong{font-size:13px}.overlay-menu-head button{padding:6px 9px}.overlay-menu-actions{display:grid;grid-template-columns:repeat(2,minmax(120px,1fr));gap:6px}.overlay-menu button{background:#242424;color:var(--color-text-soft);border:1px solid var(--color-border-strong)}.overlay-inspector{display:grid;gap:8px}.overlay-inspector label{display:grid;gap:5px;color:var(--color-text-muted);font-size:12px}.overlay-inspector input[type=text],.overlay-inspector input[type=number]{width:100%;background:var(--color-brand-black);color:var(--color-text);border:1px solid var(--color-border-strong);border-radius:6px;padding:8px}.overlay-inspector input[type=color]{width:42px;height:32px;padding:2px;border:1px solid var(--color-border-strong);border-radius:6px;background:var(--color-brand-black)}.overlay-inspector input[type=range]{width:100%;accent-color:var(--color-brand-green)}.overlay-inspector-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.overlay-inspector-row>*{flex:1 1 96px}.overlay-inspector-check{display:flex!important;grid-template-columns:none!important;align-items:center;gap:8px}.overlay-inspector-check input{width:auto}.overlay-inspector-section{display:grid;gap:8px;padding:8px;border:1px solid rgba(231,231,232,.1);border-radius:8px;background:rgba(231,231,232,.035)}.overlay-inspector-section summary{cursor:pointer;color:var(--color-text-soft);font-size:12px;font-weight:800;list-style:none}.overlay-inspector-section summary::-webkit-details-marker{display:none}.overlay-inspector-section[open] summary{padding-bottom:6px;border-bottom:1px solid rgba(231,231,232,.08)}.overlay-image-source{display:grid;grid-template-columns:44px 1fr;gap:8px;align-items:center}.overlay-image-source img,.overlay-image-source span{display:block;width:44px;height:44px;border:1px solid rgba(231,231,232,.14);border-radius:6px;background:#050505;object-fit:contain}.overlay-inspector-actions{display:flex;gap:8px;flex-wrap:wrap}.overlay-inspector-actions button{flex:1 1 120px}.overlay-danger{color:var(--color-danger)!important;border-color:#5b2626!important;background:#251111!important}.image-upload{padding:10px;border:1px dashed var(--color-border-strong);border-radius:8px;background:#0f0f0f}.overlay-layer-list{display:grid;gap:6px}.overlay-layer-row{display:flex;justify-content:space-between;gap:8px;align-items:center;padding:8px;border:1px solid #242424;border-radius:6px;background:#101010}.overlay-layer-row span{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.overlay-layer-row button{padding:6px 9px;background:#242424;color:var(--color-text-soft);border:1px solid var(--color-border-strong)}.overlay-empty{padding:10px;border:1px dashed var(--color-border-strong);border-radius:8px;color:var(--color-text-muted)}
p{color:#bebebe}.peak{color:#fff;font-size:16px;line-height:1.35}dl{display:grid;grid-template-columns:auto 1fr;gap:4px 10px;color:#aaa}dt{color:#707070}dd{margin:0}.transcript-copy{max-height:220px;overflow:auto;margin-top:10px;padding:10px;border:1px solid rgba(231,231,232,.08);border-radius:8px;background:rgba(0,0,0,.18)}.transcript-copy p{margin:0;line-height:1.45}
body[data-tab=import] main,body[data-tab=import] .final-stage{display:none}body[data-tab=import] .import-stage{display:block}body[data-tab=final] main,body[data-tab=final] .import-stage{display:none}body[data-tab=final] .final-stage{display:block}.final-stage{display:none;margin:18px auto;max-width:1240px;padding:18px;border:1px solid var(--color-border);border-radius:8px;background:var(--color-surface-raised)}.stage-head{display:flex;justify-content:space-between;gap:16px;align-items:center}.render-status{margin-top:12px;color:var(--color-text-muted)}.render-results{display:grid;gap:12px;margin-top:14px}.result-item{border:1px solid #303030;border-radius:8px;background:#090909;overflow:hidden}.result-item[open]{border-color:var(--color-metal-gray)}.result-item summary{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:12px 14px;border:0;color:var(--color-text)}.result-item summary strong{font-size:14px}.result-item summary span{color:var(--color-text-muted);font-size:12px}.result-body{display:grid;grid-template-columns:minmax(260px,420px) minmax(240px,1fr);gap:14px;padding:0 14px 14px}.result-body video{width:100%;max-height:70vh;background:#000;border-radius:6px;object-fit:contain}.result-meta{display:grid;align-content:start;gap:10px}.result-meta dl{margin:0}.result-path{display:block;max-width:100%;padding:8px 10px;border:1px solid rgba(17,162,207,.28);border-radius:6px;background:rgba(17,162,207,.08);color:var(--color-text);font-size:12px;line-height:1.35;overflow-wrap:anywhere}.result-actions{display:flex;gap:8px;flex-wrap:wrap}.result-actions a,.result-actions button{display:inline-flex;align-items:center;justify-content:center;min-height:38px;padding:9px 12px;border-radius:6px;background:var(--color-brand-white);color:var(--color-brand-black);text-decoration:none}.result-actions a.secondary,.result-actions button.secondary{background:#242424;color:var(--color-text-soft);border:1px solid var(--color-border-strong)}
.empty-project-stage{display:none;max-width:720px;margin:18px auto;padding:0 18px}.empty-project-panel{display:grid;gap:10px;padding:18px;border:1px solid var(--glass-border);border-radius:var(--radius-panel);background:var(--glass-bg-strong);box-shadow:var(--glass-shadow),inset 0 1px 0 var(--glass-edge);backdrop-filter:blur(24px) saturate(1.45);text-align:center}.empty-project-panel p{margin:0;color:var(--color-text-muted)}.empty-project-panel button{justify-self:center}body[data-project-empty=true][data-tab=edit] main{display:none}body[data-project-empty=true][data-tab=edit] .empty-project-stage{display:block}
.settings-backdrop{position:fixed;inset:0;z-index:50;display:grid;place-items:center;padding:18px;background:rgba(0,0,0,.58)}.settings-backdrop[hidden]{display:none}.settings-panel{width:min(560px,100%);border:1px solid var(--color-border);border-radius:8px;background:var(--color-surface-raised);box-shadow:var(--shadow-panel);padding:16px}.settings-head{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.settings-head p{margin:3px 0 0;color:var(--color-text-muted)}.settings-form{display:grid;gap:12px;margin-top:14px}.settings-form label{display:grid;gap:6px;color:var(--color-text-muted);font-size:12px}.settings-form input,.settings-form select{width:100%;border:1px solid var(--color-border-strong);border-radius:6px;background:var(--color-brand-black);color:var(--color-text);padding:9px 10px;font:inherit}.settings-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.settings-status,.settings-usage{padding:10px;border:1px solid var(--color-border);border-radius:8px;background:#0b0b0b;color:var(--color-text-soft)}.settings-usage{display:grid;gap:3px;color:var(--color-text-muted)}.settings-actions{display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap}.settings-form small{color:var(--color-text-muted)}
button{background:var(--color-brand-white);color:var(--color-brand-black);border:0;border-radius:6px;padding:9px 12px;cursor:pointer}#reset-ui,button[data-action=discard]{background:#242424;color:var(--color-text-soft)}
@media(max-width:860px){header{position:relative;grid-template-columns:1fr;justify-items:center}.header-actions{justify-content:center}.brand-logo{width:min(390px,88vw);height:64px}.brand-lockup p{max-width:86vw}.tabs{top:0;overflow:auto}.preview-strip button{font-size:12px;padding:7px 9px}main{padding:12px}.clip-summary{grid-template-columns:auto minmax(0,1fr);align-items:start}.clip-row-timeline,.clip-status{grid-column:1/-1}.clip-status{justify-content:flex-start}.editor-shell,.result-body,.camera-segments,.camera-smart-row,.camera-smart-ai,.camera-path-actions,.camera-keyframe-panel,.caption-settings,.preview-bar,.import-grid,.duration-profile,.import-path-row,.settings-grid,.effect-split,.bumper-actions{grid-template-columns:1fr}.preview-frame{max-width:100%}.preview-strip{justify-content:center}.preview-controls{width:max-content;max-width:100%;flex-wrap:wrap}.media{max-height:none}.stage-head{align-items:flex-start;flex-direction:column}.result-item summary{align-items:flex-start;flex-direction:column}.camera-card-buttons,.effect-card-buttons,.overlay-card-buttons,.overlay-menu{grid-template-columns:1fr}}
"""


def liquid_ui_css() -> str:
    return """
:root{--glass-bg:rgba(18,18,18,.54);--glass-bg-strong:rgba(22,22,22,.76);--glass-border:rgba(231,231,232,.18);--glass-edge:rgba(255,255,255,.34);--glass-highlight:rgba(255,255,255,.12);--glass-shadow:0 22px 56px rgba(0,0,0,.46);--control-bg:rgba(28,28,28,.58);--control-hover:rgba(54,54,54,.7);--control-active:rgba(17,162,207,.2);--radius-control:999px;--radius-panel:8px;--focus-ring:0 0 0 2px rgba(17,162,207,.55)}
html{min-height:100%;background:var(--color-brand-black)}
body{min-height:100vh;background:linear-gradient(145deg,rgba(17,162,207,.16) 0%,rgba(5,5,5,.04) 24%,rgba(5,5,5,0) 52%,rgba(175,207,42,.12) 100%),linear-gradient(180deg,#050505 0%,#080808 42%,#050505 100%);background-repeat:no-repeat;background-size:100vw 100vh,100vw 100vh;background-attachment:fixed;font-family:Inter,Arial,sans-serif;letter-spacing:0}
button,.import-result a,.result-actions a{position:relative;min-height:36px;border:1px solid var(--glass-border);border-radius:var(--radius-control);background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.025) 38%,rgba(0,0,0,.08)),var(--control-bg);color:var(--color-text-soft);box-shadow:inset 0 1px 0 var(--glass-edge),inset 0 -10px 18px rgba(0,0,0,.16),0 8px 22px rgba(0,0,0,.22);transition:background .16s ease,border-color .16s ease,color .16s ease,transform .16s ease,box-shadow .16s ease}
button:hover,.import-result a:hover,.result-actions a:hover{background:linear-gradient(180deg,rgba(255,255,255,.14),rgba(255,255,255,.035) 42%,rgba(0,0,0,.08)),var(--control-hover);border-color:rgba(231,231,232,.3);box-shadow:inset 0 1px 0 rgba(255,255,255,.42),inset 0 -10px 18px rgba(0,0,0,.14),0 10px 26px rgba(0,0,0,.26)}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:0;box-shadow:var(--focus-ring)}
button:active{transform:translateY(1px)}
button:disabled{opacity:.48;cursor:not-allowed;transform:none}
header{background:linear-gradient(180deg,rgba(5,5,5,.92),rgba(5,5,5,.68));backdrop-filter:blur(22px) saturate(1.35);border-bottom:1px solid var(--glass-border)}
.brand-logo{width:min(500px,48vw);height:70px}.brand-lockup p{margin-top:0;color:rgba(231,231,232,.56)}
.header-actions button,#reset-ui{background:linear-gradient(180deg,rgba(255,255,255,.12),rgba(255,255,255,.03)),rgba(231,231,232,.08);color:var(--color-text-soft);border-color:var(--glass-border)}
.tabs{justify-content:center;background:rgba(5,5,5,.58);backdrop-filter:blur(22px) saturate(1.35);border-bottom:1px solid var(--glass-border)}
.tabs button{min-width:98px;background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.025)),rgba(231,231,232,.055);border-color:var(--glass-border);color:rgba(231,231,232,.78);font-weight:700}
.tabs button.active{background:var(--color-brand-white);color:var(--color-brand-black);border-color:var(--color-brand-white)}
.card,.import-panel,.final-stage{border-color:var(--glass-border);background:linear-gradient(180deg,rgba(17,17,17,.92),rgba(10,10,10,.94));box-shadow:0 10px 34px rgba(0,0,0,.22)}
.card[open]{border-color:rgba(231,231,232,.22);background:linear-gradient(180deg,rgba(20,20,20,.96),rgba(12,12,12,.96))}
.card.liked,.card.liked[open]{border-color:rgba(175,207,42,.68)}.card.liked [data-status-pill]{background:rgba(175,207,42,.16);border-color:rgba(175,207,42,.58);color:var(--color-brand-green)}
.clip-summary{min-height:58px}.clip-status span,.format-previews span{background:rgba(231,231,232,.07);border:1px solid var(--glass-border);color:rgba(231,231,232,.72)}
.preview-bar{gap:10px;padding:10px;width:100%;border:1px solid var(--glass-border);border-radius:var(--radius-panel);background:linear-gradient(160deg,rgba(255,255,255,.12),rgba(255,255,255,.035) 34%,rgba(0,0,0,.1) 100%),var(--glass-bg);box-shadow:var(--glass-shadow),inset 0 1px 0 var(--glass-edge),inset 0 -18px 30px rgba(0,0,0,.18);backdrop-filter:blur(26px) saturate(1.55)}
.preview-strip{width:100%;justify-content:center}.preview-strip button,.platform-tags button,.camera-card-buttons button,.effect-card-buttons button,.overlay-card-buttons button{border-color:var(--glass-border);background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.025)),rgba(231,231,232,.055);color:rgba(231,231,232,.82);font-weight:700;text-align:center}
.preview-strip button.active,.platform-tags button.active,.camera-card-buttons button.active,.effect-card-buttons button.active,.overlay-card-buttons button.active{background:var(--control-active);color:var(--color-brand-blue);border-color:rgba(17,162,207,.72)}
.preview-controls{gap:8px;padding:5px 8px;border-color:var(--glass-border);background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.025)),rgba(5,5,5,.26);box-shadow:inset 0 1px 0 var(--glass-edge),0 8px 22px rgba(0,0,0,.24);backdrop-filter:blur(18px) saturate(1.45)}
.preview-icon,.preview-step{border-color:var(--glass-border);background:linear-gradient(180deg,rgba(255,255,255,.14),rgba(255,255,255,.035)),rgba(231,231,232,.08);color:var(--color-text);box-shadow:inset 0 1px 0 rgba(255,255,255,.36),inset 0 -8px 14px rgba(0,0,0,.14)}
.preview-play{width:38px;height:38px;min-width:38px;background:var(--color-brand-white);color:var(--color-brand-black);border-color:var(--color-brand-white)}
.preview-volume-group{border-left:1px solid rgba(231,231,232,.12)}.preview-volume-group output{color:rgba(231,231,232,.72);font-variant-numeric:tabular-nums}
.preview-bar,.preview-controls,.preview-camera-timeline,.preview-volume-group{overflow:visible}.preview-bar{position:relative;z-index:20}.preview-topbar{display:flex;align-items:center;justify-content:space-between;gap:8px;width:100%;min-width:0}.preview-topbar .preview-strip{flex:1 1 auto;width:auto;min-width:0;justify-content:flex-start;flex-wrap:nowrap;overflow-x:auto;overflow-y:hidden;padding-bottom:0;scrollbar-width:none}.preview-topbar .preview-strip::-webkit-scrollbar{display:none}.preview-topbar .preview-strip button{flex:0 0 auto;min-height:32px;padding:7px 9px;font-size:12px}.preview-controls{display:block;width:100%;max-width:100%;padding:0;border:0;background:transparent;box-shadow:none;backdrop-filter:none}.preview-transport-group{flex:0 0 auto;display:flex;align-items:center;gap:6px;padding:5px 6px;border:1px solid var(--glass-border);border-radius:999px;background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.025)),rgba(5,5,5,.26);box-shadow:inset 0 1px 0 var(--glass-edge),0 8px 22px rgba(0,0,0,.18);backdrop-filter:blur(18px) saturate(1.45)}.preview-volume-group{position:relative;padding-left:0;border-left:0}.preview-camera-timeline{position:relative;width:100%;min-width:0;display:grid;align-items:center;min-height:42px;padding:6px 12px;border:1px solid rgba(17,162,207,.42);border-radius:4px;background:linear-gradient(180deg,rgba(17,162,207,.11),rgba(255,255,255,.025)),rgba(5,5,5,.24);box-shadow:inset 0 1px 0 var(--glass-edge),0 8px 22px rgba(0,0,0,.18);backdrop-filter:blur(18px) saturate(1.45)}.preview-camera-rail{position:relative;width:100%;height:24px;cursor:pointer;touch-action:none}.preview-audio-waveform{position:absolute;inset:1px 0;z-index:0;display:flex;align-items:center;gap:1px;opacity:.78;pointer-events:none}.preview-audio-waveform[hidden]{display:none}.preview-audio-waveform span{flex:1;min-width:1px;max-height:21px;background:rgba(175,207,42,.42);border-radius:1px}.preview-camera-track{position:absolute;left:0;right:0;top:50%;z-index:1;height:3px;border-radius:0;background:linear-gradient(90deg,rgba(17,162,207,.5),rgba(231,231,232,.12));box-shadow:inset 0 0 0 1px rgba(255,255,255,.04);transform:translateY(-50%)}.preview-camera-playhead{position:absolute;top:50%;z-index:4;width:2px;height:20px;border-radius:999px;background:var(--color-brand-white);box-shadow:0 0 0 1px rgba(0,0,0,.7);transform:translate(-50%,-50%);pointer-events:none}.preview-camera-marker{position:absolute;top:50%;z-index:3;width:9px;height:22px;min-width:9px;padding:0;border:1px solid rgba(17,162,207,.84);border-radius:3px;background:rgba(17,162,207,.16);box-shadow:inset 0 1px 0 rgba(255,255,255,.2),0 0 0 2px rgba(17,162,207,.06);transform:translate(-50%,-50%);cursor:pointer}.preview-camera-marker:active{transform:translate(-50%,-50%)}.preview-camera-marker.active{background:var(--color-brand-blue);box-shadow:0 0 0 3px rgba(17,162,207,.18),0 0 14px rgba(17,162,207,.32)}.preview-camera-popover,.preview-volume-popover{position:absolute;z-index:1000;display:grid;gap:8px;padding:10px;border:1px solid var(--glass-border);border-radius:8px;background:#101010;box-shadow:var(--shadow-panel)}.preview-camera-popover{top:calc(100% + 8px);left:50%;width:min(260px,92vw);transform:translateX(-50%)}.preview-camera-popover[hidden],.preview-volume-popover[hidden]{display:none}.preview-camera-popover label{display:grid;gap:5px;color:var(--color-text-muted);font-size:12px}.preview-camera-popover select{width:100%;background:var(--color-brand-black);color:var(--color-text);border:1px solid var(--color-border-strong);border-radius:6px;padding:8px}.preview-camera-popover input{width:100%;accent-color:var(--color-brand-blue)}.preview-camera-popover button{min-height:32px;background:#242424;color:var(--color-text-soft);border:1px solid var(--color-border-strong)}.preview-volume-popover{right:50%;bottom:calc(100% + 8px);width:auto;height:128px;padding:12px 8px;place-items:center;transform:translateX(50%)}.preview-volume-slider{display:block;width:110px;accent-color:var(--color-brand-blue);writing-mode:vertical-rl;direction:rtl}
.preview-topbar{justify-content:flex-start;position:relative;z-index:80}.preview-format-menu{position:relative;z-index:1400;min-width:134px}.preview-format-trigger{display:flex;align-items:center;justify-content:space-between;gap:10px;width:100%;min-height:38px;padding:8px 12px;border:1px solid var(--glass-border);border-radius:999px;background:linear-gradient(180deg,rgba(255,255,255,.1),rgba(255,255,255,.025)),rgba(5,5,5,.26);color:var(--color-text-soft);font-weight:800}.preview-format-trigger:after{content:"";width:7px;height:7px;border-right:1px solid currentColor;border-bottom:1px solid currentColor;transform:rotate(45deg) translateY(-2px);opacity:.72}.preview-format-trigger[aria-expanded=true]{border-color:rgba(17,162,207,.72);color:var(--color-brand-blue)}.preview-format-options{position:absolute;top:calc(100% + 7px);left:0;z-index:1500;display:grid;gap:4px;width:max(100%,160px);padding:7px;border:1px solid var(--glass-border);border-radius:8px;background:#101010;box-shadow:var(--shadow-panel)}.preview-format-options[hidden]{display:none}.preview-format-options button{display:flex;justify-content:flex-start;min-height:32px;padding:7px 9px;border:1px solid transparent;border-radius:6px;background:transparent;color:var(--color-text-soft);font-weight:700;text-align:left}.preview-format-options button.active{border-color:rgba(17,162,207,.52);background:rgba(17,162,207,.14);color:var(--color-brand-blue)}
.preview-motion-control{display:flex;align-items:center;gap:7px;min-height:38px;padding:7px 10px;border:1px solid var(--glass-border);border-radius:999px;background:linear-gradient(180deg,rgba(255,255,255,.08),rgba(255,255,255,.02)),rgba(5,5,5,.22);color:var(--color-text-muted);font-size:11px;font-weight:800;white-space:nowrap}.preview-motion-control input{width:82px;accent-color:var(--color-brand-blue)}
.clip-summary{grid-template-columns:auto minmax(0,1fr) auto;align-items:start;gap:10px 12px;cursor:pointer}.clip-status{grid-column:3;grid-row:1;align-self:start}.clip-row-timeline{grid-column:2/4;width:100%;min-width:0;height:36px;min-height:36px;padding:0;cursor:default}.clip-row-timeline.preview-camera-timeline{display:block;align-items:initial}.card[open]{overflow:visible}.card[open] .clip-summary{position:relative;overflow:visible;padding:14px 18px 16px;grid-template-columns:auto minmax(0,1fr) auto}.card[open] .clip-row-timeline{grid-column:1/-1;height:auto;min-height:226px}.card[open] .clip-row-timeline.preview-camera-timeline--live{width:calc(100% + 36px);min-height:226px;margin:4px -18px 0;border:0!important;background:transparent!important;box-shadow:none!important;overflow:visible!important;backdrop-filter:none}.card[open] .clip-row-timeline.preview-camera-timeline--live .timeline-shell{min-height:224px;overflow:visible!important;border:0!important;border-radius:0!important;background:linear-gradient(90deg,rgba(255,255,255,.028) 1px,transparent 1px) 0 0/28px 100%,linear-gradient(180deg,rgba(17,162,207,.055),transparent 38%)!important;box-shadow:none!important}.card[open] .clip-row-timeline.preview-camera-timeline--live .timeline-canvas{overflow:visible}.card[open] .clip-row-timeline.preview-camera-timeline--live .playhead-control{z-index:12}.card[open] .clip-row-timeline.preview-camera-timeline--live .trim-handle,.card[open] .clip-row-timeline.preview-camera-timeline--live .trim-handle:hover,.card[open] .clip-row-timeline.preview-camera-timeline--live .trim-handle:focus-visible,.card[open] .clip-row-timeline.preview-camera-timeline--live .trim-handle.is-dragging{z-index:10!important;padding:0!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;transform:none!important}.card:not([open]) .clip-row-timeline.preview-camera-timeline{overflow:hidden}.card:not([open]) .clip-row-timeline .preview-camera-popover,.card:not([open]) .clip-row-timeline .volume-popover{display:none!important}
.media{border:1px solid rgba(255,255,255,.08);border-radius:var(--radius-panel);background:#000;box-shadow:0 14px 44px rgba(0,0,0,.32)}
.tool-section,.export-dock,.overlay-menu,.settings-panel{border-color:var(--glass-border);border-radius:var(--radius-panel);background:linear-gradient(160deg,rgba(255,255,255,.08),rgba(255,255,255,.025) 36%,rgba(0,0,0,.08) 100%),var(--glass-bg-strong);box-shadow:var(--glass-shadow),inset 0 1px 0 var(--glass-edge),inset 0 -18px 28px rgba(0,0,0,.14);backdrop-filter:blur(24px) saturate(1.45)}
.tool-section>summary{color:rgba(231,231,232,.9)}.export-dock{padding:14px}.export-dock span{color:rgba(231,231,232,.6)}
.timeline-scrub-track,.timeline-track{border-color:rgba(231,231,232,.12);background:linear-gradient(90deg,rgba(17,162,207,.18),rgba(231,231,232,.08))}
.timeline-selected{background:rgba(17,162,207,.2)}.timeline-playhead,.timeline-playhead:before,.timeline-fill{background:var(--color-brand-white)}
button[data-action=like],.import-panel button[type=submit],#finalize-videos,.import-result a,.result-actions a,.result-actions button{background:var(--color-brand-white);color:var(--color-brand-black);border-color:var(--color-brand-white);font-weight:800}
button[data-action=discard],.result-actions a.secondary,.result-actions button.secondary{background:rgba(231,231,232,.07);color:rgba(231,231,232,.76);border-color:var(--glass-border)}
.import-panel input,.import-panel select,.import-panel textarea,.camera-card-controls select,.caption-settings select,.caption-settings input,.overlay-inspector input[type=text],.overlay-inspector input[type=number],.settings-form input,.settings-form select{border-color:var(--glass-border);border-radius:var(--radius-panel);background:rgba(5,5,5,.72);color:var(--color-text)}
.duration-profile span,.camera-path-editor,.camera-segment,.layer-chip,.overlay-layer-row,.image-upload{border-color:var(--glass-border);background:rgba(231,231,232,.05)}
.duration-profile input:checked+span,.layer-chip.is-selected{border-color:rgba(17,162,207,.72);background:var(--control-active);color:var(--color-text)}
.camera-path-rail{background:linear-gradient(90deg,rgba(17,162,207,.28),rgba(231,231,232,.1),rgba(175,207,42,.18))}.camera-path-marker{border-color:var(--glass-border);background:linear-gradient(180deg,rgba(255,255,255,.14),rgba(255,255,255,.035)),rgba(231,231,232,.12);box-shadow:inset 0 1px 0 rgba(255,255,255,.32),0 6px 14px rgba(0,0,0,.26)}.camera-path-marker.active{background:var(--color-brand-blue);border-color:rgba(17,162,207,.88);box-shadow:0 0 0 4px rgba(17,162,207,.16),0 0 24px rgba(17,162,207,.26)}
.preview-camera-marker span,.camera-path-marker span{position:absolute;left:50%;bottom:calc(100% + 4px);max-width:72px;padding:2px 5px;border:1px solid rgba(231,231,232,.2);border-radius:999px;background:rgba(5,5,5,.82);color:var(--color-text-soft);font-size:10px;line-height:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transform:translateX(-50%);pointer-events:none}.camera-path-marker{overflow:visible}.preview-camera-marker{overflow:visible}.camera-path-marker span{bottom:calc(100% + 5px)}.preview-camera-marker.active span,.camera-path-marker.active span{border-color:rgba(17,162,207,.7);color:#fff}
.preview-camera-popover{overflow:hidden}.preview-camera-popover--live{gap:7px;padding:11px;border-color:rgba(17,162,207,.42);border-radius:12px;background:radial-gradient(circle at 26% 0,rgba(17,162,207,.26),transparent 36%),linear-gradient(135deg,rgba(231,231,232,.16),transparent 32%),rgba(7,7,7,.86);box-shadow:inset 0 1px rgba(255,255,255,.22),inset 0 -1px rgba(0,0,0,.62),0 22px 58px rgba(0,0,0,.58),0 0 36px rgba(17,162,207,.24);backdrop-filter:blur(24px) saturate(1.28);animation:preview-camera-popover-in 220ms cubic-bezier(.2,.9,.2,1)}.preview-camera-popover-aura,.preview-camera-popover-lens,.preview-camera-popover-beam{position:absolute;pointer-events:none}.preview-camera-popover-aura{inset:-34px;background:conic-gradient(from 140deg,transparent,rgba(17,162,207,.24),transparent 42%),radial-gradient(circle at 76% 18%,rgba(175,207,42,.16),transparent 20%);opacity:.48;animation:preview-camera-popover-orbit 5.2s linear infinite}.preview-camera-popover-lens{right:10px;top:12px;width:50px;height:50px;border:1px solid rgba(231,231,232,.12);border-radius:50%;background:radial-gradient(circle at 36% 30%,rgba(255,255,255,.24),transparent 28%),radial-gradient(circle,rgba(17,162,207,.16),transparent 68%);opacity:.64}.preview-camera-popover-beam{left:50%;bottom:-34px;width:2px;height:34px;background:linear-gradient(180deg,rgba(17,162,207,.9),transparent);box-shadow:0 0 18px rgba(17,162,207,.54)}.preview-camera-popover-head,.preview-camera-popover label,.preview-camera-popover small,.preview-camera-popover-actions,.preview-camera-popover-meter,.preview-camera-popover-primary{position:relative;z-index:1}.preview-camera-popover-head{display:grid;grid-template-columns:1fr auto auto;gap:7px;align-items:center}.preview-camera-popover-head strong{font-size:12px;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-shadow:0 0 16px rgba(17,162,207,.36)}.preview-camera-popover-head span,.preview-camera-popover small{color:rgba(231,231,232,.64);font-size:11px}.preview-camera-popover-close{display:inline-grid!important;place-items:center;width:22px!important;height:22px!important;min-width:22px!important;min-height:22px!important;padding:0!important;border-radius:999px!important;background:rgba(231,231,232,.08)!important}.preview-camera-popover label{gap:4px;font-size:11px;text-transform:none}.preview-camera-popover select{min-height:31px;padding:6px 8px;border-color:rgba(17,162,207,.34);background:rgba(0,0,0,.56)}.preview-camera-popover input{height:18px}.preview-camera-popover-meter{overflow:hidden;height:6px;margin:1px 0 2px;border-radius:999px;background:rgba(0,0,0,.28);box-shadow:inset 0 0 10px rgba(0,0,0,.58)}.preview-camera-popover-meter i{position:relative;display:block;height:100%;border-radius:inherit;background:linear-gradient(90deg,var(--color-brand-blue),rgba(231,231,232,.9));box-shadow:0 0 16px rgba(17,162,207,.52);animation:preview-camera-meter-breathe 1.8s ease-in-out infinite}.preview-camera-popover-meter i::after{position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,.52),transparent);content:"";transform:translateX(-110%);animation:preview-camera-meter-scan 2.4s ease-in-out infinite}.preview-camera-popover-actions{display:grid;grid-template-columns:1fr auto;gap:7px;align-items:center}.preview-camera-popover button{min-height:31px}.preview-camera-popover-primary{border-color:rgba(17,162,207,.56)!important;background:linear-gradient(180deg,rgba(17,162,207,.34),rgba(17,162,207,.12))!important;color:var(--color-text)!important;font-weight:900}.preview-camera-popover-danger{min-width:70px;color:#ff8f8f!important;border-color:rgba(255,111,111,.32)!important;background:linear-gradient(180deg,rgba(255,111,111,.12),rgba(255,111,111,.04))!important}.preview-camera-popover-danger:disabled{opacity:.42}.preview-camera-popover--portal{position:fixed!important;z-index:3200!important;width:min(236px,calc(100vw - 16px))!important;max-width:calc(100vw - 16px);transform:none!important}@keyframes preview-camera-popover-in{from{opacity:0;transform:translateY(12px) scale(.94);filter:blur(6px)}to{opacity:1;transform:translateY(0) scale(1);filter:blur(0)}}@keyframes preview-camera-popover-orbit{to{transform:rotate(360deg)}}@keyframes preview-camera-meter-breathe{0%,100%{filter:brightness(.94)}50%{filter:brightness(1.18)}}@keyframes preview-camera-meter-scan{0%,18%{transform:translateX(-110%)}58%,100%{transform:translateX(130%)}}
.preview-volume-group{z-index:2300}.preview-volume-popover{z-index:2600!important;width:44px!important;min-width:44px!important;height:120px!important;padding:10px 6px!important;overflow:visible}.preview-volume-slider{width:92px!important;max-width:92px}.preview-ai-button{display:inline-grid;place-items:center;min-width:42px;height:32px;padding:0 12px;border:1px solid rgba(17,162,207,.72);border-radius:999px;background:linear-gradient(180deg,rgba(17,162,207,.28),rgba(17,162,207,.1));color:var(--color-text);font-weight:900;letter-spacing:0}.preview-ai-button:disabled{opacity:.62;cursor:progress}.preview-ai-status{min-height:16px;width:100%;color:rgba(231,231,232,.62);font-size:12px;line-height:1.25;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.overlay-menu button,.overlay-layer-row button{background:rgba(231,231,232,.08);color:rgba(231,231,232,.8);border-color:var(--glass-border)}
.overlay-danger{background:rgba(80,20,20,.72)!important;border-color:rgba(255,120,120,.46)!important;color:#ffd2d2!important}
.settings-status,.settings-usage{border-color:var(--glass-border);background:rgba(231,231,232,.05)}.settings-backdrop{backdrop-filter:blur(14px)}
.result-item{border-color:var(--glass-border);background:rgba(9,9,9,.82)}.result-item[open]{border-color:rgba(231,231,232,.25)}
.result-body video{border:1px solid rgba(255,255,255,.08);border-radius:var(--radius-panel)}
.tabs{display:none!important}header{grid-template-columns:minmax(120px,1fr) auto minmax(240px,1fr);padding:14px 26px 16px}.brand-logo{width:min(560px,52vw);height:84px}.header-actions{align-items:center}.header-actions #finalize-videos{padding-inline:18px}.clip-summary{grid-template-columns:auto minmax(220px,1fr) minmax(560px,760px);align-items:center;gap:10px 14px;min-height:104px;padding:12px 18px;overflow:visible}.clip-rank{align-self:center;font-size:13px;letter-spacing:.08em}.clip-title strong{font-size:16px;letter-spacing:0}.clip-title small{font-size:12px}.clip-control-surface{grid-column:3;grid-row:1;display:flex!important;justify-content:flex-end;width:100%;min-width:0;margin:0!important}.clip-control-surface:empty{display:none!important}.clip-control-surface .cuted-control-bar{width:min(100%,760px);min-width:0;min-height:82px;padding:7px 12px;border-radius:16px}.clip-control-surface .cuted-render-zone{min-height:64px;justify-content:flex-end;overflow:visible}.clip-control-surface .cuted-tool-group{flex:0 1 354px;min-height:64px}.clip-control-surface .cuted-tile-button{flex:0 0 58px;width:58px;height:54px;font-size:26px}.clip-control-surface .cuted-insert-button span{font-size:18px}.clip-control-surface .cuted-format-trigger{flex:0 0 104px;width:104px;height:54px;gap:7px;padding:6px 8px}.clip-control-surface .cuted-format-copy small{display:none}.clip-control-surface .cuted-format-copy strong{font-size:18px}.clip-control-surface .cuted-ratio-vertical{width:14px;height:30px}.clip-control-surface .cuted-ratio-feed{width:20px;height:26px}.clip-control-surface .cuted-ratio-wide{width:29px;height:16px}.clip-control-surface .cuted-divider{height:42px;margin:0 6px}.clip-control-surface .cuted-audio-group{flex:0 0 52px;min-width:52px}.clip-control-surface .cuted-ready-region{flex:0 0 116px;width:116px;min-height:54px;margin-left:auto}.clip-control-surface .cuted-approve-button{width:52px;height:52px}.clip-control-surface .cuted-approve-button svg{width:31px;height:31px}.clip-control-surface .cuted-discard-button{width:40px;height:40px}.clip-row-timeline{grid-column:1/-1;grid-row:2;width:100%;min-width:0;height:34px;min-height:34px;margin-top:2px}.card[open] .clip-summary{grid-template-columns:auto minmax(220px,1fr) minmax(560px,760px);align-items:center;padding:14px 18px 16px}.card[open] .clip-row-timeline{grid-column:1/-1;grid-row:2}.card[open] .clip-row-timeline.preview-camera-timeline--live{width:calc(100% + 36px);margin:6px -18px 0}.editor-shell{display:grid;grid-template-columns:1fr;padding:0 18px 22px}.editor-preview{justify-items:center}.preview-frame{width:100%;justify-items:center;max-width:100%}.card[data-preview-format=tiktok] .preview-frame,.card[data-preview-format=shorts] .preview-frame,.card[data-preview-format=instagram] .preview-frame{max-width:100%}.card[data-preview-format=facebook] .preview-frame,.card[data-preview-format=youtube] .preview-frame{max-width:100%}.media{width:min(100%,calc(72vh * 9 / 16));max-width:520px;max-height:72vh}.card[data-preview-format=facebook] .media{width:min(100%,calc(72vh * 4 / 5));max-width:560px}.card[data-preview-format=youtube] .media{width:min(100%,920px);max-width:920px}.edit-hidden-hooks{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}.preview-bar,.editor-tools,.tool-stack,.tool-section,.export-dock,.clip-status{display:none!important}@media(max-width:1120px){.clip-summary,.card[open] .clip-summary{grid-template-columns:auto minmax(0,1fr);align-items:start}.clip-control-surface{grid-column:1/-1;grid-row:2;justify-content:center}.clip-row-timeline{grid-row:3}.clip-control-surface .cuted-control-bar{width:min(100%,760px)}}@media(max-width:860px){header{grid-template-columns:1fr;padding:12px}.brand-logo{width:min(420px,90vw);height:70px}.clip-summary,.card[open] .clip-summary{grid-template-columns:auto minmax(0,1fr);padding:12px}.clip-control-surface{grid-column:1/-1;grid-row:2}.clip-row-timeline{grid-column:1/-1;grid-row:3}.clip-control-surface .cuted-control-bar{width:100%;min-height:80px;padding:7px 9px}.editor-shell{padding:0 12px 16px}.media{max-height:none;width:100%;max-width:min(100%,520px)}}
@supports not (backdrop-filter:blur(1px)){.preview-bar,.preview-controls,.tool-section,.export-dock,.overlay-menu,header,.tabs{background:#111}}
@media(max-width:860px){.brand-logo{width:min(360px,86vw);height:58px}.tabs{justify-content:flex-start}.tabs button{min-width:auto}.preview-bar{padding:8px}.preview-controls{grid-template-columns:1fr;max-width:100%;justify-content:stretch}.preview-transport-group{justify-self:center}.preview-camera-timeline{width:100%}.preview-volume-group{flex-wrap:nowrap}}
@media(max-width:860px){body{overflow-x:hidden}.brand-logo{width:min(420px,90vw);height:70px}.card[open] .clip-row-timeline{grid-row:3}.card[open] .clip-row-timeline.preview-camera-timeline--live{width:100%;margin:6px 0 0}.clip-control-surface .cuted-format-menu{left:auto;right:0;width:min(300px,calc(100vw - 48px))}.clip-control-surface .cuted-format-option{width:100%}}
body{position:relative;background:linear-gradient(180deg,#050505 0%,#070907 58%,#050505 100%);background-attachment:fixed}body::before{position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(circle at 16% 8%,rgba(17,162,207,.22),transparent 30%),radial-gradient(circle at 88% 38%,rgba(175,207,42,.19),transparent 34%);content:"";opacity:.72;animation:cuted-edit-bg-breathe 22s ease-in-out infinite}header,main,.empty-project-stage,.settings-backdrop,.app-notice{position:relative;z-index:1}@keyframes cuted-edit-bg-breathe{0%,100%{opacity:.5}50%{opacity:.82}}header{padding:18px 26px 2px!important;background:transparent!important;border-bottom:0!important;box-shadow:none!important}.brand-lockup{gap:1px}.brand-logo{width:min(672px,62vw);height:101px;transform:translateY(4px)}.brand-lockup p{display:none!important}.tabs{border-bottom:0!important}main{padding-top:0}.card,.card[open]{border:0!important;background:transparent!important;box-shadow:none!important;overflow:visible}.clip-summary,.card[open] .clip-summary{grid-template-columns:1fr;align-items:stretch;gap:0;min-height:0;padding:0;overflow:visible}.clip-control-surface{grid-column:1/-1;grid-row:1;display:block!important;width:100%;min-width:0;margin:0!important}.clip-control-surface:empty{display:none!important}.clip-control-surface .cuted-control-bar{width:100%;max-width:none;min-width:0;min-height:88px;margin:0;padding:7px 12px 7px 18px;border-radius:16px}.clip-control-surface .cuted-clip-info{flex:0 1 30%;max-width:30%;min-width:0;padding-right:10px}.clip-control-surface .cuted-clip-copy,.clip-control-surface .cuted-clip-copy strong,.clip-control-surface .cuted-clip-copy small{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.clip-control-surface .cuted-render-zone{flex:1 1 auto;min-width:0;min-height:64px;justify-content:flex-end;overflow:visible}.clip-control-surface .cuted-tool-group{flex:0 1 354px;min-height:64px}.clip-control-surface .cuted-tile-button{flex:0 0 58px;width:58px;height:54px;font-size:26px}.clip-control-surface .cuted-format-trigger{flex:0 0 104px;width:104px;height:54px}.clip-control-surface .cuted-audio-group{flex:0 0 52px;min-width:52px}.clip-control-surface .cuted-divider{height:42px;margin:0 6px}.clip-row-timeline,.clip-row-timeline.preview-camera-timeline{display:none!important}.card[open] .clip-row-timeline,.card[open] .clip-row-timeline.preview-camera-timeline{display:block!important;grid-column:1/-1;grid-row:2;margin-top:0}.card[open] .clip-row-timeline.preview-camera-timeline--live{width:100%;margin:-12px 0 0}.editor-shell{display:grid;grid-template-columns:1fr;padding:0 0 16px;margin-top:-18px}.editor-preview{gap:0}.preview-frame{gap:0}@media(max-width:1120px){.clip-control-surface .cuted-control-bar{flex-wrap:wrap;gap:10px}.clip-control-surface .cuted-clip-info{flex:0 1 100%;max-width:100%}.clip-control-surface .cuted-render-zone{flex:1 1 auto}.card[open] .clip-row-timeline{grid-row:2}}@media(max-width:860px){.clip-control-surface .cuted-control-bar{min-height:80px;padding:10px}.card[open] .clip-row-timeline.preview-camera-timeline--live{width:100%;margin:-12px 0 0}}
.brand-logo{transform:translateY(-16px)}.clip-control-surface .cuted-render-zone{justify-content:flex-end;padding-left:clamp(96px,12vw,190px);gap:14px}.clip-control-surface .cuted-ready-region{flex:0 0 116px;width:116px;min-height:54px;margin-left:14px}.clip-control-surface .cuted-tool-group{flex:0 0 354px}.clip-control-surface .cuted-tool-buttons{justify-content:flex-end}.clip-control-surface .cuted-format-trigger{flex:0 0 132px;width:132px;height:58px;gap:8px;padding:6px 10px}.clip-control-surface .cuted-format-copy small{display:block;font-size:10px;line-height:1.05}.clip-control-surface .cuted-format-copy strong{font-size:18px}.clip-control-surface .cuted-ratio-vertical{width:14px;height:30px}.clip-control-surface .cuted-ratio-feed{width:20px;height:26px}.clip-control-surface .cuted-ratio-wide{width:29px;height:16px}
.clip-control-surface{position:relative;z-index:2600}.clip-control-surface .cuted-control-bar{position:relative;z-index:2600;overflow:visible}.clip-control-surface .cuted-effect-menu,.clip-control-surface .cuted-insert-menu,.clip-control-surface .cuted-caption-menu,.clip-control-surface .cuted-format-menu,.clip-control-surface .cuted-volume-popover{z-index:3200}.card[open] .clip-row-timeline.preview-camera-timeline--live{position:relative;z-index:1}
.header-actions{gap:10px;align-items:center}.header-actions .header-icon-button,#reset-ui.header-icon-button,#finalize-videos.header-icon-button,#open-settings.header-icon-button{position:relative;display:inline-grid;place-items:center;width:52px;height:52px;min-width:52px;padding:0!important;border:1px solid rgba(231,231,232,.18)!important;border-radius:16px;background:linear-gradient(180deg,rgba(255,255,255,.11),rgba(255,255,255,.025)),rgba(8,9,10,.52)!important;color:rgba(231,231,232,.8)!important;box-shadow:inset 0 1px rgba(255,255,255,.15),0 14px 34px rgba(0,0,0,.3);backdrop-filter:blur(18px) saturate(1.2);overflow:hidden}.header-actions .header-icon-button:before{position:absolute;inset:7px;border-radius:12px;background:radial-gradient(circle at 50% 22%,rgba(17,162,207,.16),transparent 62%);opacity:.64;content:"";transition:opacity .18s ease,transform .18s ease}.header-actions .header-icon-button svg{position:relative;z-index:1;width:28px;height:28px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}.header-actions .header-icon-button:hover,.header-actions .header-icon-button:focus-visible{border-color:rgba(17,162,207,.58)!important;color:var(--color-text)!important;box-shadow:inset 0 1px rgba(255,255,255,.2),0 0 24px rgba(17,162,207,.22),0 16px 38px rgba(0,0,0,.34)}.header-actions .header-icon-button:hover:before,.header-actions .header-icon-button:focus-visible:before{opacity:1;transform:scale(1.08)}.header-actions .header-render-button,#finalize-videos.header-render-button{width:58px;height:58px;min-width:58px;border-color:rgba(175,207,42,.48)!important;color:var(--color-brand-green)!important;background:linear-gradient(180deg,rgba(175,207,42,.18),rgba(17,162,207,.065)),rgba(12,14,9,.7)!important;box-shadow:inset 0 1px rgba(255,255,255,.2),0 0 24px rgba(175,207,42,.22),0 16px 38px rgba(0,0,0,.36)}.header-actions .header-render-button:before{background:radial-gradient(circle at 58% 25%,rgba(175,207,42,.28),transparent 60%),radial-gradient(circle at 32% 70%,rgba(17,162,207,.12),transparent 56%)}.header-actions .header-render-button svg{width:32px;height:32px;stroke-width:1.85}.header-actions .header-render-button.is-rendering,#finalize-videos.header-render-button.is-rendering{border-color:rgba(175,207,42,.78)!important;color:var(--color-brand-green)!important;box-shadow:inset 0 1px rgba(255,255,255,.24),0 0 28px rgba(175,207,42,.34),0 0 42px rgba(17,162,207,.14),0 16px 38px rgba(0,0,0,.36);animation:cuted-render-button-pulse 1.65s ease-in-out infinite}.header-actions .header-render-button.is-rendering:before,#finalize-videos.header-render-button.is-rendering:before{opacity:1;transform:scale(1.12);animation:cuted-render-button-scan 1.4s ease-in-out infinite}.header-actions .header-render-button.is-rendering svg,#finalize-videos.header-render-button.is-rendering svg{animation:cuted-render-icon-drift 1.9s ease-in-out infinite;filter:drop-shadow(0 0 9px rgba(175,207,42,.42))}.header-actions .header-settings-button svg{width:26px;height:26px}.header-actions .header-new-project svg{width:29px;height:29px}#open-settings.header-settings-button.is-openai-ready{border-color:rgba(175,207,42,.62)!important;color:var(--color-brand-green)!important;background:linear-gradient(180deg,rgba(175,207,42,.2),rgba(17,162,207,.055)),rgba(10,14,8,.7)!important;box-shadow:inset 0 1px rgba(255,255,255,.2),0 0 24px rgba(175,207,42,.26),0 16px 38px rgba(0,0,0,.36)}#open-settings.header-settings-button.is-openai-ready:before{background:radial-gradient(circle at 50% 34%,rgba(175,207,42,.32),transparent 62%)}#open-settings.header-settings-button.is-openai-ready svg{animation:cuted-openai-gear-spin 5.8s linear infinite;filter:drop-shadow(0 0 8px rgba(175,207,42,.34))}@keyframes cuted-openai-gear-spin{to{transform:rotate(360deg)}}@keyframes cuted-render-button-pulse{0%,100%{filter:brightness(1)}50%{filter:brightness(1.2)}}@keyframes cuted-render-button-scan{0%,100%{opacity:.72;transform:scale(1.04) rotate(0deg)}50%{opacity:1;transform:scale(1.16) rotate(3deg)}}@keyframes cuted-render-icon-drift{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-1px) rotate(9deg)}}
.settings-backdrop{position:fixed!important;inset:0!important;z-index:5000!important;display:grid!important;place-items:center!important;padding:32px;background:radial-gradient(circle at 50% 42%,rgba(17,162,207,.18),transparent 30%),radial-gradient(circle at 64% 58%,rgba(175,207,42,.12),transparent 26%),rgba(0,0,0,.68)!important;backdrop-filter:blur(18px) saturate(1.18)!important;opacity:0;pointer-events:none;transition:opacity 180ms ease}.settings-backdrop[hidden]{display:none!important}.settings-backdrop.is-open{opacity:1;pointer-events:auto}.settings-backdrop.is-closing{opacity:0;pointer-events:none}.settings-panel{position:relative!important;isolation:isolate;width:min(640px,calc(100vw - 48px))!important;max-height:min(760px,calc(100vh - 56px));overflow:hidden auto;padding:20px!important;border:1px solid rgba(17,162,207,.34)!important;border-radius:22px!important;background:linear-gradient(145deg,rgba(231,231,232,.11),rgba(5,5,5,.8) 46%,rgba(11,15,10,.88)),rgba(5,5,5,.92)!important;box-shadow:0 0 0 1px rgba(255,255,255,.055),0 0 42px rgba(17,162,207,.2),0 0 58px rgba(175,207,42,.12),0 32px 86px rgba(0,0,0,.72)!important;transform:translateY(18px) scale(.965);opacity:0;outline:none;transition:transform 210ms cubic-bezier(.2,.9,.2,1),opacity 180ms ease}.settings-backdrop.is-open .settings-panel{transform:translateY(0) scale(1);opacity:1}.settings-backdrop.is-closing .settings-panel{transform:translateY(12px) scale(.975);opacity:0}.settings-aura{position:absolute;inset:-46px;z-index:-1;background:conic-gradient(from 130deg,transparent,rgba(17,162,207,.22),transparent 32%,rgba(175,207,42,.18),transparent 62%);opacity:.54;filter:blur(12px);animation:settings-aura-drift 8s linear infinite}.settings-head{position:relative;display:flex!important;align-items:flex-start!important;justify-content:space-between!important;gap:18px;padding:0 0 16px;border-bottom:1px solid rgba(231,231,232,.1)}.settings-title-row{display:flex;align-items:center;gap:14px;min-width:0}.settings-orb{display:grid;place-items:center;width:52px;height:52px;min-width:52px;border:1px solid rgba(175,207,42,.44);border-radius:16px;background:radial-gradient(circle at 50% 32%,rgba(175,207,42,.22),transparent 62%),rgba(8,11,8,.78);color:var(--color-brand-green);box-shadow:inset 0 1px rgba(255,255,255,.16),0 0 26px rgba(175,207,42,.18)}.settings-orb svg{width:27px;height:27px;fill:none;stroke:currentColor;stroke-width:1.9;animation:cuted-openai-gear-spin 7.2s linear infinite}.settings-head strong{display:block;color:var(--color-text);font-size:22px;line-height:1.05}.settings-head p{margin:5px 0 0!important;color:rgba(231,231,232,.62)!important;font-size:13px;line-height:1.25}.settings-close-button{display:grid!important;place-items:center;width:40px!important;height:40px!important;min-width:40px!important;padding:0!important;border:1px solid rgba(231,231,232,.16)!important;border-radius:14px!important;background:rgba(231,231,232,.06)!important;color:rgba(231,231,232,.75)!important;font-weight:900!important}.settings-close-button:hover,.settings-close-button:focus-visible{border-color:rgba(255,111,111,.42)!important;color:#ff9d9d!important;box-shadow:0 0 22px rgba(255,111,111,.18)}.settings-form{display:grid!important;gap:14px!important;margin-top:16px!important}.settings-status{padding:12px 14px!important;border:1px solid rgba(17,162,207,.26)!important;border-radius:14px!important;background:linear-gradient(90deg,rgba(17,162,207,.12),rgba(175,207,42,.065)),rgba(0,0,0,.3)!important;color:rgba(231,231,232,.82)!important;font-size:13px}.settings-field{display:grid!important;gap:7px!important;color:rgba(231,231,232,.68)!important;font-size:12px!important;font-weight:800;letter-spacing:.01em}.settings-form input,.settings-form select{min-height:44px!important;border:1px solid rgba(231,231,232,.14)!important;border-radius:14px!important;background:rgba(0,0,0,.52)!important;color:var(--color-text)!important;padding:10px 12px!important;box-shadow:inset 0 1px rgba(255,255,255,.05)!important}.settings-form input:focus,.settings-form select:focus{border-color:rgba(17,162,207,.62)!important;outline:none;box-shadow:0 0 0 3px rgba(17,162,207,.16),inset 0 1px rgba(255,255,255,.07)!important}.settings-grid{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:10px!important}.settings-usage{display:grid!important;gap:5px!important;padding:12px 14px!important;border:1px solid rgba(231,231,232,.12)!important;border-radius:14px!important;background:rgba(231,231,232,.045)!important;color:rgba(231,231,232,.6)!important;font-size:12px!important}.settings-usage strong{color:rgba(231,231,232,.86)}.settings-actions{display:flex!important;justify-content:flex-end!important;gap:10px!important;flex-wrap:wrap!important;padding-top:2px}.settings-actions button{min-height:42px!important;border-radius:999px!important;padding:0 18px!important}.settings-actions button[type=submit]{border-color:rgba(175,207,42,.56)!important;background:linear-gradient(90deg,rgba(175,207,42,.95),rgba(17,162,207,.88))!important;color:#050505!important;font-weight:900!important}.settings-actions [data-settings-test]{border-color:rgba(17,162,207,.36)!important;background:rgba(17,162,207,.08)!important;color:var(--color-text)!important}.settings-form small{color:rgba(231,231,232,.5)!important;font-size:11px!important}@keyframes settings-aura-drift{to{transform:rotate(360deg)}}@media(max-width:760px){.settings-backdrop{padding:18px}.settings-panel{width:calc(100vw - 28px)!important;padding:16px!important}.settings-grid{grid-template-columns:1fr!important}.settings-head strong{font-size:20px}}
.settings-panel{scrollbar-width:none}.settings-panel::-webkit-scrollbar{width:0;height:0}
.render-queue-backdrop{position:fixed!important;inset:0!important;z-index:4900!important;display:grid!important;place-items:center!important;padding:32px;background:radial-gradient(circle at 46% 38%,rgba(17,162,207,.18),transparent 30%),radial-gradient(circle at 63% 62%,rgba(175,207,42,.12),transparent 28%),rgba(0,0,0,.7)!important;backdrop-filter:blur(18px) saturate(1.18)!important;opacity:0;pointer-events:none;transition:opacity 180ms ease}.render-queue-backdrop[hidden]{display:none!important}.render-queue-backdrop.is-open{opacity:1;pointer-events:auto}.render-queue-backdrop.is-closing{opacity:0;pointer-events:none}.render-queue-panel{position:relative;isolation:isolate;width:min(760px,calc(100vw - 56px));max-height:min(780px,calc(100vh - 56px));overflow:hidden;padding:20px;border:1px solid rgba(17,162,207,.34);border-radius:22px;background:linear-gradient(145deg,rgba(231,231,232,.11),rgba(5,5,5,.82) 46%,rgba(11,15,10,.9)),rgba(5,5,5,.94);box-shadow:0 0 0 1px rgba(255,255,255,.055),0 0 42px rgba(17,162,207,.2),0 0 58px rgba(175,207,42,.12),0 32px 86px rgba(0,0,0,.72);transform:translateY(18px) scale(.965);opacity:0;outline:none;transition:transform 210ms cubic-bezier(.2,.9,.2,1),opacity 180ms ease}.render-queue-backdrop.is-open .render-queue-panel{transform:translateY(0) scale(1);opacity:1}.render-queue-aura{position:absolute;inset:-46px;z-index:-1;background:conic-gradient(from 120deg,transparent,rgba(17,162,207,.2),transparent 34%,rgba(175,207,42,.18),transparent 64%);opacity:.48;filter:blur(12px);animation:settings-aura-drift 8.5s linear infinite}.render-queue-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;padding-bottom:16px;border-bottom:1px solid rgba(231,231,232,.1)}.render-queue-head strong{display:block;font-size:22px;line-height:1.05}.render-queue-head p{margin:5px 0 0;color:rgba(231,231,232,.62);font-size:13px}.render-queue-close{display:grid;place-items:center;width:40px;height:40px;min-width:40px;padding:0;border:1px solid rgba(231,231,232,.16);border-radius:14px;background:rgba(231,231,232,.06);color:rgba(231,231,232,.75);font-weight:900}.render-resource-switch{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:16px 0}.render-resource-switch button{min-height:42px;border:1px solid rgba(231,231,232,.16);border-radius:14px;background:rgba(231,231,232,.055);color:rgba(231,231,232,.74);font-weight:900}.render-resource-switch button.active{border-color:rgba(175,207,42,.58);background:linear-gradient(90deg,rgba(175,207,42,.2),rgba(17,162,207,.08));color:var(--color-text);box-shadow:0 0 22px rgba(175,207,42,.14)}.render-queue-status{min-height:42px;padding:12px 14px;border:1px solid rgba(17,162,207,.26);border-radius:14px;background:linear-gradient(90deg,rgba(17,162,207,.12),rgba(175,207,42,.065)),rgba(0,0,0,.3);color:rgba(231,231,232,.82);font-size:13px}.render-queue-list{display:grid;gap:10px;max-height:min(486px,calc(100vh - 288px));margin-top:12px;overflow:auto;padding-right:4px;scrollbar-width:thin;scrollbar-color:rgba(175,207,42,.55) rgba(255,255,255,.055)}.render-queue-list::-webkit-scrollbar{width:8px}.render-queue-list::-webkit-scrollbar-thumb{border-radius:999px;background:linear-gradient(180deg,rgba(17,162,207,.72),rgba(175,207,42,.72))}.render-job-card{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:center;padding:13px 14px;border:1px solid rgba(231,231,232,.12);border-radius:16px;background:linear-gradient(180deg,rgba(231,231,232,.07),rgba(231,231,232,.025)),rgba(0,0,0,.34)}.render-job-card[data-status=ready]{border-color:rgba(175,207,42,.38)}.render-job-card[data-status=failed],.render-job-card[data-status=cancelled]{border-color:rgba(255,111,111,.36)}.render-job-main{display:grid;gap:7px;min-width:0}.render-job-title{display:flex;gap:8px;align-items:center;min-width:0}.render-job-title strong{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.render-job-pill{display:inline-flex;align-items:center;min-height:22px;padding:3px 8px;border-radius:999px;background:rgba(17,162,207,.12);color:rgba(36,220,255,.9);font-size:11px;font-weight:900;text-transform:uppercase}.render-job-card[data-status=cancelled] .render-job-pill,.render-job-card[data-status=failed] .render-job-pill{background:rgba(255,111,111,.12);color:#ff9d9d}.render-job-meta{color:rgba(231,231,232,.58);font-size:12px}.render-job-progress{position:relative;height:5px;overflow:hidden;border-radius:999px;background:rgba(231,231,232,.1)}.render-job-progress span{position:absolute;inset:0 auto 0 0;width:var(--progress);border-radius:inherit;background:linear-gradient(90deg,var(--color-brand-blue),var(--color-brand-green));box-shadow:0 0 14px rgba(17,162,207,.34)}.render-job-actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;justify-content:flex-end}.render-job-actions button{min-height:34px;padding:7px 11px;border:1px solid rgba(231,231,232,.16);border-radius:999px;background:rgba(231,231,232,.07);color:rgba(231,231,232,.82);font-weight:800}.render-job-actions button.primary{border-color:rgba(175,207,42,.52);background:rgba(175,207,42,.14);color:var(--color-brand-green)}.render-job-actions [data-render-cancel],.render-job-actions [data-render-remove]{border-color:rgba(255,111,111,.34);background:rgba(255,111,111,.08);color:#ffb3b3}.render-empty{padding:18px;border:1px dashed rgba(231,231,232,.16);border-radius:16px;color:rgba(231,231,232,.58);text-align:center}
.render-cover-frame-toggle{display:flex;gap:10px;align-items:center;margin:-4px 0 14px;padding:10px 12px;border:1px solid rgba(231,231,232,.13);border-radius:14px;background:rgba(231,231,232,.045);color:rgba(231,231,232,.82);cursor:pointer}.render-cover-frame-toggle input{width:18px;height:18px;accent-color:var(--color-brand-green)}.render-cover-frame-toggle span{display:grid;gap:2px}.render-cover-frame-toggle strong{font-size:13px}.render-cover-frame-toggle small{color:rgba(231,231,232,.54);font-size:11px;line-height:1.25}
.workspace-exit-backdrop{position:fixed!important;inset:0!important;z-index:4950!important;display:grid!important;place-items:center!important;padding:32px;background:radial-gradient(circle at 45% 38%,rgba(17,162,207,.18),transparent 30%),radial-gradient(circle at 62% 62%,rgba(175,207,42,.12),transparent 28%),rgba(0,0,0,.72)!important;backdrop-filter:blur(18px) saturate(1.18)!important;opacity:0;pointer-events:none;transition:opacity 180ms ease}.workspace-exit-backdrop[hidden]{display:none!important}.workspace-exit-backdrop.is-open{opacity:1;pointer-events:auto}.workspace-exit-backdrop.is-closing{opacity:0;pointer-events:none}.workspace-exit-panel{position:relative;isolation:isolate;width:min(620px,calc(100vw - 48px));overflow:hidden;padding:20px;border:1px solid rgba(17,162,207,.34);border-radius:22px;background:linear-gradient(145deg,rgba(231,231,232,.11),rgba(5,5,5,.83) 46%,rgba(11,15,10,.9)),rgba(5,5,5,.94);box-shadow:0 0 0 1px rgba(255,255,255,.055),0 0 42px rgba(17,162,207,.2),0 0 58px rgba(175,207,42,.12),0 32px 86px rgba(0,0,0,.72);transform:translateY(18px) scale(.965);opacity:0;outline:none;transition:transform 210ms cubic-bezier(.2,.9,.2,1),opacity 180ms ease}.workspace-exit-backdrop.is-open .workspace-exit-panel{transform:translateY(0) scale(1);opacity:1}.workspace-exit-aura{position:absolute;inset:-46px;z-index:-1;background:conic-gradient(from 120deg,transparent,rgba(17,162,207,.2),transparent 34%,rgba(175,207,42,.18),transparent 64%);opacity:.48;filter:blur(12px);animation:settings-aura-drift 8.5s linear infinite}.workspace-exit-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;padding-bottom:16px;border-bottom:1px solid rgba(231,231,232,.1)}.workspace-exit-head strong{display:block;font-size:22px;line-height:1.05}.workspace-exit-head p,.workspace-exit-body p{margin:5px 0 0;color:rgba(231,231,232,.62);font-size:13px;line-height:1.35}.workspace-exit-body{display:grid;gap:8px;padding:16px 0}.workspace-exit-close{display:grid;place-items:center;width:40px;height:40px;min-width:40px;padding:0;border:1px solid rgba(231,231,232,.16);border-radius:14px;background:rgba(231,231,232,.06);color:rgba(231,231,232,.75);font-weight:900}.workspace-exit-actions{display:flex;justify-content:flex-end;gap:10px;flex-wrap:wrap}.workspace-exit-actions button{min-height:42px;border-radius:999px;padding:0 18px;border:1px solid rgba(231,231,232,.16);background:rgba(231,231,232,.07);color:rgba(231,231,232,.82);font-weight:900}.workspace-exit-actions button.primary{border-color:rgba(175,207,42,.56);background:var(--color-brand-white);color:var(--color-brand-black)}
.header-actions{position:absolute;right:26px;top:50%;display:flex;justify-content:flex-end;align-items:center;gap:10px;width:auto;margin:0;transform:translateY(-50%)}header{grid-template-columns:1fr!important;justify-items:center;padding:18px 26px 2px!important}.header-actions .header-icon-button,#reset-ui.header-icon-button,#finalize-videos.header-icon-button,#open-settings.header-icon-button{width:56px!important;height:56px!important;min-width:56px!important;border-color:rgba(17,162,207,.42)!important;background:linear-gradient(145deg,rgba(17,162,207,.16),rgba(175,207,42,.08) 48%,rgba(5,5,5,.84)),rgba(5,5,5,.88)!important;color:var(--color-text)!important;box-shadow:inset 0 1px rgba(255,255,255,.12),0 0 18px rgba(17,162,207,.12),0 14px 34px rgba(0,0,0,.36)!important;transition:transform 170ms ease,border-color 170ms ease,box-shadow 170ms ease,color 170ms ease!important}.header-actions .header-icon-button:before,#finalize-videos.header-render-button:before,#open-settings.header-settings-button.is-openai-ready:before{background:radial-gradient(circle at 45% 22%,rgba(17,162,207,.24),transparent 58%),radial-gradient(circle at 70% 72%,rgba(175,207,42,.18),transparent 62%)!important;opacity:.66!important;transition:opacity 170ms ease,transform 170ms ease!important}.header-actions .header-icon-button:hover,.header-actions .header-icon-button:focus-visible{border-color:rgba(175,207,42,.7)!important;color:var(--color-text)!important;box-shadow:inset 0 1px rgba(255,255,255,.16),0 0 24px rgba(17,162,207,.24),0 0 26px rgba(175,207,42,.16),0 18px 40px rgba(0,0,0,.42)!important;transform:translateY(-2px) scale(1.035)}.header-actions .header-icon-button:hover:before,.header-actions .header-icon-button:focus-visible:before{opacity:1!important;transform:scale(1.12) rotate(2deg)!important}.header-actions .header-render-button,#finalize-videos.header-render-button{width:56px!important;height:56px!important;min-width:56px!important;animation:none!important}.header-actions .header-render-button svg,#finalize-videos.header-render-button svg{width:30px;height:30px;stroke-width:1.85;animation:none!important;filter:none!important}#open-settings.header-settings-button.is-openai-ready{border-color:rgba(17,162,207,.42)!important;background:linear-gradient(145deg,rgba(17,162,207,.16),rgba(175,207,42,.08) 48%,rgba(5,5,5,.84)),rgba(5,5,5,.88)!important;color:var(--color-text)!important;box-shadow:inset 0 1px rgba(255,255,255,.12),0 0 18px rgba(17,162,207,.12),0 14px 34px rgba(0,0,0,.36)!important}#open-settings.header-settings-button.is-openai-ready svg{animation:cuted-openai-gear-spin 5.8s linear infinite;filter:drop-shadow(0 0 8px rgba(175,207,42,.24))}.header-actions .header-render-button.is-rendering,#finalize-videos.header-render-button.is-rendering{border-color:rgba(175,207,42,.78)!important;background:linear-gradient(180deg,rgba(175,207,42,.2),rgba(17,162,207,.065)),rgba(12,14,9,.72)!important;color:var(--color-brand-green)!important;box-shadow:inset 0 1px rgba(255,255,255,.24),0 0 28px rgba(175,207,42,.34),0 0 42px rgba(17,162,207,.14),0 16px 38px rgba(0,0,0,.36)!important;animation:cuted-render-button-pulse 1.65s ease-in-out infinite!important}.header-actions .header-render-button.is-rendering:before,#finalize-videos.header-render-button.is-rendering:before{background:radial-gradient(circle at 58% 25%,rgba(175,207,42,.28),transparent 60%),radial-gradient(circle at 32% 70%,rgba(17,162,207,.12),transparent 56%)!important;opacity:1!important;transform:scale(1.12);animation:cuted-render-button-scan 1.4s ease-in-out infinite}.header-actions .header-render-button.is-rendering svg,#finalize-videos.header-render-button.is-rendering svg{animation:cuted-render-icon-drift 1.9s ease-in-out infinite!important;filter:drop-shadow(0 0 9px rgba(175,207,42,.42))!important}@media(max-width:1080px){.header-actions{position:static;justify-content:center;width:100%;margin:0;transform:none}.brand-logo{width:min(520px,88vw)}header{grid-template-columns:1fr!important;gap:8px;padding:12px!important}}@media(max-width:860px){.header-actions{justify-content:center;width:100%;margin:0;transform:none}header{grid-template-columns:1fr!important;padding:12px!important}}
.clip-control-surface .cuted-render-zone.is-ready .cuted-ready-region{flex:0 0 46px;width:46px;min-width:46px}.clip-control-surface .cuted-render-zone.is-ready .cuted-ready-pill{width:46px}
.card[open] .editor-shell{grid-template-columns:minmax(210px,260px) minmax(340px,1fr) minmax(260px,330px);gap:14px;align-items:start;padding:0 18px 18px;margin-top:-10px}.card[open] .editor-preview{grid-column:2}.publish-panel{display:grid;gap:10px;align-content:start;min-width:0;max-height:72vh;overflow:auto;padding:12px;border:1px solid rgba(231,231,232,.12);border-radius:12px;background:linear-gradient(180deg,rgba(231,231,232,.075),rgba(231,231,232,.025)),rgba(5,5,5,.52);box-shadow:inset 0 1px rgba(255,255,255,.08),0 12px 34px rgba(0,0,0,.24);backdrop-filter:blur(16px) saturate(1.1)}.publish-panel strong{color:rgba(231,231,232,.72);font-size:11px;letter-spacing:.08em;text-transform:uppercase}.publish-panel h2{margin:0;color:var(--color-text);font-size:17px;line-height:1.18;letter-spacing:0}.publish-panel p{margin:0;color:rgba(231,231,232,.72);font-size:12px;line-height:1.38}.publish-panel small{color:rgba(231,231,232,.5);font-size:11px;line-height:1.34}.publish-cover-frame{position:relative;overflow:hidden;aspect-ratio:9/16;border:1px solid rgba(231,231,232,.1);border-radius:8px;background:#050505}.publish-cover-frame img{display:block;width:100%;height:100%;object-fit:cover}.publish-cover-frame span{display:block;width:100%;height:100%;background:linear-gradient(135deg,rgba(17,162,207,.18),rgba(175,207,42,.08))}.publish-cover-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}.publish-cover-options button{min-height:58px;padding:2px;border:1px solid rgba(231,231,232,.14);border-radius:8px;background:rgba(0,0,0,.38);overflow:hidden}.publish-cover-options button.active{border-color:rgba(175,207,42,.82);box-shadow:0 0 0 2px rgba(175,207,42,.16)}.publish-cover-options img{display:block;width:100%;aspect-ratio:9/16;object-fit:cover;border-radius:5px}.publish-hook{padding:9px 10px;border-left:3px solid rgba(175,207,42,.78);border-radius:8px;background:rgba(175,207,42,.075);color:var(--color-text)!important;font-weight:800}.publish-tags{display:flex;gap:6px;flex-wrap:wrap}.publish-tags span{display:inline-flex;align-items:center;min-height:24px;max-width:100%;padding:4px 7px;border:1px solid rgba(17,162,207,.24);border-radius:999px;background:rgba(17,162,207,.09);color:rgba(231,231,232,.84);font-size:11px;line-height:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}@media(max-width:1180px){.card[open] .editor-shell{grid-template-columns:minmax(0,1fr);margin-top:0}.card[open] .editor-preview{grid-column:1}.publish-panel{max-height:none}.publish-cover-panel{grid-row:2}.publish-copy-panel{grid-row:3}.publish-cover-frame{max-width:180px}}@media(max-width:860px){.card[open] .editor-shell{padding:0 12px 16px}.publish-panel{border-radius:10px}.publish-cover-frame{max-width:150px}}
.card[open] .editor-shell{grid-template-columns:minmax(205px,252px) minmax(340px,calc(72vh * 9 / 16)) minmax(260px,330px);gap:8px;align-items:center;justify-content:center}.card[data-preview-format=facebook][open] .editor-shell{grid-template-columns:minmax(205px,252px) minmax(390px,calc(72vh * 4 / 5)) minmax(260px,330px)}.card[data-preview-format=youtube][open] .editor-shell{grid-template-columns:minmax(205px,252px) minmax(520px,720px) minmax(260px,330px)}.publish-panel{gap:9px;align-content:center;align-self:center;padding:11px}.publish-cover-panel{justify-self:end}.publish-copy-panel{justify-self:start}.publish-panel-head{display:flex;justify-content:space-between;gap:10px;align-items:center}.publish-panel-head button{min-height:26px;padding:4px 8px;border-radius:999px;font-size:11px}.publish-field{display:grid;gap:5px;color:rgba(231,231,232,.62);font-size:11px;font-weight:800;letter-spacing:0}.publish-field input,.publish-field textarea{width:100%;min-height:34px;padding:7px 9px;border:1px solid rgba(231,231,232,.14);border-radius:8px;background:rgba(0,0,0,.42);color:var(--color-text);font:inherit;font-size:12px;line-height:1.28;letter-spacing:0}.publish-field textarea{resize:vertical;min-height:72px}.publish-field input:focus,.publish-field textarea:focus{border-color:rgba(17,162,207,.58);outline:0;box-shadow:0 0 0 2px rgba(17,162,207,.16)}@media(max-width:1180px){.card[open] .editor-shell{grid-template-columns:minmax(0,1fr)}.publish-panel{align-content:start}.publish-cover-panel{justify-self:center}.publish-copy-panel{justify-self:stretch}}
.publish-cover-stage{position:relative}.publish-cover-frame{touch-action:none}.publish-cover-frame[data-publish-cover-can-drag="1"]{cursor:grab}.publish-cover-frame[data-publish-cover-dragging="1"]{cursor:grabbing}.publish-cover-frame>img{user-select:none;-webkit-user-drag:none;transform:scale(var(--publish-cover-zoom,1));transform-origin:var(--publish-cover-x,50%) var(--publish-cover-y,50%);transition:transform 120ms ease;will-change:transform}.publish-cover-frame[data-publish-cover-dragging="1"]>img{transition:none}.publish-cover-layer-list{position:absolute;inset:0;z-index:2;pointer-events:none}.publish-cover-layer{position:absolute;display:grid;align-items:center;min-height:24px;padding:5px 7px;border-radius:6px;color:var(--cover-layer-color,#fff);font-weight:800;line-height:1.05;overflow:hidden;text-overflow:ellipsis;cursor:move;pointer-events:auto;touch-action:none}.publish-cover-layer.is-selected{outline:2px solid var(--color-focus);outline-offset:2px}.publish-cover-layer span{overflow:hidden;text-overflow:ellipsis}.publish-cover-layer[data-cover-layer-kind=text]{background:rgba(var(--cover-layer-bg,0,0,0),var(--cover-layer-bg-opacity,.7))}.publish-cover-layer[data-cover-layer-kind=speech]{border-radius:11px;background:rgba(var(--cover-layer-bg,255,255,255),var(--cover-layer-bg-opacity,.94));box-shadow:0 8px 18px rgba(0,0,0,.22);color:var(--cover-layer-color,#050505);font-weight:900;overflow:visible}.publish-cover-layer[data-cover-layer-kind=speech]:after{position:absolute;left:18%;bottom:-8px;width:15px;height:12px;border-radius:0 0 14px 0;background:inherit;content:"";transform:skewX(-18deg)}.publish-cover-layer[data-cover-layer-kind=image]{padding:0;background:transparent}.publish-cover-layer[data-cover-layer-kind=image] img{display:block;width:100%;height:auto;object-fit:contain;transform:none;transform-origin:center;opacity:var(--cover-layer-opacity,1);pointer-events:none}.publish-cover-resize{position:absolute;right:2px;bottom:2px;width:18px;height:18px;padding:0;border:1px solid rgba(255,255,255,.56);border-radius:5px;background:rgba(0,0,0,.34);cursor:nwse-resize}.publish-cover-adjust{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center}.publish-cover-adjust label{display:grid;grid-template-columns:auto 1fr auto;gap:7px;align-items:center;color:rgba(231,231,232,.62);font-size:11px;font-weight:800;letter-spacing:0}.publish-cover-adjust output{min-width:38px;color:rgba(231,231,232,.84);font-size:11px;text-align:right}.publish-cover-adjust input{width:100%;accent-color:var(--color-brand-green)}.publish-cover-adjust button{min-height:28px;padding:4px 8px;border-radius:999px;font-size:11px}.publish-cover-menu{z-index:7;width:min(320px,96%);max-height:min(380px,calc(100vh - 24px))}
.preview-caption-layer{bottom:var(--preview-caption-bottom,16.25%)}.card[data-preview-format=facebook] .preview-caption-layer{bottom:var(--preview-caption-bottom,8.8%)}.card[data-preview-format=youtube] .preview-caption-layer{bottom:var(--preview-caption-bottom,11%)}.preview-caption-layer[data-mode=animated] .preview-caption-window{display:inline-grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;gap:.54em;width:min(94%,18em);padding:0;border-radius:0;background:transparent;color:var(--preview-caption-color,#fff);font-size:calc(var(--preview-caption-size,28px) * .76);line-height:1;text-shadow:0 2px 8px rgba(0,0,0,.75);-webkit-text-stroke:0;white-space:nowrap;box-decoration-break:slice;-webkit-box-decoration-break:slice;animation:cuted-caption-window-step 190ms cubic-bezier(.2,.9,.2,1)}.preview-caption-layer[data-mode=animated] .preview-caption-word{display:inline-grid;place-items:center;min-width:.56em;max-width:100%;padding:.1em .32em;border-radius:.22em;background:var(--preview-caption-bg,transparent);color:var(--preview-caption-color,#fff);font-size:1em;overflow:hidden;text-overflow:ellipsis;box-decoration-break:slice;-webkit-box-decoration-break:slice}.preview-caption-layer[data-mode=animated] .preview-caption-side{opacity:.72;font-size:.76em;transform:translateY(.1em)}.preview-caption-layer[data-mode=animated] .preview-caption-side:empty{min-width:0;padding:0;background:transparent}.preview-caption-layer[data-mode=animated] .preview-caption-prev{justify-self:end}.preview-caption-layer[data-mode=animated] .preview-caption-next{justify-self:start}.preview-caption-layer[data-mode=animated] .preview-caption-active{justify-self:center;max-width:7.4em;padding:.15em .44em;border-radius:.25em;background:var(--preview-caption-highlight-bg,var(--preview-caption-bg,rgba(0,0,0,.82)));color:var(--preview-caption-color,#fff);font-size:1em;box-shadow:0 8px 22px rgba(0,0,0,.34),0 0 0 1px rgba(255,255,255,.12);animation:cuted-caption-pop 220ms cubic-bezier(.2,.9,.2,1)}@keyframes cuted-caption-pop{0%{opacity:.72;transform:translateY(7px) scale(.88)}64%{opacity:1;transform:translateY(-5px) scale(1.12)}100%{opacity:1;transform:translateY(0) scale(1)}}@keyframes cuted-caption-window-step{0%{transform:translateX(.18em);filter:blur(.8px)}100%{transform:translateX(0);filter:blur(0)}}
.overlay-menu[data-overlay-menu-mode=add]{display:block;width:max-content;min-width:0;max-width:calc(100vw - 28px);max-height:none;overflow:visible;padding:6px;border-radius:999px;background:linear-gradient(135deg,rgba(17,162,207,.16),rgba(175,207,42,.08)),rgba(5,5,5,.9);box-shadow:0 12px 30px rgba(0,0,0,.42),0 0 18px rgba(17,162,207,.18);backdrop-filter:blur(18px) saturate(1.16)}.overlay-menu[data-overlay-menu-mode=add] .overlay-icon-actions{display:flex;gap:6px;align-items:center}.overlay-icon-action{display:grid!important;place-items:center;width:38px;height:38px;min-width:38px;min-height:38px;padding:0!important;border-radius:12px!important;background:rgba(231,231,232,.075)!important;color:rgba(231,231,232,.9)!important;font-size:11px!important;font-weight:950!important;letter-spacing:0!important;line-height:1!important}.overlay-icon-action:hover,.overlay-icon-action:focus-visible{border-color:rgba(175,207,42,.68)!important;color:var(--color-brand-green)!important;box-shadow:0 0 16px rgba(175,207,42,.2)}.overlay-icon-close{width:30px!important;height:30px!important;min-width:30px!important;min-height:30px!important;border-radius:999px!important;color:rgba(231,231,232,.68)!important;font-size:14px!important}.overlay-icon-close:hover,.overlay-icon-close:focus-visible{border-color:rgba(255,111,111,.5)!important;color:#ffb2b2!important;box-shadow:0 0 16px rgba(255,111,111,.16)!important}.overlay-menu[hidden],.publish-cover-menu[hidden]{display:none!important}.publish-cover-menu[data-overlay-menu-mode=add]{width:max-content;max-height:none}.clip-control-surface .cuted-control-bar{min-height:82px}.clip-control-surface .cuted-render-zone{min-height:58px}.clip-control-surface .cuted-tool-group{flex-basis:330px;min-height:58px}.clip-control-surface .cuted-tile-button{flex-basis:54px;width:54px;height:50px;font-size:24px}.card[open] .clip-row-timeline.preview-camera-timeline--live .timeline-shell{min-height:214px}.card[open] .clip-row-timeline.preview-camera-timeline--live{min-height:216px;margin:-10px 0 0}
"""


def js() -> str:
    return """
function galleryStorageKey(name){
  return `${name}:${currentGalleryPath() || window.location.pathname || "root"}`;
}
const editorStateStorageKey = galleryStorageKey("cutted-state");
const editorTabStorageKey = galleryStorageKey("cutted-tab");
if (new URLSearchParams(location.search).has("reset")) {
  localStorage.removeItem(editorStateStorageKey);
  localStorage.removeItem(editorTabStorageKey);
  localStorage.removeItem("cutted-state");
  localStorage.removeItem("cutted-tab");
  localStorage.removeItem("cutted-empty-gallery");
  history.replaceState(null, "", location.pathname);
}
const state = JSON.parse(localStorage.getItem(editorStateStorageKey) || "{}");
const emptyGalleryStorageKey = "cutted-empty-gallery";
const maxOverlayImageBytes = 1800000;
const maxOverlayImageSourceBytes = 6000000;
const maxOverlayImagePixels = 1600;
const coverLayerVerticalLift = .30;
const maxBumperVideoBytes = 48000000;
const cameraAnalysisFetchTimeoutMs = 180000;
const cameraReadinessPollMs = 3500;
function save(){
  try {
    localStorage.setItem(editorStateStorageKey, JSON.stringify(state));
    clearAppNotice();
    return true;
  } catch (error) {
    showAppNotice("A imagem ficou pesada demais para salvar nesta tela. Remova ou use uma versao menor antes de continuar.");
    console.warn("CUTED state was not saved", error);
    return false;
  }
}
function showAppNotice(message){
  let notice = document.querySelector("[data-app-notice]");
  if (!notice) {
    notice = document.createElement("div");
    notice.dataset.appNotice = "";
    notice.className = "app-notice";
    document.body.prepend(notice);
  }
  notice.textContent = message;
  notice.hidden = false;
}
function clearAppNotice(){
  const notice = document.querySelector("[data-app-notice]");
  if (notice) notice.hidden = true;
}
function cardState(rank){
  const raw = state[rank];
  if (typeof raw === "string") return { status: raw, trimStart: 0, trimEnd: 0, platforms: [], camera: defaultCamera(), camera_path: [], director_plan: null, cameraMotionMs: defaultCameraMotionMs, effect: defaultEffect(), overlay: defaultOverlay(), overlays: [], bumpers: defaultBumpers(), platformEdits: {}, publish: {} };
  const next = Object.assign({ status: null, trimStart: 0, trimEnd: 0, platforms: [], camera: defaultCamera(), camera_path: [], director_plan: null, cameraMotionMs: defaultCameraMotionMs, effect: defaultEffect(), overlay: defaultOverlay(), overlays: [], bumpers: defaultBumpers(), platformEdits: {}, publish: {} }, raw || {});
  next.platforms = next.status === "discarded" ? [] : uniquePlatforms(next.platforms);
  next.camera = normalizeCamera(next.camera);
  next.director_plan = normalizeDirectorPlan(next.director_plan);
  next.effect = normalizeEffect(next.effect);
  next.overlay = normalizeOverlay(next.overlay);
  next.overlays = normalizeOverlayLayers(next.overlays, next.overlay);
  next.bumpers = normalizeBumpers(next.bumpers);
  next.cameraMotionMs = normalizeCameraMotionMs(next.cameraMotionMs);
  next.platformEdits = normalizePlatformEdits(next.platformEdits, next);
  next.publish = normalizePublishEdit(next.publish);
  return next;
}
function setCardState(rank, patch){ state[rank] = Object.assign(cardState(rank), patch); save(); }
function normalizeCameraMotionMs(value){
  const raw = Number(value || defaultCameraMotionMs);
  return Math.round(Math.max(350, Math.min(raw, 1400)) / 50) * 50;
}
function fixed(value){ return `${Number(value || 0).toFixed(1)}s`; }
const platformMeta = {
  tiktok: { label: "TikTok", width: 1080, height: 1920, resolution_preset: "vertical_9_16" },
  shorts: { label: "Shorts", width: 1080, height: 1920, resolution_preset: "vertical_9_16" },
  instagram: { label: "Instagram", width: 1080, height: 1920, resolution_preset: "vertical_9_16" },
  facebook: { label: "Facebook", width: 1080, height: 1350, resolution_preset: "vertical_4_5" },
  youtube: { label: "YouTube", width: 1920, height: 1080, resolution_preset: "horizontal_16_9" }
};
const resolutionPresets = {
  vertical_9_16: { label: "Vertical 9:16", width: 1080, height: 1920, platform: "tiktok", destinations: ["tiktok", "shorts", "instagram"] },
  vertical_4_5: { label: "Vertical 4:5", width: 1080, height: 1350, platform: "facebook", destinations: ["facebook"] },
  horizontal_16_9: { label: "Horizontal 16:9", width: 1920, height: 1080, platform: "youtube", destinations: ["youtube"] }
};
const defaultPreviewVolume = 0.2;
const defaultCameraMotionMs = 700;
const effectMeta = {
  none: { label: "Sem efeito", note: "Preview limpo" },
  "light-grain": { label: "Chuvisco Leve", note: "Granulado sutil" },
  "old-film": { label: "Filme Antigo", note: "Vintage com vinheta" },
  vhs: { label: "VHS / TV Antiga", note: "Ruido analogico" },
  "bw-old": { label: "Preto e Branco Antigo", note: "P&B com grao" }
};
const cameraMeta = {
  center: { label: "Centro manual", note: "Crop limpo no centro", x: 50, scale: 1 },
  "face-center": { label: "Centro + zoom manual", note: "Zoom leve no centro", x: 50, scale: 1.1 },
  "face-left": { label: "Esquerda manual", note: "Prioriza o lado esquerdo", x: 22, scale: 1 },
  "face-right": { label: "Direita manual", note: "Prioriza o lado direito", x: 78, scale: 1 },
  alternate: { label: "Alternar manual", note: "Pan suave entre lados", x: 50, scale: 1 },
  "jump-cut": { label: "Corte manual", note: "Troca seca entre lados", x: 50, scale: 1 },
  "fit-blur": { label: "Fit com blur", note: "Quadro inteiro com fundo desfocado", x: 50, scale: 1 },
  "soft-zoom": { label: "Zoom sutil", note: "Aproxima sem trocar o foco", x: 50, scale: 1.12 },
  "punch-in": { label: "Punch-in", note: "Mais fechado e energetico", x: 50, scale: 1.22 }
};
const manualAlternateHoldSeconds = 3.5;
const manualAlternateMoveSeconds = 1.2;
const smartCameraModes = {
  "auto-director": { label: "Auto Director", note: "Escolhe o enquadramento usando rosto principal e contexto multi-rosto", featured: true },
  "ai-director": { label: "IA", note: "Direcao automatica por IA com mapa visual local", featured: true },
  "ai-director-group": { label: "AI Grupo", note: "Preserva duas ou mais pessoas antes de fechar em close" },
  "ai-director-speaker": { label: "AI Fala", note: "Prioriza quem parece conduzir o trecho sem cortar contexto" },
  "ai-director-reactions": { label: "AI Reacoes", note: "Alterna foco entre pessoas visiveis com pausas editoriais" },
  "ai-director-cuts": { label: "AI Cortes", note: "Troca enquadramentos em cortes secos com pausas editoriais" },
  "follow-face": { label: "Seguir rosto", note: "Acompanha o rosto principal detectado" },
  "stable-face": { label: "Mais estavel", note: "Trava no enquadramento medio do rosto" },
  "face-zoom": { label: "Mais close", note: "Aproxima usando deteccao real" }
};
const cameraParts = [
  { key: "start", label: "Inicio" },
  { key: "middle", label: "Meio" },
  { key: "end", label: "Fim" }
];
const overlayMeta = {
  none: { label: "Sem chamada", title: "", subtitle: "", accent: "#000000" },
  subscribe: { label: "Inscreva-se", title: "Inscreva-se", subtitle: "Novos cortes toda semana", accent: "#ff3b30" },
  follow: { label: "Siga-nos", title: "Siga-nos", subtitle: "Mais cortes no perfil", accent: "#AFCF2A" },
  description: { label: "Veja a descricao", title: "Veja a descricao", subtitle: "Link e contexto completo", accent: "#4da3ff" },
  "like-share": { label: "Curta e compartilhe", title: "Curta e compartilhe", subtitle: "Mostre para alguem", accent: "#ffd166" },
  "pinned-comment": { label: "Comentario fixado", title: "Comentario fixado", subtitle: "Detalhes no primeiro comentario", accent: "#b388ff" },
  watermark: { label: "Marca d'agua", title: "CUTED", subtitle: "clip selecionado", accent: "#E7E7E8" }
};
function applyTab(tab){
  const next = ["import", "edit", "final"].includes(tab) ? tab : "edit";
  document.body.dataset.tab = next;
  localStorage.setItem(editorTabStorageKey, next);
  document.querySelectorAll(".tabs [data-tab]").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === next);
  });
  renderFinalStage();
  if (next === "final") restoreFinalizeResults();
}
function platformLabel(key){
  return resolutionPresetLabel(resolutionPresetForPlatform(key));
}
function validPlatform(format){
  return Object.prototype.hasOwnProperty.call(platformMeta, format) ? format : "tiktok";
}
function resolutionPresetForPlatform(platform){
  const key = platformMeta[validPlatform(platform)]?.resolution_preset || "vertical_9_16";
  return resolutionPresets[key] ? key : "vertical_9_16";
}
function resolutionPresetLabel(key){
  return (resolutionPresets[key] || resolutionPresets.vertical_9_16).label;
}
function platformForResolutionPreset(key){
  return validPlatform((resolutionPresets[key] || resolutionPresets.vertical_9_16).platform);
}
function representativePlatform(platform){
  return platformForResolutionPreset(resolutionPresetForPlatform(platform));
}
function destinationResolutionMap(){
  return Object.fromEntries(Object.keys(platformMeta).map(platform => [platform, resolutionPresetForPlatform(platform)]));
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
  const pathSource = Object.prototype.hasOwnProperty.call(source, "camera_path") ? source.camera_path : base.camera_path;
  const captionSource = Object.prototype.hasOwnProperty.call(source, "captions") ? source.captions : null;
  const captionBase = Object.prototype.hasOwnProperty.call(base, "captions") ? base.captions : null;
  return {
    camera: normalizeCamera(source.camera || base.camera || defaultCamera()),
    camera_path: normalizeCameraPath(pathSource),
    captions: normalizeCaptionSettings(captionSource, captionBase),
    director_plan: normalizeDirectorPlan(source.director_plan || base.director_plan),
    effect: normalizeEffect(source.effect || base.effect || defaultEffect()),
    overlay: overlays.find(layer => layer.kind !== "image") || defaultOverlay(),
    overlays,
    bumpers: normalizeBumpers(source.bumpers || base.bumpers || defaultBumpers())
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
function defaultCaptionSettings(){
  return { enabled: captionEnabled(), style: captionStyle() };
}
function normalizeCaptionSettings(value, fallback = null){
  const source = value && typeof value === "object" ? value : {};
  const base = fallback && typeof fallback === "object" ? fallback : defaultCaptionSettings();
  const style = normalizeCaptionStyleObject(Object.assign({}, base.style || {}, source.style || {}));
  const enabled = Object.prototype.hasOwnProperty.call(source, "enabled")
    ? Boolean(source.enabled)
    : Object.prototype.hasOwnProperty.call(base, "enabled")
      ? Boolean(base.enabled)
      : captionEnabled();
  return {
    enabled: style.mode === "off" ? false : enabled,
    style: Object.assign(style, { mode: enabled ? style.mode === "off" ? "on" : style.mode : "off" })
  };
}
function normalizeCaptionStyleObject(value){
  const source = value && typeof value === "object" ? value : {};
  const backgroundColor = normalizeCaptionBackground(source.backgroundColor || source.background_color);
  return {
    size: clampNumber(Number(source.size || defaultCaptionSize()), 24, 140),
    width: clampNumber(Number(source.width || 28), 12, 56),
    bottom: clampNumber(Number(source.bottom || source.height || defaultCaptionBottom()), 6, 32),
    mode: normalizeCaptionMode(source.mode || source.captionMode),
    textColor: normalizeCaptionColor(source.textColor || source.text_color, "#ffffff"),
    backgroundColor,
    highlightBackgroundColor: normalizeCaptionHighlightBackground(
      source.highlightBackgroundColor || source.highlight_background_color || source.activeBackgroundColor || source.active_background_color || backgroundColor
    )
  };
}
function normalizeCaptionMode(value){
  const mode = String(value || "").trim().toLowerCase();
  if (mode === "animated" || mode === "animada") return "animated";
  if (mode === "on" || mode === "static") return "on";
  if (mode === "off" || mode === "false" || mode === "0") return "off";
  return "on";
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
function cameraEditLabel(edit, duration){
  const path = normalizeCameraPath(edit?.camera_path);
  const shots = normalizeDirectorPlan(edit?.director_plan).shots;
  if (path.length && shots.length) return `Director plan: ${shots.length} cenas`;
  if (path.length) return `Camera path: ${path.length} pontos`;
  return cameraLabel(edit?.camera || defaultCamera());
}
function cameraForRank(rank, platform = activePlatformForRank(rank)){ return platformEditForRank(rank, platform).camera; }
function updateCardCameraSummary(card, camera, edit = null){
  const summary = card?.querySelector("[data-camera-current]");
  if (summary) {
    const context = card ? cameraContextForCard(card) : { duration: 0 };
    summary.textContent = edit ? cameraEditLabel(edit, context.duration) : cameraLabel(camera);
  }
}
function setCameraSegmentForRank(rank, part, patch, platform = activePlatformForRank(rank)){
  const targetPlatform = validPlatform(platform);
  const camera = cameraForRank(rank, targetPlatform);
  const segments = camera.segments.map(segment => {
    if (segment.part !== part) return segment;
    return normalizeCameraSegment(Object.assign({}, segment, patch), part);
  });
  setPlatformEditForRank(rank, targetPlatform, { camera: cameraSequence(segments), camera_path: [], director_plan: null });
  const card = cardForRank(rank);
  if (card) {
    const nextCamera = cameraForRank(rank, activePlatformForRank(rank));
    updateCardCameraSummary(card, nextCamera);
    updateCameraSurfaceForCard(card);
  }
  renderFinalStage();
}
function cameraPathHasMovement(path){
  return normalizeCameraPath(path).some(frame => Math.abs(Number(frame.x || 50) - 50) > .2 || Math.abs(Number(frame.zoom || 1) - 1) > .002 || frame.key && frame.key !== "center");
}
function cameraEditHasMovement(edit){
  const path = normalizeCameraPath(edit?.camera_path);
  return path.length ? cameraPathHasMovement(path) : cameraHasMovement(edit?.camera || defaultCamera());
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
function normalizeCameraPath(path){
  const source = Array.isArray(path) ? path : Array.isArray(path?.keyframes) ? path.keyframes : [];
  return source.map(frame => normalizeCameraPathFrame(frame)).filter(Boolean).sort((a, b) => a.time - b.time);
}
function normalizeCameraPathFrame(frame){
  if (!frame || typeof frame !== "object") return null;
  const time = Math.max(0, Number(frame.time ?? frame.t ?? 0));
  const key = cameraMeta[frame.key] ? frame.key : cameraMeta[frame.camera_key] ? frame.camera_key : null;
  const strength = Math.max(0, Math.min(Number(frame.strength ?? 60), 100));
  const base = key ? normalizeSingleCamera({ key, strength }) : null;
  const x = Math.max(0, Math.min(Number(frame.x ?? (base ? cameraCropPercent(base, time) : 50)), 100));
  const y = Math.max(0, Math.min(Number(frame.y ?? 50), 100));
  const zoom = Math.max(1, Math.min(Number(frame.zoom ?? (base ? cameraScaleValue(base) : 1)), 2));
  return {
    time: Number(time.toFixed(3)),
    x: Number(x.toFixed(2)),
    y: Number(y.toFixed(2)),
    zoom: Number(zoom.toFixed(3)),
    fit: String(frame.fit || "").toLowerCase() === "contain" || String(frame.source || "").includes("group-fit") ? "contain" : undefined,
    source: String(frame.source || (key ? "manual-segment" : "manual-path")),
    confidence: Math.max(0, Math.min(Number(frame.confidence ?? 1), 1)),
    intent: frame.intent ? String(frame.intent) : undefined,
    reason: frame.reason ? String(frame.reason) : undefined,
    transition: frame.transition ? String(frame.transition) : undefined,
    part: frame.part ? String(frame.part) : undefined,
    key: key || undefined,
    label: frame.label ? String(frame.label) : key ? cameraMeta[key].label : undefined,
    strength: key ? strength : undefined
  };
}
function normalizeDirectorPlan(plan){
  if (!plan || typeof plan !== "object") return { version: 1, source: "none", resolution_preset: "vertical_9_16", shots: [] };
  const shots = Array.isArray(plan.shots) ? plan.shots.map(normalizeDirectorShot).filter(Boolean) : [];
  return {
    version: Number(plan.version || 1),
    source: String(plan.source || "director-plan"),
    mode: String(plan.mode || ""),
    resolution_preset: resolutionPresets[plan.resolution_preset] ? plan.resolution_preset : "vertical_9_16",
    style: String(plan.style || "normal"),
    energy: String(plan.energy || "normal"),
    shots
  };
}
function normalizeDirectorShot(shot){
  if (!shot || typeof shot !== "object") return null;
  const start = Math.max(0, Number(shot.start || 0));
  const end = Math.max(start, Number(shot.end || start));
  const label = String(shot.label || directorIntentLabel(shot.intent || "speaker_hold"));
  return {
    id: String(shot.id || `shot-${Math.round(start * 1000)}`),
    start: Number(start.toFixed(3)),
    end: Number(end.toFixed(3)),
    intent: String(shot.intent || "speaker_hold"),
    label,
    subject: String(shot.subject || "primary"),
    transition: String(shot.transition || "hold"),
    reason: String(shot.reason || "")
  };
}
function directorPlanFromCameraPath(path, duration, platform, source = "manual"){
  const frames = normalizeCameraPath(path);
  const safeDuration = Math.max(Number(duration) || 0, .3);
  const shots = (frames.length ? frames : [normalizeCameraPathFrame({ time: 0, x: 50, y: 50, zoom: 1 })])
    .map((frame, index, sourceFrames) => directorShotFromFrame(frame, index, sourceFrames, safeDuration));
  return { version: 1, source, mode: "", resolution_preset: resolutionPresetForPlatform(platform), style: "normal", energy: "normal", shots };
}
function directorShotFromFrame(frame, index, frames, duration){
  const start = clampNumber(Number(frame.time || 0), 0, duration);
  const next = frames[index + 1];
  const end = next ? clampNumber(Number(next.time || duration), start, duration) : duration;
  const intent = frame.intent || directorIntentFromFrame(frame);
  return { id: `shot-${String(index + 1).padStart(3, "0")}`, start, end, intent, label: directorIntentLabel(intent), subject: directorSubject(intent), transition: directorTransition(frame, intent), reason: frame.reason || directorReason(intent) };
}
function directorIntentFromFrame(frame){
  const source = String(frame?.source || "");
  if (cameraFrameUsesGroupFit(frame) || source.includes("group")) return "group_open";
  if (source.includes("reaction")) return "reaction_focus";
  if (source.includes("cuts")) return "cut_focus";
  return Number(frame?.zoom || 1) >= 1.18 ? "speaker_close" : "speaker_hold";
}
function directorIntentLabel(intent){
  return {
    group_open: "Group",
    reaction_focus: "Reaction",
    cut_focus: "Cut",
    center_hold: "Center",
    speaker_close: "Zoom",
    speaker_hold: "Speaker"
  }[intent] || "Camera";
}
function directorSubject(intent){
  if (intent === "group_open") return "group";
  if (intent === "reaction_focus") return "secondary";
  if (intent === "center_hold") return "center";
  return "primary";
}
function directorTransition(frame, intent){
  if (intent === "cut_focus" || cameraFrameUsesHardCut(frame)) return "cut";
  return ["group_open", "speaker_hold", "center_hold"].includes(intent) ? "hold" : "smooth";
}
function directorReason(intent){
  return {
    group_open: "Preserva o grupo.",
    reaction_focus: "Realca reacao.",
    cut_focus: "Corte seco para ritmo.",
    center_hold: "Volta para o centro seguro.",
    speaker_close: "Aproxima o foco.",
    speaker_hold: "Segura foco estavel."
  }[intent] || "";
}
function directorIntentOptions(){
  return [
    { intent: "speaker_hold", label: "Speaker" },
    { intent: "group_open", label: "Group" },
    { intent: "reaction_focus", label: "Reaction" },
    { intent: "center_hold", label: "Center" },
    { intent: "speaker_close", label: "Zoom" },
    { intent: "cut_focus", label: "Hard cut" }
  ];
}
function directorIntentOptionsHtml(selectedIntent){
  return directorIntentOptions().map(item => {
    const selected = item.intent === selectedIntent ? " selected" : "";
    return `<option value="${escapeAttr(item.intent)}"${selected}>${escapeHtml(item.label)}</option>`;
  }).join("");
}
function cameraFramePatchForIntent(intent, frame){
  const current = normalizeCameraPathFrame(frame) || normalizeCameraPathFrame({ time: 0, x: 50, y: 50, zoom: 1 });
  const base = { intent, label: directorIntentLabel(intent), reason: directorReason(intent), transition: directorTransition(current, intent), key: undefined, strength: undefined };
  if (intent === "group_open") return Object.assign({}, current, base, { x: 50, y: 50, zoom: 1, fit: "contain", source: "manual-director-group" });
  if (intent === "reaction_focus") {
    const x = Number(current.x || 50) <= 50 ? 72 : 28;
    return Object.assign({}, current, base, { x, y: 50, zoom: 1.14, fit: undefined, source: "manual-director-reaction" });
  }
  if (intent === "cut_focus") return Object.assign({}, current, base, { zoom: Math.max(Number(current.zoom || 1.12), 1.12), fit: undefined, source: "ai-director-cuts-manual" });
  if (intent === "center_hold") return Object.assign({}, current, base, { x: 50, y: 50, zoom: 1, fit: undefined, source: "manual-director-center" });
  if (intent === "speaker_close") return Object.assign({}, current, base, { zoom: Math.max(Number(current.zoom || 1), 1.22), fit: undefined, source: "manual-director-zoom" });
  return Object.assign({}, current, base, { zoom: Math.max(Number(current.zoom || 1), 1.08), fit: undefined, source: "manual-director-speaker" });
}
function directorShotForFrame(plan, frame){
  const shots = normalizeDirectorPlan(plan).shots;
  const time = Number(frame?.time || 0);
  return shots.find(shot => Math.abs(Number(shot.start || 0) - time) < .16) || null;
}
function directorMarkerLabel(plan, frame){
  const shot = directorShotForFrame(plan, frame);
  if (shot?.label) return shot.label;
  if (frame?.label) return frame.label;
  if (frame?.key) return cameraMeta[frame.key]?.label || "Camera";
  return directorIntentLabel(directorIntentFromFrame(frame));
}
function directorMarkerTitle(plan, frame){
  const shot = directorShotForFrame(plan, frame);
  const label = directorMarkerLabel(plan, frame);
  const detail = shot?.reason ? ` - ${shot.reason}` : "";
  return `${fixed(frame?.time || 0)} - ${label}${detail}`;
}
function cameraCropPercent(camera, elapsed = 0){
  const current = normalizeSingleCamera(camera);
  const strength = current.strength;
  if (current.key === "face-left") return clampNumber((0.22 - strength * 0.0012) * 100, 0, 100);
  if (current.key === "face-right") return clampNumber((0.78 + strength * 0.0012) * 100, 0, 100);
  if (current.key === "alternate") {
    const amplitude = 0.12 + (strength / 100) * 0.22;
    return manualAlternateCropPercent(0.5 - amplitude, 0.5 + amplitude, Number(elapsed || 0));
  }
  if (current.key === "jump-cut") {
    const left = 0.22 - strength * 0.0012;
    const right = 0.78 + strength * 0.0012;
    return clampNumber((Number(elapsed || 0) % 6 < 3 ? left : right) * 100, 0, 100);
  }
  return 50;
}
function manualAlternateCropPercent(left, right, elapsed){
  const hold = manualAlternateHoldSeconds;
  const move = manualAlternateMoveSeconds;
  const cycle = (hold + move) * 2;
  const phase = positiveModulo(elapsed, cycle);
  let ratio = left;
  if (phase < hold) ratio = left;
  else if (phase < hold + move) ratio = easedCameraRatio(left, right, (phase - hold) / move);
  else if (phase < hold + move + hold) ratio = right;
  else ratio = easedCameraRatio(right, left, (phase - hold - move - hold) / move);
  return clampNumber(ratio * 100, 0, 100);
}
function easedCameraRatio(start, end, progress){
  const amount = (1 - Math.cos(Math.PI * clampNumber(progress, 0, 1))) / 2;
  return start + (end - start) * amount;
}
function positiveModulo(value, size){
  return ((Number(value || 0) % size) + size) % size;
}
function cameraScaleValue(camera){
  const current = normalizeSingleCamera(camera);
  const strength = current.strength;
  if (current.key === "face-center") return 1.06 + (strength / 100) * 0.08;
  if (current.key === "soft-zoom") return 1.04 + (strength / 100) * 0.10;
  if (current.key === "punch-in") return 1.12 + (strength / 100) * 0.16;
  return 1;
}
function cameraSegmentForTime(camera, position, duration){
  const current = normalizeCamera(camera);
  const safeDuration = Math.max(Number(duration) || 0, .3);
  const segmentDuration = safeDuration / cameraParts.length;
  const safePosition = clampNumber(Number(position) || 0, 0, Math.max(safeDuration - .001, 0));
  const index = Math.min(cameraParts.length - 1, Math.max(0, Math.floor(safePosition / segmentDuration)));
  const part = cameraParts[index] || cameraParts[0];
  const segment = current.segments.find(item => item.part === part.key) || defaultCameraSegment(part.key);
  return { segment, elapsed: Math.max(0, safePosition - segmentDuration * index) };
}
function cameraFrameFromSegment(segment, time, elapsed){
  const current = normalizeCameraSegment(segment, segment.part || "start");
  const frame = {
    time: Number(Math.max(0, Number(time) || 0).toFixed(3)),
    x: Number(cameraCropPercent(current, elapsed).toFixed(2)),
    y: 50,
    zoom: Number(cameraScaleValue(current).toFixed(3)),
    source: "manual-segment",
    confidence: 1,
    part: current.part,
    key: current.key,
    label: current.label,
    strength: current.strength
  };
  if (current.key === "fit-blur") frame.fit = "contain";
  return frame;
}
function cameraPathFromCamera(camera, duration){
  const current = normalizeCamera(camera);
  const safeDuration = Math.max(Number(duration) || 0, .3);
  const segmentDuration = safeDuration / cameraParts.length;
  return cameraParts.map((part, index) => {
    const segment = current.segments.find(item => item.part === part.key) || defaultCameraSegment(part.key);
    return cameraFrameFromSegment(segment, segmentDuration * index, 0);
  });
}
function cameraPathForEdit(edit, duration){
  const path = normalizeCameraPath(edit?.camera_path);
  return path.length ? path : cameraPathFromCamera(edit?.camera || defaultCamera(), duration);
}
function exportCameraPathForEdit(edit, sourceDuration, trimStart, adjustedDuration){
  const safeSourceDuration = Math.max(Number(sourceDuration) || Number(adjustedDuration) || 0, .3);
  const safeTrimStart = clampNumber(Number(trimStart) || 0, 0, Math.max(safeSourceDuration - .001, 0));
  const safeAdjustedDuration = Math.max(Number(adjustedDuration) || (safeSourceDuration - safeTrimStart), .3);
  const sourcePath = cameraPathForEdit(edit, safeSourceDuration);
  const active = cameraFrameForTime(edit?.camera, sourcePath, safeTrimStart, safeSourceDuration);
  const frames = [Object.assign({}, active, { time: 0 })];
  sourcePath.forEach(frame => {
    const time = Number(frame.time || 0);
    if (time <= safeTrimStart + .001) return;
    if (time >= safeTrimStart + safeAdjustedDuration - .001) return;
    frames.push(Object.assign({}, frame, { time: Number((time - safeTrimStart).toFixed(3)) }));
  });
  return normalizeCameraPath(frames);
}
function sourceDurationForMoment(moment){
  return Number(moment?.duration || (Number(moment?.end || 0) - Number(moment?.start || 0)) || moment?.adjusted_duration || 0);
}
function explicitCameraPathForEdit(edit){
  return normalizeCameraPath(edit?.camera_path);
}
function selectedCameraPathIndex(card, path){
  const count = path.length;
  if (!count) return 0;
  const index = Number(card?.dataset.cameraPathIndex ?? 0);
  return Math.min(Math.max(Number.isFinite(index) ? index : 0, 0), count - 1);
}
function setSelectedCameraPathIndex(card, index){
  if (!card) return;
  card.dataset.cameraPathIndex = String(Math.max(0, Number(index) || 0));
}
function cameraPathWithFrame(path, frame, index = null){
  const frames = normalizeCameraPath(path);
  const next = normalizeCameraPathFrame(frame);
  if (!next) return frames;
  const exactIndex = index === null ? frames.findIndex(item => Math.abs(item.time - next.time) < .15) : Number(index);
  if (exactIndex >= 0 && exactIndex < frames.length) {
    frames[exactIndex] = next;
  } else {
    frames.push(next);
  }
  return normalizeCameraPath(frames);
}
function cameraPathFrameWithPreset(frame, key, strength){
  const next = cameraFrameFromSegment({ part: frame.part || "", key, strength }, frame.time, 0);
  next.source = "manual-path";
  return next;
}
function setCameraPathForRank(rank, path, platform = activePlatformForRank(rank), rerender = true){
  const normalized = normalizeCameraPath(path);
  const duration = cardForRank(rank) ? cameraTimelineDurationForCard(cardForRank(rank)) : 0;
  setPlatformEditForRank(rank, platform, { camera_path: normalized, director_plan: directorPlanFromCameraPath(normalized, duration, platform) });
  const card = cardForRank(rank);
  if (card) {
    const edit = platformEditForRank(rank, platform);
    if (rerender) updateCameraUi(card);
    updateCardCameraSummary(card, edit.camera, edit);
    updateCameraSurfaceForCard(card);
    renderPreviewCameraTimeline(card);
  }
  renderFinalStage();
}
function addCameraPathFrameForCard(card){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card);
  const edit = platformEditForRank(rank, platform);
  const sourcePath = cameraPathForEdit(edit, duration);
  const frame = cameraFrameForTime(edit.camera, sourcePath, position, duration);
  const next = Object.assign({}, frame, { time: Number(position.toFixed(3)), source: "manual-path" });
  const path = cameraPathWithFrame(sourcePath, next);
  const index = path.findIndex(item => Math.abs(item.time - next.time) < .01);
  setSelectedCameraPathIndex(card, index >= 0 ? index : path.length - 1);
  setCameraPathForRank(rank, path, platform);
}
function addCenterCameraFrameForCard(card){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card);
  const edit = platformEditForRank(rank, platform);
  const sourcePath = cameraPathForEdit(edit, duration);
  const next = normalizeCameraPathFrame({
    time: Number(position.toFixed(3)),
    key: "center",
    strength: 60,
    source: "manual-path"
  });
  const path = next ? cameraPathWithFrame(sourcePath, next) : sourcePath;
  const index = next ? path.findIndex(item => Math.abs(item.time - next.time) < .01) : path.length - 1;
  setSelectedCameraPathIndex(card, index >= 0 ? index : path.length - 1);
  setCameraPathForRank(rank, path, platform);
}
function updateCameraPathFrameForCard(card, patch, rerender = true){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const edit = platformEditForRank(rank, platform);
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card);
  const path = cameraPathForEdit(edit, duration);
  const index = selectedCameraPathIndex(card, path);
  const current = path[index] || cameraFrameForTime(edit.camera, path, position, duration);
  let frame = Object.assign({}, current, patch);
  if (patch.key || patch.strength !== undefined) {
    frame = cameraPathFrameWithPreset(frame, patch.key || current.key || "center", patch.strength ?? current.strength ?? 60);
  }
  const nextPath = cameraPathWithFrame(path, frame, index);
  setSelectedCameraPathIndex(card, Math.min(index, nextPath.length - 1));
  setCameraPathForRank(rank, nextPath, platform, rerender);
}
function updateCameraPathFrameIntentForCard(card, intent){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const edit = platformEditForRank(rank, platform);
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card);
  const path = cameraPathForEdit(edit, duration);
  const index = selectedCameraPathIndex(card, path);
  const current = path[index] || cameraFrameForTime(edit.camera, path, position, duration);
  const frame = cameraFramePatchForIntent(intent, current);
  const nextPath = cameraPathWithFrame(path, frame, index);
  setSelectedCameraPathIndex(card, Math.min(index, nextPath.length - 1));
  setCameraPathForRank(rank, nextPath, platform);
}
function addCameraIntentFrameForCard(card, intent){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card);
  const edit = platformEditForRank(rank, platform);
  const sourcePath = cameraPathForEdit(edit, duration);
  const base = cameraFrameForTime(edit.camera, sourcePath, position, duration);
  const frame = cameraFramePatchForIntent(intent, Object.assign({}, base, { time: Number(position.toFixed(3)) }));
  const path = cameraPathWithFrame(sourcePath, frame);
  const index = path.findIndex(item => Math.abs(item.time - frame.time) < .01);
  setSelectedCameraPathIndex(card, index >= 0 ? index : path.length - 1);
  setCameraPathForRank(rank, path, platform);
}
function moveCameraPathFrameToPlayhead(card){
  const position = cameraTimelinePositionForCard(card);
  updateCameraPathFrameForCard(card, { time: Number(position.toFixed(3)) });
}
function deleteCameraPathFrameForCard(card){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const edit = platformEditForRank(rank, platform);
  const duration = cameraTimelineDurationForCard(card);
  const path = cameraPathForEdit(edit, duration);
  if (path.length <= 1) return;
  const index = selectedCameraPathIndex(card, path);
  path.splice(index, 1);
  setSelectedCameraPathIndex(card, Math.max(0, index - 1));
  setCameraPathForRank(rank, path, platform);
}
function resetCameraPathForCard(card){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  setSelectedCameraPathIndex(card, 0);
  setCameraPathForRank(rank, [], platform);
}
function cameraAnalysisRequestPayload(card, smartMode, forceRefresh){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const moment = (window.CUTTED_DATA.moments || []).find(item => String(item.rank) === String(rank));
  const values = trimValues(card);
  return {
    gallery_path: currentGalleryPath(),
    rank,
    platform,
    mode: smartMode,
    force_refresh: forceRefresh,
    allow_completed_cache: true,
    clip_file: moment?.clip_file || "",
    title: moment?.title || "",
    transcript: moment?.transcript || moment?.text || "",
    trim_start_seconds: values.trimStart,
    source_start_seconds: Number(moment?.start || 0) + values.trimStart,
    adjusted_duration: Math.max(values.endPos - values.startPos, .3)
  };
}
function cameraStatusUrl(card, smartMode){
  const payload = cameraAnalysisRequestPayload(card, smartMode, false);
  const params = new URLSearchParams();
  Object.entries(payload).forEach(([key, value]) => {
    if (value !== undefined && value !== null) params.set(key, String(value));
  });
  return `/api/camera/status?${params.toString()}`;
}
function scheduleAiReadinessRefresh(card){
  if (card.dataset.aiPollScheduled === "1") return;
  card.dataset.aiPollScheduled = "1";
  window.setTimeout(() => {
    delete card.dataset.aiPollScheduled;
    refreshAiReadinessForCard(card);
  }, cameraReadinessPollMs);
}
async function refreshAiReadinessForCard(card){
  const button = card.querySelector("[data-camera-ai]");
  if (card.dataset.aiApplying === "1") return;
  if (card.dataset.aiStatusLoading === "1") return;
  card.dataset.aiStatusLoading = "1";
  try {
    const response = await fetch(cameraStatusUrl(card, "ai-director"));
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "status indisponivel");
    card.dataset.aiReady = payload.ready ? "1" : "0";
    card.dataset.aiCacheReady = payload.cache_ready ? "1" : "0";
    if (button) {
      button.disabled = !payload.ready;
      button.textContent = payload.ready ? "IA" : "...";
    }
    if (payload.cache_ready) setCameraAutoStatus(card, "IA pronta do cache");
    else if (payload.ready) setCameraAutoStatus(card, "IA pronta");
    else {
      setCameraAutoStatus(card, "Mapeando video...");
      scheduleAiReadinessRefresh(card);
    }
  } catch (_error) {
    card.dataset.aiReady = "0";
    if (button) {
      button.disabled = true;
      button.textContent = "...";
    }
    setCameraAutoStatus(card, "Mapeando video...");
    scheduleAiReadinessRefresh(card);
  } finally {
    delete card.dataset.aiStatusLoading;
    updateControlSurfaceForCard(card);
  }
}
async function analyzeCameraForCard(card, mode = "auto-director"){
  const rank = card.dataset.rank;
  const platform = activePlatformForRank(rank);
  const smartMode = smartCameraModes[mode] ? mode : "auto-director";
  const currentEdit = platformEditForRank(rank, platform);
  const hasCachedAiPath = smartMode === "ai-director" && explicitCameraPathForEdit(currentEdit).length > 0;
  const forceRefresh = smartMode === "ai-director" && !hasCachedAiPath;
  const button = card.querySelector(`[data-camera-smart-mode="${smartMode}"]`) || card.querySelector("[data-camera-ai]") || card.querySelector("[data-camera-auto]");
  if (smartMode === "ai-director" && card.dataset.aiReady !== "1") {
    setCameraAutoStatus(card, "Mapeando video...");
    refreshAiReadinessForCard(card);
    return;
  }
  card.dataset.aiApplying = "1";
  setCameraAutoStatus(card, `Aplicando ${smartCameraModes[smartMode].label}...`);
  if (button) {
    button.disabled = true;
    if (smartMode === "ai-director") button.textContent = "...";
  }
  try {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), cameraAnalysisFetchTimeoutMs);
    let response;
    try {
      response = await fetch("/api/camera/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify(cameraAnalysisRequestPayload(card, smartMode, forceRefresh))
      });
    } finally {
      window.clearTimeout(timeoutId);
    }
    const payload = await response.json();
    const diagnosticText = cameraDiagnosticsText(payload.diagnostics);
    if (!response.ok || !payload.ok) {
      const detail = diagnosticText ? ` (${diagnosticText})` : "";
      throw new Error(`${payload.error || "Falha ao analisar camera."}${detail}`);
    }
    const path = normalizeCameraPath(payload.camera_path);
    if (!path.length) throw new Error("A analise nao retornou keyframes.");
    setSelectedCameraPathIndex(card, 0);
    const directorPlan = normalizeDirectorPlan(payload.director_plan);
    setPlatformEditForRank(rank, platform, { camera_path: path, director_plan: directorPlan });
    updateCameraUi(card);
    updateCameraSurfaceForCard(card);
    renderPreviewCameraTimeline(card);
    renderFinalStage();
    const label = payload.mode_label || smartCameraModes[smartMode].label;
    const suffix = diagnosticText ? ` (${diagnosticText})` : "";
    const applied = payload.cache_recovered ? `${label}: mantive ultimo resultado bom` : payload.completed_cache ? `${label} pronto do cache` : payload.cached ? `${label} aplicado do cache` : payload.cache_bypassed ? `${label} recalculado` : `${label} aplicado`;
    setCameraAutoStatus(card, `${applied}.${suffix}`);
  } catch (error) {
    const message = error && error.name === "AbortError"
      ? "IA ainda esta aplicando; tente novamente em alguns segundos para buscar o resultado pronto."
      : (error.message || "Falha na auto camera.");
    setCameraAutoStatus(card, message);
  } finally {
    delete card.dataset.aiApplying;
    const nextButton = card.querySelector(`[data-camera-smart-mode="${smartMode}"]`) || card.querySelector("[data-camera-ai]") || card.querySelector("[data-camera-auto]");
    if (nextButton) {
      nextButton.disabled = false;
      if (smartMode === "ai-director") nextButton.textContent = "IA";
    }
    if (smartMode === "ai-director") refreshAiReadinessForCard(card);
  }
}
function setCameraAutoStatus(card, message){
  const status = card.querySelector("[data-camera-auto-status]");
  if (status) status.textContent = message || "";
  updateControlSurfaceForCard(card);
}
function cameraDiagnosticsText(diagnostics){
  if (!diagnostics || typeof diagnostics !== "object") return "";
  const samples = Number(diagnostics.sample_count || 0);
  const detected = Number(diagnostics.detection_frames || 0);
  const width = Number(diagnostics.video_width || 0);
  const height = Number(diagnostics.video_height || 0);
  const keyframes = Number(diagnostics.camera_keyframes || 0);
  const visualMap = diagnostics.visual_map || {};
  let input = diagnostics.analysis_input === "source" ? "source" : "clip";
  if (visualMap && visualMap.used) input = "mapa visual";
  const multi = Number(diagnostics.multi_face_frames || 0);
  const edge = Number(diagnostics.edge_face_frames || 0);
  const maxGap = Number(diagnostics.camera_max_gap_seconds || 0);
  const risk = Number(diagnostics.camera_risk_frames || 0);
  const protectedFrames = Number(diagnostics.camera_protected_keyframes || 0);
  const size = width && height ? `${width}x${height}` : "video";
  const parts = [input, `${detected}/${samples} frames`, size, `${keyframes} keyframes`];
  if (visualMap && visualMap.segment_samples) parts.splice(1, 0, `${Number(visualMap.segment_samples)} do mapa`);
  const ai = diagnostics.ai_director || {};
  const intent = ai && ai.intent ? `IA ${ai.intent}` : "IA";
  if (diagnostics.ai_cache_recovered && diagnostics.ai_cache_recovered.used) parts.push("cache bom preservado");
  if (ai && ai.status === "visual_map_pending") parts.push("mapa visual preparando");
  else if (ai && ai.status === "timeout") parts.push(`${intent} timeout`);
  else if (ai && ai.status === "quality_rejected") parts.push(`${intent} rejeitada por monotonia`);
  else if (ai && ai.status === "no_key") parts.push("IA sem chave");
  else if (ai && ai.enabled) parts.push(ai.error ? `${intent} fallback local` : `${intent} aplicada`);
  if (ai && !ai.enabled && ai.error && ai.status !== "no_key") parts.push("IA sem chave");
  if (Number(ai.director_plan_shots || 0)) parts.push(`${Number(ai.director_plan_shots)} cenas`);
  if (multi) parts.splice(1, 0, `${multi} multi-face`);
  if (edge) parts.splice(2, 0, `${edge} borda`);
  if (maxGap) parts.push(`gap max ${maxGap.toFixed(1)}s`);
  if (protectedFrames) parts.push(`${protectedFrames} protegidos`);
  if (risk) parts.push(`${risk} riscos`);
  return parts.join(" | ");
}
function cameraFrameForTime(camera, cameraPath, position, duration){
  const path = normalizeCameraPath(cameraPath);
  if (!path.length) {
    const active = cameraSegmentForTime(camera, position, duration);
    return cameraFrameFromSegment(active.segment, position, active.elapsed);
  }
  const safePosition = Math.max(0, Number(position) || 0);
  let previous = path[0];
  let next = path[path.length - 1];
  for (let index = 0; index < path.length; index += 1) {
    if (path[index].time <= safePosition) previous = path[index];
    if (path[index].time >= safePosition) {
      next = path[index];
      break;
    }
  }
  if (previous.key || cameraFrameUsesHardCut(previous) || cameraFrameUsesGroupFit(previous)) {
    return previous.key ? cameraFrameFromSegment(previous, safePosition, Math.max(0, safePosition - previous.time)) : previous;
  }
  if (previous === next || next.time <= previous.time) return previous;
  if (cameraFrameUsesHardCut(next) || cameraFrameUsesGroupFit(next)) return previous;
  const ratio = (safePosition - previous.time) / (next.time - previous.time);
  return {
    time: Number(safePosition.toFixed(3)),
    x: Number((previous.x + (next.x - previous.x) * ratio).toFixed(2)),
    y: Number((previous.y + (next.y - previous.y) * ratio).toFixed(2)),
    zoom: Number((previous.zoom + (next.zoom - previous.zoom) * ratio).toFixed(3)),
    source: previous.source || "manual-path",
    confidence: Math.min(previous.confidence ?? 1, next.confidence ?? 1)
  };
}
function cameraFrameUsesHardCut(frame){
  return String(frame?.source || "").includes("ai-director-cuts");
}
function cameraFrameUsesGroupFit(frame){
  return String(frame?.fit || "").toLowerCase() === "contain" || String(frame?.source || "").includes("group-fit");
}
function cameraPreviewStyle(camera, elapsed = 0){
  const current = normalizeSingleCamera(camera);
  const x = cameraCropPercent(current, elapsed).toFixed(2);
  const scale = cameraScaleValue(current).toFixed(3);
  return `--camera-x:${x}%;--camera-scale:${scale}`;
}
function cameraPreviewStyleFromFrame(frame){
  const current = normalizeCameraPathFrame(frame) || { x: 50, zoom: 1 };
  if (cameraFrameUsesGroupFit(current)) return "--camera-x:50%;--camera-scale:1";
  return `--camera-x:${current.x.toFixed(2)}%;--camera-scale:${current.zoom.toFixed(3)}`;
}
function cameraHasMovement(camera){
  return normalizeCamera(camera).segments.some(segment => segment.key !== "center");
}
function applyCameraSurface(surface, camera, position = 0, duration = 0, cameraPath = []){
  if (!surface) return;
  const frame = cameraFrameForTime(camera, cameraPath, position, duration);
  surface.dataset.cameraKey = frame.key || "path";
  surface.dataset.cameraCut = cameraFrameUsesHardCut(frame) ? "hard" : "smooth";
  surface.dataset.cameraFit = cameraFrameUsesGroupFit(frame) ? "contain" : "cover";
  surface.setAttribute("style", cameraPreviewStyleFromFrame(frame));
  syncCameraFitBackground(surface);
}
function applyCameraMotionSpeed(card){
  const speed = normalizeCameraMotionMs(cardState(card.dataset.rank).cameraMotionMs);
  card.style.setProperty("--camera-transition-ms", `${speed}ms`);
  const input = card.querySelector("[data-camera-motion-speed]");
  if (input) input.value = String(speed);
}
function setCameraMotionSpeed(card, value){
  const speed = normalizeCameraMotionMs(value);
  setCardState(card.dataset.rank, { cameraMotionMs: speed });
  applyCameraMotionSpeed(card);
}
function primaryCameraVideo(scope){
  return scope?.querySelector("video:not(.camera-fit-bg)") || null;
}
function cameraFitBackgroundFor(scope){
  const surface = scope?.classList?.contains("camera-surface") ? scope : scope?.querySelector(".camera-surface");
  if (!surface) return null;
  const existing = surface.querySelector(".camera-fit-bg");
  if (existing) return existing;
  const bg = document.createElement("video");
  bg.className = "camera-fit-bg";
  bg.dataset.cameraFitBg = "1";
  bg.muted = true;
  bg.playsInline = true;
  bg.preload = "none";
  bg.setAttribute("aria-hidden", "true");
  bg.setAttribute("tabindex", "-1");
  const main = primaryCameraVideo(surface);
  if (main) main.insertAdjacentElement("afterend", bg);
  else surface.prepend(bg);
  return bg;
}
function syncCameraFitBackground(scope){
  const surface = scope?.classList?.contains("camera-surface") ? scope : scope?.querySelector(".camera-surface");
  if (!surface) return;
  const main = primaryCameraVideo(surface);
  const bg = cameraFitBackgroundFor(surface);
  if (!main || !bg) return;
  const nextSrc = main.currentSrc || main.getAttribute("src") || main.dataset.src || "";
  if (nextSrc && bg.getAttribute("src") !== nextSrc) {
    bg.setAttribute("src", nextSrc);
    bg.load();
  }
  bg.muted = true;
  bg.playsInline = true;
  if (bg.readyState > 0 && Number.isFinite(main.currentTime) && Math.abs(bg.currentTime - main.currentTime) > .12) {
    bg.currentTime = main.currentTime;
  }
  if (surface.dataset.cameraFit === "contain" && !main.paused && !main.ended) {
    const playback = bg.play();
    if (playback && typeof playback.catch === "function") playback.catch(() => {
      bg.dataset.playbackBlocked = "1";
    });
  } else {
    bg.pause();
  }
}
function unloadCameraFitBackground(scope){
  const bg = cameraFitBackgroundFor(scope?.classList?.contains("camera-surface") ? scope : scope?.querySelector(".camera-surface"));
  if (!bg) return;
  bg.pause();
  bg.removeAttribute("src");
  bg.load();
}
function cameraContextForCard(card, time = null){
  const values = trimValues(card);
  const video = primaryCameraVideo(card);
  const raw = time === null && video && Number.isFinite(video.currentTime) ? video.currentTime : time;
  const current = clampPreviewTime(values, Number(raw ?? values.trimStart));
  return {
    position: Math.max(0, current - values.trimStart),
    duration: Math.max(values.endPos - values.trimStart, .3)
  };
}
function cameraTimelineDurationForCard(card){
  const values = trimValues(card);
  return Math.max(Number(values.duration) || Number(card?.dataset?.duration) || 0, .3);
}
function cameraTimelinePositionForCard(card, time = null){
  const values = trimValues(card);
  const video = primaryCameraVideo(card);
  const raw = time === null && video && Number.isFinite(video.currentTime) ? video.currentTime : time;
  return clampPreviewTime(values, Number(raw ?? values.trimStart));
}
function updateCameraSurfaceForCard(card, time = null){
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card, time);
  const edit = platformEditForRank(card.dataset.rank, activePlatformForRank(card.dataset.rank));
  applyCameraSurface(card.querySelector(".camera-surface"), edit.camera, position, duration, cameraPathForEdit(edit, duration));
}
function startCameraFrameSync(video, update){
  if (!video || typeof requestAnimationFrame !== "function") return;
  const tick = () => {
    if (video.paused || video.ended) {
      delete video.dataset.cameraFrameSync;
      return;
    }
    update();
    video.dataset.cameraFrameSync = String(requestAnimationFrame(tick));
  };
  if (video.dataset.cameraFrameSync) return;
  update();
  video.dataset.cameraFrameSync = String(requestAnimationFrame(tick));
}
function stopCameraFrameSync(video, update){
  if (!video || !video.dataset.cameraFrameSync) {
    if (update) update();
    return;
  }
  cancelAnimationFrame(Number(video.dataset.cameraFrameSync));
  delete video.dataset.cameraFrameSync;
  if (update) update();
}
function cameraStyle(camera){
  return cameraPreviewStyle(camera, 0);
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
  if (card) {
    updateEffectUi(card);
    updateControlSurfaceForCard(card);
  }
  renderFinalStage();
}
function effectOpacity(effect){
  const current = normalizeEffect(effect);
  return current.key === "none" ? 0 : Math.max(.12, current.intensity / 185);
}
function defaultBumpers(){ return {}; }
function normalizeBumperSlot(slot){ return slot === "outro" ? "outro" : "intro"; }
function normalizeBumper(bumper, slot){
  if (!bumper || typeof bumper !== "object") return null;
  const assetFile = String(bumper.asset_file || "");
  const dataUrl = String(bumper.video_data_url || "");
  if (!assetFile && !dataUrl) return null;
  const safeSlot = normalizeBumperSlot(slot || bumper.slot);
  return {
    id: String(bumper.id || `bumper-${safeSlot}-${Date.now().toString(36)}`),
    slot: safeSlot,
    label: String(bumper.label || "vinheta.mp4"),
    asset_file: assetFile,
    video_data_url: dataUrl,
    width: Number(bumper.width || 0),
    height: Number(bumper.height || 0),
    duration: Math.max(Number(bumper.duration || 0), 0)
  };
}
function normalizeBumpers(bumpers){
  if (!bumpers || typeof bumpers !== "object") return defaultBumpers();
  const result = {};
  ["intro", "outro"].forEach(slot => {
    const bumper = normalizeBumper(bumpers[slot], slot);
    if (bumper) result[slot] = bumper;
  });
  return result;
}
function bumpersForRank(rank, platform = activePlatformForRank(rank)){ return platformEditForRank(rank, platform).bumpers; }
function setBumperForRank(rank, slot, bumper, platform = activePlatformForRank(rank)){
  const key = validPlatform(platform);
  const safeSlot = normalizeBumperSlot(slot);
  const current = bumpersForRank(rank, key);
  const next = Object.assign({}, current, { [safeSlot]: normalizeBumper(bumper, safeSlot) });
  if (!next[safeSlot]) delete next[safeSlot];
  setPlatformEditForRank(rank, key, { bumpers: normalizeBumpers(next) });
  const card = cardForRank(rank);
  if (card) {
    updateEffectUi(card);
    updateControlSurfaceForCard(card);
  }
  renderFinalStage();
}
function removeBumperForRank(rank, slot, platform = activePlatformForRank(rank)){
  const key = validPlatform(platform);
  const safeSlot = normalizeBumperSlot(slot);
  const next = Object.assign({}, bumpersForRank(rank, key));
  delete next[safeSlot];
  setPlatformEditForRank(rank, key, { bumpers: normalizeBumpers(next) });
  const card = cardForRank(rank);
  if (card) {
    updateEffectUi(card);
    updateControlSurfaceForCard(card);
  }
  renderFinalStage();
}
function bumperSlotLabel(slot){ return normalizeBumperSlot(slot) === "intro" ? "Entrada" : "Saida"; }
function bumperSummary(bumpers){
  const current = normalizeBumpers(bumpers);
  const labels = [];
  if (current.intro) labels.push("Entrada");
  if (current.outro) labels.push("Saida");
  return labels.length ? labels.join(" + ") : "Sem vinheta";
}
function defaultOverlay(){ return { id: "", kind: "cta", key: "none", label: overlayMeta.none.label, x: .62, y: .78, width: .34, opacity: 95 }; }
function overlayId(){
  return `layer-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}
function defaultTextOverlay(text = "Digite seu texto"){
  return {
    id: overlayId(),
    kind: "text",
    key: "text",
    label: text,
    text,
    x: .36,
    y: .34,
    width: .42,
    opacity: 100,
    font_size: 44,
    font_weight: "700",
    color: "#ffffff",
    background_enabled: true,
    background_color: "#000000",
    background_opacity: 70,
    start_seconds: 0,
    duration_seconds: 3
  };
}
function defaultSpeechOverlay(text = "Fala rapida"){
  return {
    id: overlayId(),
    kind: "speech",
    key: "speech",
    label: text,
    text,
    x: .32,
    y: .24,
    width: .56,
    opacity: 96,
    font_size: 34,
    font_weight: "800",
    color: "#050505",
    background_enabled: true,
    background_color: "#ffffff",
    background_opacity: 94,
    tail: "bottom-left",
    start_seconds: 0,
    duration_seconds: 3
  };
}
function normalizeOverlay(overlay){
  const key = overlayMeta[overlay?.key] ? overlay.key : "none";
  if (key === "none") return defaultOverlay();
  const text = String(overlay?.text || overlayMeta[key].title || overlayMeta[key].label);
  return normalizeTextOverlay(Object.assign({}, overlay, { text, label: text }));
}
function normalizeTextOverlay(layer){
  const text = String(layer?.text || layer?.label || "Digite seu texto").trim() || "Digite seu texto";
  return {
    id: String(layer?.id || overlayId()),
    kind: "text",
    key: "text",
    label: text,
    text,
    x: clampNumber(layer?.x ?? .36, 0, 1),
    y: clampNumber(layer?.y ?? .34, 0, 1),
    width: clampNumber(layer?.width ?? .42, .16, .9),
    opacity: clampNumber(layer?.opacity ?? 100, 10, 100),
    font_size: clampNumber(layer?.font_size ?? 44, 14, 96),
    font_weight: String(layer?.font_weight || "700"),
    color: normalizeHexColor(layer?.color, "#ffffff"),
    background_enabled: layer?.background_enabled !== false,
    background_color: normalizeHexColor(layer?.background_color, "#000000"),
    background_opacity: clampNumber(layer?.background_opacity ?? 70, 0, 100),
    start_seconds: clampNumber(layer?.start_seconds ?? 0, 0, 9999),
    duration_seconds: clampNumber(layer?.duration_seconds ?? 3, .3, 60)
  };
}
function normalizeSpeechOverlay(layer){
  const base = normalizeTextOverlay(Object.assign({}, defaultSpeechOverlay(), layer, {
    background_enabled: true,
    background_color: layer?.background_color || "#ffffff",
    background_opacity: layer?.background_opacity ?? 94,
    color: layer?.color || "#050505",
    font_weight: layer?.font_weight || "800"
  }));
  return Object.assign(base, {
    kind: "speech",
    key: "speech",
    label: base.text,
    tail: String(layer?.tail || "bottom-left"),
    start_seconds: clampNumber(layer?.start_seconds ?? 0, 0, 9999),
    duration_seconds: clampNumber(layer?.duration_seconds ?? 3, .3, 60)
  });
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
    image_file: String(layer?.image_file || ""),
    start_seconds: clampNumber(layer?.start_seconds ?? 0, 0, 9999),
    duration_seconds: clampNumber(layer?.duration_seconds ?? 3, .3, 60)
  };
}
function normalizeOverlayLayer(layer){
  if (layer?.kind === "image" || layer?.key === "image") return normalizeImageOverlay(layer);
  if (layer?.kind === "speech" || layer?.key === "speech") return normalizeSpeechOverlay(layer);
  if (layer?.kind === "text" || layer?.key === "text") return normalizeTextOverlay(layer);
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
function overlayPlatformForItem(item){
  return validPlatform(item?.dataset?.platform || item?.dataset?.previewFormat || activePlatformForRank(item?.dataset?.rank));
}
function setOverlayLayersForRank(rank, layers, rerender = true, platform = activePlatformForRank(rank)){
  const normalized = normalizeOverlayLayers(layers, defaultOverlay());
  setPlatformEditForRank(rank, platform, { overlays: normalized, overlay: normalized.find(layer => layer.kind !== "image") || defaultOverlay() });
  const card = cardForRank(rank);
  if (card && rerender) updateOverlayUi(card);
  renderFinalStage();
}
function addOverlayLayerForRank(rank, layer, platform = activePlatformForRank(rank)){
  setOverlayLayersForRank(rank, [...overlayLayersForRank(rank, platform), normalizeOverlayLayer(layer)], true, platform);
}
function patchOverlayLayerForRank(rank, id, patch, rerender = true, platform = activePlatformForRank(rank)){
  const layers = overlayLayersForRank(rank, platform).map(layer => layer.id === id ? normalizeOverlayLayer(Object.assign({}, layer, patch)) : layer);
  setOverlayLayersForRank(rank, layers, rerender, platform);
}
function removeOverlayLayerForRank(rank, id, platform = activePlatformForRank(rank)){
  setOverlayLayersForRank(rank, overlayLayersForRank(rank, platform).filter(layer => layer.id !== id), true, platform);
}
function setOverlayForRank(rank, patch, rerender = true, platform = activePlatformForRank(rank)){
  const layers = overlayLayersForRank(rank, platform);
  const first = layers.find(layer => layer.kind !== "image");
  if (first) {
    patchOverlayLayerForRank(rank, first.id, patch, rerender, platform);
    return;
  }
  setOverlayLayersForRank(rank, [normalizeOverlay(Object.assign({}, defaultOverlay(), patch))], rerender, platform);
}
function overlayLabel(overlay){
  const current = normalizeOverlayLayer(overlay);
  if (current.key === "none") return current.label;
  return `${current.label} - ${Math.round(current.opacity)}%`;
}
function overlayStyle(overlay){
  const current = normalizeOverlayLayer(overlay);
  const meta = overlayMeta[current.key] || overlayMeta.none;
  const textLike = current.kind === "text" || current.kind === "speech";
  const backgroundRgb = textLike ? hexToRgb(current.background_color).join(",") : "0,0,0";
  const color = textLike ? current.color : "#ffffff";
  const fontSize = textLike ? `${current.font_size}px` : "20px";
  const backgroundOpacity = textLike ? current.background_opacity / 100 : .7;
  return `--overlay-x:${current.x};--overlay-y:${current.y};--overlay-width:${current.width};--overlay-opacity:${current.opacity / 100};--overlay-accent:${meta.accent};--overlay-color:${color};--overlay-font-size:${fontSize};--overlay-bg-rgb:${backgroundRgb};--overlay-bg-opacity:${backgroundOpacity}`;
}
function overlayTimingForLayer(layer){
  return {
    start: clampNumber(layer?.start_seconds ?? 0, 0, 9999),
    duration: clampNumber(layer?.duration_seconds ?? 3, .3, 60)
  };
}
function overlayTimingAttrs(layer){
  const timing = overlayTimingForLayer(layer);
  return `data-overlay-start="${timing.start.toFixed(3)}" data-overlay-duration="${timing.duration.toFixed(3)}"`;
}
function overlayTimingForCard(card){
  const context = cameraContextForCard(card);
  const start = clampNumber(context.position, 0, Math.max(context.duration - .3, 0));
  const duration = clampNumber(Math.min(3, Math.max(context.duration - start, .3)), .3, 60);
  return { start_seconds: Number(start.toFixed(3)), duration_seconds: Number(duration.toFixed(3)) };
}
function speechOverlayTimingForCard(card){ return overlayTimingForCard(card); }
function overlayBoxVisibleAtPosition(box, position){
  if (box.dataset.overlayStart === undefined) return true;
  const start = clampNumber(box.dataset.overlayStart ?? 0, 0, 9999);
  const duration = clampNumber(box.dataset.overlayDuration ?? 3, .3, 60);
  return position >= start && position < start + duration;
}
function setOverlayBoxVisibility(box, visible){
  box.hidden = false;
  box.dataset.overlayVisible = visible ? "true" : "false";
  box.setAttribute("aria-hidden", visible ? "false" : "true");
}
function syncTimedOverlayVisibility(item, time = null){
  const boxes = item?.querySelectorAll?.("[data-overlay-drag]");
  if (!boxes?.length) return;
  const video = item.querySelector("video");
  const raw = time ?? (video && Number.isFinite(video.currentTime) ? video.currentTime : 0);
  const position = item.classList.contains("card") ? cameraContextForCard(item, raw).position : Number(raw || 0);
  boxes.forEach(box => setOverlayBoxVisibility(box, overlayBoxVisibleAtPosition(box, position)));
  syncOverlayTimelineActive(item, position);
}
function syncOverlayTimelineActive(item, position){
  item?.querySelectorAll?.("[data-overlay-timeline-layer]").forEach(node => {
    const start = clampNumber(node.dataset.overlayStart ?? 0, 0, 9999);
    const duration = clampNumber(node.dataset.overlayDuration ?? 3, .3, 60);
    node.classList.toggle("is-active", position >= start && position < start + duration);
  });
}
function normalizeHexColor(value, fallback){
  const raw = String(value || "").trim();
  const hex = raw.startsWith("#") ? raw.slice(1) : raw;
  return /^[0-9a-fA-F]{6}$/.test(hex) ? `#${hex.toLowerCase()}` : fallback;
}
function hexToRgb(value){
  const hex = normalizeHexColor(value, "#000000").slice(1);
  return [0, 2, 4].map(index => parseInt(hex.slice(index, index + 2), 16));
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
  return "Em edicao";
}
function setCardPreviewFormat(card, format){
  const next = validPlatform(format);
  card.dataset.previewFormat = next;
  card.querySelectorAll("[data-card-format-preview]").forEach(button => {
    button.classList.toggle("active", button.dataset.cardFormatPreview === next);
    button.setAttribute("aria-selected", button.dataset.cardFormatPreview === next ? "true" : "false");
  });
  const trigger = card.querySelector("[data-preview-format-trigger]");
  if (trigger) trigger.setAttribute("aria-label", `Formato do preview: ${platformLabel(next)}`);
  const label = card.querySelector("[data-preview-format-current]");
  if (label) label.textContent = platformLabel(next);
  const status = card.querySelector("[data-platform-preset-current]");
  if (status) status.textContent = `Preset: ${platformLabel(next)}`;
  updateControlSurfaceForCard(card);
}
function closePreviewFormatMenus(except = null){
  document.querySelectorAll("[data-preview-format-menu]").forEach(menu => {
    if (menu === except) return;
    menu.querySelector("[data-preview-format-options]")?.setAttribute("hidden", "");
    menu.querySelector("[data-preview-format-trigger]")?.setAttribute("aria-expanded", "false");
  });
}
function togglePreviewFormatMenu(card){
  const menu = card.querySelector("[data-preview-format-menu]");
  const options = card.querySelector("[data-preview-format-options]");
  const trigger = card.querySelector("[data-preview-format-trigger]");
  if (!menu || !options || !trigger) return;
  const willOpen = options.hasAttribute("hidden");
  closePreviewFormatMenus(menu);
  options.toggleAttribute("hidden", !willOpen);
  trigger.setAttribute("aria-expanded", willOpen ? "true" : "false");
}
function bindPreviewFormatDismiss(){
  if (document.body.dataset.previewFormatDismissBound) return;
  document.body.dataset.previewFormatDismissBound = "1";
  document.addEventListener("click", event => {
    if (event.target instanceof Element && event.target.closest("[data-preview-format-menu]")) return;
    closePreviewFormatMenus();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") closePreviewFormatMenus();
  });
}
function updateCardTools(card){
  updateCameraUi(card);
  updateEffectUi(card);
  updateOverlayUi(card);
  syncPreviewCaptions(card);
  updateControlSurfaceForCard(card);
}
function updateControlSurfaceForCard(card){
  if (!card) return;
  const slot = card.querySelector("[data-cuted-control-surface]");
  if (!slot || typeof window.createCutedControlBar !== "function") return;
  const next = controlSurfaceStateForCard(card);
  if (card.__cutedControlSurface) {
    card.__cutedControlSurface.update(next);
    return;
  }
  card.__cutedControlSurface = window.createCutedControlBar(slot, Object.assign(next, {
    mockBumpers: false,
    callbacks: controlSurfaceCallbacksForCard(card)
  }));
}
function destroyControlSurfaceForCard(card){
  if (!card || !card.__cutedControlSurface) return;
  card.__cutedControlSurface.destroy();
  delete card.__cutedControlSurface;
}
function controlSurfaceStateForCard(card){
  const rank = card.dataset.rank;
  const current = cardState(rank);
  const platform = activePlatformForRank(rank);
  const edit = platformEditForRank(rank, platform);
  const effect = effectForRank(rank, platform);
  const video = primaryCameraVideo(card);
  const platforms = uniquePlatforms(current.platforms);
  const busy = controlSurfaceBusy(card);
  const trim = trimValues(card);
  return {
    aiStatus: busy ? "loading" : controlSurfaceAiStatus(card),
    aspectRatio: controlSurfaceAspectRatio(platform),
    bumpers: bumpersForRank(rank, platform),
    busy,
    captionMode: edit.captions.style.mode,
    captionsEnabled: edit.captions.enabled,
    captionStyle: edit.captions.style,
    clipInfo: controlSurfaceClipInfo(card),
    effectStyle: controlSurfaceEffectStyle(effect),
    muted: video ? video.muted || video.volume <= 0 : false,
    ready: current.status === "liked" && platforms.includes(platform),
    discarded: current.status === "discarded",
    status: controlSurfaceStatus(card),
    trimApplied: trimRangeActive(trim),
    trimMode: !busy && card.dataset.trimMode === "1",
    volume: video ? Math.round((video.muted ? 0 : video.volume) * 100) : Math.round(defaultPreviewVolume * 100)
  };
}
function controlSurfaceClipInfo(card){
  const rank = String(card.dataset.rank || "").padStart(2, "0");
  const title = card.dataset.clipTitle || card.querySelector(".clip-title strong")?.textContent || "Corte sem titulo";
  const summary = card.querySelector("[data-card-summary]")?.textContent || card.dataset.clipSummary || "";
  return { rank: `#${rank}`, title, summary };
}
function controlSurfaceCallbacksForCard(card){
  return {
    onAiClick: () => analyzeCameraForCard(card, "ai-director"),
    onApproveClick: () => markControlSurfaceReady(card),
    onBumperClick: payload => openControlSurfaceBumperInput(card, payload.slot),
    onBumperRemove: payload => removeBumperForRank(card.dataset.rank, payload.slot),
    onCaptionToggle: payload => setControlSurfaceCaptions(payload.captionsEnabled, payload.captionStyle),
    onCaptionStyleChange: payload => setControlSurfaceCaptions(payload.captionsEnabled, payload.captionStyle),
    onDiscardClick: () => discardControlSurfaceCard(card),
    onEffectStyleChange: payload => setEffectForRank(card.dataset.rank, { key: appEffectKeyFromControlSurface(payload.effectStyle) }),
    onFormatChange: payload => setControlSurfaceFormat(card, payload.aspectRatio),
    onReadyCancel: () => cancelControlSurfaceReady(card),
    onSendRender: () => sendCardToRenderQueue(card),
    onTrimToggle: payload => setControlSurfaceTrimMode(card, payload.trimMode),
    onVolumeChange: payload => setPreviewVolume(card, payload.muted ? 0 : payload.volume / 100)
  };
}
function controlSurfaceAiStatus(card){
  const edit = platformEditForRank(card.dataset.rank, activePlatformForRank(card.dataset.rank));
  return explicitCameraPathForEdit(edit).length ? "active" : "idle";
}
function controlSurfaceBusy(card){
  return card.dataset.aiApplying === "1" || controlSurfaceMapping(card);
}
function controlSurfaceMapping(card){
  if (card.dataset.aiApplying === "1") return false;
  if (controlSurfaceAiStatus(card) === "active") return false;
  return card.dataset.aiReady !== "1" && card.dataset.aiCacheReady !== "1";
}
function controlSurfaceStatus(card){
  const current = cardState(card.dataset.rank);
  const platform = activePlatformForRank(card.dataset.rank);
  const platforms = uniquePlatforms(current.platforms);
  if (card.dataset.bumperStatus) return { kind: "error", label: card.dataset.bumperStatus, tone: "red" };
  if (current.status === "discarded") return { kind: "discarded", label: "CUT DISCARDED", persistent: true, tone: "red" };
  if (card.dataset.aiApplying === "1") return { kind: "ai", label: "IA ajustando keyframes...", progress: 58, persistent: true, tone: "blue" };
  if (controlSurfaceMapping(card)) return { kind: "mapping", label: "Projeto sendo mapeado...", progress: 28, persistent: true, tone: "blue" };
  if (current.status === "liked" && platforms.includes(platform)) return { kind: "ready", label: "Ready", persistent: true, tone: "green" };
  return null;
}
function controlSurfaceAspectRatio(platform){
  const preset = resolutionPresetForPlatform(platform);
  if (preset === "vertical_4_5") return "4:5";
  if (preset === "horizontal_16_9") return "16:9";
  return "9:16";
}
function controlSurfacePlatform(aspectRatio){
  if (aspectRatio === "4:5") return "facebook";
  if (aspectRatio === "16:9") return "youtube";
  return "tiktok";
}
function controlSurfaceEffectStyle(effect){
  const key = normalizeEffect(effect).key;
  if (key === "vhs") return "vhs";
  if (key === "old-film") return "film";
  if (key === "light-grain" || key === "bw-old") return "grain";
  return "clean";
}
function appEffectKeyFromControlSurface(style){
  if (style === "vhs") return "vhs";
  if (style === "film") return "old-film";
  if (style === "grain") return "light-grain";
  return "none";
}
function setControlSurfaceFormat(card, aspectRatio){
  card.dataset.previewTouched = "1";
  setPreviewPlayback(card, false);
  setCardPreviewFormat(card, controlSurfacePlatform(aspectRatio));
  updateCardTools(card);
  renderFinalStage();
}
function openControlSurfaceBumperInput(card, slot){
  const safeSlot = normalizeBumperSlot(slot);
  updateEffectUi(card);
  const input = card.querySelector(`[data-bumper-video="${safeSlot}"]`);
  if (input) input.click();
}
function setControlSurfaceCaptions(enabled, style = null){
  document.querySelectorAll(".card[open]").forEach(card => {
    const rank = card.dataset.rank;
    const platform = activePlatformForRank(rank);
    const current = platformEditForRank(rank, platform).captions;
    const nextStyle = normalizeCaptionStyleObject(Object.assign({}, style || current.style));
    const nextEnabled = nextStyle.mode === "off" ? false : Boolean(enabled);
    setPlatformEditForRank(rank, platform, {
      captions: normalizeCaptionSettings({
        enabled: nextEnabled,
        style: nextStyle
      }, current)
    });
  });
  const nextMode = normalizeCaptionMode(style?.mode || (enabled ? "on" : "off"));
  localStorage.setItem("cutted-caption-enabled", nextMode === "off" ? "0" : "1");
  localStorage.setItem("cutted-caption-mode", nextMode);
  storeCaptionStyle(Object.assign({}, style || {}, { mode: nextMode }));
  syncCaptionInputs();
  syncPreviewCaptionsForOpenCards();
  renderCaptionQueue();
  renderFinalStage();
  document.querySelectorAll(".card[open]").forEach(updateControlSurfaceForCard);
}
function setControlSurfaceTrimMode(card, enabled){
  if (!card) return;
  const active = Boolean(enabled);
  card.dataset.trimMode = active ? "1" : "0";
  card.classList.toggle("is-trim-mode", active);
  const timeline = card.querySelector("[data-preview-camera-timeline]");
  if (timeline) timeline.dataset.trimMode = active ? "1" : "0";
  updateControlSurfaceForCard(card);
  syncLiveTimelinePlaybackState(card);
}
function markControlSurfaceReady(card){
  const current = cardState(card.dataset.rank);
  const platform = activePlatformForRank(card.dataset.rank);
  const platforms = uniquePlatforms([...(current.platforms || []), platform]);
  setCardState(card.dataset.rank, { status: "liked", platforms });
  paint(card);
  updatePlatformUi(card);
  updateControlSurfaceForCard(card);
  renderCaptionQueue();
  renderFinalStage();
}
function cancelControlSurfaceReady(card){
  const current = cardState(card.dataset.rank);
  if (current.status === "discarded") {
    setCardState(card.dataset.rank, { status: null, platforms: [] });
    paint(card);
    updatePlatformUi(card);
    updateControlSurfaceForCard(card);
    renderCaptionQueue();
    renderFinalStage();
    return;
  }
  const platform = activePlatformForRank(card.dataset.rank);
  const platforms = uniquePlatforms(current.platforms).filter(item => item !== platform);
  setCardState(card.dataset.rank, { status: platforms.length ? "liked" : null, platforms });
  paint(card);
  updatePlatformUi(card);
  updateControlSurfaceForCard(card);
  renderCaptionQueue();
  renderFinalStage();
}
function discardControlSurfaceCard(card){
  setCardState(card.dataset.rank, { status: "discarded", platforms: [] });
  paint(card);
  updatePlatformUi(card);
  updateControlSurfaceForCard(card);
  renderCaptionQueue();
  renderFinalStage();
}
function updateCameraUi(card){
  const edit = platformEditForRank(card.dataset.rank, activePlatformForRank(card.dataset.rank));
  const camera = edit.camera;
  const context = cameraContextForCard(card);
  const surface = card.querySelector(".camera-surface");
  if (surface) updateCameraSurfaceForCard(card);
  updateCardCameraSummary(card, camera, edit);
  renderPreviewCameraTimeline(card);
  const container = card.querySelector("[data-card-camera]");
  if (!container) return;
  container.innerHTML = `<div class="camera-card-controls">${cameraPathEditorHtml(card, edit, context.duration, camera)}</div>`;
  bindCardCameraControls(card);
}
function bindCardCameraControls(card){
  const rank = card.dataset.rank;
  card.querySelectorAll("[data-camera-path-marker]").forEach(button => {
    button.addEventListener("click", () => {
      setSelectedCameraPathIndex(card, button.dataset.cameraPathMarker);
      updateCameraUi(card);
      updateCameraSurfaceForCard(card);
    });
  });
  card.querySelector("[data-camera-path-add]")?.addEventListener("click", () => addCameraPathFrameForCard(card));
  card.querySelector("[data-camera-auto]")?.addEventListener("click", () => analyzeCameraForCard(card));
  card.querySelectorAll("[data-camera-smart-mode]").forEach(button => {
    button.addEventListener("click", () => analyzeCameraForCard(card, button.dataset.cameraSmartMode));
  });
  refreshAiReadinessForCard(card);
  card.querySelector("[data-camera-path-reset]")?.addEventListener("click", () => resetCameraPathForCard(card));
  card.querySelector("[data-camera-path-set-time]")?.addEventListener("click", () => moveCameraPathFrameToPlayhead(card));
  card.querySelector("[data-camera-path-delete]")?.addEventListener("click", () => deleteCameraPathFrameForCard(card));
  card.querySelector("[data-camera-path-key]")?.addEventListener("change", event => {
    updateCameraPathFrameForCard(card, { key: event.target.value });
  });
  const keyframeStrength = card.querySelector("[data-camera-path-strength]");
  keyframeStrength?.addEventListener("input", event => {
    updateCameraPathFrameForCard(card, { strength: Number(event.target.value) }, false);
  });
  keyframeStrength?.addEventListener("change", event => {
    updateCameraPathFrameForCard(card, { strength: Number(event.target.value) });
  });
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
  const bumpers = bumpersForRank(card.dataset.rank);
  card.dataset.effect = effect.key;
  card.style.setProperty("--effect-opacity", effectOpacity(effect));
  const summary = card.querySelector("[data-effect-current]");
  if (summary) summary.textContent = `${effectLabel(effect)} | ${bumperSummary(bumpers)}`;
  renderBumperSequence(card, bumpers);
  bindBumperInputs(card);
  const container = card.querySelector("[data-card-effect]");
  if (!container) return;
  container.innerHTML = `<div class="effect-card-controls">
    <div class="effect-split">
      <section class="effect-subpanel">
        <strong>Visual</strong>
        <div class="effect-card-buttons" role="group" aria-label="Efeito do corte ${escapeAttr(card.dataset.rank)}">${effectButtonsHtml(effect)}</div>
        <label>Intensidade
          <input data-preview-effect-intensity type="range" min="0" max="100" step="5" value="${effect.intensity}">
        </label>
      </section>
      <section class="effect-subpanel">
        <strong>Vinhetas</strong>
        <div class="bumper-actions">
          ${bumperUploadHtml("intro", card.dataset.rank)}
          ${bumperUploadHtml("outro", card.dataset.rank)}
        </div>
        <div class="bumper-strip" data-bumper-strip>${bumperChipsHtml(bumpers)}</div>
        <small data-bumper-status style="min-height:16px;color:var(--color-danger);font-size:12px">${escapeHtml(card.dataset.bumperStatus || "")}</small>
        <small data-bumper-current>${escapeHtml(bumperSummary(bumpers))}</small>
      </section>
    </div>
  </div>`;
  bindCardEffectControls(card);
}
function bindBumperInputs(card){
  card.querySelectorAll("[data-bumper-video]").forEach(input => {
    if (input.dataset.bumperBound === "1") return;
    input.dataset.bumperBound = "1";
    input.addEventListener("change", () => addBumperFromInput(card, input));
  });
  card.querySelectorAll("[data-bumper-remove]").forEach(button => {
    if (button.dataset.bumperBound === "1") return;
    button.dataset.bumperBound = "1";
    button.addEventListener("click", () => removeBumperForRank(card.dataset.rank, button.dataset.bumperRemove));
  });
}
function renderBumperSequence(card, bumpers){
  const target = card.querySelector("[data-bumper-sequence]");
  if (!target) return;
  const current = normalizeBumpers(bumpers);
  const parts = [];
  if (current.intro) parts.push(`Entrada: ${current.intro.label}`);
  parts.push("Corte");
  if (current.outro) parts.push(`Saida: ${current.outro.label}`);
  target.innerHTML = parts.length > 1
    ? parts.map(part => `<span>${escapeHtml(part)}</span>`).join('<b>-></b>')
    : "";
}
function bumperUploadHtml(slot, rank){
  const label = bumperSlotLabel(slot);
  const platform = activePlatformForRank(rank);
  const preset = platformMeta[platform] || platformMeta.tiktok;
  const resolution = resolutionPresets[resolutionPresetForPlatform(platform)] || resolutionPresets.vertical_9_16;
  return `<label class="bumper-upload">
    <span>${escapeHtml(label)}</span>
    <small style="color:var(--color-text-muted);font-size:11px">${escapeHtml(resolution.label)}: ${preset.width}x${preset.height}</small>
    <input data-bumper-video="${escapeAttr(slot)}" type="file" accept="video/mp4,video/quicktime,video/webm,video/x-m4v">
  </label>`;
}
function bumperChipsHtml(bumpers){
  const current = normalizeBumpers(bumpers);
  const chips = ["intro", "outro"].map(slot => {
    const bumper = current[slot];
    if (!bumper) return "";
    const meta = [bumper.width && bumper.height ? `${bumper.width}x${bumper.height}` : "", bumper.duration ? fixed(bumper.duration) : ""].filter(Boolean).join(" - ");
    return `<span class="layer-chip bumper-chip" data-bumper-chip="${escapeAttr(slot)}">
      <span>${escapeHtml(bumperSlotLabel(slot))}: ${escapeHtml(bumper.label)}${meta ? ` (${escapeHtml(meta)})` : ""}</span>
      <button data-bumper-remove="${escapeAttr(slot)}" type="button" title="Remover vinheta" aria-label="Remover vinheta">x</button>
    </span>`;
  }).filter(Boolean).join("");
  return chips || '<span class="bumper-empty">Sem vinheta nesta plataforma</span>';
}
function bindCardEffectControls(card){
  const rank = card.dataset.rank;
  card.querySelectorAll("[data-preview-effect]").forEach(button => {
    button.addEventListener("click", () => setEffectForRank(rank, { key: button.dataset.previewEffect }));
  });
  const intensity = card.querySelector("[data-preview-effect-intensity]");
  if (intensity) {
    intensity.addEventListener("input", () => setEffectForRank(rank, { intensity: Number(intensity.value) }));
    intensity.addEventListener("change", () => setEffectForRank(rank, { intensity: Number(intensity.value) }));
  }
  bindBumperInputs(card);
}
function setBumperStatus(card, message = ""){
  card.dataset.bumperStatus = message;
  const status = card.querySelector("[data-bumper-status]");
  if (status) status.textContent = message;
}
async function addBumperFromInput(card, input){
  const file = input.files && input.files[0];
  if (!file) return;
  const rank = card.dataset.rank;
  const slot = normalizeBumperSlot(input.dataset.bumperVideo);
  const platform = activePlatformForRank(rank);
  const preset = platformMeta[platform] || platformMeta.tiktok;
  const resolution = resolutionPresets[resolutionPresetForPlatform(platform)] || resolutionPresets.vertical_9_16;
  try {
    if (file.size > maxBumperVideoBytes) throw new Error("Vinheta muito pesada. Use um video menor para o MVP local.");
    const metadata = await videoMetadataForFile(file);
    if (metadata.width !== preset.width || metadata.height !== preset.height) {
      throw new Error(`Use um video ${preset.width}x${preset.height} para ${resolution.label}.`);
    }
    showAppNotice(`Enviando vinheta de ${bumperSlotLabel(slot).toLowerCase()}...`);
    const dataUrl = await readFileAsDataUrl(file);
    const bumper = await uploadBumperAsset({
      slot,
      platform,
      label: file.name,
      width: metadata.width,
      height: metadata.height,
      duration: metadata.duration,
      data_url: dataUrl,
      gallery_path: currentGalleryPath()
    });
    setBumperForRank(rank, slot, bumper, platform);
    setBumperStatus(card, "");
    clearAppNotice();
  } catch (error) {
    const message = error.message || "Nao foi possivel usar esta vinheta.";
    showAppNotice(message);
    setBumperStatus(card, message);
    console.warn("CUTED bumper was rejected", error);
  } finally {
    input.value = "";
  }
}
function videoMetadataForFile(file){
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = () => {
      const metadata = {
        width: Number(video.videoWidth || 0),
        height: Number(video.videoHeight || 0),
        duration: Number(video.duration || 0)
      };
      URL.revokeObjectURL(url);
      if (!metadata.width || !metadata.height || !metadata.duration) {
        reject(new Error("Nao consegui ler os metadados da vinheta."));
        return;
      }
      resolve(metadata);
    };
    video.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Video de vinheta invalido ou corrompido."));
    };
    video.src = url;
  });
}
async function uploadBumperAsset(payload){
  const response = await fetch("/api/bumper-assets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok || !data.ok || !data.bumper) throw new Error(data.error || "Falha ao salvar a vinheta.");
  return data.bumper;
}
function updateOverlayUi(card){
  const layers = overlayLayersForRank(card.dataset.rank);
  const summary = card.querySelector("[data-overlay-current]");
  if (summary) summary.textContent = layers.length ? `${layers.length} camada(s)` : "Sem chamada";
  renderOverlayLayerBoxes(card, layers);
  renderOverlayTimeline(card);
  bindCardOverlayControls(card);
}
function renderOverlayLayerBoxes(card, layers){
  const list = card.querySelector("[data-overlay-layer-list]");
  if (list) {
    list.innerHTML = layers.map(overlayLayerBoxHtml).join("");
  }
  syncTimedOverlayVisibility(card);
  renderLayerStrip(card, layers);
}
function renderLayerStrip(card, layers){
  const strip = card.querySelector("[data-layer-strip]");
  if (!strip) return;
  const selectedId = card.dataset.selectedOverlayLayer || "";
  strip.innerHTML = layers.map(layer => {
    const selected = layer.id === selectedId ? " is-selected" : "";
    return `<span class="layer-chip${selected}" data-layer-chip="${escapeAttr(layer.id)}">
      <span>${escapeHtml(layerStripLabel(layer))}</span>
      <button data-layer-strip-remove="${escapeAttr(layer.id)}" type="button" title="Remover camada" aria-label="Remover camada">x</button>
    </span>`;
  }).join("");
  bindLayerStripControls(card, strip);
}
function layerStripLabel(layer){
  if (layer.kind === "image") return layer.label || "Imagem";
  if (layer.kind === "speech") return `Fala: ${layer.text || layer.label || ""}`.trim();
  if (layer.kind === "text") return layer.text || layer.label || "Texto";
  return overlayMeta[layer.key]?.label || layer.label || "Camada";
}
function bindLayerStripControls(card, strip){
  if (strip.dataset.layerStripBound) return;
  strip.dataset.layerStripBound = "1";
  strip.addEventListener("click", event => {
    const removeButton = event.target.closest("[data-layer-strip-remove]");
    if (removeButton) {
      event.preventDefault();
      event.stopPropagation();
      removeOverlayLayerForRank(card.dataset.rank, removeButton.dataset.layerStripRemove);
      delete card.dataset.selectedOverlayLayer;
      closeOverlayMenu(card);
      return;
    }
    const chip = event.target.closest("[data-layer-chip]");
    if (!chip) return;
    card.dataset.selectedOverlayLayer = chip.dataset.layerChip;
    showOverlayInspectorForLayer(card, chip.dataset.layerChip);
  });
}
function overlayLayerBoxHtml(layer){
  const selected = document.querySelector(`.card[data-rank="${CSS.escape(String(activeRankForLayer(layer)))}"]`)?.dataset.selectedOverlayLayer === layer.id;
  const selectedClass = selected ? " is-selected" : "";
  if (layer.kind === "image") {
    const src = layer.image_data_url || layer.image_file || "";
    return `<div class="overlay-box overlay-image-box${selectedClass}" data-overlay-drag data-overlay-layer="${escapeAttr(layer.id)}" data-overlay-key="image" ${overlayTimingAttrs(layer)} style="${escapeAttr(overlayStyle(layer))}">
      <img src="${escapeAttr(src)}" alt="${escapeAttr(layer.label)}">
      <button class="overlay-resize" data-overlay-resize title="Redimensionar"></button>
    </div>`;
  }
  if (layer.kind === "text") {
    return `<div class="overlay-box overlay-text-box${selectedClass}" data-overlay-drag data-overlay-layer="${escapeAttr(layer.id)}" data-overlay-key="text" data-overlay-bg="${layer.background_enabled ? "on" : "off"}" ${overlayTimingAttrs(layer)} style="${escapeAttr(overlayStyle(layer))}">
      <span>${escapeHtml(layer.text)}</span>
      <button class="overlay-resize" data-overlay-resize title="Redimensionar"></button>
    </div>`;
  }
  if (layer.kind === "speech") {
    return `<div class="overlay-box overlay-speech-box${selectedClass}" data-overlay-drag data-overlay-layer="${escapeAttr(layer.id)}" data-overlay-key="speech" ${overlayTimingAttrs(layer)} style="${escapeAttr(overlayStyle(layer))}">
      <span>${escapeHtml(layer.text)}</span>
      <button class="overlay-resize" data-overlay-resize title="Redimensionar"></button>
    </div>`;
  }
  const meta = overlayMeta[layer.key] || overlayMeta.none;
  return `<div class="overlay-box${selectedClass}" data-overlay-drag data-overlay-layer="${escapeAttr(layer.id)}" data-overlay-key="${escapeAttr(layer.key)}" style="${escapeAttr(overlayStyle(layer))}">
    <strong>${escapeHtml(meta.title)}</strong>
    <em>${escapeHtml(meta.subtitle)}</em>
    <button class="overlay-resize" data-overlay-resize title="Redimensionar"></button>
  </div>`;
}
function activeRankForLayer(layer){
  const card = Array.from(document.querySelectorAll(".card")).find(item => overlayLayersForRank(item.dataset.rank).some(current => current.id === layer.id));
  return card?.dataset.rank || "";
}
function overlayPlaceButtonsHtml(){
  return `<div class="overlay-icon-actions" aria-label="Adicionar camada">
      <button class="overlay-icon-action" data-overlay-place-text type="button" aria-label="Texto" title="Texto"><span aria-hidden="true">T</span></button>
      <button class="overlay-icon-action" data-overlay-place-speech type="button" aria-label="Fala" title="Fala"><span aria-hidden="true">F</span></button>
      <button class="overlay-icon-action" data-overlay-place-image type="button" aria-label="Imagem transparente" title="Imagem"><span aria-hidden="true">IMG</span></button>
      <button class="overlay-icon-action" data-overlay-place-camera type="button" aria-label="Camera" title="Camera"><span aria-hidden="true">CAM</span></button>
      <button class="overlay-icon-action overlay-icon-close" data-overlay-close type="button" aria-label="Fechar menu de camadas" title="Fechar"><span aria-hidden="true">x</span></button>
    </div>`;
}
function coverPlaceButtonsHtml(){
  return `<div class="overlay-icon-actions overlay-icon-actions-cover" aria-label="Adicionar na capa">
      <button class="overlay-icon-action" data-publish-cover-add="text" type="button" aria-label="Texto" title="Texto"><span aria-hidden="true">T</span></button>
      <button class="overlay-icon-action" data-publish-cover-add="speech" type="button" aria-label="Fala" title="Fala"><span aria-hidden="true">F</span></button>
      <button class="overlay-icon-action" data-publish-cover-add="image" type="button" aria-label="Imagem transparente" title="Imagem"><span aria-hidden="true">IMG</span></button>
      <button class="overlay-icon-action overlay-icon-close" data-overlay-close type="button" aria-label="Fechar menu da capa" title="Fechar"><span aria-hidden="true">x</span></button>
    </div>`;
}
function overlayInspectorHtml(layer){
  if (!layer) return overlayPlaceButtonsHtml();
  if (layer.kind === "image") {
    return overlayInspectorShell("Imagem", `${overlayImageSourceHtml(layer)}${overlayTimingInspectorHtml(layer)}${overlaySizeControlsHtml(layer, "Largura")}${overlayImageInspectorActionsHtml()}`);
  }
  if (layer.kind === "speech") {
    return overlayInspectorShell("Fala", `${overlayTextFieldHtml(layer)}${overlayTimingInspectorHtml(layer)}${overlayTextSizeControlsHtml(layer)}${overlaySpeechStyleHtml(layer)}${overlayRemoveButtonHtml()}`);
  }
  return overlayInspectorShell("Texto", `${overlayTextFieldHtml(layer)}${overlayTimingInspectorHtml(layer)}${overlayTextSizeControlsHtml(layer)}${overlayTextStyleHtml(layer)}${overlayRemoveButtonHtml()}`);
}
function coverInspectorHtml(layer){
  if (!layer) return "";
  if (layer.kind === "image") {
    return overlayInspectorShell("Imagem da capa", `${overlayImageSourceHtml(layer)}${overlaySizeControlsHtml(layer, "Largura")}${overlayImageInspectorActionsHtml()}`);
  }
  if (layer.kind === "speech") {
    return overlayInspectorShell("Fala da capa", `${overlayTextFieldHtml(layer)}${overlayTextSizeControlsHtml(layer)}${overlaySpeechStyleHtml(layer)}${overlayRemoveButtonHtml()}`);
  }
  return overlayInspectorShell("Texto da capa", `${overlayTextFieldHtml(layer)}${overlayTextSizeControlsHtml(layer)}${overlayTextStyleHtml(layer)}${overlayRemoveButtonHtml()}`);
}
function overlayInspectorShell(title, body){
  return `<div class="overlay-menu-head" data-overlay-menu-drag><strong>${escapeHtml(title)}</strong><button data-overlay-close>Fechar</button></div>
    <div class="overlay-inspector">
      ${body}
    </div>`;
}
function overlayTextFieldHtml(layer){
  return `<label>Conteudo
    <input data-layer-text type="text" value="${escapeAttr(layer.text || layer.label || "")}">
  </label>`;
}
function overlayTimingInspectorHtml(layer){
  const timing = overlayTimingForLayer(layer);
  return `<div class="overlay-inspector-row overlay-time-row">
    <label>Inicio
      <input data-layer-start type="number" min="0" max="9999" step="0.1" value="${timing.start.toFixed(1)}">
    </label>
    <label>Duracao
      <input data-layer-duration type="number" min="0.3" max="60" step="0.1" value="${timing.duration.toFixed(1)}">
    </label>
  </div>`;
}
function overlayTextSizeControlsHtml(layer){
  return `<div class="overlay-inspector-row">
    <label>Tamanho
      <input data-layer-font-size type="number" min="14" max="96" step="1" value="${Math.round(layer.font_size || 44)}">
    </label>
    <label>Largura
      <input data-layer-width type="range" min="16" max="90" step="1" value="${Math.round(layer.width * 100)}">
    </label>
    <label>Opacidade
      <input data-layer-opacity type="range" min="10" max="100" step="5" value="${layer.opacity}">
    </label>
  </div>`;
}
function overlaySizeControlsHtml(layer, widthLabel){
  return `<div class="overlay-inspector-row">
    <label>${escapeHtml(widthLabel)}
      <input data-layer-width type="range" min="8" max="90" step="1" value="${Math.round(layer.width * 100)}">
    </label>
    <label>Opacidade
      <input data-layer-opacity type="range" min="10" max="100" step="5" value="${layer.opacity}">
    </label>
  </div>`;
}
function overlayTextStyleHtml(layer){
  return `<details class="overlay-inspector-section" open>
    <summary>Aparencia</summary>
    <div class="overlay-inspector-row">
      <label>Cor
        <input data-layer-color type="color" value="${escapeAttr(layer.color || "#ffffff")}">
      </label>
      <label class="overlay-inspector-check">
        <input data-layer-background-enabled type="checkbox" ${layer.background_enabled ? "checked" : ""}>
        Fundo
      </label>
    </div>
    <div class="overlay-inspector-row">
      <label>Cor do fundo
        <input data-layer-background-color type="color" value="${escapeAttr(layer.background_color || "#000000")}">
      </label>
      <label>Opacidade fundo
        <input data-layer-background-opacity type="range" min="0" max="100" step="5" value="${layer.background_opacity}">
      </label>
    </div>
  </details>`;
}
function overlaySpeechStyleHtml(layer){
  return `<details class="overlay-inspector-section" open>
    <summary>Aparencia</summary>
    <div class="overlay-inspector-row">
      <label>Texto
        <input data-layer-color type="color" value="${escapeAttr(layer.color || "#050505")}">
      </label>
      <label>Balao
        <input data-layer-background-color type="color" value="${escapeAttr(layer.background_color || "#ffffff")}">
      </label>
    </div>
    <label>Opacidade do balao
      <input data-layer-background-opacity type="range" min="20" max="100" step="5" value="${layer.background_opacity}">
    </label>
  </details>`;
}
function overlayImageSourceHtml(layer){
  const src = layer.image_data_url || layer.image_file || "";
  return `<div class="overlay-image-source">
    ${src ? `<img src="${escapeAttr(src)}" alt="">` : "<span></span>"}
    <button type="button" data-layer-replace-image>Trocar imagem</button>
  </div>`;
}
function overlayImageInspectorActionsHtml(){
  return `<div class="overlay-inspector-actions">${overlayRemoveButtonHtml()}</div>`;
}
function overlayRemoveButtonHtml(){
  return `<button class="overlay-danger" data-layer-remove>Remover camada</button>`;
}
function bindCardOverlayControls(card){
  const imageInput = card.querySelector("[data-overlay-image]");
  if (imageInput && !imageInput.dataset.overlayImageBound) {
    imageInput.dataset.overlayImageBound = "1";
    imageInput.addEventListener("change", () => addImageOverlayFromInput(card, imageInput));
  }
  bindOverlayDrag(card);
  bindOverlayPlacement(card);
}
function addImageOverlayFromInput(card, input){
  const file = input.files && input.files[0];
  if (!file) return;
  const replaceLayerId = String(input.dataset.overlayReplaceLayer || "");
  const platform = overlayPlatformForItem(card);
  const currentLayer = replaceLayerId ? overlayLayersForRank(card.dataset.rank, platform).find(row => row.id === replaceLayerId) : null;
  const x = Number(input.dataset.overlayX || .36);
  const y = Number(input.dataset.overlayY || .34);
  const timing = {
    start_seconds: Number(input.dataset.overlayStart || 0),
    duration_seconds: Number(input.dataset.overlayDuration || 3)
  };
  overlayImageDataUrl(file).then(dataUrl => {
    const layer = normalizeImageOverlay({
      id: overlayId(),
      kind: "image",
      key: "image",
      label: file.name,
      image_data_url: dataUrl,
      x,
      y,
      width: .28,
      opacity: 100,
      ...timing
    });
    if (currentLayer) {
      card.dataset.selectedOverlayLayer = replaceLayerId;
      patchOverlayLayerForRank(card.dataset.rank, replaceLayerId, {
        image_data_url: dataUrl,
        image_file: "",
        label: file.name
      }, true, platform);
    } else {
      card.dataset.selectedOverlayLayer = layer.id;
      addOverlayLayerForRank(card.dataset.rank, layer, platform);
    }
    const surface = card.querySelector("[data-overlay-surface]");
    if (surface) {
      const inspectorLayer = currentLayer || layer;
      showOverlayInspectorForLayer(card, replaceLayerId || layer.id, inspectorLayer.x * surface.clientWidth, inspectorLayer.y * surface.clientHeight);
    }
    clearAppNotice();
  }).catch(error => {
    showAppNotice(error.message || "Nao foi possivel usar esta imagem. Tente uma versao menor.");
    console.warn("CUTED image overlay was rejected", error);
  }).finally(() => {
    input.value = "";
    delete input.dataset.overlayReplaceLayer;
  });
}
function overlayImageDataUrl(file){
  if (!["image/png", "image/webp", "image/jpeg"].includes(file.type)) {
    return Promise.reject(new Error("Use PNG, WebP ou JPG para a camada de imagem."));
  }
  if (file.size > maxOverlayImageSourceBytes) {
    return Promise.reject(new Error("Imagem muito pesada. Use uma versao de ate 6 MB para nao travar o editor."));
  }
  return readFileAsDataUrl(file).then(dataUrl => {
    if (dataUrl.length <= maxOverlayImageBytes) return dataUrl;
    return downscaleImageDataUrl(dataUrl, file.type);
  }).then(dataUrl => {
    if (dataUrl.length > maxOverlayImageBytes) {
      throw new Error("Imagem ainda ficou pesada depois da otimizacao. Use uma versao menor.");
    }
    return dataUrl;
  });
}
function readFileAsDataUrl(file){
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(new Error("Falha ao ler a imagem."));
    reader.readAsDataURL(file);
  });
}
function downscaleImageDataUrl(dataUrl, sourceType){
  return loadImageForOverlay(dataUrl).then(image => {
    const originalWidth = image.naturalWidth || image.width;
    const originalHeight = image.naturalHeight || image.height;
    const longSide = Math.max(originalWidth, originalHeight, 1);
    const outputType = sourceType === "image/jpeg" ? "image/jpeg" : "image/webp";
    const plans = [
      { pixels: maxOverlayImagePixels, quality: outputType === "image/jpeg" ? .86 : .84 },
      { pixels: 1280, quality: outputType === "image/jpeg" ? .8 : .78 },
      { pixels: 960, quality: outputType === "image/jpeg" ? .74 : .72 },
      { pixels: 720, quality: outputType === "image/jpeg" ? .7 : .68 }
    ];
    let best = "";
    return plans.reduce((chain, plan) => chain.then(done => {
      if (done) return done;
      const scale = Math.min(1, plan.pixels / longSide);
      const width = Math.max(1, Math.round(originalWidth * scale));
      const height = Math.max(1, Math.round(originalHeight * scale));
      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext("2d");
      if (!context) throw new Error("Nao foi possivel otimizar a imagem.");
      context.clearRect(0, 0, width, height);
      context.drawImage(image, 0, 0, width, height);
      return canvasToDataUrl(canvas, outputType, plan.quality).catch(() => canvasToDataUrl(canvas, "image/png")).then(candidate => {
        best = candidate.length < (best.length || Infinity) ? candidate : best;
        return candidate.length <= maxOverlayImageBytes ? candidate : "";
      });
    }), Promise.resolve("")).then(done => done || best);
  });
}
function loadImageForOverlay(dataUrl){
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("Imagem invalida ou corrompida."));
    image.src = dataUrl;
  });
}
function canvasToDataUrl(canvas, type, quality){
  return new Promise((resolve, reject) => {
    canvas.toBlob(blob => {
      if (!blob) {
        reject(new Error("Nao foi possivel otimizar a imagem."));
        return;
      }
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ""));
      reader.onerror = () => reject(new Error("Falha ao preparar a imagem."));
      reader.readAsDataURL(blob);
    }, type, quality);
  });
}
function bindOverlayPlacement(card){
  const surface = card.querySelector("[data-overlay-surface]");
  const menu = card.querySelector("[data-overlay-menu]");
  if (!surface || !menu) return;
  surface.onclick = event => {
    if (card.dataset.overlaySuppressClick) {
      delete card.dataset.overlaySuppressClick;
      return;
    }
    if (event.target.closest("[data-overlay-drag]") || event.target.closest("[data-overlay-menu]") || event.target.closest(".preview-bar")) return;
    const rect = surface.getBoundingClientRect();
    const x = clampNumber((event.clientX - rect.left) / rect.width, 0, 1);
    const y = clampNumber((event.clientY - rect.top) / rect.height, 0, 1);
    card.dataset.overlayMenuX = x;
    card.dataset.overlayMenuY = y;
    showOverlayAddMenu(card, event.clientX - rect.left, event.clientY - rect.top);
  };
  document.addEventListener("pointerdown", event => {
    if (menu.hidden || surface.contains(event.target)) return;
    closeOverlayMenu(card);
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") closeOverlayMenu(card);
  });
}
function closeOverlayMenu(card){
  const menu = card.querySelector("[data-overlay-menu]");
  if (!menu) return;
  menu.hidden = true;
  if (menu.dataset.overlayMenuMode === "add") menu.innerHTML = "";
}
function showOverlayAddMenu(card, left, top){
  const surface = card.querySelector("[data-overlay-surface]");
  const menu = card.querySelector("[data-overlay-menu]");
  if (!surface || !menu) return;
  menu.innerHTML = overlayPlaceButtonsHtml();
  menu.dataset.overlayMenuMode = "add";
  bindOverlayMenuBasics(card);
  menu.querySelector("[data-overlay-place-text]")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    const layer = defaultTextOverlay();
    Object.assign(layer, overlayTimingForCard(card));
    layer.x = Number(card.dataset.overlayMenuX || .36);
    layer.y = Number(card.dataset.overlayMenuY || .34);
    card.dataset.selectedOverlayLayer = layer.id;
    addOverlayLayerForRank(card.dataset.rank, layer, overlayPlatformForItem(card));
    showOverlayInspectorForLayer(card, layer.id, left, top);
  });
  menu.querySelector("[data-overlay-place-speech]")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    const layer = defaultSpeechOverlay();
    Object.assign(layer, overlayTimingForCard(card));
    layer.x = Number(card.dataset.overlayMenuX || .32);
    layer.y = Number(card.dataset.overlayMenuY || .24);
    card.dataset.selectedOverlayLayer = layer.id;
    addOverlayLayerForRank(card.dataset.rank, layer, overlayPlatformForItem(card));
    showOverlayInspectorForLayer(card, layer.id, left, top);
  });
  menu.querySelector("[data-overlay-place-image]")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    const input = card.querySelector("[data-overlay-image]");
    if (!input) return;
    const timing = overlayTimingForCard(card);
    input.dataset.overlayX = String(card.dataset.overlayMenuX || .36);
    input.dataset.overlayY = String(card.dataset.overlayMenuY || .34);
    input.dataset.overlayStart = String(timing.start_seconds);
    input.dataset.overlayDuration = String(timing.duration_seconds);
    closeOverlayMenu(card);
    input.click();
  });
  menu.querySelector("[data-overlay-place-camera]")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    closeOverlayMenu(card);
    addCenterCameraFrameForCard(card);
    openPreviewCameraPopover(card);
  });
  positionOverlayMenu(surface, menu, left, top);
  menu.hidden = false;
}
function showOverlayInspectorForLayer(card, layerId, left = null, top = null){
  const surface = card.querySelector("[data-overlay-surface]");
  const menu = card.querySelector("[data-overlay-menu]");
  if (!surface || !menu) return;
  const platform = overlayPlatformForItem(card);
  const layer = overlayLayersForRank(card.dataset.rank, platform).find(item => item.id === layerId);
  if (!layer) return;
  card.dataset.selectedOverlayLayer = layer.id;
  menu.innerHTML = overlayInspectorHtml(layer);
  menu.dataset.overlayMenuMode = "inspect";
  bindOverlayMenuBasics(card);
  bindOverlayInspectorControls(card, layer, platform);
  const box = card.querySelector(`[data-overlay-layer="${CSS.escape(layer.id)}"]`);
  menu.hidden = false;
  if (box) {
    positionOverlayInspectorNearLayer(surface, menu, box);
  } else {
    positionOverlayMenu(surface, menu, Number(left ?? 8), Number(top ?? 8));
  }
  renderOverlayLayerBoxes(card, overlayLayersForRank(card.dataset.rank, platform));
  bindOverlayDrag(card);
}
function positionOverlayInspectorNearLayer(surface, menu, box){
  const surfaceRect = surface.getBoundingClientRect();
  const boxRect = box.getBoundingClientRect();
  const menuWidth = menu.offsetWidth || Math.min(360, surfaceRect.width * .94);
  const menuHeight = menu.offsetHeight || 150;
  const boxLeft = boxRect.left - surfaceRect.left;
  const boxTop = boxRect.top - surfaceRect.top;
  const boxRight = boxLeft + boxRect.width;
  const boxBottom = boxTop + boxRect.height;
  const candidates = [
    { left: boxRight + 8, top: boxTop },
    { left: boxLeft - menuWidth - 8, top: boxTop },
    { left: boxLeft, top: boxTop - menuHeight - 8 },
    { left: boxLeft, top: boxBottom + 8 },
    { left: 8, top: 8 }
  ];
  const best = candidates.find(candidate => {
    const left = clampNumber(candidate.left, 8, Math.max(surfaceRect.width - menuWidth - 8, 8));
    const top = clampNumber(candidate.top, 8, Math.max(surfaceRect.height - menuHeight - 8, 8));
    return !rectsOverlap(
      { left, top, right: left + menuWidth, bottom: top + menuHeight },
      { left: boxLeft, top: boxTop, right: boxRight, bottom: boxBottom }
    );
  }) || candidates[candidates.length - 1];
  positionOverlayMenu(surface, menu, best.left, best.top);
}
function rectsOverlap(a, b){
  return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
}
function bindOverlayMenuBasics(card){
  const surface = card.querySelector("[data-overlay-surface]");
  const menu = card.querySelector("[data-overlay-menu]");
  if (!surface || !menu) return;
  menu.querySelector("[data-overlay-close]")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    closeOverlayMenu(card);
  });
  bindOverlayMenuDrag(surface, menu);
}
function bindOverlayInspectorControls(card, layer, platform = overlayPlatformForItem(card)){
  const rank = card.dataset.rank;
  const patch = (value, rerender = true) => patchOverlayLayerForRank(rank, layer.id, value, rerender, platform);
  const start = card.querySelector("[data-layer-start]");
  if (start) start.addEventListener("input", () => patch({ start_seconds: Number(start.value) }));
  const duration = card.querySelector("[data-layer-duration]");
  if (duration) duration.addEventListener("input", () => patch({ duration_seconds: Number(duration.value) }));
  const text = card.querySelector("[data-layer-text]");
  if (text) text.addEventListener("input", () => patch({ text: text.value, label: text.value }));
  const fontSize = card.querySelector("[data-layer-font-size]");
  if (fontSize) fontSize.addEventListener("input", () => patch({ font_size: Number(fontSize.value) }));
  const color = card.querySelector("[data-layer-color]");
  if (color) color.addEventListener("input", () => patch({ color: color.value }));
  const opacity = card.querySelector("[data-layer-opacity]");
  if (opacity) opacity.addEventListener("input", () => patch({ opacity: Number(opacity.value) }));
  const width = card.querySelector("[data-layer-width]");
  if (width) width.addEventListener("input", () => patch({ width: Number(width.value) / 100 }));
  card.querySelector("[data-layer-replace-image]")?.addEventListener("click", () => {
    const input = card.querySelector("[data-overlay-image]");
    if (!input) return;
    input.dataset.overlayReplaceLayer = layer.id;
    closeOverlayMenu(card);
    input.click();
  });
  const backgroundEnabled = card.querySelector("[data-layer-background-enabled]");
  if (backgroundEnabled) backgroundEnabled.addEventListener("change", () => patch({ background_enabled: backgroundEnabled.checked }));
  const backgroundColor = card.querySelector("[data-layer-background-color]");
  if (backgroundColor) backgroundColor.addEventListener("input", () => patch({ background_color: backgroundColor.value }));
  const backgroundOpacity = card.querySelector("[data-layer-background-opacity]");
  if (backgroundOpacity) backgroundOpacity.addEventListener("input", () => patch({ background_opacity: Number(backgroundOpacity.value) }));
  card.querySelector("[data-layer-remove]")?.addEventListener("click", () => {
    removeOverlayLayerForRank(rank, layer.id, platform);
    delete card.dataset.selectedOverlayLayer;
    closeOverlayMenu(card);
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
  const platforms = uniquePlatforms(current.platforms);
  card.querySelectorAll("[data-platform]").forEach(btn => {
    btn.classList.toggle("active", platforms.includes(btn.dataset.platform));
  });
  const fallback = document.body.dataset.format || "tiktok";
  const summary = platforms.length
    ? `Fila: ${platforms.map(platformLabel).join(", ")}`
    : (current.status === "liked" ? `Fila: ${platformLabel(fallback)}` : "Sem destino");
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
  if (card.dataset.publishBound === "1") syncPublishPanel(card);
}
function syncPublishPanel(card){
  const moment = (window.CUTTED_DATA.moments || []).find(item => String(item.rank) === String(card.dataset.rank));
  if (!moment) return;
  const metadata = publishMetadata(activePlatformForRank(card.dataset.rank), moment);
  const cover = metadata.cover || {};
  setPublishFieldValue(card, "title", metadata.title || "");
  setPublishFieldValue(card, "hook", metadata.hook || "");
  setPublishFieldValue(card, "description", metadata.description || "");
  setPublishFieldValue(card, "hashtags", (metadata.hashtags || []).join(" "));
  syncPublishCoverPanel(card, moment, cover);
  const tags = card.querySelector(".publish-tags");
  if (tags) tags.innerHTML = (metadata.hashtags || []).map(tag => `<span>${escapeHtml(tag)}</span>`).join("");
}
function syncPublishCoverPanel(card, moment, cover){
  const selected = cover.selected_frame || moment.frame_file || "";
  const zoom = normalizePublishCoverZoom(cover.zoom, 1);
  const x = normalizePublishCoverPosition(cover.x, zoom);
  const y = normalizePublishCoverPosition(cover.y, zoom);
  const frame = card.querySelector("[data-publish-cover-preview]");
  const preview = frame?.querySelector("img");
  if (frame) {
    frame.dataset.publishCoverCanDrag = zoom > 1.001 ? "1" : "0";
    frame.dataset.publishCoverX = String(Math.round(x));
    frame.dataset.publishCoverY = String(Math.round(y));
  }
  if (preview && selected) {
    preview.src = cacheBustedPreview(selected, `${moment.rank}-${selected}`);
    preview.style.setProperty("--publish-cover-zoom", String(zoom));
    preview.style.setProperty("--publish-cover-x", `${x}%`);
    preview.style.setProperty("--publish-cover-y", `${y}%`);
  }
  const zoomInput = card.querySelector("[data-publish-cover-zoom]");
  if (zoomInput && document.activeElement !== zoomInput) zoomInput.value = String(Math.round(zoom * 100));
  const zoomValue = card.querySelector("[data-publish-cover-zoom-value]");
  if (zoomValue) zoomValue.textContent = `${Math.round(zoom * 100)}%`;
  card.querySelectorAll("[data-publish-cover-option]").forEach(button => {
    button.classList.toggle("active", button.dataset.publishCoverOption === selected);
  });
  syncPublishCoverLayerPreview(card, cover);
  refreshPublishCoverFloatingMenu(card);
}
function syncPublishCoverLayerPreview(card, cover = null){
  const moment = (window.CUTTED_DATA.moments || []).find(item => String(item.rank) === String(card.dataset.rank));
  const currentCover = cover || (moment ? publishMetadata(activePlatformForRank(card.dataset.rank), moment).cover || {} : {});
  const layers = normalizeCoverOverlayLayers(currentCover.layers);
  const layerList = card.querySelector("[data-publish-cover-layer-list]");
  if (layerList) layerList.innerHTML = layers.map(publishCoverLayerHtml).join("");
  const layerCount = card.querySelector("[data-publish-cover-layer-count]");
  if (layerCount) layerCount.textContent = layers.length === 1 ? "1 camada" : `${layers.length} camadas`;
  bindPublishCoverLayerControls(card);
}
function setPublishFieldValue(card, field, value){
  const input = card.querySelector(`[data-publish-field="${field}"]`);
  if (!input || document.activeElement === input) return;
  input.value = value;
}
function bindPublishCoverDrag(card){
  const frame = card.querySelector("[data-publish-cover-preview]");
  if (!frame) return;
  frame.addEventListener("pointerdown", event => beginPublishCoverDrag(card, event));
}
function bindPublishCoverPlacement(card){
  const frame = card.querySelector("[data-publish-cover-preview]");
  if (!frame || frame.dataset.publishCoverPlacementBound === "1") return;
  frame.dataset.publishCoverPlacementBound = "1";
  frame.addEventListener("click", event => {
    if (card.dataset.publishCoverFrameMoved === "1") return;
    if (event.target.closest("[data-publish-cover-layer]")) return;
    showPublishCoverAddMenu(card, event.clientX, event.clientY);
  });
}
function publishCoverForCard(card){
  const moment = (window.CUTTED_DATA.moments || []).find(item => String(item.rank) === String(card.dataset.rank));
  if (!moment) return null;
  const metadata = publishMetadata(activePlatformForRank(card.dataset.rank), moment);
  return metadata.cover || {};
}
function beginPublishCoverDrag(card, event){
  if (event.button !== undefined && event.button !== 0) return;
  if (event.target.closest("[data-publish-cover-layer]")) return;
  const frame = event.currentTarget;
  const cover = publishCoverForCard(card);
  if (!cover) return;
  const zoom = normalizePublishCoverZoom(cover.zoom, 1);
  if (zoom <= 1.001) return;
  const rect = frame.getBoundingClientRect();
  const drag = {
    rank: card.dataset.rank,
    startClientX: event.clientX,
    startClientY: event.clientY,
    startX: normalizePublishCoverPosition(cover.x, zoom),
    startY: normalizePublishCoverPosition(cover.y, zoom),
    width: Math.max(rect.width, 1),
    height: Math.max(rect.height, 1),
    zoom,
    moved: false
  };
  event.preventDefault();
  frame.dataset.publishCoverDragging = "1";
  frame.setPointerCapture?.(event.pointerId);
  const move = pointerEvent => movePublishCoverDrag(card, drag, pointerEvent);
  const end = () => endPublishCoverDrag(frame, event.pointerId, move, end);
  frame.addEventListener("pointermove", move);
  frame.addEventListener("pointerup", end);
  frame.addEventListener("pointercancel", end);
}
function movePublishCoverDrag(card, drag, event){
  event.preventDefault();
  if (Math.abs(event.clientX - drag.startClientX) > 2 || Math.abs(event.clientY - drag.startClientY) > 2) drag.moved = true;
  if (drag.moved) card.querySelector("[data-publish-cover-preview]")?.setAttribute("data-publish-cover-moved", "1");
  const publish = normalizePublishEdit(cardState(drag.rank).publish);
  publish.coverZoom = drag.zoom;
  publish.coverX = normalizePublishCoverPosition(drag.startX + publishCoverDragDelta(drag.startClientX, event.clientX, drag.width, drag.zoom), drag.zoom);
  publish.coverY = normalizePublishCoverPosition(drag.startY + publishCoverDragDelta(drag.startClientY, event.clientY, drag.height, drag.zoom), drag.zoom);
  setCardState(drag.rank, { publish });
  syncPublishPanel(card);
}
function endPublishCoverDrag(frame, pointerId, move, end){
  const card = frame.closest(".card");
  if (card && frame.dataset.publishCoverMoved === "1") {
    card.dataset.publishCoverFrameMoved = "1";
    window.setTimeout(() => { delete card.dataset.publishCoverFrameMoved; }, 120);
  }
  delete frame.dataset.publishCoverMoved;
  frame.dataset.publishCoverDragging = "0";
  if (frame.hasPointerCapture?.(pointerId)) frame.releasePointerCapture(pointerId);
  frame.removeEventListener("pointermove", move);
  frame.removeEventListener("pointerup", end);
  frame.removeEventListener("pointercancel", end);
  renderCaptionQueue();
}
function publishCoverDragDelta(start, current, size, zoom){
  const zoomGap = Math.max(normalizePublishCoverZoom(zoom, 1) - 1, 0.08);
  return ((start - current) / Math.max(size, 1)) * 100 / zoomGap;
}
function bindPublishCoverImageInput(card){
  const input = card.querySelector("[data-publish-cover-image]");
  if (!input || input.dataset.publishCoverImageBound === "1") return;
  input.dataset.publishCoverImageBound = "1";
  input.addEventListener("change", () => addPublishCoverImageFromInput(card, input));
}
function addPublishCoverLayer(card, kind){
  if (kind === "image") {
    const input = card.querySelector("[data-publish-cover-image]");
    if (input) {
      delete input.dataset.coverReplaceLayer;
      input.dataset.coverX = String(card.dataset.coverMenuX || .28);
      input.dataset.coverY = String(card.dataset.coverMenuY || .28);
      closePublishCoverMenu(card);
      input.click();
    }
    return;
  }
  const layer = kind === "speech" ? defaultSpeechOverlay() : defaultTextOverlay();
  layer.x = clampNumber(Number(card.dataset.coverMenuX || (kind === "speech" ? .18 : .16)), 0, .84);
  layer.y = clampNumber(Number(card.dataset.coverMenuY || (kind === "speech" ? .18 : .12)), 0, .9);
  layer.width = kind === "speech" ? .64 : .68;
  layer.start_seconds = 0;
  layer.duration_seconds = 3;
  card.dataset.selectedCoverLayer = layer.id;
  addCoverLayerForRank(card.dataset.rank, layer);
  showPublishCoverInspector(card, layer.id);
}
function addPublishCoverImageFromInput(card, input){
  const file = input.files && input.files[0];
  if (!file) return;
  const replaceLayerId = String(input.dataset.coverReplaceLayer || "");
  overlayImageDataUrl(file).then(dataUrl => {
    if (replaceLayerId) {
      patchCoverLayerForRank(card.dataset.rank, replaceLayerId, {
        image_data_url: dataUrl,
        image_file: "",
        label: file.name
      });
      card.dataset.selectedCoverLayer = replaceLayerId;
      showPublishCoverInspector(card, replaceLayerId);
    } else {
      const layer = normalizeImageOverlay({
        id: overlayId(),
        kind: "image",
        key: "image",
        label: file.name,
        image_data_url: dataUrl,
        x: clampNumber(Number(input.dataset.coverX || .28), 0, .92),
        y: clampNumber(Number(input.dataset.coverY || .28), 0, .92),
        width: .42,
        opacity: 100,
        start_seconds: 0,
        duration_seconds: 3
      });
      card.dataset.selectedCoverLayer = layer.id;
      addCoverLayerForRank(card.dataset.rank, layer);
      showPublishCoverInspector(card, layer.id);
    }
    clearAppNotice();
  }).catch(error => {
    showAppNotice(error.message || "Nao foi possivel usar esta imagem na capa.");
    console.warn("CUTED cover image overlay was rejected", error);
  }).finally(() => {
    input.value = "";
    delete input.dataset.coverReplaceLayer;
    delete input.dataset.coverX;
    delete input.dataset.coverY;
  });
}
function coverLayersForRank(rank){
  return normalizePublishEdit(cardState(String(rank)).publish).coverLayers;
}
function setCoverLayersForRank(rank, layers, rerender = true){
  const current = cardState(String(rank));
  const publish = normalizePublishEdit(current.publish);
  publish.coverLayers = normalizeCoverOverlayLayers(layers);
  setCardState(String(rank), { publish });
  const card = cardForRank(rank);
  if (rerender && card) syncPublishPanel(card);
  if (rerender) renderCaptionQueue();
}
function addCoverLayerForRank(rank, layer){
  setCoverLayersForRank(rank, [...coverLayersForRank(rank), normalizeOverlayLayer(layer)]);
}
function patchCoverLayerForRank(rank, id, patch, rerender = true){
  const layers = coverLayersForRank(rank).map(layer => {
    if (layer.id !== id) return layer;
    return normalizeOverlayLayer(Object.assign({}, layer, patch));
  });
  setCoverLayersForRank(rank, layers, rerender);
}
function removeCoverLayerForRank(rank, id){
  setCoverLayersForRank(rank, coverLayersForRank(rank).filter(layer => layer.id !== id));
}
function selectedCoverLayerForCard(card){
  const selected = String(card.dataset.selectedCoverLayer || "");
  return coverLayersForRank(card.dataset.rank).find(layer => layer.id === selected) || null;
}
function publishCoverMenuSurface(card){
  return card.querySelector("[data-publish-cover-stage]") || card.querySelector("[data-publish-cover-preview]");
}
function closePublishCoverMenu(card){
  const menu = card.querySelector("[data-publish-cover-menu]");
  if (!menu) return;
  menu.hidden = true;
  menu.innerHTML = "";
  delete card.dataset.selectedCoverLayer;
}
function bindPublishCoverMenuBasics(card){
  const surface = publishCoverMenuSurface(card);
  const menu = card.querySelector("[data-publish-cover-menu]");
  if (!surface || !menu) return;
  menu.querySelector("[data-overlay-close]")?.addEventListener("click", event => {
    event.preventDefault();
    event.stopPropagation();
    closePublishCoverMenu(card);
  });
  bindOverlayMenuDrag(surface, menu);
}
function publishCoverMenuPoint(card, clientX, clientY){
  const frame = card.querySelector("[data-publish-cover-preview]");
  const surface = publishCoverMenuSurface(card);
  const frameRect = frame?.getBoundingClientRect();
  const surfaceRect = surface?.getBoundingClientRect();
  if (!frameRect || !surfaceRect) return { x: .28, y: .28, left: 8, top: 8 };
  const x = clampNumber((clientX - frameRect.left) / Math.max(frameRect.width, 1), 0, .92);
  const y = clampNumber((clientY - frameRect.top) / Math.max(frameRect.height, 1), 0, .92);
  return { x, y, left: clientX - surfaceRect.left, top: clientY - surfaceRect.top };
}
function showPublishCoverAddMenu(card, clientX, clientY){
  const surface = publishCoverMenuSurface(card);
  const menu = card.querySelector("[data-publish-cover-menu]");
  if (!surface || !menu) return;
  const point = publishCoverMenuPoint(card, clientX, clientY);
  card.dataset.coverMenuX = String(point.x);
  card.dataset.coverMenuY = String(point.y);
  delete card.dataset.selectedCoverLayer;
  menu.innerHTML = coverPlaceButtonsHtml();
  menu.dataset.overlayMenuMode = "add";
  bindPublishCoverMenuBasics(card);
  bindPublishCoverAddButtons(card);
  positionOverlayMenu(surface, menu, point.left, point.top);
  menu.hidden = false;
}
function refreshPublishCoverFloatingMenu(card){
  const layer = selectedCoverLayerForCard(card);
  const menu = card.querySelector("[data-publish-cover-menu]");
  if (!menu || menu.hidden || !layer) return;
  showPublishCoverInspector(card, layer.id);
}
function showPublishCoverInspector(card, layerId){
  const surface = publishCoverMenuSurface(card);
  const menu = card.querySelector("[data-publish-cover-menu]");
  if (!surface || !menu) return;
  card.dataset.selectedCoverLayer = layerId;
  const layer = selectedCoverLayerForCard(card);
  if (!layer) return;
  menu.innerHTML = coverInspectorHtml(layer);
  menu.dataset.overlayMenuMode = "inspect";
  bindPublishCoverMenuBasics(card);
  bindPublishCoverInspectorControls(card, layer);
  menu.hidden = false;
  const box = card.querySelector(`[data-publish-cover-layer="${CSS.escape(layer.id)}"]`);
  if (box) positionOverlayInspectorNearLayer(surface, menu, box);
  else positionOverlayMenu(surface, menu, 8, 8);
}
function bindPublishCoverInspectorControls(card, layer){
  const rank = card.dataset.rank;
  const patch = value => {
    patchCoverLayerForRank(rank, layer.id, value, false);
    syncPublishCoverLayerPreview(card);
    renderCaptionQueue();
  };
  const menu = card.querySelector("[data-publish-cover-menu]");
  const text = menu?.querySelector("[data-layer-text]");
  if (text) text.addEventListener("input", () => patch({ text: text.value, label: text.value }));
  const fontSize = menu?.querySelector("[data-layer-font-size]");
  if (fontSize) fontSize.addEventListener("input", () => patch({ font_size: Number(fontSize.value) }));
  const color = menu?.querySelector("[data-layer-color]");
  if (color) color.addEventListener("input", () => patch({ color: color.value }));
  const opacity = menu?.querySelector("[data-layer-opacity]");
  if (opacity) opacity.addEventListener("input", () => patch({ opacity: Number(opacity.value) }));
  const width = menu?.querySelector("[data-layer-width]");
  if (width) width.addEventListener("input", () => patch({ width: Number(width.value) / 100 }));
  const backgroundEnabled = menu?.querySelector("[data-layer-background-enabled]");
  if (backgroundEnabled) backgroundEnabled.addEventListener("change", () => patch({ background_enabled: backgroundEnabled.checked }));
  const backgroundColor = menu?.querySelector("[data-layer-background-color]");
  if (backgroundColor) backgroundColor.addEventListener("input", () => patch({ background_color: backgroundColor.value }));
  const backgroundOpacity = menu?.querySelector("[data-layer-background-opacity]");
  if (backgroundOpacity) backgroundOpacity.addEventListener("input", () => patch({ background_opacity: Number(backgroundOpacity.value) }));
  menu?.querySelector("[data-layer-replace-image]")?.addEventListener("click", () => {
    const input = card.querySelector("[data-publish-cover-image]");
    if (!input) return;
    input.dataset.coverReplaceLayer = layer.id;
    closePublishCoverMenu(card);
    input.click();
  });
  menu?.querySelector("[data-layer-remove]")?.addEventListener("click", () => {
    removeCoverLayerForRank(rank, layer.id);
    closePublishCoverMenu(card);
  });
}
function bindPublishCoverAddButtons(card){
  const menu = card.querySelector("[data-publish-cover-menu]");
  if (!menu) return;
  menu.querySelectorAll("[data-publish-cover-add]").forEach(button => {
    button.addEventListener("click", () => addPublishCoverLayer(card, button.dataset.publishCoverAdd));
  });
}
function bindPublishCoverLayerControls(card){
  const frame = card.querySelector("[data-publish-cover-preview]");
  if (!frame) return;
  frame.querySelectorAll("[data-publish-cover-layer]").forEach(layerNode => bindPublishCoverLayerDrag(card, frame, layerNode));
}
function bindPublishCoverLayerDrag(card, frame, layerNode){
  let drag = null;
  const start = event => {
    if (event.type === "mousedown" && drag) return;
    const resizing = !!event.target?.closest?.("[data-publish-cover-resize]");
    const frameRect = frame.getBoundingClientRect();
    const layerRect = layerNode.getBoundingClientRect();
    drag = {
      pointerId: event.pointerId,
      type: resizing ? "resize" : "move",
      startX: event.clientX,
      startY: event.clientY,
      startLeft: layerRect.left - frameRect.left,
      startTop: layerRect.top - frameRect.top,
      startWidth: layerRect.width,
      frameWidth: Math.max(frameRect.width, 1),
      frameHeight: Math.max(frameRect.height, 1),
      moved: false
    };
    card.dataset.selectedCoverLayer = layerNode.dataset.publishCoverLayer;
    layerNode.classList.add("is-selected");
    if (event.pointerId !== undefined && layerNode.setPointerCapture) layerNode.setPointerCapture(event.pointerId);
    document.addEventListener("pointermove", move);
    document.addEventListener("pointerup", end, { once: true });
    document.addEventListener("pointercancel", end, { once: true });
    document.addEventListener("mousemove", move);
    document.addEventListener("mouseup", end, { once: true });
    event.preventDefault();
    event.stopPropagation();
  };
  const move = event => {
    if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
    const dx = event.clientX - drag.startX;
    const dy = event.clientY - drag.startY;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) drag.moved = true;
    const patch = {};
    if (drag.type === "resize") {
      const minWidth = layerNode.dataset.coverLayerKind === "image" ? .08 : .16;
      patch.width = clampNumber((drag.startWidth + dx) / drag.frameWidth, minWidth, .9);
      layerNode.style.width = `${patch.width * 100}%`;
    } else {
      const layerRect = layerNode.getBoundingClientRect();
      const left = clampNumber(drag.startLeft + dx, 0, Math.max(drag.frameWidth - layerRect.width, 0));
      const top = clampNumber(drag.startTop + dy, 0, Math.max(drag.frameHeight - layerRect.height, 0));
      patch.x = left / drag.frameWidth;
      patch.y = clampNumber(top / drag.frameHeight + coverLayerVerticalLift, 0, 1);
      layerNode.style.left = `${patch.x * 100}%`;
      layerNode.style.top = `${liftedCoverLayerY(patch.y) * 100}%`;
    }
    patchCoverLayerForRank(card.dataset.rank, layerNode.dataset.publishCoverLayer, patch, false);
    event.preventDefault();
    event.stopPropagation();
  };
  const end = event => {
    if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
    const shouldInspect = !drag.moved;
    drag = null;
    document.removeEventListener("pointermove", move);
    document.removeEventListener("mousemove", move);
    document.removeEventListener("pointerup", end);
    document.removeEventListener("pointercancel", end);
    document.removeEventListener("mouseup", end);
    syncPublishPanel(card);
    renderCaptionQueue();
    if (shouldInspect) showPublishCoverInspector(card, layerNode.dataset.publishCoverLayer);
    event.preventDefault();
    event.stopPropagation();
  };
  layerNode.onpointerdown = start;
  layerNode.onmousedown = start;
  layerNode.querySelectorAll("[data-publish-cover-resize]").forEach(handle => {
    handle.onpointerdown = start;
    handle.onmousedown = start;
  });
}
function bindPublishPanel(card){
  if (card.dataset.publishBound === "1") return;
  card.dataset.publishBound = "1";
  syncPublishPanel(card);
  bindPublishCoverDrag(card);
  bindPublishCoverPlacement(card);
  bindPublishCoverImageInput(card);
  card.querySelectorAll("[data-publish-field]").forEach(input => {
    input.addEventListener("input", () => {
      const current = cardState(card.dataset.rank);
      const publish = normalizePublishEdit(current.publish);
      publish[input.dataset.publishField] = input.dataset.publishField === "hashtags"
        ? normalizePublishHashtags(input.value)
        : cleanPublishField(input.value, input.dataset.publishField === "description" ? 360 : 140);
      setCardState(card.dataset.rank, { publish });
      syncPublishPanel(card);
      renderCaptionQueue();
    });
  });
  card.querySelectorAll("[data-publish-cover-option]").forEach(button => {
    button.addEventListener("click", () => {
      const publish = normalizePublishEdit(cardState(card.dataset.rank).publish);
      publish.coverFrame = cleanPublishField(button.dataset.publishCoverOption, 260);
      setCardState(card.dataset.rank, { publish });
      syncPublishPanel(card);
      renderCaptionQueue();
    });
  });
  card.querySelector("[data-publish-cover-zoom]")?.addEventListener("input", event => {
    const publish = normalizePublishEdit(cardState(card.dataset.rank).publish);
    const zoom = normalizePublishCoverZoom(Number(event.target.value) / 100, 1);
    publish.coverZoom = zoom;
    if (zoom <= 1.001) {
      publish.coverX = 50;
      publish.coverY = 50;
    }
    setCardState(card.dataset.rank, { publish });
    syncPublishPanel(card);
    renderCaptionQueue();
  });
  card.querySelector("[data-publish-cover-zoom-reset]")?.addEventListener("click", () => {
    const publish = normalizePublishEdit(cardState(card.dataset.rank).publish);
    publish.coverZoom = 1;
    publish.coverX = 50;
    publish.coverY = 50;
    setCardState(card.dataset.rank, { publish });
    syncPublishPanel(card);
    renderCaptionQueue();
  });
  card.querySelector("[data-publish-reset]")?.addEventListener("click", () => {
    setCardState(card.dataset.rank, { publish: {} });
    syncPublishPanel(card);
    renderCaptionQueue();
  });
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
  const scrubInput = card.querySelector("[data-trim-scrub]");
  if (startInput) {
    startInput.max = values.duration.toFixed(1);
    startInput.value = values.startPos;
  }
  if (endInput) {
    endInput.max = values.duration.toFixed(1);
    endInput.value = values.endPos;
  }
  if (scrubInput) scrubInput.max = values.duration.toFixed(1);
  const startOutput = card.querySelector("[data-output=start]");
  const endOutput = card.querySelector("[data-output=end]");
  if (startOutput) startOutput.textContent = fixed(values.trimStart);
  if (endOutput) endOutput.textContent = fixed(values.trimEnd);
  const summary = `${fixed(values.adjustedStart)} - ${fixed(values.adjustedEnd)} (${fixed(values.adjustedEnd - values.adjustedStart)})`;
  const trimSummary = card.querySelector("[data-trim-summary]");
  if (trimSummary) trimSummary.textContent = summary;
  const cardSummary = card.querySelector("[data-card-summary]");
  if (cardSummary) cardSummary.textContent = summary;
  const fill = card.querySelector("[data-trim-fill]");
  const duration = Math.max(values.duration, .1);
  if (fill) {
    fill.style.left = `${(values.startPos / duration) * 100}%`;
    fill.style.right = `${100 - ((values.endPos / duration) * 100)}%`;
  }
  const selected = card.querySelector("[data-timeline-selected]");
  if (selected && fill) {
    selected.style.left = fill.style.left;
    selected.style.right = fill.style.right;
  }
  const windowLabel = card.querySelector("[data-timeline-window]");
  if (windowLabel) windowLabel.textContent = `${fixed(values.startPos)} - ${fixed(values.endPos)} no clipe`;
  renderCardRowTimeline(card, values);
  updateTimelinePlayhead(card);
  syncPreviewCaptions(card);
}
function renderCardRowTimeline(card, values = null){
  const container = card.querySelector("[data-card-row-timeline]");
  if (!container) return;
  if (card.open && (card.__liveTimelineController || card.__liveTimelineLoading)) return;
  const current = values || trimValues(card);
  const duration = Math.max(current.duration, .1);
  const endPos = trimEndPosition(current);
  const platform = activePlatformForRank(card.dataset.rank);
  const edit = platformEditForRank(card.dataset.rank, platform);
  const path = cameraPathForEdit(edit, duration).slice(0, 24);
  const left = clampNumber((current.trimStart / duration) * 100, 0, 100);
  const right = clampNumber((endPos / duration) * 100, 0, 100);
  const context = cameraContextForCard(card);
  const playhead = clampNumber((context.position / duration) * 100, 0, 100);
  const markers = path.map(frame => {
    const markerLeft = clampNumber((Number(frame.time || 0) / duration) * 100, 0, 100);
    const label = directorMarkerTitle(edit.director_plan, frame);
    return `<span class="clip-row-timeline-marker" style="left:${markerLeft.toFixed(2)}%" title="${escapeAttr(label)}"></span>`;
  }).join("");
  container.innerHTML = `<span class="clip-row-timeline-track"></span>
    <span class="clip-row-timeline-window" style="left:${left.toFixed(2)}%;right:${(100 - right).toFixed(2)}%"></span>
    ${markers}
    <span class="clip-row-timeline-playhead" style="left:${playhead.toFixed(2)}%"></span>`;
}
function updateTimelinePlayhead(card, time = null){
  const values = trimValues(card);
  const video = primaryCameraVideo(card);
  const raw = time === null && video && Number.isFinite(video.currentTime) ? video.currentTime : time;
  const current = clampPreviewTime(values, Number(raw ?? values.trimStart));
  if (time === null && video && trimRangeActive(values) && Math.abs(Number(video.currentTime || 0) - current) > .05) {
    video.currentTime = current;
  }
  syncPreviewPlaybackFrame(card, current);
}
function syncPreviewPlaybackFrame(card, time = null){
  const values = trimValues(card);
  const video = primaryCameraVideo(card);
  const raw = time === null && video && Number.isFinite(video.currentTime) ? video.currentTime : time;
  const current = clampPreviewTime(values, Number(raw ?? values.trimStart));
  const scrubInput = card.querySelector("[data-trim-scrub]");
  if (scrubInput) scrubInput.value = current.toFixed(1);
  const playhead = card.querySelector("[data-timeline-playhead]");
  if (playhead) playhead.style.left = `${(current / Math.max(values.duration, .1)) * 100}%`;
  const output = card.querySelector("[data-output=current]");
  if (output) output.textContent = fixed(values.start + current);
  updateCameraSurfaceForCard(card, current);
  updatePreviewCameraTimelinePlayhead(card, current);
  syncPreviewCaptions(card, current);
  syncTimedOverlayVisibility(card, current);
}
function previewCameraTimelineContext(card){
  const values = trimValues(card);
  const context = cameraContextForCard(card);
  const duration = cameraTimelineDurationForCard(card);
  const platform = activePlatformForRank(card.dataset.rank);
  const edit = platformEditForRank(card.dataset.rank, platform);
  const path = cameraPathForEdit(edit, duration);
  return { values, context, duration, platform, edit, path };
}
function renderPreviewCameraTimeline(card){
  if (card.open) {
    if (renderLivePreviewCameraTimeline(card)) return;
    renderLegacyPreviewCameraTimeline(card);
    return;
  }
  destroyLivePreviewCameraTimeline(card);
  renderCardRowTimeline(card);
}
function overlayTimelineLayersForCard(card){
  return overlayLayersForRank(card.dataset.rank)
    .filter(layer => ["image", "speech", "text"].includes(layer.kind));
}
function overlayTimelineLabel(layer){
  if (layer.kind === "image") return "Img";
  if (layer.kind === "speech") return "Fala";
  return "Texto";
}
function overlayTimelineItemHtml(layer, duration, index){
  const timing = overlayTimingForLayer(layer);
  const start = clampNumber(timing.start, 0, Math.max(duration - .3, 0));
  const itemDuration = clampNumber(timing.duration, .3, Math.max(duration - start, .3));
  const left = clampNumber((start / Math.max(duration, .3)) * 100, 0, 100);
  const width = clampNumber((itemDuration / Math.max(duration, .3)) * 100, 1, 100 - left);
  const row = index % 3;
  const selected = document.querySelector(`.card[data-rank="${CSS.escape(String(activeRankForLayer(layer)))}"]`)?.dataset.selectedOverlayLayer === layer.id;
  return `<button class="overlay-timeline-item${selected ? " is-selected" : ""}" data-overlay-timeline-layer="${escapeAttr(layer.id)}" data-overlay-kind="${escapeAttr(layer.kind)}" data-overlay-start="${start.toFixed(3)}" data-overlay-duration="${itemDuration.toFixed(3)}" style="--overlay-time-left:${left.toFixed(3)}%;--overlay-time-width:${width.toFixed(3)}%;--overlay-time-row:${row}" type="button" title="${escapeAttr(`${overlayTimelineLabel(layer)} ${fixed(start)} por ${fixed(itemDuration)}`)}"><span>${escapeHtml(overlayTimelineLabel(layer))}</span><i data-overlay-timeline-resize></i></button>`;
}
function renderOverlayTimeline(card){
  const container = card.querySelector("[data-preview-camera-timeline]");
  if (!container) return;
  let track = card.querySelector("[data-overlay-timeline]");
  const layers = overlayTimelineLayersForCard(card);
  if (!track) {
    track = document.createElement("div");
    track.className = "overlay-timeline";
    track.setAttribute("data-overlay-timeline", "");
  }
  if (track.parentElement !== container) {
    container.appendChild(track);
  }
  const duration = cameraTimelineDurationForCard(card);
  track.innerHTML = layers.map((layer, index) => overlayTimelineItemHtml(layer, duration, index)).join("");
  track.hidden = !layers.length;
  bindOverlayTimelineControls(card, track);
  syncTimedOverlayVisibility(card);
}
function bindOverlayTimelineControls(card, track){
  if (track.dataset.overlayTimelineBound) return;
  track.dataset.overlayTimelineBound = "1";
  track.addEventListener("pointerdown", event => startOverlayTimelineDrag(card, track, event));
}
function startOverlayTimelineDrag(card, track, event){
  const item = event.target.closest("[data-overlay-timeline-layer]");
  if (!item) return;
  event.preventDefault();
  event.stopPropagation();
  const platform = overlayPlatformForItem(card);
  const layer = overlayLayersForRank(card.dataset.rank, platform).find(row => row.id === item.dataset.overlayTimelineLayer);
  if (!layer) return;
  const timing = overlayTimingForLayer(layer);
  const state = {
    duration: cameraTimelineDurationForCard(card),
    id: layer.id,
    moved: false,
    resizing: Boolean(event.target.closest("[data-overlay-timeline-resize]")),
    startDuration: timing.duration,
    startSeconds: timing.start,
    startX: event.clientX
  };
  if (item.setPointerCapture && event.pointerId !== undefined) item.setPointerCapture(event.pointerId);
  const move = moveEvent => moveOverlayTimelineDrag(card, track, item, state, moveEvent, platform);
  const end = endEvent => endOverlayTimelineDrag(card, item, state, endEvent, move, platform);
  document.addEventListener("pointermove", move);
  document.addEventListener("pointerup", end, { once: true });
  document.addEventListener("pointercancel", end, { once: true });
}
function overlayTimelinePatchFromDrag(track, state, event){
  const rect = track.getBoundingClientRect();
  const delta = rect.width ? ((event.clientX - state.startX) / rect.width) * state.duration : 0;
  if (state.resizing) {
    const maxDuration = Math.max(state.duration - state.startSeconds, .3);
    return { duration_seconds: Number(clampNumber(state.startDuration + delta, .3, maxDuration).toFixed(3)) };
  }
  const start = clampNumber(state.startSeconds + delta, 0, Math.max(state.duration - state.startDuration, 0));
  return { start_seconds: Number(start.toFixed(3)) };
}
function moveOverlayTimelineDrag(card, track, item, state, event, platform){
  event.preventDefault();
  event.stopPropagation();
  state.moved = state.moved || Math.abs(event.clientX - state.startX) > 2;
  const patch = overlayTimelinePatchFromDrag(track, state, event);
  patchOverlayLayerForRank(card.dataset.rank, state.id, patch, false, platform);
  updateOverlayTimingDom(card, state.id, patch);
  updateOverlayTimelineItem(item, patch, state.duration);
  syncTimedOverlayVisibility(card);
}
function endOverlayTimelineDrag(card, item, state, event, move, platform){
  document.removeEventListener("pointermove", move);
  event.preventDefault();
  event.stopPropagation();
  if (!state.moved) {
    card.dataset.selectedOverlayLayer = state.id;
    showOverlayInspectorForLayer(card, state.id);
  }
  renderOverlayTimeline(card);
}
function updateOverlayTimingDom(card, layerId, patch){
  const box = card.querySelector(`[data-overlay-layer="${CSS.escape(layerId)}"]`);
  if (box && patch.start_seconds !== undefined) box.dataset.overlayStart = Number(patch.start_seconds).toFixed(3);
  if (box && patch.duration_seconds !== undefined) box.dataset.overlayDuration = Number(patch.duration_seconds).toFixed(3);
}
function updateOverlayTimelineItem(item, patch, totalDuration){
  const start = clampNumber(patch.start_seconds ?? item.dataset.overlayStart ?? 0, 0, Math.max(totalDuration - .3, 0));
  const duration = clampNumber(patch.duration_seconds ?? item.dataset.overlayDuration ?? 3, .3, Math.max(totalDuration - start, .3));
  item.dataset.overlayStart = start.toFixed(3);
  item.dataset.overlayDuration = duration.toFixed(3);
  item.style.setProperty("--overlay-time-left", `${((start / Math.max(totalDuration, .3)) * 100).toFixed(3)}%`);
  item.style.setProperty("--overlay-time-width", `${((duration / Math.max(totalDuration, .3)) * 100).toFixed(3)}%`);
}
function renderLivePreviewCameraTimeline(card){
  const container = card.querySelector("[data-preview-camera-timeline]");
  if (!container || container.dataset.liveTimelineFailed === "1") return false;
  const live = window.CuttedLiveTimeline;
  if (!live || typeof live.createLiveTimeline !== "function") return false;
  const options = liveTimelineOptionsForCard(card);
  container.classList.add("preview-camera-timeline--live");
  if (card.__liveTimelineController) {
    ensureLivePreviewCameraPopover(card);
    card.__liveTimelineController.update(options);
    loadLiveTimelineWaveform(card);
    renderOverlayTimeline(card);
    return true;
  }
  if (card.__liveTimelineLoading) return true;
  card.__liveTimelineLoading = true;
  container.innerHTML = '<div class="preview-live-timeline-loading">Carregando timeline...</div>';
  live.createLiveTimeline(container, options).then(controller => {
    card.__liveTimelineController = controller;
    delete card.__liveTimelineLoading;
    controller.update(liveTimelineOptionsForCard(card));
    ensureLivePreviewCameraPopover(card);
    loadLiveTimelineWaveform(card);
    renderOverlayTimeline(card);
  }).catch(error => {
    console.warn("Timeline viva indisponivel; usando timeline compacta.", error);
    delete card.__liveTimelineLoading;
    container.dataset.liveTimelineFailed = "1";
    renderLegacyPreviewCameraTimeline(card);
  });
  return true;
}
function destroyLivePreviewCameraTimeline(card){
  if (card.__liveTimelineController && typeof card.__liveTimelineController.destroy === "function") {
    card.__liveTimelineController.destroy();
  }
  delete card.__liveTimelineController;
  delete card.__liveTimelineLoading;
  const container = card.querySelector("[data-preview-camera-timeline]");
  if (container) {
    container.classList.remove("preview-camera-timeline--live");
    container.removeAttribute("style");
  }
}
function liveTimelineOptionsForCard(card){
  const values = trimValues(card);
  const duration = cameraTimelineDurationForCard(card);
  const platform = activePlatformForRank(card.dataset.rank);
  const edit = platformEditForRank(card.dataset.rank, platform);
  const path = cameraPathForEdit(edit, duration);
  const video = primaryCameraVideo(card);
  const pending = Number(card.dataset.pendingSeek);
  const playhead = Number.isFinite(pending) ? pending : cameraTimelinePositionForCard(card);
  const model = {
    cameraPath: path,
    duration,
    effectKeyframes: liveTimelineEffectKeyframesForCard(card),
    muted: video ? video.muted : false,
    playhead,
    selectedCameraIndex: selectedCameraPathIndex(card, path),
    trimEndPosition: trimEndPosition(values),
    trimStart: values.trimStart,
    volume: video ? video.volume : defaultPreviewVolume,
    waveformPayload: parsePreviewWaveform(card.dataset.previewWaveformPeaks)
  };
  const live = window.CuttedLiveTimeline || {};
  const options = typeof live.createLiveTimelineOptionsFromCuttedModel === "function"
    ? live.createLiveTimelineOptionsFromCuttedModel(model)
    : fallbackLiveTimelineOptions(model);
  return Object.assign(options, {
    callbacks: liveTimelineCallbacksForCard(card),
    logoUrl: "assets/brand/cuted-logo-transparent.png",
    playing: video ? !video.paused && !video.ended : false,
    showInspector: false,
    showVolume: false,
    trimEnabled: card.dataset.trimMode === "1"
  });
}
function fallbackLiveTimelineOptions(model){
  const camera = (model.cameraPath || []).map((frame, index) => ({
    id: `camera-${index}`,
    layer: "camera",
    time: clampNumber(Number(frame.time || 0), 0, Math.max(model.duration, .3)),
    label: frame.label || frame.key || frame.source || `Camera ${index + 1}`,
    editable: true,
    intensity: clampNumber(Number(frame.confidence ?? 0.68), .18, 1)
  }));
  return {
    duration: model.duration,
    keyframes: camera,
    muted: model.muted,
    peaks: model.waveformPayload,
    playhead: model.playhead,
    selectedKeyframeId: camera[model.selectedCameraIndex]?.id || null,
    trimEnd: model.trimEndPosition,
    trimStart: model.trimStart,
    volume: model.volume
  };
}
function liveTimelineEffectKeyframesForCard(card){
  const current = cardState(card.dataset.rank);
  const effectFrames = Array.isArray(current.effect_keyframes) ? current.effect_keyframes : [];
  return effectFrames;
}
function liveTimelineCallbacksForCard(card){
  return {
    onSeek: time => {
      setPreviewPlayback(card, false);
      seekTimeline(card, time, { userInitiated: true, mode: "free" });
    },
    onTrimChange: trim => applyLiveTimelineTrim(card, trim),
    onKeyframeOpen: keyframe => openLiveTimelineKeyframe(card, keyframe),
    onPlayToggle: playing => setPreviewPlayback(card, playing)
  };
}
function applyLiveTimelineTrim(card, trim){
  setPreviewPlayback(card, false);
  const duration = Number(card.dataset.duration) || 0;
  const start = clampNumber(Number(trim.start || 0), 0, Math.max(duration - 1, 0));
  const end = clampNumber(Number(trim.end || duration), start + 1, Math.max(duration, start + 1));
  setCardState(card.dataset.rank, { trimStart: start, trimEnd: Math.max(duration - end, 0) });
  updateTrimUi(card);
  seekTimeline(card, trim.side === "end" ? end : start, { userInitiated: true, mode: "trim" });
  renderCaptionQueue();
}
function openLiveTimelineKeyframe(card, keyframe){
  if (!keyframe || keyframe.layer !== "camera") return;
  setPreviewPlayback(card, false);
  const match = String(keyframe.id || "").match(/camera-(\\d+)/);
  if (match) setSelectedCameraPathIndex(card, Number(match[1]));
  ensureLivePreviewCameraPopover(card);
  updateCameraUi(card);
  openPreviewCameraPopover(card, "edit");
}
function ensureLivePreviewCameraPopover(card){
  const rank = String(card?.dataset?.rank || "");
  if (!rank) return null;
  let popover = livePreviewCameraPopoverForRank(rank);
  if (!popover) {
    popover = document.createElement("div");
    popover.className = "preview-camera-popover preview-camera-popover--live preview-camera-popover--portal";
    popover.dataset.previewCameraPopover = "";
    popover.dataset.previewCameraPopoverRank = rank;
    popover.hidden = true;
    document.body.appendChild(popover);
    bindPreviewCameraPopover(card, popover);
  }
  bindPreviewCameraTimeline(card);
  return popover;
}
function livePreviewCameraPopoverForRank(rank){
  return Array.from(document.querySelectorAll(".preview-camera-popover--portal"))
    .find(popover => String(popover.dataset.previewCameraPopoverRank || "") === String(rank)) || null;
}
function previewCameraPopoverForCard(card){
  return livePreviewCameraPopoverForRank(card?.dataset?.rank) || card.querySelector("[data-preview-camera-popover]");
}
function loadLiveTimelineWaveform(card){
  if (parsePreviewWaveform(card.dataset.previewWaveformPeaks).length) return;
  const src = previewWaveformSource(card);
  if (!src || card.dataset.previewWaveformLoading === src) return;
  card.dataset.previewWaveformLoading = src;
  fetch(cacheBustedPreview(src, `waveform-${card.dataset.rank || ""}`))
    .then(response => response.ok ? response.json() : null)
    .then(payload => {
      const peaks = parsePreviewWaveform(payload?.peaks);
      delete card.dataset.previewWaveformLoading;
      if (!peaks.length) return;
      card.dataset.previewWaveformPeaks = JSON.stringify(peaks);
      renderPreviewCameraTimeline(card);
    })
    .catch(error => {
      console.debug("Nao consegui carregar waveform da timeline viva.", error);
      delete card.dataset.previewWaveformLoading;
    });
}
function renderLegacyPreviewCameraTimeline(card){
  const container = card.querySelector("[data-preview-camera-timeline]");
  if (!container) return;
  container.classList.remove("preview-camera-timeline--live");
  const state = previewCameraTimelineContext(card);
  const selectedIndex = selectedCameraPathIndex(card, state.path);
  const markers = state.path.map((frame, index) => {
    const left = clampNumber((Number(frame.time || 0) / state.duration) * 100, 0, 100);
    const active = index === selectedIndex ? " active" : "";
    const label = directorMarkerLabel(state.edit.director_plan, frame);
    const title = directorMarkerTitle(state.edit.director_plan, frame);
    return `<button class="preview-camera-marker${active}" data-preview-camera-marker="${index}" type="button" style="left:${left.toFixed(2)}%" title="${escapeAttr(title)}" aria-label="${escapeAttr(`Editar camera ${label} em ${fixed(frame.time)}`)}"><span>${escapeHtml(label)}</span></button>`;
  }).join("");
  container.innerHTML = `<div class="preview-camera-rail" data-preview-camera-rail>
    <div class="preview-audio-waveform" data-preview-audio-waveform hidden></div>
    <div class="preview-camera-track"></div>
    ${markers}
    <span class="preview-camera-playhead" data-preview-camera-playhead style="left:0%"></span>
  </div>
  <div class="preview-camera-popover" data-preview-camera-popover hidden></div>`;
  bindPreviewCameraTimeline(card);
  renderPreviewAudioWaveform(card);
  updatePreviewCameraTimelinePlayhead(card);
  renderOverlayTimeline(card);
}
function renderPreviewAudioWaveform(card){
  const layer = card.querySelector("[data-preview-audio-waveform]");
  if (!layer) return;
  const cached = parsePreviewWaveform(card.dataset.previewWaveformPeaks);
  if (cached.length) {
    layer.innerHTML = previewWaveformBarsHtml(cached);
    layer.hidden = false;
    return;
  }
  loadPreviewAudioWaveform(card, layer);
}
function loadPreviewAudioWaveform(card, layer){
  const src = previewWaveformSource(card);
  if (!src) {
    layer.hidden = true;
    return;
  }
  if (card.dataset.previewWaveformLoading === src) return;
  card.dataset.previewWaveformLoading = src;
  fetch(cacheBustedPreview(src, `waveform-${card.dataset.rank || ""}`))
    .then(response => response.ok ? response.json() : null)
    .then(payload => applyPreviewWaveformPayload(card, payload))
    .catch(error => {
      console.debug("Nao consegui carregar waveform do preview.", error);
      layer.hidden = true;
    });
}
function applyPreviewWaveformPayload(card, payload){
  const peaks = parsePreviewWaveform(payload?.peaks);
  const layer = card.querySelector("[data-preview-audio-waveform]");
  delete card.dataset.previewWaveformLoading;
  if (!layer || !peaks.length) {
    if (layer) layer.hidden = true;
    return;
  }
  card.dataset.previewWaveformPeaks = JSON.stringify(peaks);
  layer.innerHTML = previewWaveformBarsHtml(peaks);
  layer.hidden = false;
}
function previewWaveformSource(card){
  const moment = (window.CUTTED_DATA.moments || []).find(item => String(item.rank) === String(card.dataset.rank));
  return moment?.waveform_file || "";
}
function parsePreviewWaveform(value){
  const raw = typeof value === "string" ? safeJsonParse(value) : value;
  if (!Array.isArray(raw)) return [];
  return raw.map(item => clampNumber(Number(item) || 0, 0, 1)).filter(item => item > 0).slice(0, 180);
}
function safeJsonParse(value){
  try { return JSON.parse(value); }
  catch (error) {
    console.debug("Waveform cache invalido.", error);
    return null;
  }
}
function previewWaveformBarsHtml(peaks){
  return peaks.map(item => `<span style="height:${Math.max(8, Math.round(item * 100))}%"></span>`).join("");
}
function updatePreviewCameraTimelinePlayhead(card, time = null){
  const playhead = card.querySelector("[data-preview-camera-playhead]");
  if (!playhead) return;
  const duration = cameraTimelineDurationForCard(card);
  const position = cameraTimelinePositionForCard(card, time);
  const left = clampNumber((position / Math.max(duration, .3)) * 100, 0, 100);
  playhead.style.left = `${left.toFixed(2)}%`;
}
function bindPreviewCameraTimeline(card){
  const container = card.querySelector("[data-preview-camera-timeline]");
  if (!container || container.dataset.previewCameraTimelineBound) return;
  container.dataset.previewCameraTimelineBound = "1";
  container.addEventListener("click", event => {
    const popoverTarget = event.target.closest("[data-preview-camera-popover]");
    if (popoverTarget) return;
    const marker = event.target.closest("[data-preview-camera-marker]");
    if (marker) {
      event.preventDefault();
      event.stopPropagation();
      setSelectedCameraPathIndex(card, marker.dataset.previewCameraMarker);
      renderPreviewCameraTimeline(card);
      openPreviewCameraPopover(card);
      return;
    }
    const rail = event.target.closest("[data-preview-camera-rail]");
    if (!rail) return;
    event.preventDefault();
    event.stopPropagation();
    const position = seekPreviewCameraTimeline(card, event, rail);
    openPreviewCameraPopover(card, "insert", position);
  });
  container.addEventListener("change", event => {
    handlePreviewCameraPopoverChange(card, event);
  });
  container.addEventListener("input", event => {
    handlePreviewCameraPopoverInput(card, event);
  });
  container.addEventListener("click", event => {
    handlePreviewCameraPopoverClick(card, event);
  });
}
function bindPreviewCameraPopover(card, popover){
  if (!popover || popover.dataset.previewCameraPopoverBound) return;
  const rank = String(card?.dataset?.rank || "");
  const currentCard = () => cardForRank(rank) || card;
  popover.dataset.previewCameraPopoverBound = "1";
  popover.addEventListener("change", event => handlePreviewCameraPopoverChange(currentCard(), event));
  popover.addEventListener("input", event => handlePreviewCameraPopoverInput(currentCard(), event));
  popover.addEventListener("click", event => handlePreviewCameraPopoverClick(currentCard(), event));
  popover.addEventListener("contextmenu", event => {
    event.stopPropagation();
  });
}
function handlePreviewCameraPopoverChange(card, event){
  if (event.target.matches("[data-preview-camera-popover-intent]")) {
    event.preventDefault();
    const mode = event.target.closest("[data-preview-camera-popover]")?.dataset.previewCameraPopoverMode || "edit";
    if (mode === "edit") {
      const index = selectedCameraPathIndex(card, previewCameraTimelineContext(card).path);
      updateCameraPathFrameIntentForCard(card, event.target.value);
      setSelectedCameraPathIndex(card, index);
      renderPreviewCameraTimeline(card);
      openPreviewCameraPopover(card, "edit");
    }
    return;
  }
  if (event.target.matches("[data-preview-camera-popover-key]")) {
    event.preventDefault();
    const index = selectedCameraPathIndex(card, previewCameraTimelineContext(card).path);
    updateCameraPathFrameForCard(card, { key: event.target.value });
    setSelectedCameraPathIndex(card, index);
    renderPreviewCameraTimeline(card);
    openPreviewCameraPopover(card);
  }
}
function handlePreviewCameraPopoverInput(card, event){
  if (!event.target.matches("[data-preview-camera-popover-strength]")) return;
  const index = selectedCameraPathIndex(card, previewCameraTimelineContext(card).path);
  updateCameraPathFrameForCard(card, { strength: Number(event.target.value) }, false);
  setSelectedCameraPathIndex(card, index);
  renderPreviewCameraTimeline(card);
  openPreviewCameraPopover(card);
}
function handlePreviewCameraPopoverClick(card, event){
  const close = event.target.closest("[data-preview-camera-popover-close]");
  if (close) {
    event.preventDefault();
    event.stopPropagation();
    closePreviewCameraPopover(card);
    return;
  }
  const add = event.target.closest("[data-preview-camera-popover-add]");
  if (add) {
    event.preventDefault();
    event.stopPropagation();
    const popover = event.target.closest("[data-preview-camera-popover]");
    const intent = popover?.querySelector("[data-preview-camera-popover-intent]")?.value || "speaker_hold";
    addCameraIntentFrameForCard(card, intent);
    renderPreviewCameraTimeline(card);
    openPreviewCameraPopover(card, "edit");
    return;
  }
  const done = event.target.closest("[data-preview-camera-popover-continue]");
  if (done) {
    event.preventDefault();
    event.stopPropagation();
    closePreviewCameraPopover(card);
    return;
  }
  const remove = event.target.closest("[data-preview-camera-popover-delete]");
  if (!remove) return;
  event.preventDefault();
  event.stopPropagation();
  deleteCameraPathFrameForCard(card);
  closePreviewCameraPopover(card);
}
function seekPreviewCameraTimeline(card, event, rail){
  const rect = rail.getBoundingClientRect();
  const ratio = rect.width ? clampNumber((event.clientX - rect.left) / rect.width, 0, 1) : 0;
  const values = trimValues(card);
  const duration = Math.max(values.duration, .3);
  const position = ratio * duration;
  seekTimeline(card, position, { userInitiated: true, mode: "free" });
  return position;
}
function openPreviewCameraPopover(card, mode = "edit", positionOverride = null){
  const popover = previewCameraPopoverForCard(card) || ensureLivePreviewCameraPopover(card);
  if (!popover) return;
  closePreviewVolumePopover(card);
  const state = previewCameraTimelineContext(card);
  const index = selectedCameraPathIndex(card, state.path);
  const frame = state.path[index] || state.path[0] || normalizeCameraPathFrame({ time: 0, key: "center", strength: 60 });
  const position = mode === "insert" ? Number(positionOverride ?? cameraTimelinePositionForCard(card)) : Number(frame.time || 0);
  const left = clampNumber((position / state.duration) * 100, 6, 94);
  const intent = mode === "insert" ? "speaker_hold" : directorIntentFromFrame(frame);
  positionPreviewCameraPopover(card, popover, left);
  popover.dataset.previewCameraPopoverMode = mode;
  popover.innerHTML = mode === "insert" ? previewCameraInsertPopoverHtml(position, intent) : previewCameraEditPopoverHtml(state, frame, intent);
  popover.hidden = false;
}
function positionPreviewCameraPopover(card, popover, leftPercent){
  if (!popover.classList.contains("preview-camera-popover--portal")) {
    popover.style.left = `${leftPercent.toFixed(2)}%`;
    return;
  }
  const container = card.querySelector("[data-preview-camera-timeline]");
  const rect = container?.getBoundingClientRect();
  if (!rect) return;
  const width = Math.min(236, Math.max(window.innerWidth - 16, 0));
  const rawLeft = rect.left + rect.width * (leftPercent / 100) - width / 2;
  const left = clampNumber(rawLeft, 8, Math.max(window.innerWidth - width - 8, 8));
  const below = rect.bottom + 8;
  const height = 236;
  const top = below + height < window.innerHeight - 8 ? below : clampNumber(rect.top - height - 8, 8, Math.max(window.innerHeight - height - 8, 8));
  popover.style.left = `${left.toFixed(1)}px`;
  popover.style.top = `${top.toFixed(1)}px`;
  popover.style.right = "auto";
  popover.style.bottom = "auto";
}
function previewCameraPopoverDecorHtml(strength){
  const amount = clampNumber(Number(strength ?? 60), 0, 100);
  return `<div class="preview-camera-popover-aura" aria-hidden="true"></div>
  <div class="preview-camera-popover-lens" aria-hidden="true"></div>
  <div class="preview-camera-popover-beam" aria-hidden="true"></div>
  <div class="preview-camera-popover-meter" aria-hidden="true"><i style="width:${amount}%"></i></div>`;
}
function previewCameraInsertPopoverHtml(position, intent){
  return `${previewCameraPopoverDecorHtml(62)}
  <div class="preview-camera-popover-head">
    <strong>Novo shot</strong>
    <span>${escapeHtml(fixed(position))}</span>
    <button class="preview-camera-popover-close" data-preview-camera-popover-close type="button" aria-label="Fechar">x</button>
  </div>
  <label>Intencao
    <select data-preview-camera-popover-intent>${directorIntentOptionsHtml(intent)}</select>
  </label>
  <button class="preview-camera-popover-primary" data-preview-camera-popover-add type="button">Continuar</button>`;
}
function previewCameraEditPopoverHtml(state, frame, intent){
  const title = directorMarkerTitle(state.edit.director_plan, frame);
  const key = frame.key || "center";
  const strength = clampNumber(Number(frame.strength ?? 60), 0, 100);
  return `${previewCameraPopoverDecorHtml(strength)}
  <div class="preview-camera-popover-head">
    <strong>${escapeHtml(directorMarkerLabel(state.edit.director_plan, frame))}</strong>
    <span>${escapeHtml(fixed(frame.time))}</span>
    <button class="preview-camera-popover-close" data-preview-camera-popover-close type="button" aria-label="Fechar">x</button>
  </div>
  <small>${escapeHtml(title)}</small>
  <label>Intencao
    <select data-preview-camera-popover-intent>${directorIntentOptionsHtml(intent)}</select>
  </label>
  <label>Camera
    <select data-preview-camera-popover-key>${cameraOptionsHtml(key)}</select>
  </label>
  <label>Forca
    <input data-preview-camera-popover-strength type="range" min="0" max="100" step="5" value="${strength}">
  </label>
  <div class="preview-camera-popover-actions">
    <button class="preview-camera-popover-primary" data-preview-camera-popover-continue type="button">Continuar</button>
    <button class="preview-camera-popover-danger" data-preview-camera-popover-delete type="button"${state.path.length > 1 ? "" : " disabled"}>Excluir</button>
  </div>`;
}
function closePreviewCameraPopover(card){
  const popover = previewCameraPopoverForCard(card);
  if (popover) popover.hidden = true;
}
function applyTimelineSeek(card, video, current){
  if (!video) return false;
  try {
    video.currentTime = current;
    updateTimelinePlayhead(card, current);
    return Math.abs(Number(video.currentTime || 0) - current) < .6;
  } catch (error) {
    return false;
  }
}
function applyPendingTimelineSeek(card, video){
  const pending = card.dataset.pendingSeek;
  if (pending === undefined) return false;
  const duration = Number(card.dataset.duration) || .1;
  const current = clampNumber(Number(pending), 0, Math.max(duration, .1));
  const applied = applyTimelineSeek(card, video, current);
  if (applied) delete card.dataset.pendingSeek;
  return applied;
}
function seekTimeline(card, time, options = {}){
  const video = primaryCameraVideo(card);
  const values = trimValues(card);
  const current = clampPreviewTime(values, Number(time));
  const mode = trimRangeActive(values) && options.mode === "free" ? "trim" : options.mode;
  if (options.userInitiated && !trimRangeActive(values)) card.dataset.timelineSeekIntent = "1";
  if (mode) card.dataset.playbackMode = mode;
  card.dataset.pendingSeek = current.toFixed(3);
  if (video) {
    loadCardVideo(card);
    if (video.readyState > 0) {
      applyPendingTimelineSeek(card, video);
    }
    window.setTimeout(() => applyPendingTimelineSeek(card, video), 120);
    window.setTimeout(() => applyPendingTimelineSeek(card, video), 400);
  }
  updateTimelinePlayhead(card, current);
}
function seekPreview(card){
  const video = primaryCameraVideo(card);
  if (!video) return;
  loadCardVideo(card);
  const values = trimValues(card);
  delete card.dataset.timelineSeekIntent;
  seekTimeline(card, values.trimStart, { mode: "range" });
}
function seekTrimHandle(card, handle){
  const video = primaryCameraVideo(card);
  if (video) video.pause();
  const values = trimValues(card);
  const target = handle === "end" ? values.endPos : values.startPos;
  delete card.dataset.timelineSeekIntent;
  seekTimeline(card, target, { mode: "trim" });
}
function trimEndPosition(values){
  return values.duration - values.trimEnd;
}
function trimRangeActive(values){
  return values.trimStart > .05 || values.trimEnd > .05;
}
function clampPreviewTime(values, time){
  const safeTime = clampNumber(Number(time), 0, Math.max(values.duration, .1));
  if (!trimRangeActive(values)) return safeTime;
  const endPos = trimEndPosition(values);
  return clampNumber(safeTime, values.trimStart, Math.max(values.trimStart, endPos));
}
function trimPlaybackStart(values, currentTime){
  const endPos = trimEndPosition(values);
  if (currentTime < values.trimStart || currentTime >= endPos - .05) return values.trimStart;
  return currentTime;
}
function pauseAtTrimEnd(card, video, values){
  const endPos = trimEndPosition(values);
  if (video.currentTime < endPos) return false;
  video.pause();
  video.currentTime = endPos;
  updateTimelinePlayhead(card, endPos);
  return true;
}
function setPreviewPlayback(card, shouldPlay){
  const video = primaryCameraVideo(card);
  if (!video) return;
  loadCardVideo(card);
  applyPreviewVolume(video);
  if (shouldPlay) {
    if (!video.paused && !video.ended) {
      syncPreviewPlaybackState(card);
      return;
    }
    const playback = video.play();
    if (playback && typeof playback.catch === "function") playback.catch(() => syncPreviewPlaybackState(card));
    return;
  }
  if (!video.paused) video.pause();
  else syncPreviewPlayButton(card);
}
function togglePreviewPlayback(card){
  const video = primaryCameraVideo(card);
  if (!video) return;
  setPreviewPlayback(card, video.paused || video.ended);
}
function syncPreviewPlaybackState(card){
  syncPreviewPlayButton(card);
  syncLiveTimelinePlaybackState(card);
}
function syncLiveTimelinePlaybackState(card){
  if (!card.__liveTimelineController || typeof card.__liveTimelineController.update !== "function") return;
  card.__liveTimelineController.update(liveTimelineOptionsForCard(card));
}
function applyPreviewVolume(video){
  if (!video) return;
  if (!video.dataset.volumeReady) {
    video.volume = defaultPreviewVolume;
    video.dataset.volumeReady = "1";
  }
}
function setPreviewVolume(card, value){
  const video = primaryCameraVideo(card);
  if (!video) return;
  video.dataset.volumeReady = "1";
  video.volume = clampNumber(value, 0, 1);
  video.muted = video.volume <= 0;
  syncPreviewVolumeButton(card);
}
function syncPreviewPlayButton(card){
  const button = card.querySelector("[data-preview-play]");
  const video = primaryCameraVideo(card);
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
function syncPreviewVolumeButton(card){
  const button = card.querySelector("[data-preview-volume]");
  const slider = card.querySelector("[data-preview-volume-slider]");
  const video = primaryCameraVideo(card);
  if (!button) return;
  if (!video) {
    button.hidden = true;
    return;
  }
  applyPreviewVolume(video);
  const value = video.muted ? 0 : Math.round(video.volume * 100);
  button.hidden = false;
  button.innerHTML = previewIcon(video.muted || video.volume <= 0 ? "volume-off" : "volume");
  button.setAttribute("aria-label", "Volume");
  button.title = "Volume";
  if (slider) slider.value = String(value);
  updateControlSurfaceForCard(card);
}
function openPreviewVolumePopover(card){
  const popover = card.querySelector("[data-preview-volume-popover]");
  if (!popover) return;
  closePreviewCameraPopover(card);
  syncPreviewVolumeButton(card);
  popover.hidden = false;
}
function closePreviewVolumePopover(card){
  const popover = card.querySelector("[data-preview-volume-popover]");
  if (popover) popover.hidden = true;
}
function togglePreviewVolumePopover(card){
  const popover = card.querySelector("[data-preview-volume-popover]");
  if (!popover) return;
  if (popover.hidden) openPreviewVolumePopover(card);
  else closePreviewVolumePopover(card);
}
function bindPreviewVolumeDismiss(){
  if (document.body.dataset.previewVolumeDismissBound) return;
  document.body.dataset.previewVolumeDismissBound = "1";
  document.addEventListener("click", event => {
    document.querySelectorAll("[data-preview-volume-popover]").forEach(popover => {
      const group = popover.closest(".preview-volume-group");
      if (!group || !group.contains(event.target)) popover.hidden = true;
    });
  });
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
  const video = card.querySelector("video:not(.camera-fit-bg)[data-src]");
  if (!video || video.getAttribute("src")) return;
  video.setAttribute("src", video.dataset.src);
  applyPreviewVolume(video);
  video.load();
  syncCameraFitBackground(card);
  syncPreviewPlayButton(card);
  syncPreviewVolumeButton(card);
}
function unloadCardVideo(card){
  destroyLivePreviewCameraTimeline(card);
  const video = card.querySelector("video:not(.camera-fit-bg)[data-src]");
  if (!video || !video.getAttribute("src")) return;
  video.pause();
  video.removeAttribute("src");
  video.load();
  unloadCameraFitBackground(card);
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
  const adjustedDuration = Number((moment.end - trimEnd - moment.start - trimStart).toFixed(3));
  const edit = platformEditForRank(moment.rank);
  const sourceDuration = sourceDurationForMoment(moment);
  return Object.assign({}, moment, {
    status: current.status || null,
    platforms,
    trim_start_seconds: trimStart,
    trim_end_seconds: trimEnd,
    adjusted_start: Number((moment.start + trimStart).toFixed(3)),
    adjusted_end: Number((moment.end - trimEnd).toFixed(3)),
    adjusted_duration: adjustedDuration,
    camera: edit.camera,
    camera_path: exportCameraPathForEdit(edit, sourceDuration, trimStart, adjustedDuration),
    director_plan: edit.director_plan,
    camera_motion_ms: current.cameraMotionMs,
    effect: effectForRank(moment.rank),
    overlay: primaryOverlayForRank(moment.rank),
    overlays: overlayLayersForRank(moment.rank),
    bumpers: bumpersForRank(moment.rank),
    platform_edits: current.platformEdits
  });
}
function resolutionEditForPlatform(rank, platform, sourceDuration, trimStart, duration){
  const key = resolutionPresetForPlatform(platform);
  const edit = platformEditForRank(rank, platform);
  return {
    resolution_preset: key,
    resolution_label: resolutionPresetLabel(key),
    source: "platform_edits",
    camera: edit.camera,
    camera_path: exportCameraPathForEdit(edit, sourceDuration, trimStart, duration),
    director_plan: edit.director_plan,
    camera_motion_ms: cardState(String(rank)).cameraMotionMs,
    effect: edit.effect,
    overlay: edit.overlays.find(layer => layer.kind !== "image") || defaultOverlay(),
    overlays: edit.overlays,
    bumpers: edit.bumpers
  };
}
function resolutionEditsForMoment(moment, exportFormat){
  const result = {};
  captionPlatforms(moment, exportFormat).forEach(platform => {
    const key = resolutionPresetForPlatform(platform);
    if (!result[key]) {
      result[key] = Object.assign(resolutionEditForPlatform(moment.rank, platform, sourceDurationForMoment(moment), moment.trim_start_seconds, moment.adjusted_duration), {
        destinations: resolutionPresets[key]?.destinations || [platform],
        shared: true
      });
    }
  });
  return result;
}
function buildExportData(){
  const data = Object.assign({}, window.CUTTED_DATA);
  data.export_format = document.body.dataset.format || "tiktok";
  data.resolution_presets = resolutionPresets;
  data.destination_resolution_map = destinationResolutionMap();
  const adjusted = data.moments.map(adjustedMoment).map(moment => Object.assign({}, moment, {
    resolution_edits: resolutionEditsForMoment(moment, data.export_format)
  }));
  data.moments = adjusted;
  data.selected = adjusted.filter(moment => captionPlatforms(moment, data.export_format).length > 0);
  data.caption_queue = data.selected.flatMap(moment => captionPlatforms(moment, data.export_format).map(platform => {
    const edit = platformEditForRank(moment.rank, platform);
    const overlays = edit.overlays;
    const cameraPath = exportCameraPathForEdit(edit, sourceDurationForMoment(moment), moment.trim_start_seconds, moment.adjusted_duration);
    const resolutionKey = resolutionPresetForPlatform(platform);
    const captions = normalizeCaptionSettings(edit.captions);
    return {
      rank: moment.rank,
      platform,
      platform_label: platformLabel(platform),
      resolution_preset: resolutionKey,
      resolution_label: resolutionPresetLabel(resolutionKey),
      shared_destinations: resolutionPresets[resolutionKey]?.destinations || [platform],
      resolution_edit: moment.resolution_edits[resolutionKey] || null,
      width: platformMeta[platform]?.width || null,
      height: platformMeta[platform]?.height || null,
      publish_metadata: publishMetadata(platform, moment),
      trim_start_seconds: moment.trim_start_seconds,
      trim_end_seconds: moment.trim_end_seconds,
      adjusted_start: moment.adjusted_start,
      adjusted_end: moment.adjusted_end,
      adjusted_duration: moment.adjusted_duration,
      camera: edit.camera,
      camera_path: cameraPath,
      director_plan: edit.director_plan,
      effect: edit.effect,
      overlay: overlays.find(layer => layer.kind !== "image") || defaultOverlay(),
      overlays,
      bumpers: edit.bumpers,
      captions_enabled: captions.enabled,
      caption_style: captions.style,
      animated_caption_windows: captions.style.mode === "animated" ? previewAnimatedCaptionTimeline(moment) : [],
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
  if (moment.status === "discarded") return [];
  const platforms = uniquePlatforms(moment.platforms);
  if (platforms.length) return platforms;
  return moment.status === "liked" && platformMeta[exportFormat] ? [exportFormat] : [];
}
function uniquePlatforms(values){
  const seen = new Set();
  return (Array.isArray(values) ? values : []).map(value => representativePlatform(String(value || "").trim().toLowerCase())).filter(platform => {
    const resolution = resolutionPresetForPlatform(platform);
    if (!platformMeta[platform] || seen.has(resolution)) return false;
    seen.add(resolution);
    return true;
  });
}
function publishMetadata(platform, moment){
  const edit = publishEditForRank(moment.rank);
  if (moment.publish_metadata && typeof moment.publish_metadata === "object") {
    const generated = moment.publish_metadata;
    const hashtags = edit.hashtags.length
      ? edit.hashtags
      : Array.isArray(generated.hashtags) && generated.hashtags.length
      ? generated.hashtags
      : suggestHashtags(platform, `${moment.title} ${moment.peak_text} ${moment.transcript}`);
    const result = Object.assign({}, generated, {
      title: edit.title || generated.title,
      hook: edit.hook || generated.hook,
      description: edit.description || generated.description,
      hashtags,
      cover: publishCoverFromEdit(edit, generated, moment),
      caption_hint: publishCaptionHintFromEdit(edit, generated, platform, moment, hashtags),
      strategy: generated.strategy || platformStrategy(platform)
    });
    return result;
  }
  const hashtags = edit.hashtags.length ? edit.hashtags : suggestHashtags(platform, `${moment.title} ${moment.peak_text} ${moment.transcript}`);
  return {
    title: edit.title || moment.title,
    hook: edit.hook || "",
    description: edit.description || "",
    hashtags,
    cover: publishCoverFromEdit(edit, null, moment),
    caption_hint: publishCaptionHintFromEdit(edit, null, platform, moment, hashtags),
    strategy: platformStrategy(platform)
  };
}
function normalizePublishEdit(value){
  const source = value && typeof value === "object" ? value : {};
  return {
    title: cleanPublishField(source.title, 110),
    hook: cleanPublishField(source.hook, 140),
    description: cleanPublishField(source.description, 360),
    coverFrame: cleanPublishField(source.coverFrame, 260),
    coverZoom: normalizePublishCoverZoom(source.coverZoom, null),
    coverX: normalizePublishCoverPosition(source.coverX, source.coverZoom || 1),
    coverY: normalizePublishCoverPosition(source.coverY, source.coverZoom || 1),
    coverLayers: normalizeCoverOverlayLayers(source.coverLayers),
    hashtags: normalizePublishHashtags(source.hashtags)
  };
}
function publishEditForRank(rank){
  return normalizePublishEdit(cardState(String(rank)).publish);
}
function cleanPublishField(value, limit){
  const cleaned = String(value || "").replace(/\\s+/g, " ").trim();
  return cleaned.length > limit ? `${cleaned.slice(0, Math.max(0, limit - 1)).trim()}…` : cleaned;
}
function normalizePublishHashtags(value){
  const raw = Array.isArray(value) ? value.join(" ") : String(value || "");
  const seen = new Set();
  return raw.split(/[\\s,]+/).map(item => item.trim()).filter(Boolean).map(item => {
    const clean = item.replace(/^#+/, "").replace(/[^\\p{L}\\p{N}_]/gu, "");
    return clean ? `#${clean}` : "";
  }).filter(tag => {
    const key = tag.toLowerCase();
    if (!tag || seen.has(key)) return false;
    seen.add(key);
    return true;
  }).slice(0, 8);
}
function publishCoverFromEdit(edit, generated, moment){
  const cover = generated?.cover && typeof generated.cover === "object" ? generated.cover : {};
  const editedFrame = cleanPublishField(edit.coverFrame, 260);
  const baseCandidates = publishCoverCandidates(moment, cover);
  const fallback = cover.selected_frame || baseCandidates[0] || moment.frame_file || "";
  const selected = editedFrame || fallback;
  const candidates = uniqueCoverFrames([selected, ...baseCandidates]);
  const zoom = normalizePublishCoverZoom(edit.coverZoom, normalizePublishCoverZoom(cover.zoom, 1));
  return {
    selected_frame: selected,
    candidates,
    zoom,
    x: normalizePublishCoverPosition(edit.coverX ?? cover.x, zoom),
    y: normalizePublishCoverPosition(edit.coverY ?? cover.y, zoom),
    layers: normalizeCoverOverlayLayers(edit.coverLayers.length ? edit.coverLayers : cover.layers),
    reason: cover.reason || "Frame de pico extraido do corte."
  };
}
function normalizeCoverOverlayLayers(layers){
  const source = Array.isArray(layers) ? layers : [];
  return source.map(normalizeOverlayLayer).filter(layer => layer.key !== "none");
}
function liftedCoverLayerY(y){
  return clampNumber(Number(y || 0) - coverLayerVerticalLift, 0, 1);
}
function publishCoverLayerHtml(layer){
  const current = normalizeOverlayLayer(layer);
  const left = clampNumber(current.x * 100, 0, 100);
  const top = clampNumber(liftedCoverLayerY(current.y) * 100, 0, 100);
  const width = clampNumber(current.width * 100, 8, 90);
  const opacity = clampNumber(current.opacity / 100, .1, 1);
  const fontSize = clampNumber((current.font_size || 34) * .42, 10, 24);
  const selected = document.querySelector(`.card[data-rank="${CSS.escape(String(activeRankForCoverLayer(current)))}"]`)?.dataset.selectedCoverLayer === current.id;
  const selectedClass = selected ? " is-selected" : "";
  const resize = '<button class="publish-cover-resize" data-publish-cover-resize type="button" title="Redimensionar"></button>';
  if (current.kind === "image") {
    const src = current.image_data_url || current.image_file || "";
    if (!src) return "";
    return `<div class="publish-cover-layer${selectedClass}" data-publish-cover-layer="${escapeAttr(current.id)}" data-cover-layer-kind="image" style="left:${left}%;top:${top}%;width:${width}%;--cover-layer-opacity:${opacity}"><img src="${escapeAttr(src)}" alt="">${resize}</div>`;
  }
  const bg = hexToRgb(current.background_color || "#000000").join(",");
  const bgOpacity = clampNumber((current.background_opacity ?? 70) / 100, 0, 1);
  const color = normalizeHexColor(current.color, current.kind === "speech" ? "#050505" : "#ffffff");
  const text = escapeHtml(current.text || current.label || "");
  return `<div class="publish-cover-layer${selectedClass}" data-publish-cover-layer="${escapeAttr(current.id)}" data-cover-layer-kind="${escapeAttr(current.kind)}" style="left:${left}%;top:${top}%;width:${width}%;font-size:${fontSize}px;opacity:${opacity};--cover-layer-color:${color};--cover-layer-bg:${bg};--cover-layer-bg-opacity:${bgOpacity}"><span>${text}</span>${resize}</div>`;
}
function activeRankForCoverLayer(layer){
  const card = Array.from(document.querySelectorAll(".card")).find(item => coverLayersForRank(item.dataset.rank).some(current => current.id === layer.id));
  return card?.dataset.rank || "";
}
function normalizePublishCoverZoom(value, fallback = 1){
  if (value === null || value === undefined || value === "") return fallback;
  const next = Number(value);
  if (!Number.isFinite(next)) return fallback;
  return clampNumber(next, 1, 1.8);
}
function normalizePublishCoverPosition(value, zoom){
  if (normalizePublishCoverZoom(zoom, 1) <= 1.001) return 50;
  const next = Number(value);
  if (!Number.isFinite(next)) return 50;
  return clampNumber(next, 0, 100);
}
function publishCoverCandidates(moment, cover){
  const raw = Array.isArray(cover.candidates) && cover.candidates.length
    ? cover.candidates
    : (Array.isArray(moment.cover_candidates) ? moment.cover_candidates : []);
  return uniqueCoverFrames([...raw, cover.selected_frame, moment.frame_file]);
}
function uniqueCoverFrames(values){
  const seen = new Set();
  return values.map(value => String(value || "").trim()).filter(value => {
    if (!value || seen.has(value)) return false;
    seen.add(value);
    return true;
  }).slice(0, 4);
}
function publishCaptionHintFromEdit(edit, generated, platform, moment, hashtags){
  const hook = edit.hook || generated?.hook || "";
  const description = edit.description || generated?.description || "";
  const parts = [hook, description, hashtags.join(" ")].filter(Boolean);
  return parts.length ? parts.join("\\n\\n") : (generated?.caption_hint || captionHint(platform, moment, hashtags));
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
  const cameraPath = cameraPathForEdit({ camera, camera_path: item.camera_path }, Number(item.adjusted_duration || 0));
  const previewFrame = cameraFrameForTime(camera, cameraPath, 0, Number(item.adjusted_duration || 0));
  const src = cacheBustedPreview(item.clip_file || "", `camera-${item.rank}-${item.adjusted_start}-${item.adjusted_end}`);
  const duration = Number(item.adjusted_duration || 0);
  return `<article class="caption-item" data-rank="${escapeAttr(item.rank)}" data-platform="${escapeAttr(item.platform)}" data-camera-duration="${escapeAttr(item.adjusted_duration || 0)}">
    <div class="caption-preview camera-surface" data-camera-key="${escapeAttr(previewFrame.key || "path")}" data-camera-cut="${cameraFrameUsesHardCut(previewFrame) ? "hard" : "smooth"}" data-camera-fit="${cameraFrameUsesGroupFit(previewFrame) ? "contain" : "cover"}" style="${escapeAttr(cameraPreviewStyleFromFrame(previewFrame))}">
      <video controls preload="metadata" src="${escapeAttr(src)}"></video>
      <video class="camera-fit-bg" data-camera-fit-bg playsinline muted preload="metadata" src="${escapeAttr(src)}" aria-hidden="true" tabindex="-1"></video>
      <img class="camera-fit-logo" src="assets/brand/cuted-logo-transparent.png" alt="" aria-hidden="true">
      <div class="camera-reticle"></div>
    </div>
    <div class="caption-item-body">
      <strong>Preview #${String(item.rank).padStart(2, "0")} ${escapeHtml(item.title || "")}</strong>
      <span>${escapeHtml(item.platform_label)}</span><span data-camera-current>${escapeHtml(cameraEditLabel({ camera, camera_path: item.camera_path }, duration))}</span>
      <div class="camera-card-controls">
        ${cameraSegmentsHtml(camera)}
      </div>
    </div>
  </article>`;
}
function cameraPathEditorHtml(card, edit, duration, camera){
  const explicit = explicitCameraPathForEdit(edit);
  const path = cameraPathForEdit(edit, duration);
  const selectedIndex = selectedCameraPathIndex(card, path);
  const selected = path[selectedIndex] || path[0] || normalizeCameraPathFrame({ time: 0, key: "center", strength: 60 });
  const safeDuration = Math.max(Number(duration) || 0, .3);
  const platform = activePlatformForRank(card.dataset.rank);
  const resolutionKey = resolutionPresetForPlatform(platform);
  const resolution = resolutionPresets[resolutionKey] || resolutionPresets.vertical_9_16;
  const shared = resolution.destinations.map(platformLabel).join(", ");
  const markers = path.map((frame, index) => {
    const left = clampNumber((Number(frame.time || 0) / safeDuration) * 100, 0, 100);
    const active = index === selectedIndex ? " active" : "";
    const label = directorMarkerLabel(edit.director_plan, frame);
    const title = directorMarkerTitle(edit.director_plan, frame);
    return `<button class="camera-path-marker${active}" data-camera-path-marker="${index}" type="button" style="left:${left.toFixed(2)}%" title="${escapeAttr(title)}"><span>${escapeHtml(label)}</span></button>`;
  }).join("");
  return `<div class="camera-path-editor" data-camera-path-editor>
    <div class="camera-smart-panel">
      <div class="camera-panel-title">
        <strong>AI Director</strong>
        <span>${escapeHtml(resolution.label)} ${resolution.width}x${resolution.height}</span>
      </div>
      <p>Direcione este formato uma vez e reuse em ${escapeHtml(shared)}. Ajuste pontos na timeline quando quiser corrigir a intencao.</p>
      ${smartCameraButtonsHtml()}
    </div>
    <div class="camera-auto-status" data-camera-auto-status></div>
    <details class="camera-advanced">
      <summary>
        <span>Ajustes avancados</span>
        <small>${explicit.length ? `${path.length} keyframes ativos` : "manual e keyframes"}</small>
      </summary>
      <div class="camera-path-head">
        <strong>Camera path</strong>
        <span>${explicit.length ? `${path.length} keyframes manuais` : "Derivado de Inicio/Meio/Fim"}</span>
      </div>
      <div class="camera-path-track" aria-label="Keyframes de camera">
        <div class="camera-path-rail"></div>
        ${markers}
      </div>
      <div class="camera-path-actions">
        <button data-camera-path-add type="button">+ no playhead</button>
        <button data-camera-path-set-time type="button"${explicit.length ? "" : " disabled"}>Mover para playhead</button>
        <button data-camera-path-reset type="button"${explicit.length ? "" : " disabled"}>Usar simples</button>
      </div>
      <div class="camera-keyframe-panel">
        <label>Keyframe
          <select data-camera-path-key${explicit.length ? "" : " disabled"}>${cameraOptionsHtml(selected?.key || "center")}</select>
        </label>
        <label>Forca
          <input data-camera-path-strength type="range" min="0" max="100" step="5" value="${selected?.strength ?? 60}"${explicit.length ? "" : " disabled"}>
        </label>
        <button class="camera-path-delete" data-camera-path-delete type="button"${path.length > 1 && explicit.length ? "" : " disabled"}>Excluir ponto</button>
      </div>
      ${cameraSegmentsHtml(camera)}
    </details>
  </div>`;
}
function smartCameraButtonsHtml(){
  const quick = ["follow-face", "stable-face", "face-zoom"];
  const ai = ["ai-director-group", "ai-director-speaker", "ai-director-reactions", "ai-director-cuts"];
  const director = cameraSmartButtonHtml("ai-director", smartCameraModes["ai-director"], true);
  const auto = cameraSmartButtonHtml("auto-director", smartCameraModes["auto-director"], false);
  const quickHtml = quick.map(key => cameraSmartButtonHtml(key, smartCameraModes[key], false)).join("");
  const aiHtml = ai.map(key => cameraSmartButtonHtml(key, smartCameraModes[key], false)).join("");
  return `${director}<div class="camera-smart-row">${auto}${quickHtml}</div><div class="camera-smart-ai">${aiHtml}</div>`;
}
function cameraSmartButtonHtml(key, meta, featured){
  const className = featured ? ' class="camera-director-action"' : "";
  return `<button${className} data-camera-smart-mode="${escapeAttr(key)}" type="button" title="${escapeAttr(meta.note)}"><strong>${escapeHtml(meta.label)}</strong><span>${escapeHtml(meta.note)}</span></button>`;
}
function cameraSegmentsHtml(camera){
  return `<div class="camera-manual-panel">
    <div class="camera-panel-title">
      <strong>Manual</strong>
      <span>Inicio / Meio / Fim</span>
    </div>
    <div class="camera-segments">${cameraParts.map(part => {
    const segment = camera.segments.find(item => item.part === part.key) || defaultCameraSegment(part.key);
    return `<div class="camera-segment" data-camera-part="${escapeAttr(part.key)}">
      <strong>${escapeHtml(part.label)}</strong>
      <select data-preview-camera-segment="${escapeAttr(part.key)}">${cameraOptionsHtml(segment.key)}</select>
      <label>Forca
        <input data-preview-camera-strength="${escapeAttr(part.key)}" type="range" min="0" max="100" step="5" value="${segment.strength}">
      </label>
    </div>`;
  }).join("")}</div>
  </div>`;
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
    const updatePreviewSurface = () => {
      const video = primaryCameraVideo(item);
      const edit = platformEditForRank(rank, item.dataset.platform);
      const duration = Number(item.dataset.cameraDuration || video?.duration || 0);
      applyCameraSurface(item.querySelector(".camera-surface"), edit.camera, Number(video?.currentTime || 0), duration, cameraPathForEdit(edit, duration));
      const summary = item.querySelector("[data-camera-current]");
      if (summary) summary.textContent = cameraEditLabel(edit, duration);
    };
    updatePreviewSurface();
    const video = primaryCameraVideo(item);
    if (video) {
      ["loadedmetadata", "durationchange", "seeked", "timeupdate"].forEach(eventName => {
        video.addEventListener(eventName, updatePreviewSurface);
      });
      video.addEventListener("play", () => startCameraFrameSync(video, updatePreviewSurface));
      ["pause", "ended"].forEach(eventName => {
        video.addEventListener(eventName, () => stopCameraFrameSync(video, updatePreviewSurface));
      });
    }
    item.querySelectorAll("[data-preview-camera-segment]").forEach(select => {
      select.addEventListener("change", () => {
        setCameraSegmentForRank(rank, select.dataset.previewCameraSegment, { key: select.value }, item.dataset.platform);
        updatePreviewSurface();
      });
    });
    item.querySelectorAll("[data-preview-camera-strength]").forEach(strength => {
      const update = () => {
        setCameraSegmentForRank(rank, strength.dataset.previewCameraStrength, { strength: Number(strength.value) }, item.dataset.platform);
        updatePreviewSurface();
      };
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
  const layers = normalizeOverlayLayers(item.overlays, item.overlay);
  const src = cacheBustedPreview(item.clip_file || "", `overlay-${item.rank}-${item.adjusted_start}-${item.adjusted_end}`);
  return `<article class="caption-item" data-rank="${escapeAttr(item.rank)}" data-platform="${escapeAttr(item.platform)}">
    <div class="caption-preview" data-overlay-surface>
      <video controls preload="metadata" src="${escapeAttr(src)}"></video>
      ${layers.map(overlayLayerBoxHtml).join("")}
    </div>
    <div class="caption-item-body">
      <strong>Preview #${String(item.rank).padStart(2, "0")} ${escapeHtml(item.title || "")}</strong>
      <span>${escapeHtml(item.platform_label)}</span><span data-overlay-current>${layers.length ? `${layers.length} camada(s)` : "Sem camada"}</span>
    </div>
  </article>`;
}
function bindOverlayPreviewControls(){
  document.querySelectorAll("[data-overlay-preview] .caption-item video").forEach(video => {
    video.volume = defaultPreviewVolume;
    ["loadedmetadata", "durationchange", "seeked", "timeupdate"].forEach(eventName => {
      video.addEventListener(eventName, () => syncTimedOverlayVisibility(video.closest(".caption-item")));
    });
  });
  document.querySelectorAll("[data-overlay-preview] .caption-item").forEach(item => {
    bindOverlayDrag(item);
    syncTimedOverlayVisibility(item);
  });
}
function bindOverlayDrag(item){
  const surface = item.querySelector("[data-overlay-surface]");
  if (!surface) return;
  item.querySelectorAll("[data-overlay-drag]").forEach(box => {
    if (box.dataset.overlayKey === "none") return;
    const platform = overlayPlatformForItem(item);
    let drag = null;
    const startDrag = event => {
      if (event.type === "mousedown" && drag) return;
      const resizing = !!event.target?.closest?.("[data-overlay-resize]");
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
        surfaceHeight: surfaceRect.height,
        moved: false
      };
      if (item.classList.contains("card")) {
        item.dataset.selectedOverlayLayer = box.dataset.overlayLayer;
        renderLayerStrip(item, overlayLayersForRank(item.dataset.rank, platform));
      }
      if (event.pointerId !== undefined && box.setPointerCapture) box.setPointerCapture(event.pointerId);
      document.addEventListener("pointermove", moveDrag);
      document.addEventListener("pointerup", endDrag, { once: true });
      document.addEventListener("pointercancel", endDrag, { once: true });
      document.addEventListener("mousemove", moveDrag);
      document.addEventListener("mouseup", endDrag, { once: true });
      event.preventDefault();
      event.stopPropagation();
    };
    const moveDrag = event => {
      if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
      const dx = event.clientX - drag.startX;
      const dy = event.clientY - drag.startY;
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) drag.moved = true;
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
      patchOverlayLayerForRank(item.dataset.rank, box.dataset.overlayLayer, patch, false, platform);
      event.preventDefault();
      event.stopPropagation();
    };
    const endDrag = event => {
      if (!drag || (event.pointerId !== undefined && event.pointerId !== drag.pointerId)) return;
      const shouldInspect = item.classList.contains("card") && !drag.moved;
      const layerId = box.dataset.overlayLayer;
      const moved = drag.moved;
      drag = null;
      document.removeEventListener("pointermove", moveDrag);
      document.removeEventListener("mousemove", moveDrag);
      document.removeEventListener("pointerup", endDrag);
      document.removeEventListener("pointercancel", endDrag);
      document.removeEventListener("mouseup", endDrag);
      if (item.classList.contains("card")) updateOverlayUi(item);
      else renderFinalStage();
      if (moved && item.classList.contains("card")) {
        item.dataset.overlaySuppressClick = "1";
        box.dataset.overlayJustDragged = "1";
        setTimeout(() => { delete box.dataset.overlayJustDragged; }, 0);
      }
      if (shouldInspect) showOverlayInspectorForLayer(item, layerId);
      event.preventDefault();
      event.stopPropagation();
    };
    const inspectLayer = event => {
      if (box.dataset.overlayJustDragged) return;
      if (!item.classList.contains("card")) return;
      event.preventDefault();
      event.stopPropagation();
      item.dataset.selectedOverlayLayer = box.dataset.overlayLayer;
      showOverlayInspectorForLayer(item, box.dataset.overlayLayer);
    };
    box.onpointerdown = startDrag;
    box.onmousedown = startDrag;
    box.onclick = inspectLayer;
    box.ondblclick = inspectLayer;
    box.querySelectorAll("[data-overlay-resize]").forEach(handle => {
      handle.onpointerdown = startDrag;
      handle.onmousedown = startDrag;
    });
  });
}
function renderFinalStage(){
  const queue = buildExportData().caption_queue || [];
  const summary = document.querySelector("[data-final-summary]");
  if (summary) {
    const cameraCount = queue.filter(item => cameraEditHasMovement(item)).length;
    const effectCount = queue.filter(item => normalizeEffect(item.effect).key !== "none").length;
    const overlayCount = queue.reduce((count, item) => count + normalizeOverlayLayers(item.overlays, item.overlay).length, 0);
    const coverLayerCount = queue.reduce((count, item) => count + normalizeCoverOverlayLayers(item.publish_metadata?.cover?.layers).length, 0);
    const bumperCount = queue.reduce((count, item) => count + Object.keys(normalizeBumpers(item.bumpers)).length, 0);
    summary.textContent = queue.length
      ? `${queue.length} na fila; ${cameraCount} camera; ${effectCount} efeito; ${overlayCount} camada; ${coverLayerCount} capa; ${bumperCount} vinheta.`
      : "Nada na fila.";
  }
}
function currentGalleryPath(){
  const path = window.location.pathname || "/";
  if (path.endsWith("/")) return path.replace(/\\/$/, "");
  return path.replace(/\\/[^/]*$/, "");
}
async function touchCurrentProject(){
  const galleryPath = currentGalleryPath();
  if (!galleryPath || galleryPath === "/index") return null;
  const response = await fetch("/api/projects/touch", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({gallery_path: galleryPath}),
    keepalive: true
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || !payload.ok) throw new Error(payload.error || "Nao consegui atualizar recentes.");
  return payload;
}
function isCurrentGalleryEmpty(){
  return localStorage.getItem(emptyGalleryStorageKey) === currentGalleryPath();
}
function syncProjectEmptyState(){
  document.body.dataset.projectEmpty = isCurrentGalleryEmpty() ? "true" : "false";
}
function markCurrentGalleryEmpty(){
  localStorage.setItem(emptyGalleryStorageKey, currentGalleryPath());
  syncProjectEmptyState();
}
function importFormPayload(form){
  const data = new FormData(form);
  return {
    source_url: String(data.get("source_url") || "").trim(),
    source_path: String(data.get("source_path") || "").trim(),
    output_path: String(data.get("output_path") || "").trim(),
    preview_count: Number(data.get("preview_count") || 10),
    language: String(data.get("language") || "").trim(),
    preset: String(data.get("preset") || "tiktok"),
    duration_profile: String(data.get("duration_profile") || "medium"),
    context_prompt: String(data.get("context_prompt") || "").trim(),
    render_previews: true
  };
}
let settingsLastFocus = null;
function setupSettingsPanel(){
  const modal = document.querySelector("[data-settings-modal]");
  const form = document.querySelector("[data-settings-form]");
  const open = document.getElementById("open-settings");
  const close = document.querySelector("[data-settings-close]");
  const test = document.querySelector("[data-settings-test]");
  if (!modal || !form || !open) return;
  open.addEventListener("click", () => openSettingsPanel());
  close?.addEventListener("click", () => closeSettingsPanel());
  modal.addEventListener("click", event => { if (event.target === modal) closeSettingsPanel(); });
  document.addEventListener("keydown", event => {
    if (modal.hidden) return;
    if (event.key === "Escape") closeSettingsPanel();
    if (event.key === "Tab") trapSettingsFocus(event);
  });
  form.addEventListener("submit", event => {
    event.preventDefault();
    saveSettingsForm(form);
  });
  test?.addEventListener("click", () => testSettingsConnection(form));
  loadOpenaiSettings();
}
function openSettingsPanel(){
  const modal = document.querySelector("[data-settings-modal]");
  if (!modal) return;
  settingsLastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  modal.hidden = false;
  modal.classList.remove("is-closing");
  requestAnimationFrame(() => modal.classList.add("is-open"));
  loadOpenaiSettings();
  modal.querySelector("[data-settings-panel]")?.focus();
}
function closeSettingsPanel(){
  const modal = document.querySelector("[data-settings-modal]");
  if (!modal || modal.hidden) return;
  modal.classList.remove("is-open");
  modal.classList.add("is-closing");
  window.setTimeout(() => {
    modal.hidden = true;
    modal.classList.remove("is-closing");
    settingsLastFocus?.focus?.();
    settingsLastFocus = null;
  }, 190);
}
function settingsFocusableElements(modal){
  return Array.from(modal.querySelectorAll("button,input,select,textarea,a[href],[tabindex]:not([tabindex='-1'])"))
    .filter(element => !element.disabled && !element.hidden && element.offsetParent !== null);
}
function trapSettingsFocus(event){
  const modal = document.querySelector("[data-settings-modal]");
  if (!modal || modal.hidden) return;
  const focusable = settingsFocusableElements(modal);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
async function loadOpenaiSettings(){
  const form = document.querySelector("[data-settings-form]");
  const status = document.querySelector("[data-settings-status]");
  if (!form) return;
  try {
    const response = await fetch("/api/settings/openai");
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao carregar configuracoes.");
    applySettingsPayload(form, payload.settings || {}, payload.usage || {});
  } catch (error) {
    if (status) status.textContent = error.message || "Nao consegui carregar configuracoes.";
  }
}
function applySettingsPayload(form, settings, usage){
  form.elements.ai_provider.value = settings.ai_provider || "openai";
  form.elements.openai_model.value = settings.openai_model || "gpt-5-mini";
  form.elements.transcribe_model.value = settings.transcribe_model || "whisper-1";
  form.elements.api_key.value = "";
  const status = document.querySelector("[data-settings-status]");
  if (status) {
    const key = settings.key_configured ? "Token configurado" : "Token nao configurado";
    status.textContent = `${key} - ${settings.openai_model || "gpt-5-mini"} / ${settings.transcribe_model || "whisper-1"}`;
  }
  updateOpenaiSettingsIndicator(settings);
  renderSettingsUsage(usage);
}
function updateOpenaiSettingsIndicator(settings){
  const button = document.getElementById("open-settings");
  if (!button) return;
  const provider = String(settings?.ai_provider || "openai");
  const ready = Boolean(settings?.key_configured) && provider !== "local";
  button.classList.toggle("is-openai-ready", ready);
  button.setAttribute("aria-label", ready ? "OpenAI configurada" : "Configuracoes OpenAI");
  button.title = ready ? "OpenAI configurada" : "Configuracoes OpenAI";
}
function settingsPayloadFromForm(form){
  const data = new FormData(form);
  const payload = {
    ai_provider: String(data.get("ai_provider") || "openai"),
    openai_model: String(data.get("openai_model") || "gpt-5-mini"),
    transcribe_model: String(data.get("transcribe_model") || "whisper-1")
  };
  const apiKey = String(data.get("api_key") || "").trim();
  if (apiKey) payload.api_key = apiKey;
  return payload;
}
async function saveSettingsForm(form){
  const status = document.querySelector("[data-settings-status]");
  if (status) status.textContent = "Salvando...";
  try {
    const response = await fetch("/api/settings/openai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(settingsPayloadFromForm(form))
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao salvar configuracoes.");
    applySettingsPayload(form, payload.settings || {}, payload.usage || {});
    if (status) status.textContent = `Salvo. ${status.textContent}`;
    refreshImportKeyBanner();
  } catch (error) {
    if (status) status.textContent = error.message || "Nao consegui salvar.";
  }
}
async function testSettingsConnection(form){
  const status = document.querySelector("[data-settings-status]");
  const button = document.querySelector("[data-settings-test]");
  if (status) status.textContent = "Testando conexao...";
  if (button) button.disabled = true;
  try {
    const payload = settingsPayloadFromForm(form);
    const response = await fetch("/api/settings/openai/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || "Falha ao testar conexao.");
    if (status) status.textContent = data.message || "Conexao OpenAI validada.";
    updateOpenaiSettingsIndicator({ ...settingsPayloadFromForm(form), key_configured: true });
  } catch (error) {
    if (status) status.textContent = error.message || "Nao consegui validar a conexao.";
    updateOpenaiSettingsIndicator({ ...settingsPayloadFromForm(form), key_configured: false });
  } finally {
    if (button) button.disabled = false;
  }
}
function renderSettingsUsage(usage){
  const target = document.querySelector("[data-settings-usage]");
  if (!target) return;
  const total = Number(usage.estimated_total_usd || 0);
  const count = Number(usage.event_count || 0);
  const last = usage.last_event || {};
  const lastText = last.operation
    ? `Ultimo: ${escapeHtml(last.operation)} em ${escapeHtml(last.model || "-")} - ${formatUsd(last.estimated_usd || 0)}`
    : "Ultimo: sem registro.";
  target.innerHTML = `<strong>Total local estimado: ${formatUsd(total)}</strong><span>${count} evento(s) registrado(s).</span><span>${lastText}</span>`;
}
function formatUsd(value){
  return `$${Number(value || 0).toFixed(4)}`;
}
function setupImportPathButtons(){
  const form = document.querySelector("[data-import-form]");
  if (!form) return;
  const outputPath = form.querySelector("[name=output_path]");
  const sourcePath = form.querySelector("[name=source_path]");
  const status = document.querySelector("[data-import-status]");
  const selectFolder = form.querySelector("[data-select-folder]");
  const selectVideoFile = form.querySelector("[data-select-video-file]");
  if (selectFolder && outputPath) {
    selectFolder.addEventListener("click", async () => {
      selectFolder.disabled = true;
      if (status) status.textContent = "Abrindo seletor de pasta...";
      try {
        const response = await fetch("/api/select-folder", { method: "POST" });
        const payload = await response.json();
        if (!response.ok || !payload.ok) throw new Error(payload.error || "Nao consegui selecionar a pasta.");
        outputPath.value = payload.path || outputPath.value;
        if (status) status.textContent = "Pasta selecionada.";
      } catch (error) {
        if (status) status.textContent = error.message || "Seletor de pasta indisponivel.";
      } finally {
        selectFolder.disabled = false;
      }
    });
  }
  if (selectVideoFile && sourcePath) {
    selectVideoFile.addEventListener("click", async () => {
      selectVideoFile.disabled = true;
      if (status) status.textContent = "Abrindo seletor de video...";
      try {
        const response = await fetch("/api/select-video-file", { method: "POST" });
        const payload = await response.json();
        if (!response.ok || !payload.ok) throw new Error(payload.error || "Nao consegui selecionar o arquivo.");
        sourcePath.value = payload.path || sourcePath.value;
        if (status) status.textContent = "Video local selecionado.";
      } catch (error) {
        if (status) status.textContent = error.message || "Seletor de arquivo indisponivel.";
      } finally {
        selectVideoFile.disabled = false;
      }
    });
  }
}
let importOpenaiState = { provider: "openai", keyConfigured: true };
function importNeedsOpenaiKey(){
  return importOpenaiState.provider === "openai" && !importOpenaiState.keyConfigured;
}
async function refreshImportKeyBanner(){
  const banner = document.querySelector("[data-import-key-banner]");
  if (!banner) return;
  try {
    const response = await fetch("/api/settings/openai");
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao carregar configuracoes.");
    const settings = payload.settings || {};
    importOpenaiState = {
      provider: String(settings.ai_provider || "openai"),
      keyConfigured: Boolean(settings.key_configured)
    };
    updateOpenaiSettingsIndicator(settings);
  } catch (error) {
    console.warn("Nao consegui checar a chave OpenAI:", error);
    importOpenaiState = { provider: "openai", keyConfigured: true };
    updateOpenaiSettingsIndicator({ ai_provider: "openai", key_configured: false });
  }
  banner.hidden = !importNeedsOpenaiKey();
}
function setupImportKeyBanner(){
  const banner = document.querySelector("[data-import-key-banner]");
  if (!banner) return;
  banner.querySelector("[data-import-key-open]")?.addEventListener("click", () => openSettingsPanel());
  refreshImportKeyBanner();
}
async function startImportJob(form){
  const status = document.querySelector("[data-import-status]");
  const result = document.querySelector("[data-import-result]");
  const button = form.querySelector("button[type=submit]");
  const outputPath = form.querySelector("[name=output_path]");
  if (!String(outputPath?.value || "").trim()) {
    if (status) status.textContent = "Escolha a pasta onde os videos finais serao salvos.";
    outputPath?.focus();
    return;
  }
  if (importNeedsOpenaiKey()) {
    if (status) status.textContent = "Adicione sua chave OpenAI nas configuracoes para importar com IA.";
    openSettingsPanel();
    return;
  }
  if (result) result.innerHTML = "";
  if (status) status.textContent = "Criando job de importacao...";
  if (button) button.disabled = true;
  try {
    const response = await fetch("/api/import-jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(importFormPayload(form))
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao importar.");
    if (status) status.textContent = payload.job?.message || "Importacao iniciada.";
    pollImportJob(payload.job.id, button);
  } catch (error) {
    if (button) button.disabled = false;
    if (status) status.textContent = "Nao consegui iniciar a importacao.";
    if (result) result.innerHTML = `<code>${escapeHtml(error.message || String(error))}</code>`;
  }
}
async function pollImportJob(jobId, button){
  const status = document.querySelector("[data-import-status]");
  const result = document.querySelector("[data-import-result]");
  try {
    const response = await fetch(`/api/import-jobs/${encodeURIComponent(jobId)}`);
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Job nao encontrado.");
    const job = payload.job || {};
    if (status) status.textContent = `${job.message || "Processando..."} (${job.status || "running"})`;
    if (job.status === "ready") {
      if (button) button.disabled = false;
      if (result) result.innerHTML = `<a href="${escapeAttr(job.output_url)}">Abrir projeto importado</a>`;
      if (job.output_url) window.location.assign(job.output_url);
      return;
    }
    if (job.status === "failed" || job.status === "cancelled") {
      if (button) button.disabled = false;
      if (result) result.innerHTML = `<code>${escapeHtml(job.stderr || job.message || "Importacao encerrada.")}</code>`;
      return;
    }
    window.setTimeout(() => pollImportJob(jobId, button), 1200);
  } catch (error) {
    if (button) button.disabled = false;
    if (status) status.textContent = "Nao consegui acompanhar a importacao.";
    if (result) result.innerHTML = `<code>${escapeHtml(error.message || String(error))}</code>`;
  }
}
function captionLines(){
  return Number(localStorage.getItem("cutted-caption-lines") || 2);
}
function captionWidth(){
  return Number(localStorage.getItem("cutted-caption-width") || 28);
}
function captionSize(){
  return Number(localStorage.getItem("cutted-caption-size") || defaultCaptionSize());
}
function defaultCaptionSize(){
  const format = document.body.dataset.format || "tiktok";
  return format === "youtube" || format === "facebook" ? 54 : 72;
}
function captionBottom(){
  return Number(localStorage.getItem("cutted-caption-bottom") || defaultCaptionBottom());
}
function defaultCaptionBottom(){
  const format = document.body.dataset.format || "tiktok";
  if (format === "youtube") return 11;
  if (format === "facebook") return 9;
  return 16;
}
function captionMode(){
  const saved = localStorage.getItem("cutted-caption-mode");
  if (saved === "animated" || saved === "on" || saved === "off") return saved;
  return localStorage.getItem("cutted-caption-enabled") === "0" ? "off" : "on";
}
function captionTextColor(){
  return normalizeCaptionColor(localStorage.getItem("cutted-caption-text-color"), "#ffffff");
}
function captionBackgroundColor(){
  return normalizeCaptionBackground(localStorage.getItem("cutted-caption-background-color"));
}
function captionHighlightBackgroundColor(){
  const stored = localStorage.getItem("cutted-caption-highlight-background-color");
  if (stored) return normalizeCaptionHighlightBackground(stored);
  const background = captionBackgroundColor();
  return background === "transparent" ? "#000000" : normalizeCaptionHighlightBackground(background);
}
function captionStyle(){
  return {
    size: captionSize(),
    width: captionWidth(),
    bottom: captionBottom(),
    mode: captionMode(),
    textColor: captionTextColor(),
    backgroundColor: captionBackgroundColor(),
    highlightBackgroundColor: captionHighlightBackgroundColor()
  };
}
function captionEnabled(){
  return captionMode() !== "off";
}
function normalizeCaptionColor(value, fallback){
  const raw = String(value || "").trim();
  return /^#[0-9a-f]{6}$/i.test(raw) ? raw.toLowerCase() : fallback;
}
function normalizeCaptionBackground(value){
  const raw = String(value || "").trim().toLowerCase();
  if (!raw || raw === "transparent" || raw === "none") return "transparent";
  return normalizeCaptionColor(raw, "#000000");
}
function normalizeCaptionHighlightBackground(value){
  return normalizeCaptionColor(value, "#000000");
}
function storeCaptionStyle(style){
  if (!style || typeof style !== "object") return;
  if (Number.isFinite(Number(style.size))) localStorage.setItem("cutted-caption-size", String(clampNumber(Number(style.size), 24, 140)));
  if (Number.isFinite(Number(style.width))) localStorage.setItem("cutted-caption-width", String(clampNumber(Number(style.width), 12, 56)));
  if (Number.isFinite(Number(style.bottom))) localStorage.setItem("cutted-caption-bottom", String(clampNumber(Number(style.bottom), 6, 32)));
  if (style.mode) localStorage.setItem("cutted-caption-mode", normalizeCaptionMode(style.mode));
  if (style.textColor) localStorage.setItem("cutted-caption-text-color", normalizeCaptionColor(style.textColor, captionTextColor()));
  if (style.backgroundColor) localStorage.setItem("cutted-caption-background-color", normalizeCaptionBackground(style.backgroundColor));
  if (style.highlightBackgroundColor) localStorage.setItem("cutted-caption-highlight-background-color", normalizeCaptionHighlightBackground(style.highlightBackgroundColor));
}
function captionSettingsForCard(card){
  if (!card?.dataset?.rank) return defaultCaptionSettings();
  return platformEditForRank(card.dataset.rank, activePlatformForRank(card.dataset.rank)).captions;
}
function syncPreviewCaptionsForOpenCards(){
  document.querySelectorAll(".card[open]").forEach(card => syncPreviewCaptions(card));
}
function syncPreviewCaptions(card, time = null){
  const layer = card?.querySelector("[data-preview-caption-layer]");
  if (!layer) return;
  const captions = captionSettingsForCard(card);
  applyPreviewCaptionStyle(card, layer);
  if (!captions.enabled) {
    layer.dataset.visible = "false";
    layer.innerHTML = "";
    delete layer.dataset.captionPopKey;
    return;
  }
  const context = previewCaptionContextForCard(card, time);
  if (!context?.event) {
    layer.dataset.visible = "false";
    layer.innerHTML = "";
    delete layer.dataset.captionPopKey;
    return;
  }
  layer.dataset.mode = captions.style.mode === "animated" ? "animated" : "static";
  if (captions.style.mode === "animated") {
    const rendered = previewAnimatedCaptionRender(context.event, context.position);
    if (!rendered.html) {
      layer.innerHTML = "";
      delete layer.dataset.captionPopKey;
    } else if (layer.dataset.captionPopKey !== rendered.key || !layer.innerHTML.trim()) {
      layer.innerHTML = rendered.html;
      layer.dataset.captionPopKey = rendered.key;
    }
  } else {
    delete layer.dataset.captionPopKey;
    const lines = wrapPreviewCaptionLines(context.event.text, captions.style.width, captionLines());
    layer.innerHTML = `<span>${lines.map(escapeHtml).join("<br>")}</span>`;
  }
  layer.dataset.visible = "true";
}
function applyPreviewCaptionStyle(card, layer){
  const style = captionSettingsForCard(card).style;
  const media = card?.querySelector(".media");
  const mediaWidth = media ? media.getBoundingClientRect().width : 0;
  const platformWidth = previewCaptionPlatformWidth(card);
  const fontSize = mediaWidth > 0 ? clampNumber((style.size / platformWidth) * mediaWidth, 14, 72) : style.size;
  layer.style.setProperty("--preview-caption-size", `${fontSize.toFixed(2)}px`);
  layer.style.setProperty("--preview-caption-bottom", `${clampNumber(Number(style.bottom || defaultCaptionBottom()), 6, 32).toFixed(1)}%`);
  layer.style.setProperty("--preview-caption-color", style.textColor);
  layer.style.setProperty("--preview-caption-bg", captionBackgroundCss(style.backgroundColor));
  layer.style.setProperty("--preview-caption-highlight-bg", captionBackgroundCss(style.highlightBackgroundColor || "#000000", true));
  layer.style.setProperty("--preview-caption-padding", style.backgroundColor === "transparent" ? "0" : ".12em .28em");
}
function previewCaptionPlatformWidth(card){
  const format = card?.dataset?.previewFormat || document.body.dataset.format || "tiktok";
  return format === "youtube" ? 1920 : 1080;
}
function captionBackgroundCss(value, forceFallback = false){
  if (value === "transparent") return forceFallback ? "#000000cc" : "transparent";
  const color = normalizeCaptionColor(value, "#000000");
  return `${color}cc`;
}
function previewCaptionEventForCard(card, time = null){
  return previewCaptionContextForCard(card, time)?.event || null;
}
function previewCaptionContextForCard(card, time = null){
  const moment = previewMomentForCard(card);
  if (!moment) return null;
  const row = adjustedMoment(moment);
  const values = trimValues(card);
  const video = primaryCameraVideo(card);
  const raw = time === null && video && Number.isFinite(video.currentTime) ? video.currentTime : time;
  const current = clampPreviewTime(values, Number(raw ?? values.trimStart));
  const position = Math.max(0, current - values.trimStart);
  if (captionSettingsForCard(card).style.mode === "animated") {
    const window = previewAnimatedCaptionTimeline(row).find(item => position >= item.start && position < item.end) || null;
    return window ? { event: window, position } : null;
  }
  const events = previewCaptionEvents(row);
  if (!events.length) return null;
  const event = events.find(item => position >= item.start && position < item.end) || null;
  return event ? { event, position } : null;
}
function animatedCaptionLeadSeconds(){
  return .14;
}
function previewMomentForCard(card){
  const rank = String(card?.dataset?.rank || "");
  return (window.CUTTED_DATA.moments || []).find(item => String(item.rank) === rank) || null;
}
function previewCaptionEvents(row){
  const duration = Math.max(Number(row.adjusted_duration || 0), .1);
  const segmentEvents = previewCaptionEventsFromSegments(row);
  if (segmentEvents.length) return normalizePreviewCaptionEvents(segmentEvents, duration);
  const chunks = previewCaptionChunks(previewCaptionSourceText(row), captionWidth(), captionLines(), duration);
  return normalizePreviewCaptionEvents(distributedPreviewCaptionEvents(chunks, duration), duration);
}
function previewCaptionEventsFromSegments(row){
  const segments = Array.isArray(row.caption_segments) ? row.caption_segments : [];
  const clipStart = Number(row.adjusted_start || row.start || 0);
  const clipEnd = Number(row.adjusted_end || row.end || (clipStart + Number(row.adjusted_duration || 0)));
  return segments.map(item => previewCaptionEventFromSegment(item, clipStart, clipEnd)).filter(Boolean);
}
function previewCaptionEventFromSegment(item, clipStart, clipEnd){
  if (!item || typeof item !== "object") return null;
  const start = Math.max(Number(item.start || 0), clipStart) - clipStart;
  const end = Math.min(Number(item.end || 0), clipEnd) - clipStart;
  const text = cleanPreviewCaptionText(String(item.text || ""));
  if (!text || end <= start) return null;
  return { start: Number(start.toFixed(3)), end: Number(Math.max(end, start + .35).toFixed(3)), text };
}
function normalizePreviewCaptionEvents(events, duration){
  return events.slice().sort((a, b) => a.start - b.start || a.end - b.end).map((event, index, source) => {
    const start = clampNumber(event.start, 0, duration);
    let end = clampNumber(event.end, start, duration);
    if (index + 1 < source.length) {
      const nextStart = clampNumber(source[index + 1].start, 0, duration);
      end = Math.min(end, Math.max(start, nextStart - .04));
    }
    return { start: Number(start.toFixed(3)), end: Number(end.toFixed(3)), text: event.text };
  }).filter(event => event.end - event.start >= .12);
}
function distributedPreviewCaptionEvents(chunks, duration){
  const slot = duration / Math.max(chunks.length, 1);
  return chunks.map((text, index) => ({
    start: Number((index * slot).toFixed(3)),
    end: Number((index === chunks.length - 1 ? duration : (index + 1) * slot).toFixed(3)),
    text
  }));
}
function previewAnimatedCaptionHtml(event, position){
  return previewAnimatedCaptionRender(event, position).html;
}
function previewAnimatedCaptionRender(event, position){
  const wordWindow = event?.active ? event : previewAnimatedCaptionWindow(event, position);
  if (!wordWindow) return { key: "", html: "" };
  const key = wordWindow.key || `${Number(event.start || 0).toFixed(2)}-${wordWindow.index || 0}`;
  const html = `<span class="preview-caption-window" data-caption-pop-key="${key}">
    <span class="preview-caption-word preview-caption-side preview-caption-prev">${escapeHtml(wordWindow.previous)}</span>
    <span class="preview-caption-word preview-caption-active">${escapeHtml(wordWindow.active)}</span>
    <span class="preview-caption-word preview-caption-side preview-caption-next">${escapeHtml(wordWindow.next)}</span>
  </span>`;
  return { key, html };
}
function previewAnimatedCaptionWindow(event, position){
  const words = previewSmartAnimatedCaptionWords(event);
  if (!words.length) return null;
  const timings = previewAnimatedCaptionWordTimings(event, words);
  const slot = timings.find(item => position >= item.start && position < item.end) || timings[timings.length - 1];
  const index = slot ? slot.index : 0;
  return {
    index,
    previous: index > 0 ? words[index - 1] : "",
    active: words[index] || words[0],
    next: index + 1 < words.length ? words[index + 1] : ""
  };
}
function previewAnimatedCaptionTimeline(row){
  const duration = Math.max(Number(row.adjusted_duration || 0), .1);
  const raw = [];
  previewCaptionEvents(row).forEach(event => {
    const words = previewSmartAnimatedCaptionWords(event);
    if (!words.length) return;
    const timings = previewAnimatedCaptionWordTimings(event, words);
    timings.forEach((slot, index) => {
      raw.push({
        start: slot.start,
        end: slot.end,
        previous: index > 0 ? timings[index - 1].word : "",
        active: slot.word,
        next: index + 1 < timings.length ? timings[index + 1].word : "",
        sourceStart: event.start
      });
    });
  });
  return previewAnimatedCaptionDisplayWindows(raw, duration);
}
function previewAnimatedCaptionDisplayWindows(windows, duration){
  let previousEnd = 0;
  return windows.map((window, index) => {
    const rawStart = clampNumber(Number(window.start || 0), 0, duration);
    const rawEnd = clampNumber(Number(window.end || rawStart), rawStart, duration);
    const rawDuration = Math.max(rawEnd - rawStart, .08);
    let start = clampNumber(rawStart - animatedCaptionLeadSeconds(), 0, duration);
    let end = clampNumber(rawEnd - animatedCaptionLeadSeconds(), start, duration);
    if (rawStart <= animatedCaptionLeadSeconds()) {
      end = clampNumber(Math.max(end, start + rawDuration), start, duration);
    }
    if (start < previousEnd) {
      start = previousEnd;
      end = clampNumber(Math.max(end, start + .08), start, duration);
    }
    previousEnd = end;
    if (end <= start) return null;
    return {
      key: `${start.toFixed(3)}-${index}`,
      index,
      start: Number(start.toFixed(3)),
      end: Number(end.toFixed(3)),
      previous: window.previous || "",
      active: window.active || "",
      next: window.next || ""
    };
  }).filter(Boolean);
}
function previewAnimatedCaptionWord(word){
  const text = String(word || "");
  return text.length <= 18 ? text : `${text.slice(0, 17)}...`;
}
const PREVIEW_ANIMATED_CAPTION_MIN_DISPLAY_SECONDS = .22;
const PREVIEW_ANIMATED_CAPTION_TARGET_MIN_WORD_SECONDS = .24;
const PREVIEW_ANIMATED_CAPTION_FAST_WORD_SECONDS = .20;
const PREVIEW_ANIMATED_CAPTION_MAX_GROUP_WORDS = 3;
const PREVIEW_ANIMATED_CAPTION_PROPER_NOUN_STOPWORDS = new Set([
  "a", "as", "o", "os", "um", "uma", "uns", "umas", "de", "da", "das", "do", "dos",
  "e", "ou", "mas", "porque", "por", "para", "pra", "com", "sem", "em", "no", "na",
  "nos", "nas", "ao", "aos", "ai", "aí", "entao", "então", "so", "só", "que", "quem",
  "qual", "quando", "onde", "como", "isso", "essa", "esse", "isto", "esta", "este",
  "eu", "tu", "ele", "ela", "nos", "nós", "voces", "vocês", "voce", "você", "meu",
  "minha", "seu", "sua", "me", "te", "se", "lhe", "nao", "não", "sim", "e", "é", "eh",
  "foi", "era", "ser", "ter", "tem", "ta", "tá", "tava", "vai", "vou", "vao", "vão",
  "fui", "faz", "fazer", "da", "dá", "dar", "precisa", "preciso", "precisava", "acho",
  "tipo", "cara", "ne", "né", "olha", "bom", "certo", "agora"
]);
const PREVIEW_ANIMATED_CAPTION_FILLER_WORDS = new Set([
  "ah", "aham", "uhum", "hum", "eh", "Ã©", "e", "ai", "aÃ­", "entao", "entÃ£o",
  "tipo", "assim", "ne", "nÃ©", "cara", "mano", "bom", "olha", "certo"
]);
const PREVIEW_ANIMATED_CAPTION_ATTACH_PREVIOUS = new Set([
]);
const PREVIEW_ANIMATED_CAPTION_ATTACH_NEXT = new Set([
  "a", "as", "o", "os", "um", "uma", "uns", "umas", "me", "te", "se", "meu", "minha", "seu", "sua",
  "de", "da", "das", "do", "dos", "com", "sem", "pra", "para", "por", "em", "no", "na", "nos", "nas", "ao", "aos"
]);
function cleanPreviewAnimatedCaptionText(text){
  const clean = cleanPreviewCaptionText(text);
  const properNouns = previewAnimatedCaptionProperNouns(clean);
  return clean.split(/\\s+/)
    .map(word => previewAnimatedCaptionDisplayWord(word, properNouns))
    .filter(Boolean)
    .join(" ");
}
function previewSmartAnimatedCaptionWords(event){
  const start = Number(event?.start || 0);
  const end = Math.max(Number(event?.end || start + .12), start + .12);
  let words = cleanPreviewAnimatedCaptionText(event?.text || "").split(/\\s+/).filter(Boolean).map(previewAnimatedCaptionWord);
  if (!words.length) return [];
  words = previewSmartAnimatedCaptionDropFillers(words, end - start);
  return previewSmartAnimatedCaptionGroupWords(words, end - start);
}
function previewSmartAnimatedCaptionDropFillers(words, duration){
  const wordSeconds = duration / Math.max(words.length, 1);
  if (wordSeconds >= PREVIEW_ANIMATED_CAPTION_FAST_WORD_SECONDS) return words;
  const filtered = words.filter(word => previewAnimatedCaptionIsNumericToken(word) || !PREVIEW_ANIMATED_CAPTION_FILLER_WORDS.has(previewAnimatedCaptionWordKey(word)));
  return filtered.length ? filtered : words;
}
function previewSmartAnimatedCaptionGroupWords(words, duration){
  const wordSeconds = duration / Math.max(words.length, 1);
  if (wordSeconds >= PREVIEW_ANIMATED_CAPTION_TARGET_MIN_WORD_SECONDS) return words;
  const groups = [];
  words.forEach(word => {
    if (previewSmartAnimatedCaptionShouldAttachToPrevious(groups, word)) {
      groups[groups.length - 1] = `${groups[groups.length - 1]} ${word}`;
      return;
    }
    groups.push(word);
  });
  return previewSmartAnimatedCaptionBalanceGroups(groups);
}
function previewSmartAnimatedCaptionShouldAttachToPrevious(groups, word){
  if (!groups.length) return false;
  const key = previewAnimatedCaptionWordKey(word);
  const previous = groups[groups.length - 1].split(/\\s+/).filter(Boolean).pop() || "";
  if (PREVIEW_ANIMATED_CAPTION_ATTACH_PREVIOUS.has(key)) return previewSmartAnimatedCaptionGroupSize(groups[groups.length - 1]) < PREVIEW_ANIMATED_CAPTION_MAX_GROUP_WORDS;
  if (PREVIEW_ANIMATED_CAPTION_ATTACH_NEXT.has(previewAnimatedCaptionWordKey(previous))) return previewSmartAnimatedCaptionGroupSize(groups[groups.length - 1]) < PREVIEW_ANIMATED_CAPTION_MAX_GROUP_WORDS;
  return key === previewAnimatedCaptionWordKey(previous) && previewSmartAnimatedCaptionGroupSize(groups[groups.length - 1]) < PREVIEW_ANIMATED_CAPTION_MAX_GROUP_WORDS;
}
function previewSmartAnimatedCaptionBalanceGroups(groups){
  const result = [];
  groups.forEach(group => {
    const key = previewAnimatedCaptionWordKey(group);
    if (result.length && PREVIEW_ANIMATED_CAPTION_ATTACH_PREVIOUS.has(key) && previewSmartAnimatedCaptionGroupSize(result[result.length - 1]) < PREVIEW_ANIMATED_CAPTION_MAX_GROUP_WORDS) {
      result[result.length - 1] = `${result[result.length - 1]} ${group}`;
      return;
    }
    result.push(group);
  });
  return result;
}
function previewSmartAnimatedCaptionGroupSize(group){
  return String(group || "").split(/\\s+/).filter(Boolean).length;
}
function previewAnimatedCaptionIsNumericToken(word){
  return /\\d/.test(String(word || ""));
}
function previewAnimatedCaptionProperNouns(text){
  const matches = Array.from(String(text || "").matchAll(/[\\p{L}\\p{N}_]+/gu));
  const result = new Set();
  matches.forEach((match, index) => {
    const word = match[0];
    if (!previewAnimatedCaptionIsCapitalizedWord(word)) return;
    const key = previewAnimatedCaptionWordKey(word);
    if (PREVIEW_ANIMATED_CAPTION_PROPER_NOUN_STOPWORDS.has(key)) return;
    const before = String(text || "").slice(0, match.index || 0);
    const sentenceStart = !before.trim() || /[.!?…]\\s*$/.test(before);
    const previousCapitalized = index > 0 && previewAnimatedCaptionIsCapitalizedWord(matches[index - 1][0]);
    const nextCapitalized = index + 1 < matches.length && previewAnimatedCaptionIsCapitalizedWord(matches[index + 1][0]);
    if (!sentenceStart || previousCapitalized || nextCapitalized) result.add(key);
  });
  return result;
}
function previewAnimatedCaptionDisplayWord(word, properNouns){
  const clean = previewAnimatedCaptionCleanWord(word);
  if (!clean) return "";
  const key = previewAnimatedCaptionWordKey(clean);
  if (previewAnimatedCaptionIsAcronym(clean) || properNouns.has(key)) return clean;
  return clean.toLocaleLowerCase("pt-BR");
}
function previewAnimatedCaptionCleanWord(word){
  const raw = String(word || "").replace(/[^\\p{L}\\p{N}_.,:%]+/gu, "");
  return Array.from(raw).filter((char, index, chars) => {
    if (".,:".includes(char)) {
      return index > 0 && index + 1 < chars.length && /\\p{N}/u.test(chars[index - 1]) && /\\p{N}/u.test(chars[index + 1]);
    }
    if (char === "%") {
      return index > 0 && /\\p{N}/u.test(chars[index - 1]);
    }
    return true;
  }).join("");
}
function previewAnimatedCaptionWordKey(word){
  return String(word || "").replace(/[^\\p{L}\\p{N}_]+/gu, "").toLocaleLowerCase("pt-BR");
}
function previewAnimatedCaptionIsCapitalizedWord(word){
  const letters = Array.from(String(word || "").matchAll(/\\p{L}/gu)).map(match => match[0]);
  return Boolean(letters.length) && letters[0] === letters[0].toLocaleUpperCase("pt-BR") && !previewAnimatedCaptionIsAcronym(word);
}
function previewAnimatedCaptionIsAcronym(word){
  const letters = Array.from(String(word || "").matchAll(/\\p{L}/gu)).map(match => match[0]).join("");
  return letters.length > 1 && letters.length <= 6 && letters === letters.toLocaleUpperCase("pt-BR");
}
function previewAnimatedCaptionWordTimings(event, words){
  const start = Number(event.start || 0);
  const end = Math.max(Number(event.end || start + .12), start + .12);
  const duration = end - start;
  const weights = words.map(previewAnimatedCaptionWordWeight);
  const total = weights.reduce((sum, value) => sum + value, 0) || Math.max(words.length, 1);
  let cursor = start;
  const timings = words.map((word, index) => {
    const wordEnd = index === words.length - 1 ? end : Math.min(end, cursor + (duration * weights[index] / total));
    const timing = { index, word, start: cursor, end: wordEnd };
    cursor = wordEnd;
    return timing;
  });
  return previewMergeFastAnimatedCaptionTimings(timings);
}
function previewMergeFastAnimatedCaptionTimings(timings){
  const groups = timings.map(item => ({ word: item.word, start: item.start, end: item.end }));
  while (groups.length > 1) {
    const index = groups.findIndex(item => item.end - item.start < PREVIEW_ANIMATED_CAPTION_MIN_DISPLAY_SECONDS);
    if (index < 0) break;
    const target = index + 1 < groups.length ? index + 1 : index - 1;
    const firstIndex = Math.min(index, target);
    const secondIndex = Math.max(index, target);
    const first = groups[firstIndex];
    const second = groups[secondIndex];
    groups.splice(firstIndex, secondIndex - firstIndex + 1, {
      word: `${first.word} ${second.word}`,
      start: first.start,
      end: second.end
    });
  }
  return groups.map((item, index) => ({ index, word: item.word, start: item.start, end: item.end }));
}
function previewAnimatedCaptionWordWeight(word){
  const core = String(word || "").replace(/[^\\p{L}\\p{N}_]+/gu, "");
  return clampNumber(Math.sqrt(Math.max(core.length, 1)), .7, 3);
}
function previewCaptionSourceText(row){
  const transcript = String(row.transcript || "").trim();
  if (transcript) return cleanPreviewCaptionText(transcript);
  return cleanPreviewCaptionText(String(row.peak_text || row.title || "Legenda do corte"));
}
const PREVIEW_CAPTION_MOJIBAKE_REPLACEMENTS = new Map([
  ["\u00c3\u00a1", "\u00e1"],
  ["\u00c3\u00a0", "\u00e0"],
  ["\u00c3\u00a2", "\u00e2"],
  ["\u00c3\u00a3", "\u00e3"],
  ["\u00c3\u00a4", "\u00e4"],
  ["\u00c3\u00a9", "\u00e9"],
  ["\u00c3\u00aa", "\u00ea"],
  ["\u00c3\u00ad", "\u00ed"],
  ["\u00c3\u00b3", "\u00f3"],
  ["\u00c3\u00b4", "\u00f4"],
  ["\u00c3\u00b5", "\u00f5"],
  ["\u00c3\u00ba", "\u00fa"],
  ["\u00c3\u00bc", "\u00fc"],
  ["\u00c3\u00a7", "\u00e7"],
  ["\u00c3\u0081", "\u00c1"],
  ["\u00c3\u0080", "\u00c0"],
  ["\u00c3\u0082", "\u00c2"],
  ["\u00c3\u0083", "\u00c3"],
  ["\u00c3\u0089", "\u00c9"],
  ["\u00c3\u008a", "\u00ca"],
  ["\u00c3\u008d", "\u00cd"],
  ["\u00c3\u0093", "\u00d3"],
  ["\u00c3\u0094", "\u00d4"],
  ["\u00c3\u0095", "\u00d5"],
  ["\u00c3\u009a", "\u00da"],
  ["\u00c3\u009c", "\u00dc"],
  ["\u00c3\u0087", "\u00c7"],
  ["\u00c2\u00ba", "\u00ba"],
  ["\u00c2\u00aa", "\u00aa"],
  ["\u00c2\u00b7", "\u00b7"],
  ["\u00c2\u00b4", "\u00b4"]
]);
function repairPreviewCaptionEncoding(value){
  const text = String(value || "");
  if (!/[ÃÂâ]/.test(text)) return text;
  const repaired = repairPreviewCaptionEncodingAsUtf8(text);
  const mapped = replacePreviewCaptionMojibakeSequences(repaired);
  return previewCaptionMojibakeScore(mapped) <= previewCaptionMojibakeScore(text) ? mapped : text;
}
function repairPreviewCaptionEncodingAsUtf8(text){
  try {
    const bytes = Array.from(text, char => {
      const code = char.charCodeAt(0);
      if (code > 255) throw new Error("Not latin-1 text");
      return code;
    });
    const repaired = new TextDecoder("utf-8", { fatal: true }).decode(new Uint8Array(bytes));
    return previewCaptionMojibakeScore(repaired) < previewCaptionMojibakeScore(text) ? repaired : text;
  } catch (_error) {
    return text;
  }
}
function replacePreviewCaptionMojibakeSequences(text){
  let clean = String(text || "");
  PREVIEW_CAPTION_MOJIBAKE_REPLACEMENTS.forEach((target, source) => {
    clean = clean.split(source).join(target);
  });
  return clean;
}
function previewCaptionMojibakeScore(text){
  return (String(text || "").match(/Ã|Â|â€|â™|�/g) || []).length;
}
function cleanPreviewCaptionText(text){
  return repairPreviewCaptionEncoding(text)
    .replace(/[\u201c\u201d]/g, '"')
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/\u2026/g, "...")
    .replace(/\ufeff/g, " ")
    .replace(/[\u2013\u2014]/g, "-")
    .replace(/(^|\\s)(>{1,3}|-{1,2})\\s*/g, " ")
    .replace(/\\s+/g, " ")
    .replace(/\\s+([,.;:!?])/g, "$1")
    .replace(/(\\d)([.,:])\\s+(?=\\d)/g, "$1$2")
    .replace(/([,.;:!?])([^\\s,.;:!?])/g, spaceAfterPreviewCaptionPunctuation)
    .replace(/^(ne\\??|aham|uhum|hum|entao|mas)\\s+/i, "")
    .trim()
    .replace(/^-+|-+$/g, "")
    .trim();
}
function spaceAfterPreviewCaptionPunctuation(match, punctuation, nextChar, offset, value){
  const previousChar = offset > 0 ? String(value || "")[offset - 1] : "";
  if (".,:".includes(punctuation) && /\\d/.test(previousChar) && /\\d/.test(nextChar)) {
    return `${punctuation}${nextChar}`;
  }
  return `${punctuation} ${nextChar}`;
}
function previewCaptionChunks(text, charsPerLine, maxLines, duration){
  const lineWidth = Math.max(12, Number(charsPerLine) || 28);
  const lineCount = Math.max(1, Number(maxLines) || 2);
  const capacity = Math.max(18, lineWidth * lineCount);
  const chunks = greedyPreviewCaptionChunks(String(text || "").split(/\\s+/).filter(Boolean), capacity);
  const limit = Math.max(1, Math.floor(Math.max(duration, 1) / 1.35));
  if (chunks.length > limit) {
    const limited = chunks.slice(0, limit);
    limited[limited.length - 1] = ellipsizePreviewCaption(limited[limited.length - 1]);
    return limited;
  }
  return chunks.length ? chunks : ["Legenda do corte"];
}
function wrapPreviewCaptionLines(text, charsPerLine, maxLines){
  const lineWidth = Math.max(12, Number(charsPerLine) || 28);
  const lineCount = Math.max(1, Number(maxLines) || 2);
  const lines = greedyPreviewCaptionChunks(String(text || "").split(/\\s+/).filter(Boolean), lineWidth);
  if (lines.length <= lineCount) return lines;
  return lines.slice(0, lineCount - 1).concat(lines.slice(lineCount - 1).join(" "));
}
function greedyPreviewCaptionChunks(words, capacity){
  const chunks = [];
  let current = [];
  words.forEach(word => {
    const candidate = current.concat(word).join(" ");
    if (current.length && candidate.length > capacity) {
      chunks.push(current.join(" "));
      current = [word];
    } else {
      current.push(word);
    }
  });
  if (current.length) chunks.push(current.join(" "));
  return chunks;
}
function ellipsizePreviewCaption(text){
  const clean = String(text || "").replace(/[ .,;:]+$/g, "");
  return clean ? `${clean}...` : "...";
}
function syncCaptionInputs(){
  document.querySelectorAll("[data-caption-lines]").forEach(input => { input.value = String(captionLines()); });
  document.querySelectorAll("[data-caption-width]").forEach(input => { input.value = String(captionWidth()); });
  document.querySelectorAll("[data-caption-size]").forEach(input => { input.value = String(captionSize()); });
  document.querySelectorAll("[data-caption-bottom]").forEach(input => { input.value = String(captionBottom()); });
  document.querySelectorAll("[data-caption-text-color]").forEach(input => { input.value = captionTextColor(); });
  document.querySelectorAll("[data-caption-background-color]").forEach(input => { input.value = captionBackgroundColor() === "transparent" ? "#000000" : captionBackgroundColor(); });
  document.querySelectorAll("[data-caption-highlight-background-color]").forEach(input => { input.value = captionHighlightBackgroundColor(); });
  document.querySelectorAll("[data-caption-enabled]").forEach(input => { input.checked = captionEnabled(); });
  document.querySelectorAll("[data-caption-current]").forEach(item => { item.textContent = captionMode() === "animated" ? "Animada" : captionEnabled() ? "Ativada" : "Desligada"; });
}
function captionCommand(){
  const chars = captionWidth();
  const lines = captionLines();
  const script = window.CUTTED_SCRIPT || "cutted.py";
  const coverFrame = renderCoverFrameEnabled() ? " --cover-frame" : "";
  return `python "${script}" caption-selected "caption-queue.json" --out "captioned-clips" --base-dir "." --chars-per-line ${chars} --max-lines ${lines}${coverFrame}`;
}
function renderCoverFrameEnabled(){
  return Boolean(renderQueueState.coverFrame);
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
        max_lines: captionLines(),
        captions_enabled: queue.some(item => item.captions_enabled !== false),
        cover_frame_enabled: renderCoverFrameEnabled(),
        gallery_path: currentGalleryPath()
      })
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao renderizar.");
    renderFinalizeResults(payload.files || []);
    const exported = payload.export_dir ? ` Exportado em: ${payload.export_dir}` : "";
    if (status) status.textContent = `${payload.count || 0} video(s) finalizado(s).${exported}`;
  } catch (error) {
    if (status) status.textContent = finalizeErrorMessage(error);
  } finally {
    button.disabled = false;
  }
}
function finalizeStorageKey(){
  return `cutted-finalize-results:${currentGalleryPath()}`;
}
function storeFinalizeResults(files){
  if (!Array.isArray(files) || !files.length) return;
  try {
    localStorage.setItem(finalizeStorageKey(), JSON.stringify(files));
  } catch (error) {
    console.warn("Nao foi possivel salvar os resultados renderizados.", error);
  }
}
function storedFinalizeResults(){
  try {
    const raw = localStorage.getItem(finalizeStorageKey());
    const files = raw ? JSON.parse(raw) : [];
    return Array.isArray(files) ? files : [];
  } catch (error) {
    console.warn("Nao foi possivel restaurar os resultados renderizados.", error);
    return [];
  }
}
async function restoreFinalizeResults(){
  const status = document.querySelector("[data-render-status]");
  const cached = storedFinalizeResults();
  if (cached.length) {
    renderFinalizeResults(cached, { skipPersist: true });
    if (status && !status.textContent) status.textContent = `${cached.length} video(s) restaurado(s) desta galeria.`;
  }
  try {
    const response = await fetch(`/api/finalize-results?gallery_path=${encodeURIComponent(currentGalleryPath())}`, { cache: "no-store" });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok) return;
    const files = Array.isArray(payload.files) ? payload.files : [];
    if (!files.length) return;
    renderFinalizeResults(files);
    const exported = payload.export_dir ? ` Exportado em: ${payload.export_dir}` : "";
    if (status) {
      status.textContent = payload.ready
        ? `${payload.count || files.length} video(s) renderizado(s) restaurado(s).${exported}`
        : `${payload.count || files.length} video(s) ja pronto(s); render ainda pode estar finalizando.`;
    }
  } catch (error) {
    if (cached.length || !status || status.textContent) return;
    status.textContent = "Nao consegui restaurar a fila renderizada agora.";
  }
}
function renderFinalizeResults(files, options = {}){
  const results = document.querySelector("[data-render-results]");
  if (!results) return;
  const safeFiles = Array.isArray(files) ? files : [];
  if (!safeFiles.length) {
    results.innerHTML = '<div class="effect-empty">Nenhum video renderizado ainda.</div>';
    return;
  }
  if (!options.skipPersist) storeFinalizeResults(safeFiles);
  results.innerHTML = safeFiles.map((file, index) => {
    const camera = normalizeCamera(file.camera);
    const effect = normalizeEffect(file.effect);
    const overlay = normalizeOverlay(file.overlay);
    const bumpers = normalizeBumpers(file.bumpers);
    const bumperText = bumperSummary(bumpers);
    const title = `#${String(file.rank || "").padStart(2, "0")} ${file.label || file.platform || "video"}`;
    const meta = [
      file.width && file.height ? `${file.width}x${file.height}` : "",
      file.final_duration ? fixed(file.final_duration) : file.adjusted_duration ? fixed(file.adjusted_duration) : "",
      cameraHasMovement(camera) ? cameraLabel(camera) : "",
      effect.key !== "none" ? effect.label : "",
      overlay.key !== "none" ? overlay.label : "",
      Object.keys(bumpers).length ? bumperText : ""
    ].filter(Boolean).join(" - ");
    const open = index === 0 ? " open" : "";
    const downloadName = file.download_name || file.url?.split("/").pop() || "cuted-video.mp4";
    const finalFile = file.final_file || file.local_file || "";
    const coverFile = file.final_cover_file || file.local_cover_file || file.cover_file || "";
    const coverFrameUrl = file.cover_frame_url || "";
    const coverFrameFile = file.final_cover_frame_file || file.local_cover_frame_file || file.cover_frame_file || "";
    const coverFrameDownloadName = file.download_cover_frame_name || coverFrameUrl.split("/").pop() || "cuted-tiktok-cover-frame.mp4";
    const finalDir = file.final_dir || "";
    const fileStatus = finalFile ? "Arquivo final exportado" : "Preview temporario";
    return `<details class="result-item"${open}>
      <summary><strong>${escapeHtml(title)}</strong><span>${escapeHtml(meta || "Video finalizado")}</span></summary>
      <div class="result-body">
        <video controls preload="metadata" src="${escapeAttr(file.url)}"></video>
        <div class="result-meta">
          <dl>
            <dt>Status</dt><dd>${escapeHtml(fileStatus)}</dd>
            <dt>Formato</dt><dd>${escapeHtml(file.label || file.platform || "-")}</dd>
            <dt>Duracao</dt><dd>${escapeHtml(file.final_duration ? fixed(file.final_duration) : file.adjusted_duration ? fixed(file.adjusted_duration) : "-")}</dd>
            <dt>Camera</dt><dd>${escapeHtml(cameraLabel(camera))}</dd>
            <dt>Efeito</dt><dd>${escapeHtml(effect.label)}</dd>
            <dt>Chamada</dt><dd>${escapeHtml(overlay.label)}</dd>
            <dt>Vinhetas</dt><dd>${escapeHtml(bumperText)}</dd>
            ${finalFile ? `<dt>Arquivo final</dt><dd><span class="result-path">${escapeHtml(finalFile)}</span></dd>` : ""}
            ${coverFile ? `<dt>Capa final</dt><dd><span class="result-path">${escapeHtml(coverFile)}</span></dd>` : ""}
            ${coverFrameFile ? `<dt>Versao TikTok</dt><dd><span class="result-path">${escapeHtml(coverFrameFile)}</span></dd>` : ""}
            ${finalDir ? `<dt>Pasta final</dt><dd><span class="result-path">${escapeHtml(finalDir)}</span></dd>` : ""}
          </dl>
          <div class="result-actions">
            <a href="${escapeAttr(file.url)}" target="_blank" rel="noopener">Abrir preview</a>
            <a class="secondary" href="${escapeAttr(file.url)}" download="${escapeAttr(downloadName)}">Baixar preview</a>
            ${coverFrameUrl ? `<a class="secondary" href="${escapeAttr(coverFrameUrl)}" target="_blank" rel="noopener">Abrir TikTok</a>` : ""}
            ${coverFrameUrl ? `<a class="secondary" href="${escapeAttr(coverFrameUrl)}" download="${escapeAttr(coverFrameDownloadName)}">Baixar TikTok</a>` : ""}
            ${finalDir ? `<button class="secondary" type="button" data-open-folder="${escapeAttr(finalDir)}">Abrir pasta</button>` : ""}
            ${finalFile ? `<button class="secondary" type="button" data-copy-path="${escapeAttr(finalFile)}">Copiar caminho</button>` : ""}
            ${coverFrameFile ? `<button class="secondary" type="button" data-copy-path="${escapeAttr(coverFrameFile)}">Copiar TikTok</button>` : ""}
          </div>
        </div>
      </div>
    </details>`;
  }).join("");
}
const renderQueueState = {
  profile: localStorage.getItem("cuted-render-profile") || "medium",
  coverFrame: localStorage.getItem("cuted-render-cover-frame") === "1",
  pollId: null,
  activityPollId: null,
  lastFocus: null,
  lastJobs: []
};
function setupRenderQueuePanel(){
  const modal = document.querySelector("[data-render-queue-modal]");
  if (!modal) return;
  document.querySelectorAll("[data-render-profile]").forEach(button => {
    button.classList.toggle("active", button.dataset.renderProfile === renderQueueState.profile);
    button.addEventListener("click", () => setRenderQueueProfile(button.dataset.renderProfile || "medium"));
  });
  document.querySelectorAll("[data-render-cover-frame]").forEach(input => {
    input.checked = renderQueueState.coverFrame;
    input.addEventListener("change", () => setRenderCoverFrameEnabled(input.checked));
  });
  document.querySelector("[data-render-queue-close]")?.addEventListener("click", () => closeRenderQueuePanel());
  modal.addEventListener("click", event => { if (event.target === modal) closeRenderQueuePanel(); });
  document.addEventListener("keydown", event => {
    if (!modal.hidden && event.key === "Escape") closeRenderQueuePanel();
  });
  document.querySelector("[data-render-queue-list]")?.addEventListener("click", event => {
    const target = event.target instanceof Element ? event.target : null;
    const folderButton = target?.closest("[data-open-folder]");
    if (folderButton) openResultFolder(folderButton.dataset.openFolder || "", folderButton);
    const cancelButton = target?.closest("[data-render-cancel]");
    if (cancelButton) cancelRenderQueueJob(cancelButton.dataset.renderCancel || "", cancelButton);
    const removeButton = target?.closest("[data-render-remove]");
    if (removeButton) removeRenderQueueJob(removeButton.dataset.renderRemove || "", removeButton);
  });
  loadRenderQueue();
}
function openRenderQueuePanel(){
  const modal = document.querySelector("[data-render-queue-modal]");
  if (!modal) return;
  renderQueueState.lastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  modal.hidden = false;
  modal.classList.remove("is-closing");
  requestAnimationFrame(() => modal.classList.add("is-open"));
  modal.querySelector("[data-render-queue-panel]")?.focus();
  loadRenderQueue();
  scheduleRenderQueuePoll();
}
function closeRenderQueuePanel(){
  const modal = document.querySelector("[data-render-queue-modal]");
  if (!modal || modal.hidden) return;
  window.clearTimeout(renderQueueState.pollId);
  modal.classList.remove("is-open");
  modal.classList.add("is-closing");
  window.setTimeout(() => {
    modal.hidden = true;
    modal.classList.remove("is-closing");
    renderQueueState.lastFocus?.focus?.();
    renderQueueState.lastFocus = null;
  }, 190);
}
function scheduleRenderQueuePoll(){
  window.clearTimeout(renderQueueState.pollId);
  renderQueueState.pollId = window.setTimeout(async () => {
    const modal = document.querySelector("[data-render-queue-modal]");
    if (!modal || modal.hidden) return;
    await loadRenderQueue();
    scheduleRenderQueuePoll();
  }, 1800);
}
async function loadRenderQueue(){
  const status = document.querySelector("[data-render-queue-status]");
  try {
    const response = await fetch(`/api/render-jobs?gallery_path=${encodeURIComponent(currentGalleryPath())}`, { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao carregar fila.");
    renderQueueJobs(payload.jobs || []);
  } catch (error) {
    if (status) status.textContent = error.message || "Nao consegui carregar a fila.";
  }
}
function renderQueueJobs(jobs){
  const list = document.querySelector("[data-render-queue-list]");
  const status = document.querySelector("[data-render-queue-status]");
  const safeJobs = Array.isArray(jobs) ? jobs : [];
  renderQueueState.lastJobs = safeJobs;
  const running = safeJobs.filter(job => job.status === "rendering" || job.status === "queued").length;
  const ready = safeJobs.filter(job => job.status === "ready").length;
  updateHeaderRenderActivity(safeJobs);
  if (status) status.textContent = safeJobs.length ? `${running} em fila; ${ready} pronto(s).` : "Nenhum render em andamento.";
  if (!list) return;
  if (!safeJobs.length) {
    list.innerHTML = '<div class="render-empty">Quando um corte for enviado, ele aparece aqui.</div>';
    return;
  }
  list.innerHTML = safeJobs.map(renderQueueJobHtml).join("");
}
function updateHeaderRenderActivity(jobs){
  const button = document.getElementById("finalize-videos");
  if (!button) return;
  const active = (Array.isArray(jobs) ? jobs : []).some(job => job.status === "rendering" || job.status === "queued");
  button.classList.toggle("is-rendering", active);
  button.setAttribute("aria-label", active ? "Render em andamento" : "Renderizar");
  button.title = active ? "Render em andamento" : "Renderizar";
  scheduleHeaderRenderActivityPoll(active);
}
function scheduleHeaderRenderActivityPoll(active){
  window.clearTimeout(renderQueueState.activityPollId);
  if (!active) return;
  renderQueueState.activityPollId = window.setTimeout(async () => {
    await loadRenderQueue();
  }, 2400);
}
function renderQueueJobHtml(job){
  const summary = job.summary || {};
  const id = String(job.id || "");
  const title = `#${String(summary.rank || "").padStart(2, "0")} ${summary.title || "Render CUTED"}`;
  const eta = Number(job.eta_seconds || 0);
  const meta = [
    summary.platform || "",
    summary.duration ? fixed(summary.duration) : "",
    summary.cover_frame_enabled ? "Capa TikTok" : "",
    renderProfileLabel(job.resource_profile),
    job.speed || "",
    eta > 0 && job.status === "rendering" ? `${formatRenderEta(eta)} restantes` : ""
  ].filter(Boolean).join(" - ");
  const progress = Math.max(0, Math.min(100, Number(job.progress || 0)));
  const folder = job.export_dir || job.output_dir || "";
  const canOpen = job.status === "ready" && folder;
  const canCancel = job.status === "queued" || job.status === "rendering";
  const canRemove = !canCancel;
  return `<article class="render-job-card" data-status="${escapeAttr(job.status || "queued")}">
    <div class="render-job-main">
      <div class="render-job-title"><span class="render-job-pill">${escapeHtml(renderStatusLabel(job.status))}</span><strong>${escapeHtml(title)}</strong></div>
      <div class="render-job-meta">${escapeHtml(job.message || meta || "Render local")}</div>
      <div class="render-job-progress" style="--progress:${progress}%"><span></span></div>
      <div class="render-job-meta">${escapeHtml(`${Math.round(progress)}%${meta ? ` - ${meta}` : ""}`)}</div>
      ${job.error ? `<div class="render-job-meta">${escapeHtml(job.error)}</div>` : ""}
    </div>
    <div class="render-job-actions">
      ${canOpen ? `<button class="primary" type="button" data-open-folder="${escapeAttr(folder)}">Abrir pasta</button>` : `<button type="button" disabled>${escapeHtml(renderStatusLabel(job.status))}</button>`}
      ${canCancel ? `<button type="button" data-render-cancel="${escapeAttr(id)}">Parar</button>` : ""}
      ${canRemove ? `<button type="button" data-render-remove="${escapeAttr(id)}">Remover</button>` : ""}
    </div>
  </article>`;
}
function renderStatusLabel(status){
  const labels = { queued: "Fila", rendering: "Render", ready: "Pronto", failed: "Falha", cancelled: "Cancelado" };
  return labels[status] || "Fila";
}
function renderProfileLabel(profile){
  const labels = { eco: "Eco", medium: "Medio", high: "Alto" };
  return labels[profile] || "Medio";
}
function formatRenderEta(value){
  const seconds = Math.max(0, Math.round(Number(value) || 0));
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return minutes ? `${minutes}m ${String(rest).padStart(2, "0")}s` : `${rest}s`;
}
async function setRenderQueueProfile(profile){
  renderQueueState.profile = profile || "medium";
  localStorage.setItem("cuted-render-profile", renderQueueState.profile);
  document.querySelectorAll("[data-render-profile]").forEach(item => {
    item.classList.toggle("active", item.dataset.renderProfile === renderQueueState.profile);
  });
  const queued = renderQueueState.lastJobs.filter(job => job.status === "queued");
  const rendering = renderQueueState.lastJobs.some(job => job.status === "rendering");
  const status = document.querySelector("[data-render-queue-status]");
  if (!queued.length) {
    if (status && rendering) {
      status.textContent = `${renderProfileLabel(renderQueueState.profile)} salvo para proximos renders. Render atual mantem os threads atuais.`;
    }
    return;
  }
  if (status) status.textContent = `Atualizando ${queued.length} render(es) em fila para ${renderProfileLabel(renderQueueState.profile)}...`;
  try {
    const results = await Promise.all(queued.map(job => updateRenderQueueProfileJob(String(job.id || ""), renderQueueState.profile)));
    const changed = results.filter(item => item.changed).length;
    if (status) status.textContent = changed
      ? `${changed} render(es) em fila atualizados para ${renderProfileLabel(renderQueueState.profile)}.`
      : `${renderProfileLabel(renderQueueState.profile)} salvo para proximos renders.`;
    await loadRenderQueue();
  } catch (error) {
    if (status) status.textContent = error.message || "Nao consegui atualizar o perfil da fila.";
  }
}
function setRenderCoverFrameEnabled(enabled){
  renderQueueState.coverFrame = Boolean(enabled);
  localStorage.setItem("cuted-render-cover-frame", renderQueueState.coverFrame ? "1" : "0");
  document.querySelectorAll("[data-render-cover-frame]").forEach(input => {
    input.checked = renderQueueState.coverFrame;
  });
  const status = document.querySelector("[data-render-queue-status]");
  if (status) {
    status.textContent = renderQueueState.coverFrame
      ? "Capa TikTok ligada para os proximos renders."
      : "Capa TikTok desligada para os proximos renders.";
  }
}
async function updateRenderQueueProfileJob(jobId, profile){
  if (!jobId) return { changed: false };
  const response = await fetch(`/api/render-jobs/${encodeURIComponent(jobId)}/profile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ gallery_path: currentGalleryPath(), resource_profile: profile })
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || !payload.ok) throw new Error(payload.error || "Nao consegui atualizar o perfil da fila.");
  if (Array.isArray(payload.jobs)) renderQueueState.lastJobs = payload.jobs;
  return payload;
}
function renderQueuePayloadForCard(card){
  const data = buildExportData();
  const rank = String(card.dataset.rank || "");
  const platform = activePlatformForRank(rank);
  const row = (data.caption_queue || []).find(item => String(item.rank) === rank && item.platform === platform);
  if (!row) throw new Error("Este corte ainda nao esta pronto para render.");
  validateActiveRenderRow(card, row, platform);
  return Object.assign({}, data, { caption_queue: [row] });
}
function validateActiveRenderRow(card, row, platform){
  const rank = String(card?.dataset?.rank || "");
  const duration = Number(row.adjusted_duration || cameraTimelineDurationForCard(card));
  const edit = platformEditForRank(rank, platform);
  const expectedPreset = resolutionPresetForPlatform(platform);
  const values = trimValues(card);
  const expectedPath = exportCameraPathForEdit(edit, values.duration, values.trimStart, duration);
  const actualPath = normalizeCameraPath(row.camera_path);
  if (row.resolution_preset !== expectedPreset) {
    throw new Error("O render nao bate com o formato ativo. Reabra o corte e tente de novo.");
  }
  if (JSON.stringify(actualPath) !== JSON.stringify(expectedPath)) {
    throw new Error("A camera ativa mudou antes do envio. Reabra o corte e tente de novo.");
  }
}
async function sendCardToRenderQueue(card){
  const status = card?.__cutedControlSurface;
  if (!card || card.dataset.renderSubmitting === "1") return;
  card.dataset.renderSubmitting = "1";
  try {
    const queue = renderQueuePayloadForCard(card);
    const response = await fetch("/api/render-jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        queue,
        chars_per_line: captionWidth(),
        max_lines: captionLines(),
        captions_enabled: queue.caption_queue.some(item => item.captions_enabled !== false),
        gallery_path: currentGalleryPath(),
        cover_frame_enabled: renderCoverFrameEnabled(),
        resource_profile: renderQueueState.profile
      })
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao enviar para render.");
    if (payload.duplicate) {
      cancelControlSurfaceReady(card);
      card?.__cutedControlSurface?.update?.({ renderQueued: false });
      card?.__cutedControlSurface?.setStatus?.({ kind: "ready", label: "Ja esta renderizando", tone: "green" }, 2600);
      await loadRenderQueue();
      return;
    }
    cancelControlSurfaceReady(card);
    card?.__cutedControlSurface?.update?.({ renderQueued: false });
    card?.__cutedControlSurface?.setStatus?.({ kind: "ready", label: "SENT TO RENDER", tone: "green" }, 1800);
    await loadRenderQueue();
  } catch (error) {
    updateControlSurfaceForCard(card);
    card?.__cutedControlSurface?.update?.({ renderQueued: false });
    status?.setStatus?.({ kind: "error", label: error.message || "Render falhou", tone: "red" }, 2200);
    showAppNotice(error.message || "Nao consegui enviar para render.");
  } finally {
    delete card.dataset.renderSubmitting;
  }
}
async function cancelRenderQueueJob(jobId, button){
  if (!jobId) return;
  await updateRenderQueueJob(`/api/render-jobs/${encodeURIComponent(jobId)}/cancel`, button, "Parando...");
}
async function removeRenderQueueJob(jobId, button){
  if (!jobId) return;
  await updateRenderQueueJob(`/api/render-jobs/${encodeURIComponent(jobId)}/remove`, button, "Removendo...");
}
async function updateRenderQueueJob(url, button, label){
  const previous = button?.textContent || "";
  try {
    if (button) {
      button.disabled = true;
      button.textContent = label;
    }
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ gallery_path: currentGalleryPath() })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Nao consegui atualizar a fila.");
    if (Array.isArray(payload.jobs)) renderQueueJobs(payload.jobs);
    else await loadRenderQueue();
  } catch (error) {
    if (button) {
      button.disabled = false;
      button.textContent = previous;
    }
    showAppNotice(error.message || "Nao consegui atualizar a fila.");
  }
}
async function openResultFolder(path, button){
  if (!path) return;
  const previous = button?.textContent || "Abrir pasta";
  try {
    if (button) {
      button.disabled = true;
      button.textContent = "Abrindo...";
    }
    const response = await fetch("/api/open-folder", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({path})
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Falha ao abrir pasta.");
    if (button) button.textContent = "Pasta aberta";
  } catch (error) {
    if (button) button.textContent = "Falhou";
    alert(error.message || String(error));
  } finally {
    window.setTimeout(() => {
      if (!button) return;
      button.disabled = false;
      button.textContent = previous;
    }, 1400);
  }
}
async function copyResultPath(path, button){
  try {
    await navigator.clipboard.writeText(path);
    if (button) button.textContent = "Copiado";
  } catch (error) {
    copyTextFallback(path);
    if (button) button.textContent = "Copiado";
  }
}
function copyTextFallback(text){
  const input = document.createElement("textarea");
  input.value = text;
  input.setAttribute("readonly", "");
  input.style.position = "fixed";
  input.style.opacity = "0";
  document.body.appendChild(input);
  input.select();
  document.execCommand("copy");
  input.remove();
}
function clearNewProjectState(){
  Object.keys(state).forEach(key => { delete state[key]; });
  localStorage.removeItem(editorStateStorageKey);
  localStorage.removeItem(editorTabStorageKey);
  localStorage.removeItem("cutted-state");
  localStorage.removeItem("cutted-tab");
  localStorage.removeItem("cutted-caption-lines");
  localStorage.removeItem("cutted-caption-width");
  localStorage.removeItem("cutted-caption-size");
  localStorage.removeItem("cutted-caption-bottom");
  localStorage.removeItem("cutted-caption-mode");
  localStorage.removeItem("cutted-caption-text-color");
  localStorage.removeItem("cutted-caption-background-color");
  localStorage.removeItem("cutted-caption-highlight-background-color");
  localStorage.removeItem("cutted-caption-enabled");
}
function resetCardPanels(card){
  card.querySelectorAll("[data-panel]").forEach(panel => {
    if (panel instanceof HTMLDetailsElement) panel.open = panel.dataset.panel === "cut";
  });
}
function resetCardsForNewProject(){
  document.querySelectorAll(".card").forEach(card => {
    delete card.dataset.selectedOverlayLayer;
    card.dataset.previewFormat = "tiktok";
    setCardState(card.dataset.rank, { cameraMotionMs: defaultCameraMotionMs });
    applyCameraMotionSpeed(card);
    setCardPreviewFormat(card, "tiktok");
    resetCardPanels(card);
    paint(card);
    updateTrimUi(card);
    updatePlatformUi(card);
    updateCardTools(card);
    const menu = card.querySelector("[data-overlay-menu]");
    if (menu) {
      menu.hidden = true;
      menu.innerHTML = "";
    }
  });
}
let workspaceExitLastFocus = null;
function workspaceExitFocusableElements(modal){
  return Array.from(modal.querySelectorAll("button,input,select,textarea,a[href],[tabindex]:not([tabindex='-1'])"))
    .filter(element => !element.disabled && !element.hidden && element.offsetParent !== null);
}
function setupWorkspaceExitModal(){
  const modal = document.querySelector("[data-workspace-exit-modal]");
  if (!modal) return;
  modal.querySelectorAll("[data-workspace-exit-cancel]").forEach(button => {
    button.addEventListener("click", () => closeWorkspaceExitModal());
  });
  modal.querySelector("[data-workspace-exit-confirm]")?.addEventListener("click", () => confirmWorkspaceExit());
  modal.addEventListener("click", event => { if (event.target === modal) closeWorkspaceExitModal(); });
  document.addEventListener("keydown", event => {
    if (modal.hidden) return;
    if (event.key === "Escape") closeWorkspaceExitModal();
    if (event.key === "Tab") trapWorkspaceExitFocus(event);
  });
}
function openWorkspaceExitModal(){
  const modal = document.querySelector("[data-workspace-exit-modal]");
  if (!modal) return;
  workspaceExitLastFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
  modal.hidden = false;
  modal.classList.remove("is-closing");
  requestAnimationFrame(() => modal.classList.add("is-open"));
  modal.querySelector("[data-workspace-exit-panel]")?.focus();
}
function closeWorkspaceExitModal(){
  const modal = document.querySelector("[data-workspace-exit-modal]");
  if (!modal || modal.hidden) return;
  modal.classList.remove("is-open");
  modal.classList.add("is-closing");
  window.setTimeout(() => {
    modal.hidden = true;
    modal.classList.remove("is-closing");
    workspaceExitLastFocus?.focus?.();
    workspaceExitLastFocus = null;
  }, 190);
}
function trapWorkspaceExitFocus(event){
  const modal = document.querySelector("[data-workspace-exit-modal]");
  if (!modal || modal.hidden) return;
  const focusable = workspaceExitFocusableElements(modal);
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
async function confirmWorkspaceExit(){
  save();
  const button = document.querySelector("[data-workspace-exit-confirm]");
  if (button) {
    button.disabled = true;
    button.textContent = "Voltando...";
  }
  try {
    await touchCurrentProject();
  } catch (error) {
    console.warn("CUTED project was not added to recents", error);
  } finally {
    window.location.assign("/index.html");
  }
}
function startNewProject(){
  openWorkspaceExitModal();
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
syncProjectEmptyState();
applyTab("edit");
syncCaptionInputs();
document.querySelectorAll(".tabs [data-tab]").forEach(btn => {
  btn.addEventListener("click", () => { applyTab(btn.dataset.tab); renderCaptionQueue(); });
});
setupSettingsPanel();
setupRenderQueuePanel();
setupWorkspaceExitModal();
touchCurrentProject().catch(error => console.warn("CUTED project was not added to recents", error));
setupImportPathButtons();
setupImportKeyBanner();
document.querySelector("[data-empty-import]")?.addEventListener("click", () => applyTab("import"));
document.querySelector("[data-import-form]")?.addEventListener("submit", event => {
  event.preventDefault();
  startImportJob(event.currentTarget);
});
document.querySelectorAll(".card").forEach(card => {
  paint(card);
  updateTrimUi(card);
  updatePlatformUi(card);
  updateCardTools(card);
  applyCameraMotionSpeed(card);
  refreshAiReadinessForCard(card);
  const summary = card.querySelector(".clip-summary");
  if (summary) {
    const isSummaryTimelineTarget = target => target instanceof Element && !target.closest(".cuted-clip-info") && Boolean(target.closest("[data-cuted-control-surface], .cuted-control-bar, .cuted-menu, .cuted-volume-popover, [data-preview-camera-timeline], .timeline-shell, .timeline-canvas, .playhead-control, .trim-handle, .volume-popover, .preview-camera-popover"));
    const stopSummaryTimelinePointer = event => {
      if (!isSummaryTimelineTarget(event.target)) return;
      event.stopPropagation();
    };
    const toggleCard = event => {
      if (isSummaryTimelineTarget(event.target)) {
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      event.preventDefault();
      card.open = !card.open;
      activateCard(card);
    };
    summary.addEventListener("pointerdown", stopSummaryTimelinePointer);
    summary.addEventListener("mousedown", stopSummaryTimelinePointer);
    summary.addEventListener("touchstart", stopSummaryTimelinePointer, { passive: true });
    summary.addEventListener("click", toggleCard);
    summary.addEventListener("keydown", event => {
      if (event.key !== "Enter" && event.key !== " ") return;
      toggleCard(event);
    });
  }
  card.querySelectorAll("[data-card-format-preview]").forEach(button => {
    button.addEventListener("click", () => {
      card.dataset.previewTouched = "1";
      setPreviewPlayback(card, false);
      setCardPreviewFormat(card, button.dataset.cardFormatPreview);
      closePreviewFormatMenus();
      updateCardTools(card);
      renderFinalStage();
    });
  });
  const previewFormatTrigger = card.querySelector("[data-preview-format-trigger]");
  if (previewFormatTrigger) {
    previewFormatTrigger.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      togglePreviewFormatMenu(card);
    });
  }
  bindPreviewFormatDismiss();
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
      togglePreviewVolumePopover(card);
    });
  }
  const volumeSlider = card.querySelector("[data-preview-volume-slider]");
  if (volumeSlider) {
    volumeSlider.addEventListener("input", event => {
      event.stopPropagation();
      setPreviewVolume(card, Number(event.target.value || 0) / 100);
    });
  }
  const motionSlider = card.querySelector("[data-camera-motion-speed]");
  if (motionSlider) {
    motionSlider.addEventListener("input", event => {
      event.stopPropagation();
      setCameraMotionSpeed(card, event.target.value);
    });
  }
  const aiButton = card.querySelector("[data-camera-ai]");
  if (aiButton) {
    aiButton.addEventListener("click", event => {
      event.preventDefault();
      event.stopPropagation();
      analyzeCameraForCard(card, "ai-director");
    });
    refreshAiReadinessForCard(card);
  }
  bindPreviewVolumeDismiss();
  const video = primaryCameraVideo(card);
  if (video) {
    applyPreviewVolume(video);
    video.addEventListener("play", () => {
      const values = trimValues(card);
      const nextTime = trimPlaybackStart(values, video.currentTime);
      card.dataset.playbackMode = "range";
      delete card.dataset.timelineSeekIntent;
      if (Math.abs(video.currentTime - nextTime) > .05) video.currentTime = nextTime;
      startCameraFrameSync(video, () => syncPreviewPlaybackFrame(card));
      syncCameraFitBackground(card);
      syncPreviewPlaybackState(card);
    });
    video.addEventListener("pause", () => {
      stopCameraFrameSync(video, () => syncPreviewPlaybackFrame(card));
      syncCameraFitBackground(card);
      syncPreviewPlaybackState(card);
    });
    video.addEventListener("ended", () => {
      stopCameraFrameSync(video, () => syncPreviewPlaybackFrame(card));
      syncCameraFitBackground(card);
      syncPreviewPlaybackState(card);
    });
    video.addEventListener("volumechange", () => {
      syncPreviewVolumeButton(card);
    });
    ["loadedmetadata", "loadeddata", "canplay", "durationchange"].forEach(eventName => {
      video.addEventListener(eventName, () => {
        if (!applyPendingTimelineSeek(card, video)) updateTimelinePlayhead(card);
      });
    });
    video.addEventListener("timeupdate", () => {
      const values = trimValues(card);
      updateTimelinePlayhead(card);
      syncCameraFitBackground(card);
      if (trimRangeActive(values) && video.currentTime >= values.duration - values.trimEnd) {
        pauseAtTrimEnd(card, video, values);
      }
    });
  }
  syncPreviewPlaybackState(card);
  syncPreviewVolumeButton(card);
  bindPublishPanel(card);
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
    seekTrimHandle(card, input.dataset.trim);
    renderCaptionQueue();
  }));
  const scrubInput = card.querySelector("[data-trim-scrub]");
  if (scrubInput) {
    scrubInput.addEventListener("input", () => {
      setPreviewPlayback(card, false);
      const duration = Number(card.dataset.duration);
      const current = clampNumber(Number(scrubInput.value), 0, Math.max(duration, .1));
      seekTimeline(card, current, { userInitiated: true, mode: "free" });
    });
  }
  card.querySelectorAll("[data-platform]").forEach(btn => btn.addEventListener("click", () => {
    const current = cardState(card.dataset.rank);
    const platforms = Array.isArray(current.platforms) ? current.platforms.slice() : [];
    const target = representativePlatform(btn.dataset.platform);
    const normalized = uniquePlatforms(platforms);
    const existing = normalized.indexOf(target);
    if (existing >= 0) normalized.splice(existing, 1);
    else normalized.push(target);
    setCardState(card.dataset.rank, { platforms: normalized, status: current.status === "discarded" ? null : current.status });
    paint(card);
    updatePlatformUi(card);
    renderCaptionQueue();
  }));
  card.querySelectorAll("button[data-action]").forEach(btn => btn.addEventListener("click", () => {
    const patch = btn.dataset.action === "like" ? { status: "liked" } : { status: "discarded", platforms: [] };
    setCardState(card.dataset.rank, patch);
    paint(card);
    updatePlatformUi(card);
    renderCaptionQueue();
  }));
  if (card.open) activateCard(card);
});
document.getElementById("reset-ui").addEventListener("click", startNewProject);
document.getElementById("finalize-videos").addEventListener("click", () => {
  openRenderQueuePanel();
});
document.querySelector("[data-render-results]")?.addEventListener("click", event => {
  const target = event.target instanceof Element ? event.target : null;
  const folderButton = target?.closest("[data-open-folder]");
  if (folderButton) {
    openResultFolder(folderButton.dataset.openFolder || "", folderButton);
    return;
  }
  const copyButton = target?.closest("[data-copy-path]");
  if (!copyButton) return;
  copyResultPath(copyButton.dataset.copyPath || "", copyButton);
});
document.querySelectorAll("[data-caption-lines],[data-caption-width],[data-caption-size],[data-caption-bottom],[data-caption-text-color],[data-caption-background-color],[data-caption-highlight-background-color],[data-caption-enabled]").forEach(input => {
  const update = () => {
    if (input.matches("[data-caption-lines]")) localStorage.setItem("cutted-caption-lines", input.value);
    if (input.matches("[data-caption-width]")) localStorage.setItem("cutted-caption-width", input.value);
    if (input.matches("[data-caption-size]")) localStorage.setItem("cutted-caption-size", input.value);
    if (input.matches("[data-caption-bottom]")) localStorage.setItem("cutted-caption-bottom", input.value);
    if (input.matches("[data-caption-text-color]")) localStorage.setItem("cutted-caption-text-color", normalizeCaptionColor(input.value, "#ffffff"));
    if (input.matches("[data-caption-background-color]")) localStorage.setItem("cutted-caption-background-color", normalizeCaptionBackground(input.value));
    if (input.matches("[data-caption-highlight-background-color]")) localStorage.setItem("cutted-caption-highlight-background-color", normalizeCaptionHighlightBackground(input.value));
    if (input.matches("[data-caption-enabled]")) {
      localStorage.setItem("cutted-caption-enabled", input.checked ? "1" : "0");
      localStorage.setItem("cutted-caption-mode", input.checked ? "on" : "off");
    }
    syncCaptionInputs();
    syncPreviewCaptionsForOpenCards();
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
