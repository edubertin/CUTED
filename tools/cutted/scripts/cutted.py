from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import html
import http.cookies
import http.server
import json
import math
import os
import platform
import re
import secrets
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

import cuted_ui_assets
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
from cuted_caption_queue import (
    caption_rows_from_data as queue_caption_rows_from_data,
    platform_edit_from_row as queue_platform_edit_from_row,
    queue_rows_for_assets as queue_queue_rows_for_assets,
    resolution_edit_from_row as queue_resolution_edit_from_row,
    row_for_platform as queue_row_for_platform,
    selected_rows_to_caption_rows as queue_selected_rows_to_caption_rows,
)
from cuted_caption_text import (
    CAPTION_MOJIBAKE_REPLACEMENTS,
    caption_chunks as caption_text_caption_chunks,
    caption_duration as caption_text_caption_duration,
    caption_events as caption_text_caption_events,
    caption_events_from_segments as caption_text_caption_events_from_segments,
    caption_mojibake_score as caption_text_caption_mojibake_score,
    caption_source_text as caption_text_caption_source_text,
    clean_caption_text as caption_text_clean_caption_text,
    distributed_caption_events as caption_text_distributed_caption_events,
    ellipsize_caption as caption_text_ellipsize_caption,
    event_from_segment as caption_text_event_from_segment,
    greedy_word_chunks as caption_text_greedy_word_chunks,
    normalize_caption_events as caption_text_normalize_caption_events,
    normalize_caption_symbols as caption_text_normalize_caption_symbols,
    repair_caption_encoding as caption_text_repair_caption_encoding,
    repair_caption_encoding_as_utf8 as caption_text_repair_caption_encoding_as_utf8,
    replace_caption_mojibake_sequences as caption_text_replace_caption_mojibake_sequences,
    space_after_caption_punctuation as caption_text_space_after_caption_punctuation,
)
from cuted_animated_captions import (
    ANIMATED_CAPTION_ATTACH_NEXT,
    ANIMATED_CAPTION_ATTACH_PREVIOUS,
    ANIMATED_CAPTION_FILLER_WORDS,
    ANIMATED_CAPTION_PROPER_NOUN_STOPWORDS,
    animated_caption_canonical_window_times as animated_captions_canonical_window_times,
    animated_caption_clean_word as animated_captions_clean_word,
    animated_caption_display_word as animated_captions_display_word,
    animated_caption_is_acronym as animated_captions_is_acronym,
    animated_caption_is_capitalized_word as animated_captions_is_capitalized_word,
    animated_caption_is_low_value_word as animated_captions_is_low_value_word,
    animated_caption_is_numeric_token as animated_captions_is_numeric_token,
    animated_caption_proper_nouns as animated_captions_proper_nouns,
    animated_caption_render_window_times as animated_captions_render_window_times,
    animated_caption_window_events as animated_captions_window_events,
    animated_caption_windows_from_row as animated_captions_windows_from_row,
    animated_caption_word_events as animated_captions_word_events,
    animated_caption_word_key as animated_captions_word_key,
    animated_caption_word_timings as animated_captions_word_timings,
    animated_caption_word_weight as animated_captions_word_weight,
    clean_animated_caption_text as animated_captions_clean_text,
    merge_fast_animated_caption_timings as animated_captions_merge_fast_timings,
    smart_animated_caption_balance_groups as animated_captions_balance_groups,
    smart_animated_caption_drop_fillers as animated_captions_drop_fillers,
    smart_animated_caption_group_size as animated_captions_group_size,
    smart_animated_caption_group_words as animated_captions_group_words,
    smart_animated_caption_should_attach_next as animated_captions_should_attach_next,
    smart_animated_caption_should_attach_to_previous as animated_captions_should_attach_to_previous,
    smart_animated_caption_words as animated_captions_smart_words,
    split_animated_caption_words as animated_captions_split_words,
)
from cuted_ass_subtitles import (
    ass_alpha_from_opacity as ass_subtitles_ass_alpha_from_opacity,
    ass_animated_caption_box_lines as ass_subtitles_ass_animated_caption_box_lines,
    ass_animated_caption_center_y as ass_subtitles_ass_animated_caption_center_y,
    ass_animated_dialogue_line as ass_subtitles_ass_animated_dialogue_line,
    ass_animated_dialogue_lines as ass_subtitles_ass_animated_dialogue_lines,
    ass_caption_active_style_line as ass_subtitles_ass_caption_active_style_line,
    ass_caption_box_style_line as ass_subtitles_ass_caption_box_style_line,
    ass_caption_side_offset as ass_subtitles_ass_caption_side_offset,
    ass_caption_side_style_line as ass_subtitles_ass_caption_side_style_line,
    ass_caption_word_width as ass_subtitles_ass_caption_word_width,
    ass_color as ass_subtitles_ass_color,
    ass_dialogue_lines as ass_subtitles_ass_dialogue_lines,
    ass_document as ass_subtitles_ass_document,
    ass_document_with_style as ass_subtitles_ass_document_with_style,
    ass_escape_text as ass_subtitles_ass_escape_text,
    ass_rgb_color as ass_subtitles_ass_rgb_color,
    ass_rounded_rect_path as ass_subtitles_ass_rounded_rect_path,
    ass_rounded_rect_points as ass_subtitles_ass_rounded_rect_points,
    ass_style_line as ass_subtitles_ass_style_line,
    ass_time as ass_subtitles_ass_time,
    ass_vector_dialogue_line as ass_subtitles_ass_vector_dialogue_line,
    caption_margin_v as ass_subtitles_caption_margin_v,
    caption_style_from_row as ass_subtitles_caption_style_from_row,
    clamp_float as ass_subtitles_clamp_float,
    clamp_int as ass_subtitles_clamp_int,
    default_caption_bottom_percent as ass_subtitles_default_caption_bottom_percent,
    normalize_caption_background_color as ass_subtitles_normalize_caption_background_color,
    normalize_caption_mode as ass_subtitles_normalize_caption_mode,
    normalize_hex_color as ass_subtitles_normalize_hex_color,
    wrap_caption_text as ass_subtitles_wrap_caption_text,
)
from cuted_bumpers import (
    BUMPER_MAX_SOURCE_BYTES,
    BUMPER_SLOTS,
    BUMPER_VIDEO_MIME_EXTENSIONS,
    clean_bumper_label as bumpers_clean_bumper_label,
    decode_data_url_video as bumpers_decode_data_url_video,
    normalize_bumper_slot as bumpers_normalize_bumper_slot,
    normalize_bumpers_from_row as bumpers_normalize_bumpers_from_row,
)
from cuted_caption_render import (
    caption_trim_start as caption_render_caption_trim_start,
    captioned_ffmpeg_command as caption_render_captioned_ffmpeg_command,
    captioned_row as caption_render_captioned_row,
    render_captioned_clip as caption_render_render_captioned_clip,
    subtitle_filter_path as caption_render_subtitle_filter_path,
)
from cuted_render_pipeline import (
    apply_bumpers_to_output as render_pipeline_apply_bumpers_to_output,
    bumper_duration as render_pipeline_bumper_duration,
    clamp as render_pipeline_clamp,
    concat_file_entry as render_pipeline_concat_file_entry,
    default_overlay as render_pipeline_default_overlay,
    effect_filter as render_pipeline_effect_filter,
    effect_from_row as render_pipeline_effect_from_row,
    ffmpeg_color as render_pipeline_ffmpeg_color,
    ffmpeg_filter_path as render_pipeline_ffmpeg_filter_path,
    ffmpeg_media_duration as render_pipeline_ffmpeg_media_duration,
    ffmpeg_text_value as render_pipeline_ffmpeg_text_value,
    find_overlay_font as render_pipeline_find_overlay_font,
    image_overlay_filter as render_pipeline_image_overlay_filter,
    image_overlay_from_raw as render_pipeline_image_overlay_from_raw,
    media_has_audio as render_pipeline_media_has_audio,
    normalize_bumper_segment as render_pipeline_normalize_bumper_segment,
    overlay_filter as render_pipeline_overlay_filter,
    overlay_from_raw as render_pipeline_overlay_from_raw,
    overlay_from_row as render_pipeline_overlay_from_row,
    overlay_layer_filter as render_pipeline_overlay_layer_filter,
    overlay_layer_from_raw as render_pipeline_overlay_layer_from_raw,
    overlay_layers_from_row as render_pipeline_overlay_layers_from_row,
    render_cover_frame_segment as render_pipeline_render_cover_frame_segment,
    render_cover_frame_tail_video as render_pipeline_render_cover_frame_tail_video,
    resolve_bumper_asset_path as render_pipeline_resolve_bumper_asset_path,
    safe_hex_color as render_pipeline_safe_hex_color,
    scaled_float as render_pipeline_scaled_float,
    scaled_value as render_pipeline_scaled_value,
    speech_overlay_filter as render_pipeline_speech_overlay_filter,
    speech_overlay_from_raw as render_pipeline_speech_overlay_from_raw,
    text_overlay_filter as render_pipeline_text_overlay_filter,
    text_overlay_from_raw as render_pipeline_text_overlay_from_raw,
    timed_overlay_enable as render_pipeline_timed_overlay_enable,
    video_crf as render_pipeline_video_crf,
    video_rate_control_args as render_pipeline_video_rate_control_args,
    visible_effect_intensity as render_pipeline_visible_effect_intensity,
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
from cuted_desktop_shell import (
    desktop_shell_status as desktop_shell_desktop_shell_status,
    open_desktop_shell as desktop_shell_open_desktop_shell,
)
from cuted_media_source import (
    bundled_node_path as media_bundled_node_path,
    caption_event_to_segment as media_caption_event_to_segment,
    cleanup_youtube_partial_sources as media_cleanup_youtube_partial_sources,
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
from cuted_render_results import (
    caption_queue_rows_by_output as results_caption_queue_rows_by_output,
    finalized_results_from_gallery as results_finalized_results_from_gallery,
    recovered_captioned_files as results_recovered_captioned_files,
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
YOUTUBE_HIGH_QUALITY_FORMAT = (
    "bv*[height<=1440][vcodec^=avc1]+ba[ext=m4a]/"
    "bv*[height<=1440]+ba/"
    "b[height<=1440]/"
    "bv*[height<=1080][vcodec^=avc1]+ba[ext=m4a]/"
    "b[height<=1080]/best"
)
YOUTUBE_MIN_FALLBACK_HEIGHT = 720
YOUTUBE_STREAM_FALLBACK_FORMAT = "b[height>=720][height<=1080]/b[height>=720]/best[height>=720]"
IMPORT_PROGRESS_PREFIX = "CUTED_IMPORT_EVENT "
PREVIEW_VIDEO_CRF = "20"
PREVIEW_DRAFT_VIDEO_CRF = "28"
LOCAL_IMPORT_MAX_INITIAL_CLIPS = 4
FINAL_VIDEO_CRF = "20"
FINAL_EFFECT_VIDEO_CRF = "19"
FINAL_GRAIN_EFFECT_VIDEO_CRF = "24"
FINAL_GRAIN_EFFECT_MAXRATE = "12M"
FINAL_GRAIN_EFFECT_BUFSIZE = "24M"
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
CAPTION_TRACK_LOCKS: dict[str, threading.Lock] = {}
CAPTION_TRACK_LOCKS_LOCK = threading.Lock()
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
    launch.add_argument("--desktop-shell", action="store_true")
    launch.add_argument("--no-browser", action="store_true")
    desktop_shell_check = subparsers.add_parser("desktop-shell-check", help="Check desktop shell packaging readiness.")
    desktop_shell_check.add_argument("--json", action="store_true")
    diagnostics = subparsers.add_parser("diagnostics", help="Write a safe local support diagnostics report.")
    diagnostics.add_argument("--json", action="store_true")
    diagnostics.add_argument("--out", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    if args.command != "diagnostics":
        load_local_env()
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
    if args.command == "desktop-shell-check":
        check_desktop_shell(args)
        return 0
    if args.command == "diagnostics":
        write_diagnostics(args)
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
    print(import_progress_line(payload), flush=True)


def import_progress_line(payload: dict[str, object]) -> str:
    return f"{IMPORT_PROGRESS_PREFIX}{json.dumps(payload, ensure_ascii=True, separators=(',', ':'))}"


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                continue


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
    require_local_bind_host(args.host)
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
    require_local_bind_host(args.host)
    workspace = prepare_workspace_dir(args.workspace)
    existing = running_workspace_port(args.host)
    if existing is not None:
        print(f"[cutted] CUTED ja esta aberto em http://{args.host}:{existing}/index.html (workspace da instancia atual mantido)")
        open_existing_workspace(args.host, existing, args.desktop_shell, args.no_browser)
        return
    bootstrap_workspace_gallery(workspace)
    for _ in range(3):
        port = find_free_port(args.host)
        try:
            start_workspace_server(workspace, args.host, port, args.no_browser, args.desktop_shell)
            return
        except OSError as error:
            append_launch_log(f"bind failed on port {port}: {error}")
    print("[cutted] Nao consegui abrir o servidor local. Feche outras janelas do CUTED e tente novamente.")
    raise SystemExit(1)


def check_desktop_shell(args: argparse.Namespace) -> None:
    status = desktop_shell_status()
    if args.json:
        print(json.dumps(status, ensure_ascii=False, indent=2))
    elif status["ok"]:
        print(f"[cutted] Desktop shell OK: {status['backend']} / {status['renderer']}")
    else:
        print(f"[cutted] Desktop shell unavailable: {status.get('reason', 'unknown error')}")
    if not status["ok"]:
        raise SystemExit(1)


def write_diagnostics(args: argparse.Namespace) -> None:
    payload = diagnostics_payload()
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.json or args.out is None:
        print(text)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        if not args.json:
            print(f"[cutted] Diagnostics written to {args.out}")


def open_existing_workspace(host: str, port: int, desktop_shell: bool, no_browser: bool) -> None:
    if desktop_shell and open_desktop_shell(host, port):
        return
    if not no_browser:
        open_browser_later(host, port, 0.0)


def start_workspace_server(workspace: Path, host: str, port: int, no_browser: bool, desktop_shell: bool) -> None:
    handler = gallery_handler(workspace)
    server = http.server.ThreadingHTTPServer((host, port), handler)
    lock_path = launch_lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(str(port), encoding="utf-8")
    append_launch_log(f"launch workspace={workspace} port={port}")
    print(f"[cutted] Serving {workspace}")
    print(f"[cutted] Open: http://{host}:{port}/index.html")
    if desktop_shell:
        serve_workspace_desktop_shell(server, host, port, no_browser)
        return
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


def serve_workspace_desktop_shell(
    server: http.server.ThreadingHTTPServer,
    host: str,
    port: int,
    no_browser: bool,
) -> None:
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        if open_desktop_shell(host, port):
            return
        if no_browser:
            print("[cutted] Desktop shell indisponivel; execute sem --no-browser para usar o navegador como fallback.")
            return
        if not no_browser:
            open_browser_later(host, port, 0.0)
        server_thread.join()
    except KeyboardInterrupt:
        print("\n[cutted] Server stopped")
    finally:
        server.shutdown()
        server.server_close()
        cleanup_launch_lock()


def cleanup_launch_lock() -> None:
    try:
        launch_lock_path().unlink()
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


def open_desktop_shell(host: str, port: int) -> bool:
    return desktop_shell_open_desktop_shell(host, port, launch_data_dir(), append_launch_log)


def desktop_shell_status() -> dict[str, str | bool]:
    return desktop_shell_desktop_shell_status(launch_data_dir())


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
    removed = data.get("removed_project_ids")
    removed_ids = [clean_project_id(item) for item in removed] if isinstance(removed, list) else []
    return {
        "version": PROJECT_CATALOG_VERSION,
        "projects": [item for item in projects if isinstance(item, dict)],
        "removed_project_ids": [item for item in removed_ids if item],
    }


def write_project_catalog(catalog: dict[str, object], path: Path | None = None) -> None:
    catalog_path = path or project_catalog_path()
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    rows = catalog.get("projects") if isinstance(catalog, dict) else []
    projects = rows if isinstance(rows, list) else []
    removed = catalog.get("removed_project_ids") if isinstance(catalog, dict) else []
    removed_ids = [clean_project_id(item) for item in removed] if isinstance(removed, list) else []
    payload = {
        "version": PROJECT_CATALOG_VERSION,
        "projects": projects[:200],
        "removed_project_ids": [item for item in removed_ids if item][:500],
    }
    temp_path = catalog_path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(catalog_path)


def project_catalog_recent(workspace: Path, limit: int = PROJECT_CATALOG_LIMIT) -> list[dict[str, object]]:
    catalog = read_project_catalog()
    projects = catalog.get("projects")
    source_rows = projects if isinstance(projects, list) else []
    if not source_rows and not project_catalog_removed_ids(catalog):
        source_rows = discover_workspace_project_catalog(workspace)
        if source_rows:
            catalog["projects"] = source_rows
            write_project_catalog(catalog)
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


def project_catalog_removed_ids(catalog: dict[str, object]) -> set[str]:
    removed = catalog.get("removed_project_ids") if isinstance(catalog, dict) else []
    values = removed if isinstance(removed, list) else []
    return {clean_project_id(item) for item in values if clean_project_id(item)}


def discover_workspace_project_catalog(workspace: Path) -> list[dict[str, object]]:
    projects_root = workspace / PROJECTS_DIR_NAME
    if not projects_root.is_dir():
        return []
    try:
        candidates = [path for path in projects_root.iterdir() if path.is_dir()]
    except OSError:
        return []
    rows = []
    for project_dir in sorted(candidates, key=project_dir_mtime, reverse=True):
        if not valid_recent_project_dir(project_dir, workspace):
            continue
        entry = project_entry_from_gallery(project_dir, workspace)
        timestamp = iso_timestamp_from_epoch(project_dir_mtime(project_dir))
        rows.append({**entry, "updated_at": timestamp, "last_opened_at": timestamp})
    return rows


def project_dir_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


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
    removed_ids = project_catalog_removed_ids(catalog)
    if project_id in removed_ids:
        catalog["removed_project_ids"] = sorted(removed_ids - {project_id})
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
    if not delete_files:
        catalog["removed_project_ids"] = sorted(project_catalog_removed_ids(catalog) | {clean_project_id(project_id)})
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


def iso_timestamp_from_epoch(value: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(max(0.0, value)))


LOCAL_SESSION_COOKIE = "cuted_session"
LOCAL_REQUEST_HOSTS = {"127.0.0.1", "localhost", "::1"}
LOCAL_SCRIPT_PATH = "tools/cutted/scripts/cutted.py"


def local_request_host_allowed(value: str, port: int) -> bool:
    try:
        parsed = urllib.parse.urlsplit(f"//{value}")
        hostname = (parsed.hostname or "").lower()
        return hostname in LOCAL_REQUEST_HOSTS and parsed.port in {None, port}
    except ValueError:
        return False


def local_request_origin_allowed(origin: str, port: int) -> bool:
    if not origin:
        return False
    try:
        parsed = urllib.parse.urlsplit(origin)
        return parsed.scheme == "http" and parsed.hostname in LOCAL_REQUEST_HOSTS and parsed.port == port
    except ValueError:
        return False


def local_session_cookie_matches(cookie_header: str, expected: str) -> bool:
    try:
        cookies = http.cookies.SimpleCookie()
        cookies.load(cookie_header)
        supplied = cookies.get(LOCAL_SESSION_COOKIE)
        return supplied is not None and hmac.compare_digest(supplied.value, expected)
    except (http.cookies.CookieError, TypeError):
        return False


def local_session_bootstrap_path(path: str) -> bool:
    return path == "/" or path.endswith("/index.html")


def require_local_bind_host(host: str) -> None:
    if host.lower().strip("[]") not in LOCAL_REQUEST_HOSTS:
        raise ValueError("CUTED only accepts 127.0.0.1, localhost, or ::1 as the local server host.")


def gallery_handler(
    base_dir: Path,
    session_token: str | None = None,
) -> type[http.server.SimpleHTTPRequestHandler]:
    token = session_token or secrets.token_urlsafe(32)

    class CuttedGalleryHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: object, **kwargs: object) -> None:
            self.issue_local_session = False
            super().__init__(*args, directory=str(base_dir), **kwargs)

        def end_headers(self) -> None:
            if self.issue_local_session:
                self.send_header(
                    "Set-Cookie",
                    f"{LOCAL_SESSION_COOKIE}={token}; HttpOnly; SameSite=Strict; Path=/",
                )
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cross-Origin-Resource-Policy", "same-origin")
            self.send_header("Content-Security-Policy", "frame-ancestors 'none'; base-uri 'none'")
            super().end_headers()

        def local_host_allowed(self) -> bool:
            port = int(self.server.server_address[1])
            return local_request_host_allowed(self.headers.get("Host", ""), port)

        def local_session_allowed(self) -> bool:
            port = int(self.server.server_address[1])
            return (
                self.local_host_allowed()
                and local_request_origin_allowed(self.headers.get("Origin", ""), port)
                and local_session_cookie_matches(self.headers.get("Cookie", ""), token)
            )

        def reject_local_request(self) -> None:
            self.issue_local_session = False
            send_json_response(self, 403, {"ok": False, "error": "Sessao local invalida. Reabra o CUTED."})

        def do_POST(self) -> None:
            self.issue_local_session = False
            if not self.local_session_allowed():
                self.reject_local_request()
                return
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
            if path == "/api/caption-tracks/translate":
                self.handle_caption_track_translate(base_dir)
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
            self.issue_local_session = False
            path = urllib.parse.urlparse(self.path).path
            if not self.local_host_allowed():
                self.reject_local_request()
                return
            if path == "/api/health":
                send_json_response(self, 200, {"ok": True})
                return
            if local_session_bootstrap_path(path):
                self.issue_local_session = True
            elif not local_session_cookie_matches(self.headers.get("Cookie", ""), token):
                self.reject_local_request()
                return
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

        def do_HEAD(self) -> None:
            self.issue_local_session = False
            if not self.local_session_allowed():
                self.reject_local_request()
                return
            super().do_HEAD()

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

        def handle_caption_track_translate(self, request_base_dir: Path) -> None:
            if self.reject_stale_render_server():
                return
            try:
                result = caption_track_translation_from_request(self, request_base_dir)
                send_json_response(self, 200 if result.get("ok") else 400, result)
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
    return results_finalized_results_from_gallery(gallery_dir, finalized_file_urls, caption_rows_from_data)


def recovered_captioned_files(gallery_dir: Path) -> list[dict[str, object]]:
    return results_recovered_captioned_files(gallery_dir, caption_rows_from_data)


def caption_queue_rows_by_output(gallery_dir: Path) -> dict[tuple[int, str], dict[str, object]]:
    return results_caption_queue_rows_by_output(gallery_dir, caption_rows_from_data)


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
    return bumpers_normalize_bumper_slot(value)


def clean_bumper_label(value: object) -> str:
    return bumpers_clean_bumper_label(value)


def decode_data_url_video(value: str) -> tuple[bytes, str]:
    return bumpers_decode_data_url_video(value)


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
        "language": import_request_language(payload.get("language")),
        "preset": clean_preset(payload.get("preset")),
        "duration_profile": clean_duration_profile(payload.get("duration_profile")),
        "context_prompt": clean_optional_text(payload.get("context_prompt"), 5000),
        "render_previews": bool(payload.get("render_previews", True)),
        "ai_provider": ai_provider,
        "mode": "openai_import" if ai_provider == "openai" else "local_fallback",
    }


def import_request_language(value: object) -> str:
    raw = clean_optional_text(value, 24).lower()
    if raw in {"pt", "pt-br", "pt_br", "portuguese", "portugues", "portugues-br"}:
        return "pt"
    return "pt"


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
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=import_process_env(),
    )
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


def import_process_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env.setdefault("PYTHONUTF8", "1")
    return env


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
    candidates: list[Path] = []
    user_secret = cuted_secret_env_path()
    candidates.append(user_secret)
    legacy_secret = legacy_repo_secret_env_path()
    if legacy_secret not in candidates:
        candidates.append(legacy_secret)
    roots = [Path.cwd(), *script_dir.parents]
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
    return cuted_data_dir() / ".env.cuted.local"


def legacy_repo_secret_env_path() -> Path:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"OPENAI_API_KEY={key}\n", encoding="utf-8")


def openai_settings_payload() -> dict[str, object]:
    key = openai_api_key()
    return {
        "ai_provider": configured_ai_provider(),
        "openai_model": openai_model(),
        "transcribe_model": openai_transcribe_model(),
        "key_configured": bool(key),
        "secret_storage": "user-data-env-file",
        "legacy_secret_configured": legacy_repo_secret_env_path().exists(),
        "settings_storage": "user-data-json",
        "pricing": pricing_payload(),
    }


def app_version() -> str:
    candidates = [
        Path(getattr(sys, "_MEIPASS", "")) / "VERSION" if getattr(sys, "_MEIPASS", "") else None,
        Path(sys.executable).resolve().parent / "VERSION",
        project_root() / "VERSION",
    ]
    for candidate in candidates:
        if candidate is not None and candidate.exists():
            try:
                return candidate.read_text(encoding="utf-8").strip() or "unknown"
            except OSError:
                return "unknown"
    return "dev"


def diagnostics_payload() -> dict[str, object]:
    shell_status = dict(desktop_shell_status())
    shell_status.pop("storage_path", None)
    return {
        "app": {
            "name": "CUTED",
            "version": app_version(),
            "packaged": bool(getattr(sys, "frozen", False)),
        },
        "runtime": {
            "python": platform.python_version(),
            "windows": platform.platform(),
            "executable": Path(sys.executable).name,
        },
        "paths": {
            "cuted_home_override": bool(os.environ.get("CUTED_HOME", "").strip()),
            "data_dir_exists": cuted_data_dir().exists(),
            "settings_exists": cuted_settings_path().exists(),
            "usage_ledger_exists": cuted_usage_path().exists(),
            "secret_storage": "user-data-env-file",
            "secret_file_exists": cuted_secret_env_path().exists(),
            "legacy_repo_secret_exists": legacy_repo_secret_env_path().exists(),
            "default_workspace_exists": default_workspace_dir().exists(),
        },
        "openai": {
            "provider": configured_ai_provider(),
            "key_configured": openai_key_configured_without_reading_secret(),
            "model": openai_model(),
            "transcribe_model": openai_transcribe_model(),
        },
        "tools": {
            "ffmpeg": tool_available(find_ffmpeg),
            "ffprobe": tool_available(find_ffprobe),
            "desktop_shell": shell_status,
        },
        "privacy": {
            "contains_api_key": False,
            "contains_source_media": False,
            "contains_transcripts": False,
            "contains_raw_provider_payloads": False,
        },
    }


def tool_available(resolver: object) -> bool:
    try:
        return bool(resolver())
    except (RuntimeError, OSError, subprocess.SubprocessError):
        return False


def openai_key_configured_without_reading_secret() -> bool:
    return bool(openai_api_key()) or cuted_secret_env_path().exists() or legacy_repo_secret_env_path().exists()


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
    handler.send_header("Cache-Control", "no-store")
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
    return queue_caption_rows_from_data(data, selected_rows_to_caption_rows)


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
    return queue_queue_rows_for_assets(data, selected_rows_to_caption_rows)


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
    return queue_selected_rows_to_caption_rows(rows, normalize_platforms, row_for_platform)


def row_for_platform(row: dict[str, object], platform: str) -> dict[str, object]:
    return queue_row_for_platform(row, platform, platform_edit_from_row)


def platform_edit_from_row(row: dict[str, object], platform: str) -> dict[str, object]:
    return queue_platform_edit_from_row(row, platform, resolution_key_for_platform)


def resolution_edit_from_row(row: dict[str, object], platform: str) -> dict[str, object]:
    return queue_resolution_edit_from_row(row, platform, resolution_key_for_platform)


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
        row = row_with_selected_caption_track(row)
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


def row_with_selected_caption_track(row: dict[str, object]) -> dict[str, object]:
    language = normalize_caption_language(row.get("caption_language") or row.get("captionLanguage"))
    segments = caption_segments_for_row_language(row, language)
    if language != CAPTION_LANGUAGE_DEFAULT and not segments:
        language = CAPTION_LANGUAGE_DEFAULT
        segments = caption_segments_for_row_language(row, language)
    result = {**row, "caption_language": language}
    if segments:
        result["caption_segments"] = segments
    return result


def caption_segments_for_row_language(row: dict[str, object], language: str) -> list[dict[str, object]]:
    tracks = row.get("caption_tracks")
    if isinstance(tracks, dict):
        raw_track = tracks.get(language)
        if raw_track is None and language == CAPTION_LANGUAGE_DEFAULT:
            raw_track = tracks.get("pt")
        if isinstance(raw_track, dict):
            status = str(raw_track.get("status") or "").strip().lower()
            segments = raw_track.get("segments")
            if status == "ready" and isinstance(segments, list):
                return [segment for segment in segments if isinstance(segment, dict)]
    fallback = row.get("caption_segments")
    return [segment for segment in fallback if isinstance(segment, dict)] if isinstance(fallback, list) else []


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
    return caption_text_caption_duration(row)


def caption_source_text(row: dict[str, object]) -> str:
    return caption_text_caption_source_text(row)


def caption_events(row: dict[str, object], chars_per_line: int, max_lines: int, duration: float) -> list[CaptionEvent]:
    return caption_text_caption_events(row, chars_per_line, max_lines, duration)


def caption_events_from_segments(row: dict[str, object], chars_per_line: int, max_lines: int) -> list[CaptionEvent]:
    return caption_text_caption_events_from_segments(row, chars_per_line, max_lines)


def event_from_segment(
    item: object, clip_start: float, clip_end: float, chars_per_line: int, max_lines: int
) -> CaptionEvent | None:
    return caption_text_event_from_segment(item, clip_start, clip_end, chars_per_line, max_lines)


def normalize_caption_events(events: list[CaptionEvent], duration: float) -> list[CaptionEvent]:
    return caption_text_normalize_caption_events(events, duration)


def distributed_caption_events(chunks: list[str], duration: float) -> list[CaptionEvent]:
    return caption_text_distributed_caption_events(chunks, duration)


def clean_caption_text(text: str) -> str:
    return caption_text_clean_caption_text(text)


def space_after_caption_punctuation(match: re.Match[str]) -> str:
    return caption_text_space_after_caption_punctuation(match)


def clean_animated_caption_text(text: str) -> str:
    return animated_captions_clean_text(text)


def animated_caption_proper_nouns(text: str) -> set[str]:
    return animated_captions_proper_nouns(text)


def animated_caption_display_word(word: str, proper_nouns: set[str]) -> str:
    return animated_captions_display_word(word, proper_nouns)


def animated_caption_clean_word(word: str) -> str:
    return animated_captions_clean_word(word)


def animated_caption_word_key(word: str) -> str:
    return animated_captions_word_key(word)


def animated_caption_is_capitalized_word(word: str) -> bool:
    return animated_captions_is_capitalized_word(word)


def animated_caption_is_acronym(word: str) -> bool:
    return animated_captions_is_acronym(word)


def animated_caption_is_numeric_token(word: str) -> bool:
    return animated_captions_is_numeric_token(word)


def animated_caption_is_low_value_word(word: str) -> bool:
    return animated_captions_is_low_value_word(word)


def smart_animated_caption_words(text: str, max_word_length: int, duration: float) -> list[str]:
    return animated_captions_smart_words(text, max_word_length, duration)


def smart_animated_caption_drop_fillers(words: list[str], duration: float) -> list[str]:
    return animated_captions_drop_fillers(words, duration)


def smart_animated_caption_group_words(words: list[str], duration: float) -> list[str]:
    return animated_captions_group_words(words, duration)


def smart_animated_caption_should_attach_to_previous(groups: list[str], word: str) -> bool:
    return animated_captions_should_attach_to_previous(groups, word)


def smart_animated_caption_should_attach_next(groups: list[str], words: list[str]) -> bool:
    return animated_captions_should_attach_next(groups, words)


def smart_animated_caption_balance_groups(groups: list[str]) -> list[str]:
    return animated_captions_balance_groups(groups)


def smart_animated_caption_group_size(group: str) -> int:
    return animated_captions_group_size(group)


def repair_caption_encoding(text: str) -> str:
    return caption_text_repair_caption_encoding(text)


def repair_caption_encoding_as_utf8(text: str) -> str:
    return caption_text_repair_caption_encoding_as_utf8(text)


def replace_caption_mojibake_sequences(text: str) -> str:
    return caption_text_replace_caption_mojibake_sequences(text)


def caption_mojibake_score(text: str) -> int:
    return caption_text_caption_mojibake_score(text)


def normalize_caption_symbols(text: str) -> str:
    return caption_text_normalize_caption_symbols(text)


def caption_chunks(text: str, chars_per_line: int, max_lines: int, duration: float) -> list[str]:
    return caption_text_caption_chunks(text, chars_per_line, max_lines, duration)


def greedy_word_chunks(words: list[str], capacity: int) -> list[str]:
    return caption_text_greedy_word_chunks(words, capacity)


def ellipsize_caption(text: str) -> str:
    return caption_text_ellipsize_caption(text)


def ass_document(events: list[CaptionEvent], duration: float, preset: PlatformPreset, chars_per_line: int, max_lines: int) -> str:
    return ass_subtitles_ass_document(events, duration, preset, chars_per_line, max_lines)


def ass_document_with_style(
    events: list[CaptionEvent], duration: float, preset: PlatformPreset, chars_per_line: int, max_lines: int,
    row: dict[str, object]
) -> str:
    return ass_subtitles_ass_document_with_style(events, duration, preset, chars_per_line, max_lines, row)


def ass_style_line(preset: PlatformPreset, style: dict[str, object] | None = None) -> str:
    return ass_subtitles_ass_style_line(preset, style)


def ass_caption_active_style_line(preset: PlatformPreset, style: dict[str, object]) -> str:
    return ass_subtitles_ass_caption_active_style_line(preset, style)


def ass_caption_side_style_line(preset: PlatformPreset, style: dict[str, object]) -> str:
    return ass_subtitles_ass_caption_side_style_line(preset, style)


def ass_caption_box_style_line(preset: PlatformPreset) -> str:
    return ass_subtitles_ass_caption_box_style_line(preset)


def caption_margin_v(preset: PlatformPreset, style: dict[str, object] | None = None) -> int:
    return ass_subtitles_caption_margin_v(preset, style)


def caption_style_from_row(row: dict[str, object], preset: PlatformPreset) -> dict[str, object]:
    return ass_subtitles_caption_style_from_row(row, preset)


def default_caption_bottom_percent(preset: PlatformPreset) -> float:
    return ass_subtitles_default_caption_bottom_percent(preset)


def normalize_caption_mode(value: object) -> str:
    return ass_subtitles_normalize_caption_mode(value)


def clamp_float(value: object, minimum: float, maximum: float, fallback: float) -> float:
    return ass_subtitles_clamp_float(value, minimum, maximum, fallback)


def clamp_int(value: object, minimum: int, maximum: int, fallback: int) -> int:
    return ass_subtitles_clamp_int(value, minimum, maximum, fallback)


def normalize_hex_color(value: object, fallback: str) -> str:
    return ass_subtitles_normalize_hex_color(value, fallback)


def normalize_caption_background_color(value: object) -> str:
    return ass_subtitles_normalize_caption_background_color(value)


def ass_color(value: str, alpha: str) -> str:
    return ass_subtitles_ass_color(value, alpha)


def ass_alpha_from_opacity(opacity: float) -> str:
    return ass_subtitles_ass_alpha_from_opacity(opacity)


def ass_rgb_color(value: str) -> str:
    return ass_subtitles_ass_rgb_color(value)


def ass_dialogue_lines(events: list[CaptionEvent], duration: float, chars_per_line: int, max_lines: int) -> list[str]:
    return ass_subtitles_ass_dialogue_lines(events, duration, chars_per_line, max_lines)


def ass_animated_dialogue_lines(
    events: list[CaptionEvent], duration: float, chars_per_line: int, preset: PlatformPreset, style: dict[str, object],
    row: dict[str, object] | None = None,
) -> list[str]:
    return ass_subtitles_ass_animated_dialogue_lines(events, duration, chars_per_line, preset, style, row)


def animated_caption_windows_from_row(row: dict[str, object], duration: float) -> list[AnimatedCaptionWindow]:
    return animated_captions_windows_from_row(row, duration)


def animated_caption_canonical_window_times(
    window: AnimatedCaptionWindow, duration: float, previous_end: float = 0.0
) -> tuple[float, float]:
    return animated_captions_canonical_window_times(window, duration, previous_end)


def animated_caption_render_window_times(
    window: AnimatedCaptionWindow, duration: float, previous_end: float = 0.0
) -> tuple[float, float]:
    return animated_captions_render_window_times(window, duration, previous_end)


def ass_animated_caption_box_lines(
    start: float, end: float, text: str, center_x: int, center_y: int, font_size: int,
    style: dict[str, object],
) -> list[str]:
    return ass_subtitles_ass_animated_caption_box_lines(start, end, text, center_x, center_y, font_size, style)


def ass_vector_dialogue_line(
    layer: int, start: float, end: float, x: int, y: int, shape: str, color: str, alpha: str, tags: str, border: str
) -> str:
    return ass_subtitles_ass_vector_dialogue_line(layer, start, end, x, y, shape, color, alpha, tags, border)


def ass_rounded_rect_path(width: int, height: int, radius: int) -> str:
    return ass_subtitles_ass_rounded_rect_path(width, height, radius)


def ass_rounded_rect_points(width: int, height: int, radius: int) -> list[tuple[int, int]]:
    return ass_subtitles_ass_rounded_rect_points(width, height, radius)


def ass_animated_dialogue_line(
    layer: int, start: float, end: float, style_name: str, text: str, x: int, y: int, tags: str
) -> str:
    return ass_subtitles_ass_animated_dialogue_line(layer, start, end, style_name, text, x, y, tags)


def ass_animated_caption_center_y(preset: PlatformPreset, style: dict[str, object], font_size: int) -> int:
    return ass_subtitles_ass_animated_caption_center_y(preset, style, font_size)


def ass_caption_side_offset(side: str, active: str, active_size: int, side_size: int) -> int:
    return ass_subtitles_ass_caption_side_offset(side, active, active_size, side_size)


def ass_caption_word_width(text: str, font_size: int) -> float:
    return ass_subtitles_ass_caption_word_width(text, font_size)


def animated_caption_word_events(events: list[CaptionEvent], duration: float, chars_per_line: int) -> list[CaptionEvent]:
    return animated_captions_word_events(events, duration, chars_per_line)


def animated_caption_word_timings(words: list[str], start: float, end: float) -> list[tuple[int, str, float, float]]:
    return animated_captions_word_timings(words, start, end)


def merge_fast_animated_caption_timings(
    timings: list[tuple[int, str, float, float]]
) -> list[tuple[int, str, float, float]]:
    return animated_captions_merge_fast_timings(timings)


def animated_caption_word_weight(word: str) -> float:
    return animated_captions_word_weight(word)


def animated_caption_window_events(events: list[CaptionEvent], duration: float, chars_per_line: int) -> list[AnimatedCaptionWindow]:
    return animated_captions_window_events(events, duration, chars_per_line)


def split_animated_caption_words(text: str, max_word_length: int) -> list[str]:
    return animated_captions_split_words(text, max_word_length)


def wrap_caption_text(text: str, chars_per_line: int, max_lines: int) -> str:
    return ass_subtitles_wrap_caption_text(text, chars_per_line, max_lines)


def ass_escape_text(text: str) -> str:
    return ass_subtitles_ass_escape_text(text)


def ass_time(value: float) -> str:
    return ass_subtitles_ass_time(value)


def render_captioned_clip(
    input_path: Path, output_path: Path, subtitle_path: Path | None, row: dict[str, object],
    preset: PlatformPreset, base_dir: Path, out_dir: Path, ffmpeg: str
) -> dict[str, object]:
    return caption_render_render_captioned_clip(
        input_path,
        output_path,
        subtitle_path,
        row,
        preset,
        base_dir,
        out_dir,
        ffmpeg,
        caption_duration,
        effect_filter,
        overlay_filter,
        render_command,
        run_ffmpeg_command,
        apply_bumpers_to_output,
        fmt_time,
    )


def captioned_ffmpeg_command(
    input_path: Path, output_path: Path, row: dict[str, object], preset: PlatformPreset,
    ffmpeg: str, filters: list[str]
) -> list[str]:
    return caption_render_captioned_ffmpeg_command(
        input_path, output_path, row, preset, ffmpeg, filters, caption_duration, render_command, fmt_time
    )


def caption_trim_start(row: dict[str, object]) -> float:
    return caption_render_caption_trim_start(row)


def subtitle_filter_path(subtitle_path: Path, out_dir: Path) -> str:
    return caption_render_subtitle_filter_path(subtitle_path, out_dir)


def captioned_row(
    row: dict[str, object], preset: PlatformPreset, output_path: Path, subtitle_path: Path | None,
    cover_path: Path | None = None, cover_frame_path: Path | None = None,
) -> dict[str, object]:
    base_duration = caption_duration(row)
    return caption_render_captioned_row(
        row,
        preset,
        output_path,
        subtitle_path,
        cover_path,
        cover_frame_path,
        base_duration,
        COVER_FRAME_TAIL_SECONDS,
        caption_style_from_row(row, preset),
        camera_from_row(row),
        camera_path_from_row(row, base_duration),
        effect_from_row(row),
        overlay_from_row(row),
        overlay_layers_from_row(row),
        normalize_bumpers_from_row(row),
    )


def apply_bumpers_to_output(
    output_path: Path, row: dict[str, object], preset: PlatformPreset, base_dir: Path, out_dir: Path, ffmpeg: str
) -> dict[str, object]:
    return render_pipeline_apply_bumpers_to_output(
        output_path,
        row,
        preset,
        base_dir,
        out_dir,
        ffmpeg,
        caption_duration,
        run_ffmpeg_command,
        fmt_time,
        ffmpeg_codec_thread_args,
        media_has_audio,
        resolve_media_path,
        video_crf(row),
        video_rate_control_args,
    )


def normalize_bumper_segment(
    source: Path, output: Path, duration: float, preset: PlatformPreset, ffmpeg: str, row: dict[str, object]
) -> None:
    render_pipeline_normalize_bumper_segment(
        source,
        output,
        duration,
        preset,
        ffmpeg,
        row,
        fmt_time,
        ffmpeg_codec_thread_args,
        media_has_audio,
        run_ffmpeg_command,
        video_crf(row),
        video_rate_control_args,
    )


def media_has_audio(path: Path, ffmpeg: str) -> bool:
    return render_pipeline_media_has_audio(path, ffmpeg)


def bumper_duration(bumper: dict[str, object], path: Path, ffmpeg: str) -> float:
    return render_pipeline_bumper_duration(bumper, path, ffmpeg)


def ffmpeg_media_duration(path: Path, ffmpeg: str) -> float:
    return render_pipeline_ffmpeg_media_duration(path, ffmpeg)


def concat_file_entry(path: Path) -> str:
    return render_pipeline_concat_file_entry(path)


def resolve_bumper_asset_path(base_dir: Path, bumper: dict[str, object]) -> Path:
    return render_pipeline_resolve_bumper_asset_path(base_dir, bumper, resolve_media_path)


def normalize_bumpers_from_row(row: dict[str, object]) -> dict[str, dict[str, object]]:
    return bumpers_normalize_bumpers_from_row(row)


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
    return render_pipeline_render_cover_frame_tail_video(
        video_path, cover_path, row, preset, out_dir, ffmpeg, COVER_FRAME_TAIL_SECONDS, fmt_time, mp4_output_args, media_has_audio, run_ffmpeg_command
    )


def render_cover_frame_segment(
    cover_path: Path,
    output: Path,
    include_audio: bool,
    preset: PlatformPreset,
    row: dict[str, object],
    ffmpeg: str,
) -> None:
    render_pipeline_render_cover_frame_segment(
        cover_path, output, include_audio, preset, row, ffmpeg, COVER_FRAME_TAIL_SECONDS, fmt_time, mp4_output_args, run_ffmpeg_command
    )


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
        *video_rate_control_args(row),
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
    return render_pipeline_effect_filter(row)


def video_crf(row: dict[str, object]) -> str:
    return render_pipeline_video_crf(row, FINAL_VIDEO_CRF, FINAL_EFFECT_VIDEO_CRF, FINAL_GRAIN_EFFECT_VIDEO_CRF)


def video_rate_control_args(row: dict[str, object]) -> list[str]:
    return render_pipeline_video_rate_control_args(row, FINAL_GRAIN_EFFECT_MAXRATE, FINAL_GRAIN_EFFECT_BUFSIZE)


def visible_effect_intensity(intensity: float) -> float:
    return render_pipeline_visible_effect_intensity(intensity)


def scaled_value(intensity: float, low: int, high: int) -> int:
    return render_pipeline_scaled_value(intensity, low, high)


def scaled_float(intensity: float, low: float, high: float) -> str:
    return render_pipeline_scaled_float(intensity, low, high)


def effect_from_row(row: dict[str, object]) -> dict[str, object]:
    return render_pipeline_effect_from_row(row)


def overlay_filter(row: dict[str, object], preset: PlatformPreset) -> str:
    return render_pipeline_overlay_filter(row, preset)


def overlay_layer_filter(overlay: dict[str, object], preset: PlatformPreset) -> str:
    return render_pipeline_overlay_layer_filter(overlay, preset)


def text_overlay_filter(overlay: dict[str, object], preset: PlatformPreset) -> str:
    return render_pipeline_text_overlay_filter(overlay, preset)


def timed_overlay_enable(overlay: dict[str, object]) -> str:
    return render_pipeline_timed_overlay_enable(overlay)


def speech_overlay_filter(overlay: dict[str, object], preset: PlatformPreset) -> str:
    return render_pipeline_speech_overlay_filter(overlay, preset)


def image_overlay_filter(overlay: dict[str, object], preset: PlatformPreset) -> str:
    return render_pipeline_image_overlay_filter(overlay, preset)


def overlay_from_row(row: dict[str, object]) -> dict[str, object]:
    return render_pipeline_overlay_from_row(row)


def overlay_layers_from_row(row: dict[str, object]) -> list[dict[str, object]]:
    return render_pipeline_overlay_layers_from_row(row)


def overlay_layer_from_raw(raw: dict[str, object]) -> dict[str, object]:
    return render_pipeline_overlay_layer_from_raw(raw)


def overlay_from_raw(raw: dict[str, object]) -> dict[str, object]:
    return render_pipeline_overlay_from_raw(raw)


def image_overlay_from_raw(raw: dict[str, object]) -> dict[str, object]:
    return render_pipeline_image_overlay_from_raw(raw)


def text_overlay_from_raw(raw: dict[str, object]) -> dict[str, object]:
    return render_pipeline_text_overlay_from_raw(raw)


def speech_overlay_from_raw(raw: dict[str, object]) -> dict[str, object]:
    return render_pipeline_speech_overlay_from_raw(raw)


def default_overlay() -> dict[str, object]:
    return render_pipeline_default_overlay()


def find_overlay_font() -> Path:
    return render_pipeline_find_overlay_font()


def ffmpeg_filter_path(path: Path) -> str:
    return render_pipeline_ffmpeg_filter_path(path)


def ffmpeg_text_value(value: str) -> str:
    return render_pipeline_ffmpeg_text_value(value)


def safe_hex_color(value: str, fallback: str) -> str:
    return render_pipeline_safe_hex_color(value, fallback)


def ffmpeg_color(value: str) -> str:
    return render_pipeline_ffmpeg_color(value)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return render_pipeline_clamp(value, minimum, maximum)


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
        cleanup_youtube_partial_sources(temp_dir)
        try:
            render_source = youtube_render_url(url)
        except RuntimeError as fallback_exc:
            raise RuntimeError(youtube_quality_fallback_error(download_error, str(fallback_exc))) from fallback_exc
        probe = probe_media_metadata(render_source, ffprobe)
        validate_youtube_fallback_quality(probe, download_error)
    metadata = source_media_metadata("youtube", label, render_source, probe, format_selector, download_error)
    cleanup = (transcribe_source,) if isinstance(transcribe_source, Path) else ()
    return SourceMedia(render_source, transcribe_source, label, cleanup, metadata)


def validate_youtube_fallback_quality(probe: dict[str, object], download_error: str) -> None:
    height = probed_video_height(probe)
    if height is None:
        return
    if height < YOUTUBE_MIN_FALLBACK_HEIGHT:
        raise RuntimeError(
            youtube_quality_fallback_error(
                download_error,
                f"Fallback YouTube resolveu apenas {height}p.",
            )
        )


def probed_video_height(probe: dict[str, object]) -> int | None:
    streams = probe.get("streams")
    if not isinstance(streams, list):
        return None
    for stream in streams:
        if not isinstance(stream, dict) or stream.get("codec_type") != "video":
            continue
        try:
            return int(stream.get("height") or 0) or None
        except (TypeError, ValueError):
            return None
    return None


def youtube_quality_fallback_error(download_error: str, fallback_error: str) -> str:
    detail = first_safe_error_line(download_error or fallback_error)
    return (
        "Nao consegui importar este YouTube com qualidade suficiente para cortes verticais. "
        f"O download local em alta falhou e o fallback remoto nao chegou a {YOUTUBE_MIN_FALLBACK_HEIGHT}p. "
        "Baixe o video em MP4 com boa qualidade e importe como arquivo local no CUTED."
        + (f" Detalhe: {detail}" if detail else "")
    )


def first_safe_error_line(message: str) -> str:
    for line in str(message or "").splitlines():
        clean = line.strip()
        if clean:
            return clean[:220]
    return ""


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


def cleanup_youtube_partial_sources(temp_dir: Path) -> None:
    media_cleanup_youtube_partial_sources(temp_dir)


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
        "Escreva title e reason sempre em portugues brasileiro, preservando o sentido do transcript. "
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
        selected.append(replace(candidate, rank=0, title=title, reason=reason_text))
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
    return replace(moment, rank=rank)


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
        return replace(moment, clip_file=None, frame_file=None, waveform_file=None, cover_candidates=())
    waveform_file = write_audio_waveform_file(clip_path, waveform_path, ffmpeg)
    return replace(
        moment,
        clip_file=rel(clip_path, clips_dir.parent),
        frame_file=rel(frame_path, frames_dir.parent),
        waveform_file=rel(waveform_path, waveforms_dir.parent) if waveform_file else None,
        cover_candidates=tuple(rel(path, frames_dir.parent) for path in cover_candidates),
    )


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
        "Todo texto gerado para hook, title, description, trend_context.summary e reason deve ser em portugues brasileiro. "
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
            "Use este contexto de origem para identificar pessoas, tema e evento. "
            "Nao copie como titulo do corte se o transcript do corte nao sustentar."
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


CAPTION_LANGUAGE_DEFAULT = "pt-BR"
CAPTION_LANGUAGE_ENGLISH = "en"
CAPTION_TRANSLATION_MAX_BATCH_SEGMENTS = 70


def caption_track_translation_from_request(
    handler: http.server.BaseHTTPRequestHandler, base_dir: Path
) -> dict[str, object]:
    payload = read_json_body(handler)
    gallery_dir = resolve_request_gallery_dir(base_dir, payload)
    rank = int(payload.get("rank") or 0)
    language = normalize_caption_language(payload.get("language") or payload.get("caption_language"))
    if rank <= 0:
        raise ValueError("Missing clip rank.")
    if language != CAPTION_LANGUAGE_ENGLISH:
        raise ValueError("Only English caption generation is supported.")
    lock = caption_track_lock(gallery_dir, rank, language)
    if not lock.acquire(blocking=False):
        return {
            "ok": False,
            "status": "running",
            "error": "English captions are already being generated for this clip.",
        }
    try:
        return generate_gallery_caption_track(gallery_dir, rank, language)
    finally:
        lock.release()


def caption_track_lock(gallery_dir: Path, rank: int, language: str) -> threading.Lock:
    key = f"{gallery_dir.resolve()}::{rank}::{language}"
    with CAPTION_TRACK_LOCKS_LOCK:
        lock = CAPTION_TRACK_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            CAPTION_TRACK_LOCKS[key] = lock
        return lock


def generate_gallery_caption_track(gallery_dir: Path, rank: int, language: str) -> dict[str, object]:
    moments_path = gallery_dir / "moments.json"
    data = read_gallery_moments_payload(moments_path)
    moments = data["moments"]
    row = gallery_moment_by_rank(moments, rank)
    tracks = row.get("caption_tracks")
    if isinstance(tracks, dict):
        existing = tracks.get(language)
        if caption_track_payload_ready(existing):
            return {"ok": True, "rank": rank, "language": language, "track": existing, "moment": row, "cached": True}
    moment = moment_from_payload(row)
    if not moment.caption_segments:
        raise ValueError("This clip has no Portuguese caption segments to translate.")
    if not openai_api_key():
        raise ValueError("OpenAI key is required to generate English captions.")
    translated = translate_single_caption_moment_to_english(moment)
    row["caption_tracks"] = caption_tracks_for_moment(moment, translated)
    write_gallery_moments_payload(moments_path, data)
    update_index_html_cuted_data(gallery_dir / "index.html", {"moments": moments})
    return {
        "ok": True,
        "rank": rank,
        "language": language,
        "track": row["caption_tracks"][language],
        "moment": row,
        "cached": False,
    }


def read_gallery_moments_payload(path: Path) -> dict[str, object]:
    require_file(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("moments"), list):
        raise ValueError("Invalid moments.json.")
    return data


def write_gallery_moments_payload(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def json_for_script(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return (
        text.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def gallery_moment_by_rank(moments: list[object], rank: int) -> dict[str, object]:
    for item in moments:
        if isinstance(item, dict) and int(item.get("rank") or 0) == rank:
            return item
    raise ValueError("Clip not found in project.")


def caption_track_payload_ready(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return str(value.get("status") or "").lower() == "ready" and isinstance(value.get("segments"), list)


def update_index_html_cuted_data(path: Path, data: dict[str, object]) -> None:
    require_file(path)
    html_text = path.read_text(encoding="utf-8")
    replacement = f"window.CUTTED_DATA = {json_for_script(data)}; window.CUTTED_SCRIPT ="
    next_text, count = re.subn(
        r"window\.CUTTED_DATA = .*?; window\.CUTTED_SCRIPT =",
        replacement,
        html_text,
        count=1,
        flags=re.DOTALL,
    )
    if count != 1:
        raise ValueError("Could not update embedded project data.")
    path.write_text(next_text, encoding="utf-8")


def moment_from_payload(row: dict[str, object]) -> Moment:
    return Moment(
        int(row.get("rank") or 0),
        float(row.get("start") or 0.0),
        float(row.get("end") or 0.0),
        float(row.get("peak") or row.get("start") or 0.0),
        float(row.get("score") or 0.0),
        str(row.get("title") or ""),
        str(row.get("reason") or ""),
        str(row.get("transcript") or ""),
        str(row.get("peak_text") or ""),
        clean_optional_text(row.get("clip_file"), 500) or None,
        clean_optional_text(row.get("frame_file"), 500) or None,
        segments_from_payload(row.get("caption_segments")),
        clean_optional_text(row.get("waveform_file"), 500) or None,
        publish_metadata=row.get("publish_metadata") if isinstance(row.get("publish_metadata"), dict) else None,
        cover_candidates=tuple(str(item) for item in row.get("cover_candidates", []) if isinstance(item, str))
        if isinstance(row.get("cover_candidates"), list) else (),
        caption_tracks=row.get("caption_tracks") if isinstance(row.get("caption_tracks"), dict) else None,
    )


def segments_from_payload(value: object) -> tuple[Segment, ...]:
    if not isinstance(value, list):
        return ()
    segments: list[Segment] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        segments.append(Segment(float(item.get("start") or 0.0), float(item.get("end") or 0.0), str(item.get("text") or "")))
    return tuple(segments)


def translate_single_caption_moment_to_english(moment: Moment) -> tuple[Segment, ...]:
    payload = request_caption_translation_batch([moment])
    translated = validated_english_caption_segments(payload, [moment])
    segments = translated.get(moment.rank)
    if not segments:
        raise RuntimeError("Caption translation response missed this clip.")
    return segments


def normalize_caption_language(value: object) -> str:
    text = str(value or "").strip().lower().replace("_", "-")
    if text in {"en", "eng", "english", "ingles"}:
        return CAPTION_LANGUAGE_ENGLISH
    return CAPTION_LANGUAGE_DEFAULT


def apply_caption_language_tracks(moments: list[Moment], args: argparse.Namespace) -> list[Moment]:
    english_segments: dict[int, tuple[Segment, ...]] = {}
    english_error = ""
    if should_translate_caption_tracks(args, moments):
        try:
            english_segments = translate_caption_tracks_to_english(moments)
        except (RuntimeError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            english_error = str(error)
            print(f"Warning: could not prepare English caption track: {error}", file=sys.stderr)
    return [
        replace(moment, caption_tracks=caption_tracks_for_moment(moment, english_segments.get(moment.rank), english_error))
        for moment in moments
    ]


def should_translate_caption_tracks(args: argparse.Namespace, moments: list[Moment]) -> bool:
    if requested_ai_provider(args) == "local":
        return False
    return bool(openai_api_key() and any(moment.caption_segments for moment in moments))


def translate_caption_tracks_to_english(moments: list[Moment]) -> dict[int, tuple[Segment, ...]]:
    translated: dict[int, tuple[Segment, ...]] = {}
    for batch in caption_translation_batches(moments):
        if not batch:
            continue
        translated.update(translate_caption_batch_with_retries(batch))
    return translated


def translate_caption_batch_with_retries(moments: list[Moment]) -> dict[int, tuple[Segment, ...]]:
    try:
        payload = request_caption_translation_batch(moments)
        translated = validated_english_caption_segments(payload, moments)
    except (RuntimeError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Warning: caption translation batch failed; retrying clips individually: {error}", file=sys.stderr)
        return translate_caption_moments_individually(moments)
    missing = caption_translation_missing_ranks(moments, translated)
    if missing:
        retry_moments = [moment for moment in moments if moment.rank in missing]
        translated.update(translate_caption_moments_individually(retry_moments))
    return translated


def translate_caption_moments_individually(moments: list[Moment]) -> dict[int, tuple[Segment, ...]]:
    translated: dict[int, tuple[Segment, ...]] = {}
    for moment in moments:
        try:
            payload = request_caption_translation_batch([moment])
            item_segments = validated_english_caption_segments(payload, [moment])
        except (RuntimeError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
            print(f"Warning: could not translate caption track for clip {moment.rank}: {error}", file=sys.stderr)
            continue
        if moment.rank in item_segments:
            translated[moment.rank] = item_segments[moment.rank]
        else:
            print(f"Warning: caption translation response missed clip {moment.rank}.", file=sys.stderr)
    return translated


def caption_translation_missing_ranks(
    moments: list[Moment], translated: dict[int, tuple[Segment, ...]]
) -> list[int]:
    return [moment.rank for moment in moments if moment.caption_segments and moment.rank not in translated]


def caption_translation_batches(
    moments: list[Moment], max_segments: int = CAPTION_TRANSLATION_MAX_BATCH_SEGMENTS
) -> list[list[Moment]]:
    batches: list[list[Moment]] = []
    current: list[Moment] = []
    current_segments = 0
    for moment in moments:
        segment_count = len(moment.caption_segments)
        if segment_count <= 0:
            continue
        if current and current_segments + segment_count > max_segments:
            batches.append(current)
            current = []
            current_segments = 0
        current.append(moment)
        current_segments += segment_count
    if current:
        batches.append(current)
    return batches


def request_caption_translation_batch(moments: list[Moment]) -> dict[str, object]:
    rows = [caption_translation_row(moment) for moment in moments if moment.caption_segments]
    return openai_structured_response(
        "You translate video subtitles from Brazilian Portuguese to natural English.",
        json.dumps(
            {
                "instructions": [
                    "Translate only the caption text.",
                    "Keep the same clip ranks, segment indexes, order, and number of segments.",
                    "Use concise spoken English suitable for burned-in social captions.",
                    "Do not add timestamps, notes, markdown, hashtags, or explanations.",
                ],
                "clips": rows,
            },
            ensure_ascii=False,
        ),
        "cuted_caption_translation",
        caption_translation_schema(),
        operation="caption_translation",
    )


def caption_translation_row(moment: Moment) -> dict[str, object]:
    return {
        "rank": moment.rank,
        "segments": [
            {"index": index, "text": segment.text}
            for index, segment in enumerate(moment.caption_segments)
        ],
    }


def caption_translation_schema() -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["clips"],
        "properties": {
            "clips": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["rank", "segments"],
                    "properties": {
                        "rank": {"type": "integer"},
                        "segments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["index", "text"],
                                "properties": {
                                    "index": {"type": "integer"},
                                    "text": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            }
        },
    }


def validated_english_caption_segments(payload: dict[str, object], moments: list[Moment]) -> dict[int, tuple[Segment, ...]]:
    source = {moment.rank: moment.caption_segments for moment in moments if moment.caption_segments}
    translated: dict[int, tuple[Segment, ...]] = {}
    rows = payload.get("clips")
    if not isinstance(rows, list):
        raise RuntimeError("Caption translation response did not include clips.")
    for row in rows:
        if not isinstance(row, dict):
            continue
        rank = int(row.get("rank", 0))
        source_segments = source.get(rank)
        raw_segments = row.get("segments")
        if not source_segments or not isinstance(raw_segments, list) or len(raw_segments) != len(source_segments):
            continue
        by_index: dict[int, str] = {}
        for item in raw_segments:
            if not isinstance(item, dict):
                continue
            index = int(item.get("index", -1))
            if 0 <= index < len(source_segments):
                by_index[index] = clean_caption_translation_text(item.get("text"))
        if len(by_index) != len(source_segments):
            continue
        translated[rank] = tuple(
            Segment(segment.start, segment.end, by_index.get(index) or segment.text)
            for index, segment in enumerate(source_segments)
        )
    return translated


def clean_caption_translation_text(value: object) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text.strip(" -")


def caption_tracks_for_moment(
    moment: Moment, english_segments: tuple[Segment, ...] | None = None, english_error: str = ""
) -> dict[str, object]:
    tracks = normalized_existing_caption_tracks(moment)
    tracks[CAPTION_LANGUAGE_DEFAULT] = caption_track_payload(
        CAPTION_LANGUAGE_DEFAULT,
        "PT-BR",
        "ready",
        "transcript",
        moment.caption_segments,
    )
    if english_segments:
        tracks[CAPTION_LANGUAGE_ENGLISH] = caption_track_payload(
            CAPTION_LANGUAGE_ENGLISH,
            "EN",
            "ready",
            "openai_translation",
            english_segments,
        )
    elif CAPTION_LANGUAGE_ENGLISH not in tracks:
        tracks[CAPTION_LANGUAGE_ENGLISH] = caption_track_payload(
            CAPTION_LANGUAGE_ENGLISH,
            "EN",
            "unavailable",
            "not_generated",
            (),
            english_error or "English captions were not generated for this import.",
        )
    return tracks


def normalized_existing_caption_tracks(moment: Moment) -> dict[str, object]:
    if not isinstance(moment.caption_tracks, dict):
        return {}
    tracks: dict[str, object] = {}
    for key, value in moment.caption_tracks.items():
        language = normalize_caption_language(key)
        if isinstance(value, dict):
            tracks[language] = value
    return tracks


def caption_track_payload(
    language: str, label: str, status: str, source: str, segments: tuple[Segment, ...], error: str = ""
) -> dict[str, object]:
    payload: dict[str, object] = {
        "language": language,
        "label": label,
        "status": status,
        "source": source,
        "segments": [segment_to_dict(segment) for segment in segments],
    }
    if error:
        payload["error"] = error
    return payload


def moment_to_dict(moment: Moment) -> dict[str, object]:
    return {
        "rank": moment.rank, "start": moment.start, "end": moment.end, "peak": moment.peak, "score": moment.score,
        "title": moment.title, "reason": moment.reason, "transcript": moment.transcript,
        "peak_text": moment.peak_text, "clip_file": moment.clip_file, "frame_file": moment.frame_file,
        "waveform_file": moment.waveform_file,
        "publish_metadata": moment.publish_metadata or {},
        "cover_candidates": list(moment.cover_candidates),
        "caption_language_default": CAPTION_LANGUAGE_DEFAULT,
        "caption_tracks": caption_tracks_for_moment(moment),
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
        <input name="language" type="hidden" value="pt">
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
    safe_data = json_for_script(json.loads(data))
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
  <script>window.CUTTED_DATA = {safe_data}; window.CUTTED_SCRIPT = {json_for_script(LOCAL_SCRIPT_PATH)};</script>
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
    return cuted_ui_assets.project_home_css()


def project_home_compact_import_css() -> str:
    return cuted_ui_assets.project_home_compact_import_css()


def project_home_js(workspace: Path) -> str:
    return cuted_ui_assets.project_home_js(workspace)


def css() -> str:
    return cuted_ui_assets.css()


def base_css() -> str:
    return cuted_ui_assets.base_css()


def liquid_ui_css() -> str:
    return cuted_ui_assets.liquid_ui_css()


def js() -> str:
    return cuted_ui_assets.js()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"[cutted] Error: {error}", file=sys.stderr)
        raise SystemExit(1)
