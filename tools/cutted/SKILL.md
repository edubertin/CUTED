---
name: cutted
description: Local AI-assisted video clipping workflow. Use when Codex needs to analyze local videos or rights-approved YouTube test URLs, transcribe speech, suggest short-form highlight moments with smart phrase boundaries, render preview clips, extract peak frames, generate a black HTML curation gallery with trim controls, and optionally clean temporary source media.
---

# Cutted

## Overview

Cutted turns a long-form video into a local review gallery of suggested short clips. It is designed for fast MVP tests: local processing, no app server, no public publishing, and simple HTML output.

Use `scripts/cutted.py` for deterministic work. Prefer local files supplied by the user. For YouTube URLs, proceed only when the user confirms the use is a private/rights-approved test or the source is clearly open/licensed.

## Quick Start

Local video:

```powershell
python scripts/cutted.py analyze "C:\path\video.mp4" --out "C:\path\cutted-output" --preset tiktok --clips 15 --language pt
```

YouTube test URL:

```powershell
python scripts/cutted.py analyze --youtube-url "https://www.youtube.com/watch?v=..." --out "C:\path\cutted-output" --preset tiktok --clips 15 --language pt --cleanup-source
```

If system Python is missing, use the bundled Codex Python when available:

```powershell
& "C:\Users\edube\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts/cutted.py analyze "C:\path\video.mp4" --out "C:\path\cutted-output" --preset tiktok --language pt
```

Open `index.html` from the output folder after generation. If the browser blocks `file://`, serve the folder locally:

```powershell
python -m http.server 8767 --bind 127.0.0.1 --directory "C:\path\cutted-output"
```

For the interactive MVP finalize button, use the CUTED local server instead of a plain static server:

```powershell
python scripts/cutted.py serve --dir "C:\path\cutted-output" --port 8778
```

This serves the gallery and exposes a local-only `/api/finalize` endpoint. The `Finalizar videos` button sends the current queue, line count, and caption width to Python, renders the selected clips into `captioned-clips/`, and returns links for playback.

## Workflow

1. Confirm the input is a local video or a rights-safe test URL.
2. Choose a preset:
   - `--preset tiktok`: target short-form clips around 42 seconds.
   - `--preset shorts`: same behavior for YouTube Shorts.
   - `--preset reels`: same behavior for Instagram Reels.
3. Run `cutted.py analyze` with `--language pt` for Portuguese.
4. Review the black HTML gallery.
5. Trim the start/end of each candidate when the cut feels early or late.
6. Mark clips with `Gostei` or `Descartar`.
7. Export selected metadata from the HTML.
8. Use `--cleanup-source` when temporary source media should be removed after rendering.

## Review Gallery

Each card includes:

- a playable video preview;
- a global format selector for TikTok, Shorts, YouTube, Instagram, and Facebook previews;
- a collapsible per-clip editor that keeps only the active preview loaded;
- per-clip panels for trim setup, camera reframing, effects, calls-to-action, captions, and transcript review;
- a persistent per-clip `Export` dock that adds or removes TikTok, Shorts, Instagram, Facebook, and YouTube destinations from the final queue;
- the peak phrase and transcript;
- `Gostei`, `Descartar`, and `Resetar corte` controls;
- a visual two-handle timeline close to the video preview;
- per-clip platform tags for TikTok, Shorts, Instagram, Facebook, and YouTube next to the trim controls;
- a final timing summary.

The first screen is now the main editing workspace. Each clip opens as a dropdown, and its local `Camera` panel applies a three-part camera line per selected cut/platform before subtitles, effects, and calls-to-action. Each selected output has `Inicio`, `Meio`, and `Fim` camera slots:

- `Centro seguro`: default centered crop.
- `Rosto no centro`: slight punch toward a central speaker.
- `Rosto a esquerda`: prioritize the left side of a podcast/table layout.
- `Rosto a direita`: prioritize the right side of a podcast/table layout.
- `Alternar focos`: slow pan between left and right.
- `Corte entre focos`: hard jump between left and right without a slow pan.
- `Zoom sutil`: steady closer framing.
- `Punch-in`: stronger close crop for emphasis.

The MVP camera presets are deterministic FFmpeg scale/crop filters and do not require OpenCV, paid APIs, or cloud processing. Three-slot camera lines render through FFmpeg `filter_complex`, splitting the clip into thirds, applying the chosen reframe to each part, and concatenating the video before captions/effects/overlays. OpenCV can be added later for automatic face anchors without changing the exported `camera.segments` object shape.

The local `Efeitos` panel applies one MVP look per selected cut:

- `Sem efeito`: clean output.
- `Chuvisco Leve`: subtle grain/noise.
- `Filme Antigo`: vintage color, grain, and vignette.
- `VHS / TV Antiga`: stronger analog-style noise and contrast.
- `Preto e Branco Antigo`: black-and-white grain with vignette.

The local format strip below each video is the active edit preset selector. TikTok, Shorts, Instagram, Facebook, and YouTube each keep their own camera line, effects, call-to-action layers, image layers, and saved positions. The `Export` dock only controls which platform presets enter the render queue.

The local `Chamadas` panel applies draggable layers per selected platform preset. Clicking the preview opens a dismissible call-to-action menu at that point before the user chooses, drags, or resizes a card. A cut can hold multiple call-to-action cards, and the panel also accepts transparent PNG/WebP/JPEG uploads as image layers. The local `Legenda` panel holds the caption line/width controls used by the final render:

- `Sem chamada`: clean output.
- `Inscreva-se`: subscribe-style CTA.
- `Siga-nos`: follow/profile CTA.
- `Veja a descricao`: description/link CTA.
- `Curta e compartilhe`: engagement CTA.
- `Comentario fixado`: pinned-comment CTA.
- `Marca d'agua`: subtle CUTED watermark.
- `Imagem`: a transparent PNG/WebP/JPEG layer shown in the browser preview and stored in the exported queue.

The browser preview stores each layer position, width, and opacity as relative values for the active platform preset. FFmpeg burns multiple text call-to-action cards into each platform size. Local render mode materializes uploaded image layers into `overlay-assets/` and composes them with `overlay=format=auto`, preserving PNG/WebP transparency for logos and stickers.

The exported `caption-queue.json` and `selected-clips.json` include a `camera` object with `key`, `label`, and `segments` for the output platform's camera line, an `effect` object with `key`, `label`, and `intensity`, a legacy `overlay` object for compatibility, an `overlays` array for multiple call-to-action or image layers, and `platform_edits` on selected moments for per-platform editing state. Older single-preset `camera` and `overlay` objects remain supported.

The trim sliders are stored in browser `localStorage`. The exported JSON includes:

- original `start` and `end`;
- `trim_start_seconds`;
- `trim_end_seconds`;
- `adjusted_start`;
- `adjusted_end`;
- `adjusted_duration`;
- `export_format`;
- `platforms`;
- `caption_queue`;
- `camera`;
- `effect`;
- `overlay`;
- `overlays`;
- `platform_edits`;
- `status`.

The `Final` tab is the local render/results gallery. When opened through `cutted.py serve`, rendering goes through `/api/finalize`. Results appear as one dropdown per rendered video, each with an inline player, an open-in-new-tab link, and a direct MP4 download link. It can still export the queue as `caption-queue.json` for manual/debug workflows.

Selection rule:

- clips marked with `Gostei` always enter the caption queue;
- if a liked clip has no platform tag, it uses the current global format as the default destination;
- explicit platform tags still win when the user marks TikTok, Shorts, Instagram, Facebook, or YouTube on the card.

Each queued item also includes deterministic publishing metadata:

- `publish_metadata.hashtags`: platform-specific hashtag suggestions from the clip text;
- `publish_metadata.caption_hint`: a short starting point for the post caption;
- `publish_metadata.strategy`: a concise platform note for the current export target.

Treat these as a draft. Before publishing, verify current platform trends and remove tags that are too generic, unrelated, or repetitive.

## Captioning Selected Clips

After exporting `caption-queue.json` from the `Final` tab, burn styled captions locally:

```powershell
python scripts/cutted.py caption-selected "C:\path\caption-queue.json" --out "C:\path\captioned-clips"
```

Useful options:

- `--base-dir "C:\path\cutted-output"`: resolve relative preview paths from a specific output folder.
- `--chars-per-line 28`: control caption line width.
- `--max-lines 2`: keep captions in a short social-video style.

This command creates:

```text
captioned-clips/
  clip-001-tiktok-captioned.mp4
  subtitles/clip-001-tiktok.ass
  captioned-clips.json
```

The caption renderer uses FFmpeg and ASS subtitles locally. It does not call an AI model when the queue already has transcript text.

When an exported queue contains a `camera`, `caption-selected` applies the selected reframe before subtitles in the final filter chain. When it contains an `effect`, the renderer applies the selected effect after subtitles. When it contains `overlays`, the renderer burns text CTA layers after the effect, using saved relative positions and platform dimensions. Grain strengths are intentionally modest so short-form outputs stay small enough for quick MVP testing.

Caption quality behavior:

- cleans Portuguese transcript artifacts such as speaker markers, repeated symbols, odd spacing, and loose punctuation;
- uses timestamped `caption_segments` when available, so captions follow the original transcript timing inside the cut;
- normalizes caption event timing so one subtitle block ends before the next begins;
- falls back to evenly distributed caption blocks for older queues that only contain full transcript text;
- keeps the current MVP style as short, bold, readable social-video captions.

## Rendering Selected Clips

After exporting `selected-clips.json` from the gallery, render final clips:

```powershell
python scripts/cutted.py render-selected "C:\path\selected-clips.json" --out "C:\path\final-clips"
```

This creates one MP4 per selected platform:

```text
final-clips/
  clip-001-tiktok.mp4
  clip-001-instagram.mp4
  clip-002-youtube.mp4
  rendered-clips.json
```

Platform output presets:

- TikTok: `1080x1920`
- Shorts: `1080x1920`
- Instagram: `1080x1920`
- Facebook: `1080x1350`
- YouTube: `1920x1080`

The current renderer uses the already generated preview clip as input, applies the human trim, then crops/scales to the selected platform. Use this as the local MVP path before building a higher-quality source-rerender path.

## Smart Boundaries

Use `--smart-boundaries` to avoid rough cuts. Presets enable it by default.

The script will:

- prefer windows near `--target-duration`;
- penalize cuts ending in weak connectors like `porque`, `entao`, `mas`, `so que`, or `ou seja`;
- penalize starts that look like sentence fragments;
- add `--lead-in` seconds before the cut and `--tail-out` seconds after the cut;
- favor clips that sound more like a complete thought.

Useful parameters:

- `--target-duration 42`: preferred duration.
- `--min-duration 30`: shortest candidate duration.
- `--max-duration 70`: longest candidate duration.
- `--lead-in 1`: extra seconds before the selected phrase.
- `--tail-out 1.5`: extra seconds after the selected phrase.
- `--no-smart-boundaries`: disable boundary heuristics.

## YouTube Mode

`--youtube-url` currently uses `yt-dlp` and FFmpeg locally.

The script:

1. tries YouTube captions first, preferring `pt-orig` and `pt`;
2. falls back to local audio transcription when captions are unavailable;
3. resolves a renderable video stream URL;
4. renders only the selected clip ranges;
5. deletes temporary source files when `--cleanup-source` is provided.

This avoids downloading the full video file for rendering. Captions also avoid full-audio transcription when YouTube provides usable timestamps.

## Dependencies

Install local helpers if needed:

```powershell
python -m pip install imageio-ffmpeg faster-whisper yt-dlp
```

The script looks for FFmpeg in this order:

1. `FFMPEG_BIN`;
2. executable on `PATH`;
3. the Python package `imageio-ffmpeg`.

`yt-dlp` is used only for YouTube test URLs.

## Output

The output folder contains:

- `index.html`: black curation interface.
- `moments.json`: machine-readable candidate data and config.
- `clips/clip-001.mp4`: rendered previews.
- `frames/clip-001.jpg`: peak-frame poster images.

## Next Improvements

Keep the tool local-first. Next upgrades should be:

- word-level timestamps with WhisperX for cleaner phrase boundaries;
- optional automatic face-anchor detection for the camera/reframe presets;
- LLM scoring for hook/context/ending quality;
- per-word animated captions on top of final rendered clips.
