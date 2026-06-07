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
clips/
frames/
caption-queue.json
captioned-clips/
overlay-assets/
```

Not every folder has every file. Some are generated only after browser export
or final render.

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
effect
overlay
overlays
platform_edits
status
```

## `platform_edits`

Per-platform state map. Each platform key may contain camera, effect, overlays,
and other platform-specific edit data.

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
