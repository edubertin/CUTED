# Local Development Runbook

## Start the Local Gallery Server

```powershell
python tools/cutted/scripts/cutted.py serve --dir "samples/<sample-folder>" --port 8779
```

Open:

```text
http://127.0.0.1:8779/
```

The first page response creates a local HttpOnly session cookie. Mutating API
requests require that cookie plus a loopback `Host` and a same-port loopback
`Origin`. If a stale tab receives HTTP 403, close it and reopen CUTED through
the launcher instead of bypassing the check.

Project files and read APIs also require the session after the initial
`index.html` navigation. Every HTTP method rejects non-loopback `Host` values
to prevent DNS rebinding. Project data embedded in HTML is escaped for script
context before it reaches the browser.

`serve` and `launch` reject non-loopback bind addresses. Mutating requests
without `Origin`, including `Origin: null`, are denied.

## When to Restart

Restart the server after changing:

- `tools/cutted/scripts/cutted.py`
- generated `index.html`
- server API behavior
- render/finalize functions

If a render fix appears not to work, confirm the running process is using the
latest script.

## Useful Commands

Install optional local helpers:

```powershell
python -m pip install imageio-ffmpeg faster-whisper yt-dlp opencv-python-headless
```

Install the local YOLO detector used by the **IA** camera direction visual map:

```powershell
python -m pip install ultralytics
```

If the bundled OpenCV runtime is locked on Windows, install YOLO in the user
site instead:

```powershell
python -m pip install --user ultralytics
```

YOLO is the preferred local visual map source. When `ultralytics` or the
configured model cannot load, camera analysis falls back to the legacy OpenCV
path so local editing still works. Use `CUTED_YOLO_MODEL` to override the
default model and `CUTED_VISION_ENGINE=opencv` to force the fallback during
local debugging. Default YOLO weights are cached outside the repository at
`%USERPROFILE%\.cuted\models`; set `CUTED_YOLO_MODEL_DIR` to use another local
cache directory.

Check branch and dirty files:

```powershell
git status --short --branch
```

Find local Python processes:

```powershell
Get-Process python -ErrorAction SilentlyContinue
```

Start a fresh sample server:

```powershell
python tools/cutted/scripts/cutted.py serve --dir "samples/cutted-o5kdfgnz-s0-tiktok-6" --port 8779
```

## AI Import Configuration

Use the in-app settings panel for the OpenAI key whenever possible. New keys are
stored under `%USERPROFILE%\.cuted\.env.cuted.local` and local provider settings
under `%USERPROFILE%\.cuted\settings.json`. Do not commit secrets.

For advanced development fallback, CUTED can still read ignored local env files:

```text
OPENAI_API_KEY=
CUTED_AI_PROVIDER=openai
CUTED_OPENAI_MODEL=gpt-5-mini
CUTED_TRANSCRIBE_MODEL=whisper-1
CUTED_OPENAI_UPLOAD_LIMIT_MB=22
CUTED_OPENAI_CHUNK_SECONDS=600
CUTED_YTDLP_JS_RUNTIME=node:C:\path\to\node.exe
CUTED_YTDLP_EXTRA_ARGS=
```

`CUTED_YTDLP_JS_RUNTIME` can be left empty when the bundled Node runtime is
discoverable. Set it explicitly when YouTube extraction warns that no supported
JavaScript runtime is available.

## Generated Artifacts

Common generated paths:

```text
samples/*/caption-queue.json
samples/*/captioned-clips/
samples/*/captioned-clips/subtitles/
samples/*/overlay-assets/
```

These files are useful for QA evidence, but generated media should not be
committed. Keep videos and final renders in the local CUTED workspace or a local
archive; only small manifests, subtitles, docs, and intentional fixtures should
be considered for Git. Check scope before staging.

## Troubleshooting

### Final render ignores a visible overlay

Check:

- Is the platform added to export?
- Does `caption-queue.json` contain the layer under `overlays`?
- Is the layer inside the selected platform in `platform_edits`?
- For image layers, does `overlay-assets/` contain the materialized file?
- Was the local server restarted after renderer code changed?

### Image logo becomes black or opaque

Check:

- Original asset format. PNG/WebP can preserve transparency; JPEG cannot.
- FFmpeg overlay filter should preserve alpha.
- The image should be composed over the video without shortening the main
  stream unexpectedly.

### Browser preview works but final render differs

Check:

- Queue payload sent to `/api/finalize`.
- Resolved platform edit used by render.
- Output manifest in `captioned-clips/captioned-clips.json`.
- `local_file` or `final_file` copied under `CUTED Renders/<import>` when
  the import has an output path.
- Whether an old server process handled the request.
