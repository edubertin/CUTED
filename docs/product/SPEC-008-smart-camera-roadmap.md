# SPEC-008 Smart Camera Roadmap

## Goal

Make Smart Camera the primary camera editing experience in CUTED. The user
should choose an intent that matches the clip, and the app should use computer
vision to generate the camera path.

## Product Direction

The Camera tab should move away from exposing beginning/middle/end and manual
keyframe editing as the default workflow. Those controls remain useful as an
advanced fallback, but the main surface should be Smart Camera modes backed by
face detection, tracking, and source-aware analysis.

## Smart Camera Modes

- Follow main face.
- Stable centered face.
- Face zoom.
- Alternate between detected faces.
- Cut between detected faces.
- Future: active speaker focus when transcript/audio diarization is available.

## Implementation Stages

1. Add diagnostics to the current OpenCV analysis so every run explains what
   media was analyzed, how many frames were sampled, how many faces were found,
   and whether multiple faces were visible.
2. Analyze source footage when available instead of only analyzing the generated
   preview clip, then map detections into the selected platform crop.
3. Replace Haar Cascade as the primary detector with a stronger detector such
   as OpenCV YuNet or MediaPipe Face Detection, keeping Haar as fallback.
4. Add lightweight tracking across frames so face identity is stable over time.
5. Refactor the Camera tab around Smart Camera presets first, with manual path
   editing hidden behind an advanced section.
6. Tune framing rules for headroom, shoulders, zoom, and fast switches.

## Acceptance Criteria

- Smart Camera responses include diagnostic evidence.
- The UI explains whether detection was weak, single-face, or multi-face.
- Multi-face modes do not silently behave like single-face mode without status.
- Manual camera controls remain available for recovery.
- Final render continues using `camera_path` as the source of truth.

