# ADR-0004 AI Director Visual Map First

## Status

Accepted

## Context

The previous Smart Camera architecture grew from manual presets, OpenCV face
detection, optional YOLO person detection, AI Director plans, cache recovery,
and several UI modes. That helped validate the product, but it also made the
camera system harder to reason about and exposed duplicate controls to users.

The product direction is now clearer: the user should click one **IA** action,
review the generated camera timeline, and edit individual keyframes only when
needed.

## Decision

Adopt a visual-map-first architecture for AI Director:

- YOLO/person detection is the preferred local visual map source.
- OpenCV face detection is no longer the product-level direction engine.
- OpenCV may remain as a compatibility fallback or video frame reader until the
  media IO layer is split out.
- `visual-map.json` uses version `visual-map-v2`.
- Source-level visual maps are preferred when the source media is available.
- Clip-level visual maps are generated under `camera-analysis/` when the source
  media is missing.
- AI Director receives structured visual map data by default.
- Vision frames are sent to OpenAI only when local visual coverage is sparse or
  uncertain.
- The primary UI exposes a single **IA** button in the player chrome.
- The camera timeline remains the manual correction surface.

## Consequences

Positive:

- The user experience becomes simpler and more product-like.
- AI costs should decrease because structured local data replaces routine image
  payloads.
- Multi-person scenes are less dependent on fragile frontal-face detection.
- Existing imports can still be improved by generating clip-level visual maps.

Negative:

- YOLO dependencies and model files remain heavier than OpenCV.
- First visual map generation can take time on CPU-only machines.
- Clip-level maps are less ideal than source-level maps because they only see
  the already-rendered preview clip.
- OpenCV cleanup is now a staged migration, not a single deletion.

## Validation

- Unit tests cover the player **IA** button and removal of the Smart Camera UI
  panel.
- Unit tests cover visual map pathing for clip-level maps.
- Unit tests cover the structured-map-only frame policy for AI Director.
- QA should validate existing `clip-001` and `clip-004` caches before requiring
  a full new import.
