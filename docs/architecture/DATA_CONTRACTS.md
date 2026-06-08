# Data Contracts

## Purpose

CUTED currently relies on JSON files as the contract between analyzer, browser
workspace, local API, and FFmpeg render pipeline. These contracts must stay
stable while the product migrates from a skill/script workflow into app modules.

## Generated Folder Contract

A generated sample folder normally contains:

```text
index.html
moments.json
_source/source-metadata.json
clips/
frames/
caption-queue.json
captioned-clips/
overlay-assets/
```

Not every folder has every file. Some are generated only after browser export
or final render.

## `_source/source-metadata.json`

Optional import diagnostic written when CUTED can probe the source media. For
YouTube imports, the analyzer first tries to materialize a high-quality local
source in `_source/` and records the selected format and probe output here. This
file is the first place to check when a vertical crop or Smart Camera render
looks soft: if the source entered as 480p or 720p, the final 1080x1920 export is
already working from limited pixels.

Important fields:

```text
kind
label
render_source_kind
render_source_file
format_selector
download_error
probe
```

## `moments.json`

Primary generated analysis output. It describes candidate clips and enough
configuration for the browser gallery to render review cards.

Expected responsibilities:

- source metadata
- preset/configuration used for generation
- ranked moments
- timestamps
- transcript snippets
- preview clip paths
- frame paths

## `caption-queue.json`

Browser-produced queue used by the caption/final render path.

Important fields:

```text
rank
title
text
start_seconds
end_seconds
trim_start_seconds
trim_end_seconds
adjusted_duration
clip_path
platform
platforms
caption_segments
caption_lines
caption_width
camera
camera_path
effect
overlay
overlays
platform_edits
publish_metadata
```

## `selected-clips.json`

Legacy/manual export contract for selected clips. It should remain supported
until all final render paths use the same queue contract.

Important fields:

```text
rank
title
text
clip_path
start_seconds
end_seconds
trim_start_seconds
trim_end_seconds
export_format
platforms
camera
camera_path
effect
overlay
overlays
platform_edits
status
```

## `platform_edits`

Per-platform state map. Each platform key may contain camera, camera_path,
effect, overlays, and other platform-specific edit data.

Supported platform keys:

```text
tiktok
shorts
instagram
facebook
youtube
```

Invariant: finalization must resolve the selected platform edit at render time,
not only when the platform was first added to export.

## Camera Path Contract

`camera` remains the compatibility contract for manual camera presets. The
new `camera_path` field is the time-based camera track that future automatic
reframing can write and the renderer can consume.

`camera_path` may be either an array of keyframes or an object with a
`keyframes` array. Each keyframe is relative to the adjusted clip timeline.

```text
time        seconds from the adjusted clip start
x           horizontal crop center, 0-100
y           vertical crop center, 0-100
zoom        scale multiplier, 1-2
source      manual-segment, manual-path, auto-face, auto-speaker, or similar
confidence  0-1 confidence score
key         optional legacy camera preset key
strength    optional legacy preset strength
part        optional start, middle, or end label for compatibility
```

When `camera_path` is absent, the app derives it from the existing
beginning/middle/end `camera` sequence. The review UI exposes this as the
simple camera mode. When the user adds or edits a timeline keyframe, the app
stores an explicit per-platform `camera_path`; that path becomes the render
source of truth for that platform.

When a user manually changes a simple camera segment, any stale stored camera
path for that platform must be cleared and regenerated from the updated camera
state. Future automatic reframing should also write into `camera_path` instead
of replacing the simple `camera` compatibility field.

OpenCV Smart camera writes explicit keyframes with sources such as
`auto-face-follow-face`, `auto-face-stable-face`, `auto-face-face-zoom`,
`auto-face-alternate-faces`, or `auto-face-cut-between-faces` and no legacy
preset `key`, so the renderer uses the numeric `x`, `y`, and `zoom` values.
These keyframes are still per-platform state and can be manually edited or
reset back to the simple camera mode.

AI Director writes keyframes with `source = ai-director`,
`ai-director-group`, `ai-director-speaker`, `ai-director-reactions`, or
`ai-director-cuts`. Safety post-processing may also write
`ai-director-group-safe`, `ai-director-cuts-group-safe`,
`ai-director-group-fit`, or `ai-director-cuts-group-fit`. These keyframes use
the same numeric render path as OpenCV keyframes and must be validated before
storage: times are relative to the adjusted clip, `x`/`y` are crop-center
percentages, and `zoom` is clamped to a safe social-video range. Group-safe
sources mean the model result was opened by the local safety pass to keep
visible faces inside the crop. Group-fit sources include `fit = contain` and
mean the platform crop cannot safely contain the visible group, so render should
use a contained foreground over a blurred background. `ai-director-cuts*`
sources also tell the browser preview to hold each shot instead of interpolating
between keyframes. AI Cuts payloads may include scene-direction hints derived
from OpenCV, such as reaction windows and group windows; those hints are
advisory and never replace the final validated `camera_path` contract. AI
Director payloads also include a `platform_viewport` object with width, height,
aspect ratio, orientation, and safe crop notes so platform-specific camera
decisions can be made for 9:16, 4:5, and 16:9 outputs. After validation, local
dense protection may add additional `ai-director-dense-primary`,
`ai-director-group-safe`, `ai-director-cuts-group-safe`, or group-fit frames
when OpenCV samples show the active crop would cut a visible face.

The legacy camera presets (`center`, `face-left`, `alternate`, `jump-cut`, and
similar) are manual controls. They may be used for compatibility and quick
operator edits, but they do not imply OpenCV detected the face position.

Smart camera API responses may include a `diagnostics` object:

```text
source_start_seconds  optional absolute source timestamp requested by UI
analysis_input        clip or source
analysis_file         file name analyzed by OpenCV
video_width           analyzed video width
video_height          analyzed video height
video_fps             analyzed video frame rate
video_duration        analyzed video duration
analysis_start        seconds from analyzed media start
analysis_duration     seconds analyzed
sample_count          frames requested for analysis
detection_frames      sampled frames with at least one face
detection_rate        detection_frames / sample_count
detected_faces_max    largest face count in one sampled frame
multi_face_frames     sampled frames with two or more faces
first_detection_time  first relative detection time, nullable
last_detection_time   last relative detection time, nullable
camera_keyframes      produced camera_path keyframe count
camera_max_gap_seconds largest gap between produced camera keyframes
camera_avg_gap_seconds average gap between produced camera keyframes
camera_risk_frames    sampled frames where the final crop still cuts a face
camera_protected_keyframes keyframes inserted or adjusted for safety
ai_director           optional hosted decision diagnostics
detection_preview     compact first detections for QA/debugging
```

When `source_start_seconds` is present, the server should prefer the import's
original source media from `source_path`, `_source/`, or `source_url`. If that
cannot be opened or no face is detected, it falls back to `clip_file` using
`trim_start_seconds`.

## Overlay Contract

`overlay` is the legacy single-overlay object. `overlays` is the current
multi-layer array.

Text overlay fields:

```text
id
type = text
text
x
y
width
height
opacity
background
font_size
```

Image overlay fields:

```text
id
type = image
src
asset_path
x
y
width
height
opacity
```

Coordinates and dimensions should be stored as relative values so the same edit
can be mapped to different platform dimensions.

## Rendered Output Manifest

`captioned-clips/captioned-clips.json` records final outputs.

Expected responsibilities:

- output path
- exported final path when `output_path` is configured
- platform
- preset dimensions
- source rank/title
- render status
- error if failed

Output path fields:

```text
file        temporary workspace MP4 used by the local preview
local_file  copied final MP4 in the configured render destination
final_file  response alias for the user-facing MP4 path
final_dir   response alias for the user-facing output folder
```

## Compatibility Rules

- Older `camera` and `overlay` fields remain supported.
- New render behavior should prefer platform-specific edits when available.
- `overlays` should support text and image layers.
- PNG/WebP image transparency must be preserved by the renderer.
- JPEG image layers are accepted but cannot carry transparency.
