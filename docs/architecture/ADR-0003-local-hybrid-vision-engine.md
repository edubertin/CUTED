# ADR-0003 Local Hybrid Vision Engine

## Status

Accepted

## Context

Smart Camera currently relies on OpenCV Haar cascades for face detection before
AI Director plans a `camera_path`. This is inexpensive and local, but it misses
common editorial scenes: side profiles, backs, partial people, low light, and
wide multi-person shots. The result is that AI Director may receive diagnostics
claiming a scene has only one reliable face even when the editor can see two or
more people.

CUTED needs better scene understanding without turning every camera analysis
into an expensive cloud vision request.

## Decision

Introduce a local hybrid Vision Engine:

- OpenCV Haar face detection remains available and remains the fallback.
- YOLO person detection via `ultralytics` is optional and local.
- Smart Camera merges reliable face detections and person detections into a
  compact scene graph.
- AI Director receives the scene graph as structured JSON and remains the
  editorial decision layer.
- The renderer continues consuming only validated `camera_path` keyframes.

## Consequences

Positive:

- Multi-person scenes can be recognized even when faces are side-on or turned
  away.
- OpenAI cost should remain controlled because the model receives text JSON,
  not a large stream of vision frames.
- The app can reason about people and objects locally before asking the AI for
  direction.
- Existing OpenCV-only behavior remains available when YOLO is not installed.

Negative:

- `ultralytics`, PyTorch, and model files increase local installation size.
- First use may download a YOLO model.
- Person detections are not identity or speaker detections; they still need
  tracking and transcript heuristics before acting as "who is speaking".
- Commercial packaging must revisit Ultralytics/model licensing before bundled
  distribution.

## Alternatives Considered

- Send many frames to OpenAI Vision: higher cost, slower, and less predictable
  for local-first editing.
- Replace everything with MediaPipe: useful for pose/landmarks, but less direct
  for generic person/object scene detection.
- Keep tuning OpenCV only: low cost, but the observed detection ceiling remains
  too low for professional camera direction.

## Validation

- Unit tests for person detection conversion and diagnostics.
- Smoke test a local clip with Smart Camera AI Dynamic.
- Compare diagnostics before/after: `multi_person_frames` should improve on
  clips where `multi_face_frames` was zero but people are visible.
