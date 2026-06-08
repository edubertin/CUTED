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

- Auto Director: default mode. Follows the primary face and inserts wider
  reaction/group framing when multi-face context is reliable or when detected
  faces sit near the vertical crop edge.
- AI Director: optional hosted layer. Uses OpenCV diagnostics, a small set of
  low-detail sampled frames, transcript context, an editorial intent, and the
  local Auto Director fallback path to decide a more editorial `camera_path`.
  Available intents are dynamic, group/podcast, speaker focus, reactions, and
  cinematic hard cuts. Multi-person scenes should bias toward group framing
  before close-ups. Dynamic may use punctual editorial cuts, but AI Cuts is the
  dedicated principal/reaction/principal mode.
- Follow main face, with safe group framing when a second face would be cut by
  the vertical crop.
- Stable centered face.
- Face zoom.
- Legacy compatibility: alternate between detected faces and cut between
  detected faces remain supported by the API, but they are no longer the main
  editing surface.
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
5. Refactor the Camera tab around Auto Director first, with manual path editing
   and beginning/middle/end controls hidden behind an advanced section.
6. Tune framing rules for headroom, shoulders, zoom, safe horizontal crop, and
   fast switches.
7. Add AI Director as an optional layer over OpenCV. It must be cached, bounded
   by a strict JSON schema, and must fall back to local Auto Director whenever
   OpenAI is unavailable or returns invalid camera data.

## Acceptance Criteria

- Smart Camera responses include diagnostic evidence.
- Auto Director is the default camera analysis mode.
- Smart Camera prefers source footage when `source_start_seconds` and source
  media are available, with clip fallback.
- The UI explains whether detection was weak, single-face, multi-face, or
  edge-risk.
- Multi-face context influences Auto Director only when detections are reliable.
- Face detections near the vertical crop edge should trigger wider or shifted
  framing instead of leaving a face cut for several seconds.
- Smart Camera and AI Director should consider the active export platform
  viewport, because TikTok/Shorts/Instagram, Facebook, and YouTube have
  different crop safety constraints.
- Manual camera controls remain available for recovery.
- Final render continues using `camera_path` as the source of truth.
- AI Director never becomes a hard dependency for camera editing.
- AI Director responses are validated and clamped before being stored.
- AI Director paths are post-processed against OpenCV face positions so a model
  close-up cannot keep cutting visible people in multi-face scenes.
- AI Director paths receive a dense local protection pass that can insert
  mandatory keyframes between model keyframes when OpenCV samples indicate a
  face would otherwise remain outside the crop.
- Very wide group-risk frames on vertical platforms may use group-fit framing:
  contained foreground over blurred background, preserving all visible people
  instead of forcing an impossible 9:16 crop.
- If dense protection still reports multi-face crop risk, Smart Camera can
  force group-fit as a final safety fallback, especially in the final seconds of
  a clip.
- AI Director intent variants keep the same render contract and fall back to
  local Auto Director when OpenAI is unavailable.
- AI Cuts uses the same `camera_path` contract, but marks frames as hard-cut
  sources so browser preview holds each shot instead of interpolating between
  keyframes. When OpenCV detects reliable secondary faces, AI Cuts should prefer
  principal -> reaction for 2-3 seconds -> principal instead of evenly spaced
  cuts.
- AI Cuts preview must disable CSS camera transitions so hard cuts do not look
  like fast manual focus pans.
