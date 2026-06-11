# SPEC-012: AI Director Resolution Workspace

## Goal

Make AI Director the primary editing experience in CUTED while preserving the
timeline as the user's precise correction surface.

The user should not have to choose many technical camera modes or duplicate the
same edit across TikTok, Shorts, and Instagram. CUTED should direct the clip
automatically, store the decision as an editable plan, and render the selected
delivery targets from shared resolution presets.

## Product Direction

CUTED should move from a platform-first editor to a resolution-first workspace.

Today, platform choices such as TikTok, Shorts, Instagram, Facebook, and
YouTube are exposed as separate editing targets. That creates duplicated camera
work even when multiple destinations share the same canvas. TikTok, Shorts, and
Instagram currently use the same 1080x1920 vertical output, so one professional
camera decision should be reusable across all three unless the user explicitly
customizes a destination.

The main user promise:

```text
Click AI Director. CUTED directs the clip. Use the timeline only when you want
to correct a specific moment.
```

## UX Principles

- One primary action: `AI Director`.
- The timeline stays central. It is not an advanced leftover; it becomes the
  visual editor for camera, cuts, overlays, captions, bumpers, and future
  modules.
- Manual camera controls remain available, but behind an advanced section.
- The user edits intent first (`Speaker`, `Group`, `Reaction`, `Zoom`, `Cut`),
  not raw `x`, `y`, and `zoom` values.
- TikTok, Shorts, and Instagram should share one vertical direction by default.
- A destination can detach from the shared resolution plan when the user makes a
  destination-specific edit.

## Resolution Presets

Resolution presets are the new primary editing units.

```text
vertical_9_16
  width: 1080
  height: 1920
  default_destinations: tiktok, shorts, instagram

vertical_4_5
  width: 1080
  height: 1350
  default_destinations: facebook

horizontal_16_9
  width: 1920
  height: 1080
  default_destinations: youtube
```

Destinations become metadata layered on top of a resolution preset.

Future platforms should be added by mapping them to a resolution preset first,
then adding platform-specific metadata only when needed:

```text
destination -> resolution_preset -> render output
```

Examples:

- A future `linkedin_vertical` destination could reuse `vertical_9_16`.
- A future `linkedin_feed` destination could reuse `vertical_4_5`.
- A custom user preset could define its own width, height, safe margins, and
  destination label.

## Data Model

### Resolution Preset

```json
{
  "key": "vertical_9_16",
  "label": "Vertical 9:16",
  "width": 1080,
  "height": 1920,
  "aspect_ratio": 0.5625,
  "orientation": "vertical",
  "safe_margins": {
    "top": 0.08,
    "bottom": 0.12,
    "left": 0.06,
    "right": 0.06
  },
  "destinations": ["tiktok", "shorts", "instagram"]
}
```

### Destination

```json
{
  "key": "tiktok",
  "label": "TikTok",
  "resolution_preset": "vertical_9_16",
  "caption_style": "default",
  "bumper_policy": "optional",
  "publish_metadata_profile": "tiktok"
}
```

### Director Plan

`director_plan` is the editable editorial layer above `camera_path`.

The renderer continues to consume `camera_path`. The plan exists so AI Director
can express intent and so the user can correct that intent on the timeline.

```json
{
  "version": 1,
  "source": "ai-director",
  "resolution_preset": "vertical_9_16",
  "style": "normal",
  "energy": "normal",
  "shots": [
    {
      "id": "shot-001",
      "start": 0.0,
      "end": 4.2,
      "intent": "group_opening",
      "label": "Group",
      "subject": "group",
      "transition": "hold",
      "reason": "Two visible people establish the scene."
    },
    {
      "id": "shot-002",
      "start": 4.2,
      "end": 9.8,
      "intent": "speaker_close",
      "label": "Speaker",
      "subject": "primary",
      "transition": "smooth",
      "reason": "Primary speaker delivers the hook."
    }
  ]
}
```

### Platform Edits Compatibility

Existing `platform_edits` remain supported.

During migration, the browser can store both:

```text
resolution_edits.vertical_9_16.director_plan
resolution_edits.vertical_9_16.camera_path
platform_edits.tiktok
platform_edits.shorts
platform_edits.instagram
```

Render resolution should be:

1. Use destination-specific `platform_edits.<destination>` if detached.
2. Otherwise use `resolution_edits.<resolution_preset>`.
3. Otherwise fall back to legacy row-level `camera_path` or `camera`.

## AI Director Flow

### One-Click Direction

When the user clicks `AI Director`, CUTED should:

1. Resolve the active resolution preset.
2. Gather local scene evidence:
   - transcript window;
   - clip title and context;
   - source dimensions and quality;
   - OpenCV face detections;
   - YOLO/person detections when available;
   - edge-risk and multi-person coverage;
   - audio waveform peaks;
   - current fallback Auto Director path.
3. Ask AI Director for a `director_plan`, not raw camera coordinates.
4. Convert `director_plan` into `camera_path` locally.
5. Run local safety passes:
   - clamp crop and zoom;
   - protect visible faces/people;
   - force group-fit when the crop cannot safely contain the scene;
   - simplify excessive keyframes.
6. Save the result under the active resolution edit.
7. Offer to apply it to all destinations mapped to that resolution.

### Cost Control

AI calls should happen per resolution preset, not per destination.

```text
TikTok + Shorts + Instagram
  old behavior: up to 3 AI calls
  target behavior: 1 AI call for vertical_9_16
```

Facebook and YouTube can be handled in two ways:

- adapt locally from the director plan when the scene is simple;
- request a separate AI Director plan when the aspect ratio changes the
  editorial decision.

### Cache Key

Camera analysis cache should eventually move from platform-based to
resolution-based keys:

```text
clip fingerprint
trim window
resolution_preset
director style / energy
analysis version
```

Destination-specific cache keys are only needed for detached edits.

## Timeline Model

The timeline is the long-term correction surface for all modules.

Initial layers:

```text
Camera
Audio waveform
Captions
Overlays
Bumpers
Cuts / moments
```

The first implementation should focus on `Camera`, but the DOM/data model
should not assume camera is the only layer.

### Camera Timeline Behavior

- AI Director keyframes appear as labeled intent markers.
- Markers should display user-facing labels such as `Group`, `Speaker`,
  `Reaction`, `Zoom`, or `Cut`.
- Clicking an empty point opens an insert menu.
- Clicking an existing marker opens an edit menu.
- The user can:
  - change intent;
  - move the marker;
  - delete the marker;
  - apply auto correction to a local range;
  - detach the current destination from the shared resolution plan.

### Timeline Interaction Menu

Empty point:

```text
Camera
Text
Image
Caption
Cut
```

Camera submenu:

```text
Auto here
Speaker
Group
Reaction
Center
Zoom
Hard cut
```

Existing camera marker:

```text
Change shot
Move
Delete
Smooth around here
Detach destination
```

## UI Surface

Default Camera panel:

```text
AI Director

Energy:
  Calm | Normal | Dynamic

Apply to:
  Vertical 9:16
  TikTok, Shorts, Instagram

Status:
  Faces: good
  Risk: low
  Cost: estimated
```

Advanced Camera panel:

```text
Manual camera presets
Beginning / Middle / End
Explicit keyframes
Raw diagnostics
```

## Implementation Plan

### Phase 1: Document And Introduce Resolution Presets

- Add resolution preset helpers next to existing platform presets.
- Map current destinations to resolution presets.
- Keep existing `PLATFORM_PRESETS` behavior intact.
- Add tests proving TikTok, Shorts, and Instagram map to `vertical_9_16`.

Acceptance:

- No render behavior changes yet.
- Existing 38 tests remain green.
- New unit tests cover preset mapping.

### Phase 2: Add Resolution Edits Contract

- Add `resolution_edits` to browser export data.
- Preserve `platform_edits`.
- Render resolution lookup should prefer detached platform edit, then shared
  resolution edit, then legacy fields.

Acceptance:

- TikTok, Shorts, and Instagram can read the same camera path from
  `resolution_edits.vertical_9_16`.
- A platform-specific edit still overrides the shared edit.

### Phase 3: Add Director Plan Contract

- Define `director_plan` schema in Python.
- Validate and clamp shot times.
- Add conversion from `director_plan` to `camera_path`.
- Keep AI Director fallback behavior.

Acceptance:

- A static `director_plan` fixture converts to a valid `camera_path`.
- Render still consumes only `camera_path`.

### Phase 4: Change AI Director To Plan First

- Update AI Director prompt/schema to request `director_plan`.
- Keep a compatibility path for old `camera_path` responses during migration.
- Run local conversion and safety protection after the model response.
- Store diagnostics with both plan and final camera path counts.

Acceptance:

- AI Director returns fewer, more intentional shots.
- Diagnostics include plan shot count and final keyframe count.
- Invalid model output falls back to local Auto Director.

### Phase 5: Share Vertical Direction Across Destinations

- When AI Director runs on `vertical_9_16`, save once and apply to TikTok,
  Shorts, and Instagram by reference.
- Add UI copy that explains the shared destination group.
- Add a detach path when the user edits only one destination.

Acceptance:

- One AI Director request can serve all vertical 9:16 destinations.
- Editing TikTok only does not mutate Shorts/Instagram after detach.

### Phase 6: Timeline As Plan Editor

- Render AI Director markers with intent labels.
- Add marker edit/delete behavior.
- Add empty-point insert menu for camera actions.
- Keep the current compact camera timeline visible.
- Hide raw manual controls behind `Advanced`.

Acceptance:

- User can correct one camera moment without rerunning AI Director.
- Timeline remains the visible control surface.
- Manual fallback remains available.

### Phase 7: Keyframe Simplifier

- Add local simplification after AI Director and manual edits:
  - merge near-duplicate shots;
  - enforce minimum shot hold;
  - limit fast alternation;
  - keep group safety frames;
  - preserve hard cuts when explicitly requested.

Acceptance:

- `camera_keyframes` decreases or stays stable on noisy outputs.
- `camera_risk_frames` does not increase.
- AI Cuts still uses held shots, not accidental CSS pans.

### Phase 8: QA Fixtures

Create or select fixtures for:

- single speaker;
- two-person podcast;
- three-person group;
- face near vertical crop edge;
- weak face detection but visible people;
- horizontal source rendered to vertical;
- no reliable face/person detection.

Track:

```text
camera_keyframes
director_plan_shots
camera_avg_gap_seconds
camera_risk_frames
camera_protected_keyframes
group_fit_count
ai_director_cost_estimate
```

## Out Of Scope

- Removing the timeline.
- Removing manual camera editing.
- Rewriting the UI stack away from web.
- Store billing or account system.
- Cloud render workers.
- Training custom models.

## Risks

- Shared resolution edits may surprise users if destination-specific overlays or
  bumpers diverge. Mitigation: detach only the edited destination and show clear
  status.
- AI Director plans may be too abstract for the renderer. Mitigation: strict
  schema, local conversion, and fallback to existing `camera_path`.
- Too much timeline complexity can recreate the current clutter. Mitigation:
  show only one active layer at first and progressively reveal modules.
- Cost can grow if every destination triggers AI. Mitigation: cache and run per
  resolution preset by default.

## Recommended First Slice

Start with a low-risk foundation slice:

1. Add resolution preset helpers.
2. Add tests for destination-to-resolution mapping.
3. Add a draft `resolution_edits` export shape without changing render output.
4. Add UI copy in the Camera panel that frames TikTok, Shorts, and Instagram as
   one shared vertical format.

Then implement `director_plan` in a second slice.

