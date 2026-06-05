# QA Regression Matrix

## Purpose

This matrix defines the minimum checks required after changes to the CUTED
review workspace, data contracts, or render pipeline.

## Smoke Checks

| Area | Check | Expected Result |
| --- | --- | --- |
| Server | Start `cutted.py serve` | Gallery opens on local port |
| Preview | Expand one clip card | Only active video is loaded |
| Playback | Click canvas | Video does not start |
| Playback | Click play button | Video starts |
| Volume | Open any video | Volume starts at 20 percent |
| Platform | Switch TikTok to Facebook | Preset state changes without losing TikTok edits |
| Text layer | Add text layer | Layer appears, moves, resizes, edits, deletes |
| Image layer | Add PNG/WebP logo | Transparency preserved in preview and render |
| Export | Add multiple platforms | Queue contains each selected platform |
| Finalize | Render final queue | MP4 files and manifest are created |

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
| Remove platform from export | Platform is absent from final queue |
| Render TikTok and YouTube | Output dimensions differ as expected |

## Render Checks

| Scenario | Expected Result |
| --- | --- |
| Captions only | Captions render with normalized timing |
| Effect only | Effect renders without blank output |
| Text overlay plus effect | Both text and effect appear |
| Image overlay plus effect | Image remains visible |
| PNG logo overlay | Alpha is preserved |
| JPEG overlay | Image renders opaque |

## Quality Gates

- Run a real local final render after render pipeline changes.
- Inspect at least one output MP4 when overlays or effects change.
- Check `git status` before commit because sample renders produce artifacts.
- Do not commit generated media unless the task explicitly asks for fixtures.
