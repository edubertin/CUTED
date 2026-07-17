from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


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


def probe_media_metadata(video: Path | str, ffprobe: str | None) -> dict[str, object]:
    if not ffprobe:
        return {"probe_available": False}
    command = [
        ffprobe, "-v", "error",
        "-show_entries",
        "stream=index,codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,bit_rate:format=duration,bit_rate,format_name",
        "-of", "json", str(video),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
    except subprocess.SubprocessError as exc:
        return {"probe_available": True, "probe_error": str(exc)}
    data = json.loads(result.stdout or "{}")
    data["probe_available"] = True
    return data


def source_media_metadata(
    kind: str, label: str, render_source: str, probe: dict[str, object],
    format_selector: str | None, download_error: str | None
) -> dict[str, object]:
    is_remote = render_source.startswith(("http://", "https://"))
    path = Path(render_source) if not is_remote else None
    is_local = bool(path and path.exists())
    video = media_video_probe(probe)
    return {
        "kind": kind,
        "label": label,
        "render_source_kind": "local-file" if is_local else "remote-url",
        "render_source_file": path.name if path and is_local else "",
        "video_width": video.get("width"),
        "video_height": video.get("height"),
        "video_bit_rate": video.get("bit_rate"),
        "format_bit_rate": probe.get("format", {}).get("bit_rate") if isinstance(probe.get("format"), dict) else None,
        "format_selector": format_selector or "",
        "download_error": download_error or "",
        "probe": probe,
    }


def media_video_probe(probe: dict[str, object]) -> dict[str, object]:
    streams = probe.get("streams")
    if not isinstance(streams, list):
        return {}
    for stream in streams:
        if isinstance(stream, dict) and stream.get("codec_type") == "video":
            return stream
    return {}


def write_source_metadata(out_dir: Path, metadata: dict[str, object] | None) -> None:
    if not metadata:
        return
    source_dir = out_dir / "_source"
    source_dir.mkdir(exist_ok=True)
    (source_dir / "source-metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def yt_dlp_command() -> list[str]:
    path_bin = shutil.which("yt-dlp")
    command = [path_bin] if path_bin else [sys.executable, "-m", "yt_dlp"]
    return command + yt_dlp_runtime_args() + yt_dlp_extra_args()


def yt_dlp_runtime_args() -> list[str]:
    runtime = os.environ.get("CUTED_YTDLP_JS_RUNTIME", "").strip()
    if runtime:
        return ["--js-runtimes", runtime]
    node = bundled_node_path() or shutil.which("node")
    return ["--js-runtimes", f"node:{node}"] if node else []


def bundled_node_path() -> str | None:
    exe_name = "node.exe" if os.name == "nt" else "node"
    candidate = Path(sys.executable).resolve().parent.parent / "node" / "bin" / exe_name
    return str(candidate) if candidate.exists() else None


def yt_dlp_extra_args() -> list[str]:
    raw = os.environ.get("CUTED_YTDLP_EXTRA_ARGS", "").strip()
    return shlex.split(raw) if raw else []


def youtube_high_quality_format(default_format: str) -> str:
    return os.environ.get("CUTED_YOUTUBE_RENDER_FORMAT", "").strip() or default_format


def run_ytdlp(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(friendly_ytdlp_error(result.stderr or result.stdout or "yt-dlp failed"))
    return result


def friendly_ytdlp_error(message: str) -> str:
    clean = "\n".join(line for line in message.strip().splitlines() if line.strip())
    lower = clean.lower()
    if "sign in to confirm" in lower or "not a bot" in lower or "cookies-from-browser" in lower:
        return (
            "O YouTube pediu login/confirmacao anti-bot. "
            "Baixe o video com a ferramenta de sua preferencia e importe o arquivo local no CUTED."
        )
    if "private video" in lower or "login required" in lower:
        return "O YouTube pediu login para este video. Importe o arquivo local no CUTED."
    return clean


def youtube_title(url: str) -> str:
    command = yt_dlp_command() + ["--no-playlist", "--print", "%(title)s", url]
    result = run_ytdlp(command)
    return result.stdout.strip() or "YouTube video"


def youtube_render_url(url: str, stream_fallback_format: str) -> str:
    command = yt_dlp_command() + ["-f", stream_fallback_format, "-g", "--no-playlist", url]
    result = run_ytdlp(command)
    urls = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith(("http://", "https://"))]
    if not urls:
        raise RuntimeError("Could not resolve a renderable YouTube media URL.")
    return urls[0]


def download_youtube_render_source(url: str, temp_dir: Path, ffmpeg: str, format_selector: str, media_extensions: set[str]) -> Path:
    output_template = temp_dir / "source.%(ext)s"
    command = yt_dlp_command() + [
        "--no-playlist",
        "--ffmpeg-location", ffmpeg,
        "-f", format_selector,
        "--merge-output-format", "mp4",
        "--remux-video", "mp4",
        "-o", str(output_template),
        url,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        cleanup_youtube_partial_sources(temp_dir)
        message = friendly_ytdlp_error(result.stderr or result.stdout or "yt-dlp high quality download failed")
        raise RuntimeError(message)
    return resolved_youtube_render_file(temp_dir, media_extensions)


def cleanup_youtube_partial_sources(temp_dir: Path) -> None:
    if not temp_dir.exists():
        return
    for path in temp_dir.glob("source.*.part"):
        if path.is_file():
            path.unlink(missing_ok=True)


def resolved_youtube_render_file(temp_dir: Path, media_extensions: set[str]) -> Path:
    candidates = sorted(
        path for path in temp_dir.glob("source.*")
        if path.is_file() and path.suffix.lower() in media_extensions
    )
    if not candidates:
        raise RuntimeError("High quality YouTube source download did not produce a media file.")
    return candidates[-1].resolve()


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
    run_ytdlp(command)
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
