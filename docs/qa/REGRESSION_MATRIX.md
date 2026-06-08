# QA Regression Matrix

## Purpose

This matrix defines the minimum checks required after changes to the CUTED
review workspace, data contracts, or render pipeline.

## Smoke Checks

| Area | Check | Expected Result |
| --- | --- | --- |
| Server | Start `cutted.py serve` | Gallery opens on local port |
| Navigation | Check workflow tabs | Labels are Importar, Editar, and Renderizar |
| Header | Check legacy export action | Exportar selecionados is absent |
| Brand | Header logo | Transparent official PNG appears without black rectangle |
| Brand | UI tokens | `:root` exposes CUTED blue, green, white, black, gray, surface, and border tokens |
| Brand | CUTED Liquid UI | Glass tokens style tabs, preview dock, tool panels, overlay menu, and render actions |
| Preview | Expand one clip card | Only active video is loaded |
| Preview | Inspect preview stack | Platform tags sit above controls, and controls sit above video |
| Preview | Mobile width | Preview dock stays constrained to video width without horizontal overflow |
| Playback | Click canvas | Video does not start |
| Playback | Click play button | Video starts |
| Playback | Local MP4 range request | Server responds with `206 Partial Content` |
| Timeline | Scrub the cut timeline, then play | Preview seeks to the scrubbed time and plays from there |
| Timeline | Drag start/end trim handles | Preview pauses and seeks to the active trim handle |
| Timeline | Play adjusted trim range | Preview starts inside the cut and pauses at the adjusted end |
| Timeline | Scrub outside an active trim range | Preview clamps to the adjusted cut window |
| Camera | Seek/play through Inicio, Meio, and Fim | Preview framing follows video time and does not drift independently |
| Camera | Play an alternating camera preset | Preview updates smoothly while playing and stops updating when paused |
| Camera path | Finalize a manually configured camera | Queue includes `camera_path` and render still matches the manual camera intent |
| Camera path | Add keyframe at playhead | Camera panel switches to explicit path and marker appears at the current adjusted time |
| Camera path | Edit keyframe preset/strength | Preview updates for the active platform without changing other platforms |
| Camera path | Reset to simple mode | Explicit path is cleared and preview returns to Inicio/Meio/Fim behavior |
| Smart camera | Click Auto Director | Face-based `camera_path` is applied to the active platform |
| Smart camera | Click AI Director with OpenAI configured | AI-backed `camera_path` is applied and diagnostics include `ai_director` |
| Smart camera | Click AI Director without OpenAI configured | Local Auto Director fallback applies without losing the current edit |
| Smart camera | Click each AI Director intent | Dynamic, group, speaker, reactions, and cuts modes call the same camera API and preserve per-platform `camera_path` |
| Smart camera | Preview AI Cuts path | Preview holds each shot until the next keyframe instead of interpolating a pan |
| Smart camera | Inspect AI Cuts preview CSS | Camera surface marks hard cuts and disables video transition |
| Smart camera | AI Cuts with a secondary face | Path cuts from principal to secondary/reaction for 2-3 seconds and returns to principal |
| Smart camera | AI Director on different platforms | Payload includes platform viewport dimensions and safe crop notes |
| Smart camera | Use AI Director on a three-person frame | Result opens to group-safe framing instead of holding a close-up on one person |
| Smart camera | AI Director with a long multi-face gap | Dense protection adds intermediate keyframes and diagnostics show max gap/risk data |
| Smart camera | Use Auto Director on multi-face footage | Output includes primary-face tracking plus occasional group/reaction framing when detections are reliable |
| Smart camera | Use Auto Director when a face is near the vertical crop edge | Camera shifts or opens framing before the face remains cut for several seconds |
| Smart camera | Use Follow face on edge-risk multi-face footage | Follow mode still uses safe group framing instead of locking to a false central target |
| Smart camera | Open advanced camera controls | Manual Inicio/Meio/Fim and keyframe controls remain available without being the default workflow |
| Smart camera | Inspect analysis status | Status includes sampled frames, detected frames, edge-risk frames, dimensions, and keyframe count |
| Smart camera | Analyze import with source media | Diagnostics show `analysis_input: source` |
| Smart camera | Source media unavailable | Endpoint falls back to `clip` and still returns diagnostics |
| Smart camera | Failed detection | Error keeps manual camera intact and includes diagnostic counts |
| Smart camera | Use Auto Director on a single-face clip | It falls back to primary-face framing instead of breaking the edit |
| Smart camera | Run without OpenCV | User-safe install message appears and manual camera controls still work |
| Smart camera | Repeat the same mode/clip analysis | Cached `camera-analysis` result is reused |
| Camera manual | Change Inicio/Meio/Fim controls | Explicit smart path is cleared and manual framing becomes source of truth |
| Volume | Open any video | Volume starts at 20 percent |
| Platform | Switch TikTok to Facebook | Preset state changes without losing TikTok edits |
| Text layer | Add text layer | Layer appears, moves, resizes, edits, deletes |
| Image layer | Add PNG/WebP logo | Transparency preserved in preview and render |
| Export | Add multiple platforms | Queue contains each selected platform |
| Finalize | Render final queue | MP4 files and manifest are created |
| Finalize | Render with import output path | Final MP4 is copied to `CUTED Renders/<import>` and UI shows the final path |
| AI import | Generate 10 suggestions from a long transcript | Suggestions are spread across distinct timeline windows |
| AI import | YouTube has captions | Captions are used without downloading full audio for transcription |
| AI import | Audio exceeds upload limit | Audio is compressed or chunked before hosted transcription |
| AI import UI | Open import tab | Local path defaults to Desktop |
| AI import UI | Suggestion count | Dropdown offers 1 through 20 |
| AI import UI | Duration profile | Short, medium, and long map to expected duration arguments |
| Render UI | Open Renderizar tab | Exportar fila is absent and render action remains available |

## Overlay Regression Checks

| Scenario | Expected Result |
| --- | --- |
| Click existing layer | Selects layer, does not create a new one |
| Double-click text layer, close editor | Layer remains movable |
| Drag image layer | Image follows pointer and stores relative position |
| Resize image layer | Render uses resized dimensions |
| Set opacity on one layer | Only that layer opacity changes |
| Text layer without background | No fixed border appears in final render |

## Platform State Checks

| Scenario | Expected Result |
| --- | --- |
| Add TikTok text, switch Facebook | Facebook starts with its own state |
| Add Facebook text, return TikTok | TikTok text is restored |
| Add platform to export, then edit layer | Final render uses latest edit |
| Edit queued camera item for Facebook | Only the targeted platform camera state changes |
| Remove platform from export | Platform is absent from final queue |
| Discard clip with platform selected | Discarded clip is absent from final queue and shows no active platform |
| Render TikTok and YouTube | Output dimensions differ as expected |

## Render Checks

| Scenario | Expected Result |
| --- | --- |
| Captions only | Captions render with normalized timing |
| Effect only | Effect renders without blank output |
| Each effect preset | Light grain, old film, VHS, and black-and-white render visible MP4 differences |
| Text overlay plus effect | Both text and effect appear |
| Image overlay plus effect | Image remains visible |
| PNG logo overlay | Alpha is preserved |
| JPEG overlay | Image renders opaque |

## Quality Gates

- Run a real local final render after render pipeline changes.
- Inspect at least one output MP4 when overlays or effects change.
- Run the clip diversity smoke test after candidate selection changes.
- Run an audio-size guard test after transcription pipeline changes.
- Check `git status` before commit because sample renders produce artifacts.
- Do not commit generated media unless the task explicitly asks for fixtures.
