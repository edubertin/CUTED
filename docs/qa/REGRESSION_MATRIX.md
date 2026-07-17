# QA Regression Matrix

## Purpose

This matrix defines the minimum checks required after changes to the CUTED
review workspace, data contracts, or render pipeline.

## Smoke Checks

| Area | Check | Expected Result |
| --- | --- | --- |
| Server | Start `cutted.py serve` | Gallery opens on local port |
| Server | Run `cutted.py launch` | Workspace gallery opens on a free local port; a second launch reuses the running instance |
| Local security | Open the gallery normally | Response creates an HttpOnly, SameSite=Strict local session cookie |
| Local security | POST without the session cookie | Server rejects the request with HTTP 403 |
| Local security | POST with external Origin or non-loopback Host | Server rejects the request with HTTP 403 |
| Local security | POST with the local cookie, loopback Host, and matching Origin | Server accepts the normal application request |
| Local security | GET a project file without a session | Server rejects the request with HTTP 403 |
| Local security | GET any path with a non-loopback Host | Server rejects the request and does not issue a cookie |
| Local security | Embed `</script>` in title/transcript metadata | Generated HTML escapes the sequence and does not create another script |
| Local security | Start `serve` or `launch` with `0.0.0.0` | Command rejects the non-loopback bind address |
| Local security | POST without `Origin` or with `Origin: null` | Server rejects the request with HTTP 403 |
| Desktop shell | Run `cutted.py launch --desktop-shell` | Workspace opens in a WebView2 desktop window when available, with browser fallback when unavailable |
| Desktop shell | Run `cuted.exe desktop-shell-check --json` in a packaged build | JSON reports `ok: true`, `backend: pywebview`, and `renderer: edgechromium` |
| Support diagnostics | Run `cuted.exe diagnostics --json` | JSON reports app/tool readiness and does not include API keys, source media, transcripts, or raw provider payloads |
| Navigation | Check workflow tabs | Labels are Importar, Editar, and Renderizar |
| Header | Check legacy export action | Exportar selecionados is absent |
| Brand | Header logo | Transparent official PNG appears without black rectangle |
| Brand | UI tokens | `:root` exposes CUTED blue, green, white, black, gray, surface, and border tokens |
| Brand | CUTED Liquid UI | Glass tokens style tabs, preview dock, tool panels, overlay menu, and render actions |
| Edit | Enter Editar after import | All clip dropdown cards start closed; the user chooses which card to open |
| Preview | Expand one clip card | Only active video is loaded |
| Preview | Inspect preview stack | Platform tags sit above controls, and controls sit above video |
| Preview | Mobile width | Preview dock stays constrained to video width without horizontal overflow |
| Playback | Click canvas | Video does not start |
| Playback | Click play button | Video starts |
| Playback | Local MP4 range request | Server responds with `206 Partial Content` |
| Preview camera timeline | Inspect preview controls | Play/volume appear first, media format opens in a downward dropdown, and timeline fills the second row |
| Preview camera timeline | Click timeline rail | Preview seeks to the clicked time and camera framing updates |
| Preview camera timeline | Click keyframe marker | Compact picker opens with camera preset and strength controls |
| Preview camera timeline | Seek timeline, click canvas, choose Camera | Center manual camera keyframe is added at the playhead and can be edited |
| Preview camera timeline | Change keyframe preset | Active platform `camera_path` updates without changing other platforms |
| Preview camera timeline | Open a clip with waveform sidecar | Low-emphasis green waveform appears behind the line without covering keyframes |
| Preview camera timeline | Click waveform-backed rail | Seek still works and camera markers remain clickable |
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
| Smart camera | AI Director on a wide two-person TikTok frame | Group-fit keyframe renders contained foreground over blurred background so both people remain visible |
| Smart camera | Preview a group-fit frame | Browser preview shows contained foreground over synchronized blurred background, not black letterbox bars |
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
| Volume | Open any video | Volume starts at 20 percent and toolbar shows one button |
| Volume | Click volume button | Vertical slider opens above the button and adjusts preview volume |
| Platform | Switch TikTok to Facebook | Preset state changes without losing TikTok edits |
| Text layer | Add text layer | Layer appears, moves, resizes, edits, deletes |
| Image layer | Add PNG/WebP logo | Transparency preserved in preview and render |
| Bumpers | Add intro video on TikTok | Intro chip appears only for TikTok |
| Bumpers | Add outro video on TikTok | Outro chip appears only for TikTok |
| Bumpers | Remove a bumper chip | Bumper disappears from preview and final queue |
| Export | Add multiple platforms | Queue contains each selected platform |
| Finalize | Render final queue | MP4 files and manifest are created |
| Finalize | Render with import output path | Final MP4 is copied to `CUTED Renders/<import>` and UI shows the final path |
| AI import | Generate 10 suggestions from a long transcript | Suggestions are spread across distinct timeline windows |
| AI import | YouTube has captions | Captions are used without downloading full audio for transcription |
| AI import | Audio exceeds upload limit | Audio is compressed or chunked before hosted transcription |
| AI import UI | Open import tab | Render destination starts empty with the folder picker only; Desktop button is absent |
| AI import UI | Import without destination | Import is blocked with a user-safe message before any request |
| AI import UI | Open import tab without OpenAI key | Key banner appears and its button opens the settings panel |
| AI import UI | Save an OpenAI key | Key banner disappears without reloading the page |
| AI import UI | Suggestion count | Dropdown offers 1 through 20 |
| AI import UI | Duration profile | Short, medium, and long map to expected duration arguments |
| AI import UI | Observe SEO loading step | SEO starts idle, becomes active after Previews, and only turns done/green before Editor starts |
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
| Add TikTok bumper, switch Facebook | Facebook has no inherited bumper |
| Add Facebook bumper, return TikTok | TikTok bumper is restored |

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
| Intro bumper only | Final MP4 duration includes intro before the edited cut |
| Outro bumper only | Final MP4 duration includes outro after the edited cut |
| Intro plus outro bumpers | Final MP4 duration includes both bumpers |
| Wrong bumper dimensions | Upload is rejected before render |

## Quality Gates

- Run a real local final render after render pipeline changes.
- Inspect at least one output MP4 when overlays or effects change.
- Run the clip diversity smoke test after candidate selection changes.
- Run an audio-size guard test after transcription pipeline changes.
- Check `git status` before commit because sample renders produce artifacts.
- Do not commit generated media unless the task explicitly asks for fixtures.
- Run the localhost Host/session/XSS integration tests before a public release.
