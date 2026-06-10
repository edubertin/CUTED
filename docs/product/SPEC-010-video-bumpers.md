# SPEC-010 Video Bumpers

## Goal

Let an editor attach a platform-specific intro video, outro video, or both to a
final CUTED export. The editor can use a finished animation, sponsor card,
channel opener, or end card without rebuilding it as an image/text overlay.

## Product Problem

The Effects panel currently changes only the look of the selected cut. It cannot
prepend or append a finished motion asset to the final video. Creators often
already have short branded animations for TikTok, Shorts, Instagram, Facebook,
or YouTube, and those assets should be attached to the rendered output without
mixing them with call-to-action layers.

## Scope

- Add a `Vinhetas` section inside the existing Effects panel.
- Store intro/outro selections per clip and per platform.
- Accept one intro and one outro video for the active platform.
- Show selected intro/outro files as removable chips in the editor.
- Include selected bumpers in the final queue and output manifest.
- Render final MP4s as intro + edited cut + outro.
- Keep current visual effects unchanged.

## Out Of Scope

- Timeline trimming for bumper videos.
- Automatic resizing of mismatched bumper assets.
- Animated transitions between bumper and cut.
- Asset library management.
- Cloud storage or publishing.

## Functional Rules

- Bumpers are separate from `overlays`; they change clip duration instead of
  drawing on top of the video.
- Bumpers are stored under the active platform edit. A TikTok bumper must not
  appear automatically on Facebook or YouTube.
- The editor supports two slots:
  - `intro`: video before the edited cut.
  - `outro`: video after the edited cut.
- The selected bumper should match the active platform dimensions:
  - TikTok, Shorts, Instagram: `1080x1920`
  - Facebook: `1080x1350`
  - YouTube: `1920x1080`
- If metadata cannot be read in the browser, the upload should be rejected with
  a user-safe message.
- Final render must continue when no bumpers are present.
- Removing a bumper chip must remove it from preview state and final queue.

## Data Contract

Each platform edit may include:

```json
{
  "bumpers": {
    "intro": {
      "id": "bumper-...",
      "slot": "intro",
      "label": "intro.mp4",
      "asset_file": "bumper-assets/intro-abc123.mp4",
      "width": 1080,
      "height": 1920,
      "duration": 3.2
    },
    "outro": {
      "id": "bumper-...",
      "slot": "outro",
      "label": "outro.mp4",
      "asset_file": "bumper-assets/outro-def456.mp4",
      "width": 1080,
      "height": 1920,
      "duration": 4.1
    }
  }
}
```

The final queue item repeats the selected platform's `bumpers` object so the
local renderer does not need to inspect browser state.

## UX

The Effects panel is split into:

- `Visual`: current effect presets and intensity.
- `Vinhetas`: intro/outro upload controls and removable chips.

The preview should expose a compact sequence summary:

```text
Entrada -> Corte -> Saida
```

The first MVP does not need a full composed playback timeline if final render is
correct and the selected bumper chips are visible.

## Render Rules

- Render the edited cut with the existing pipeline first.
- Normalize each bumper and the edited cut to the platform dimensions, 30 fps,
  H.264 video, AAC audio, and `yuv420p`.
- Concatenate only the present files in order:
  - intro
  - edited cut
  - outro
- Replace the final output file with the concatenated MP4.
- Record bumper metadata and final duration in `captioned-clips.json`.

## Acceptance Criteria

- User can add an intro bumper for TikTok and it appears as a chip.
- User can add an outro bumper for TikTok and it appears as a chip.
- Switching to Facebook does not inherit TikTok bumpers.
- Returning to TikTok restores the TikTok bumper chips.
- Removing a chip removes the bumper from the final queue.
- Final render without bumpers is unchanged.
- Final render with intro/outro creates a valid MP4 with a longer duration.
- Wrong-dimension bumper files are rejected before render.
