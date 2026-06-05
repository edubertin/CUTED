# Local Development Runbook

## Start the Local Gallery Server

```powershell
python tools/cutted/scripts/cutted.py serve --dir "samples/<sample-folder>" --port 8779
```

Open:

```text
http://127.0.0.1:8779/
```

## When to Restart

Restart the server after changing:

- `tools/cutted/scripts/cutted.py`
- generated `index.html`
- server API behavior
- render/finalize functions

If a render fix appears not to work, confirm the running process is using the
latest script.

## Useful Commands

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

## Generated Artifacts

Common generated paths:

```text
samples/*/caption-queue.json
samples/*/captioned-clips/
samples/*/captioned-clips/subtitles/
samples/*/overlay-assets/
```

These files are useful for QA evidence, but they can dirty the repository. Check
scope before staging.

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
- Whether an old server process handled the request.
