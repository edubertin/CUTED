# SPEC-001: Review Workspace

## Objective

Define the current browser editing workspace used by generated CUTED samples.
This spec captures the expected MVP behavior before the workspace is extracted
into a dedicated app.

## Scope

- Collapsible clip cards.
- Single active video preview per expanded card.
- Trim/timeline editing.
- Importar, Editar, and Renderizar workflow tabs.
- Platform preset editing for TikTok, Shorts, Instagram, Facebook, and YouTube.
- Camera, effects, captions, transcript review, text overlays, image overlays,
  layer movement, layer resizing, opacity, and export queue selection.
- Final tab handoff to the local render API.

## Out of Scope

- Cloud job orchestration.
- Authenticated users.
- Publishing integrations.
- Collaborative editing.
- Full design-system extraction.

## Layout Rules

- The first screen is the main editing workspace.
- Each clip is represented as a dropdown card.
- After import completes and CUTED enters the Editar tab, all clip dropdown
  cards should start closed. The user chooses which clip/card to open first;
  the first card must not auto-open by default.
- Only the active card should load and play its video preview.
- Each clip owns its own platform switcher; there is no global Format toolbar in
  the Edit tab.
- The preview stack order is platform switcher, compact playback/timeline
  controls, then the video composition canvas.
- Preview playback controls should live outside the video, not on top of the
  composition canvas.
- Platform edit tags and compact playback controls are centered relative to the
  preview width.
- The controls container should respond to the video preview width.

## Preview Interaction Rules

- Clicking the video canvas must not start playback.
- Playback starts only from the explicit play control.
- Volume defaults to 20 percent for every opened video.
- The preview exposes a single volume button. Clicking it opens a compact
  vertical slider; the main toolbar does not show volume percentages or step
  controls.
- The first preview toolbar row starts with compact play and volume controls,
  followed by a downward media-format dropdown above the timeline.
- The preview controls include a compact camera timeline on its own full-width
  row. The line shows camera keyframes in CUTED blue, follows the playhead, lets
  the user seek by clicking the line, and may show a low-emphasis green audio
  waveform behind the camera controls.
- Clicking a camera keyframe opens a small picker for changing the camera preset
  and strength for the active platform.
- Clicking the video canvas opens the layer insertion menu. Choosing Camera adds
  a center manual camera keyframe at the current timeline playhead.
- Canvas clicks create or open the layer insertion menu only when the target is
  the canvas, not an existing layer.
- Existing layers can be selected, moved, resized, edited, and deleted without
  creating a new layer.

## Platform Preset Rules

Each platform preset owns its own edit state:

- `camera`
- `camera_path`
- `effect`
- text overlays
- image overlays
- layer positions
- layer dimensions
- layer opacity
- caption settings when applicable

When the user switches from TikTok to Facebook and edits a layer, the Facebook
state must not overwrite the TikTok state. When the user returns to TikTok, the
TikTok-specific state must be restored.

## Export Dock Rules

- Platform tags above the preview select the active edit preset.
- The export dock controls which presets enter the final render queue.
- The final render must read the latest state at finalization time, even if the
  platform was added to export before later edits.
- A clip with no explicit export destination falls back to TikTok only when the
  selection rule requires a default.

## Layer Rules

Text layers:

- User-provided text, not fixed CTA buttons.
- Optional background.
- Optional opacity per item.
- Resizable bounding box.
- No permanent decorative border in the rendered output.
- Editing handles can be visible in the browser UI but must not render.

Image layers:

- User-uploaded image layer.
- PNG and WebP transparency should be preserved in render.
- JPEG is supported but has no alpha channel.
- Image position and size are stored as relative values.
- Image upload should materialize to local `overlay-assets/` before render.

## Acceptance Criteria

- A user can add more than one text layer to a clip.
- A user can add at least one image layer to a clip.
- Clicking an existing layer selects it instead of opening the add-layer menu.
- Double-clicking and closing the edit box does not break later layer movement.
- Switching platform presets restores the correct saved layers for each preset.
- Final render receives all active per-platform edits.
- The top navigation labels are `Importar`, `Editar`, and `Renderizar`.
- The header does not show the legacy `Exportar selecionados` action.
- The Renderizar tab does not show the legacy `Exportar fila` action.
