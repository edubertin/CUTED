# SPEC-009 Vision Engine Smart Camera

## Goal

Improve Smart Camera reliability by replacing the current face-only detection
assumption with a local hybrid vision engine. The editor should understand
people and scene composition well enough for AI Director to make professional
camera choices without increasing OpenAI cost materially.

## Product Problem

The current Smart Camera stack can create strong editorial camera paths, but it
is limited by OpenCV Haar face detection. Side profiles, people turned away,
partially cropped people, and low-resolution frames often produce weak or
single-face diagnostics even when the scene visibly contains multiple people.
When the detector misses those people, AI Director cannot plan reliable
principal, reaction, group, or fit shots.

## Scope

- Add a local `Vision Engine` layer for Smart Camera analysis.
- Keep OpenCV face detection as a fallback.
- Add YOLO person detection when the `ultralytics` package and model are
  available locally.
- Send compact person/scene diagnostics to AI Director alongside existing face
  diagnostics and transcript context.
- Preserve the existing `camera_path` render contract.
- Keep the UI surface simple; diagnostics can mention vision coverage, but the
  operator should still click the same Smart Camera modes.

## Out Of Scope

- Cloud-hosted object detection.
- Training custom YOLO models.
- Full speaker diarization UI.
- Replacing the render pipeline.
- Requiring OpenAI for local camera fallback.

## Users

- Video editors using CUTED to generate social clips from multi-person videos.
- Operators testing Smart Camera quality during local import and render.

## Functional Rules

- If YOLO is installed, Smart Camera should detect `person` boxes in sampled
  frames and merge them into the local scene graph.
- If YOLO is missing, fails to load, or cannot detect people, Smart Camera must
  continue with OpenCV face detection.
- Person detections can support group/fit/cut safety, especially when face
  detection reports weak coverage.
- Face detections remain preferred for tight close-ups when reliable.
- AI Director receives compact fields such as detection engine, person frame
  count, max people, multi-person coverage, and per-time person positions.
- Low-confidence person detections should not force close-ups. They may trigger
  wider fit or group-safe framing.
- The final output remains `camera_path`; render behavior does not depend on
  detector internals.

## Acceptance Criteria

- Camera analysis diagnostics include `vision_engine`.
- Diagnostics distinguish OpenCV face coverage from YOLO person coverage.
- AI Director payload includes a `vision_detection_summary` and compact
  `vision_detections`.
- A scene with weak face detection but visible YOLO persons can produce
  multi-person context for group-fit or cuts.
- Tests cover YOLO-to-camera-row conversion, merge behavior, diagnostics, and
  payload presence.
- Local dev docs explain the optional YOLO install and fallback behavior.

## Risks

- YOLO dependencies are heavier than OpenCV and may increase local processing
  time.
- Ultralytics licensing and redistribution must be reviewed before packaging a
  commercial app with bundled model/runtime.
- Person detectors can confuse posters, screens, mannequins, or reflections
  with real participants.
- Body boxes are not face boxes; they should guide framing and safety more than
  precise close-up composition.

## QA Notes

- Compare clips with people side-on or partially turned away.
- Confirm `multi_person_frames` increases where OpenCV reported zero
  `multi_face_frames`.
- Confirm AI Director falls back cleanly when `ultralytics` is absent.
- Confirm render output still uses the same `camera_path` segmentation.
