# SPEC-014 - Control Bar Surface Implementation Plan

## Goal

Turn `prototypes/control-bar-spike` into the production control surface that
will sit between the video preview and the live timeline in CUTED.

The bar should feel like an intelligent editing dock: compact, cinematic,
reactive to the current cut, and ready to expose AI, effects, captions, insert
bumpers, platform format, volume, cancel, and render-ready state without
crowding the video.

## Workflow Context

Mode: implementation plan.

Risk: medium. The current work is still isolated in the prototype, but the next
step touches the generated review workspace, per-platform edit state, and final
render queue.

Specialist routing:

- UX expert: motion hierarchy, overlay behavior, information density,
  accessibility, and menu affordances.
- Architect: component boundary, data contract, asset packaging, and lifecycle
  with the live timeline.
- Developer: implementation sequence, adapter shape, event callbacks, and
  maintainability.
- QA engineer: visual regression, keyboard access, render-state parity, and
  fallback checks.

## Current Prototype

Prototype folder:

- `prototypes/control-bar-spike/index.html`
- `prototypes/control-bar-spike/styles.css`
- `prototypes/control-bar-spike/script.js`

Current public entry:

```js
window.createCutedControlBar(container, options)
```

Current controls:

- volume with mute and animated sonic rail;
- format dropdown with `9:16`, `4:5`, and `16:9`;
- AI button with idle, loading, and active state;
- FX menu with Clean, VHS, Film, and Grain;
- Insert menu with Start and End bumper slots;
- CC toggle;
- discard action;
- Ready action with animated final state.

## Product Direction

The production version should be named internally as the CUTED control surface,
not only a button bar. It should behave as the bridge between three layers:

- video preview: what the user sees;
- live timeline: where timing, camera, waveform, and keyframes live;
- render state: what will be exported.

The user should not feel that they are jumping between panels. The bar should
make the active edit feel continuous: format, AI, effect, caption, insert, and
ready all belong to the same clip decision.

## Scope

Implement a reusable control surface module and integrate it into the generated
review workspace for the active opened clip.

Included:

- Keep the existing visual language from the spike.
- Package CSS and JS as static assets, like the live timeline assets.
- Mount the control surface near the video/timeline area of each opened card.
- Keep the app state as source of truth.
- Map control callbacks to existing CUTED handlers.
- Add a contextual status strip for analysis, progress, and short feedback.
- Preserve per-platform edits for format, effects, captions, and bumpers.
- Keep the current render pipeline contract for intro/outro bumpers.

Out of scope for first integration:

- Rewriting final render.
- Replacing the full Effects, Camera, or Captions panels.
- Real-time composed preview of intro/outro MP4 files.
- Upload library management for bumper assets.
- Shipping Rive or Lottie assets before the CSS/JS implementation is stable.

## UX Plan

### Layout

Place the bar as a floating glass dock over the boundary between video preview
and live timeline.

Recommended layout:

```text
Video preview
[ contextual status strip ]
[ volume | format | AI | FX | Insert | CC | X | OK/Ready ]
Live timeline
```

The bar should overlap the edge of both surfaces lightly, so it feels attached
to the edit instead of becoming another panel. It must not cover subtitles,
play controls, timeline handles, or keyframe markers.

### Status Strip

Add a slim contextual strip above or inside the top edge of the bar. It should
show only one short active message at a time:

- `AI analyzing frame safety... 42%`
- `Effect preview: VHS`
- `Intro attached: start-bumper.mp4`
- `Captions on`
- `Ready`

The strip should be passive until something meaningful happens. It should not
be permanent instructional copy.

### Interaction Rules

- Only one menu opens at a time: format, FX, or Insert.
- Menus close on outside click, `Escape`, or when another menu opens.
- `AI` enters loading, then active. Active means the user has used AI at least
  once for that cut.
- `FX` opens visual styles and stores the selected effect per platform edit.
- `Insert` opens Start and End slots, backed by `bumpers.intro` and
  `bumpers.outro`.
- `CC` toggles captions for the current platform edit.
- `Ready` collapses X and OK, then reveals the `Ready` word animation.
- The small X beside `Ready` returns the bar to the editable state.

### Motion Language

Use motion to confirm state changes, not to decorate every idle element.

Primary motions:

- AI: scan pulse while loading, then blue active glow.
- FX: popover rise with cyan/green edge trace.
- Insert: two-slot drawer, each slot lighting when attached.
- CC: short subtitle-line flicker when enabled.
- Ready: OK and X implode, letters reveal one by one, green pulse settles.
- Volume: waveform reacts while adjusting, muted icon becomes quiet and red.
- Status strip: text crossfades and number increments for progress.

Respect `prefers-reduced-motion` by shortening transitions and removing loops.

## Technical Architecture

### Module Shape

Create a production module after the spike is approved:

```text
prototypes/control-bar-spike/
tools/cutted/assets/control-bar/control-bar.js
tools/cutted/assets/control-bar/control-bar.css
```

The generated gallery should copy the production assets to:

```text
assets/control-bar/control-bar.js
assets/control-bar/control-bar.css
```

Public API:

```ts
createCutedControlBar(container, {
  volume,
  muted,
  aspectRatio,
  aiStatus,
  effectStyle,
  captionsEnabled,
  bumpers,
  ready,
  status,
  callbacks
})
```

The API should expose:

```ts
controller.update(nextState)
controller.destroy()
```

The component must not own final state. It mirrors state, emits user intent,
and lets the existing card/platform logic decide what is saved.

### State Mapping

Map UI state to existing CUTED contracts:

| Control | Source of truth | Render impact |
| --- | --- | --- |
| Volume | preview player only | none |
| Format | active platform edit | target dimensions |
| AI | camera/analysis diagnostics | camera path or status only |
| FX | `platform_edits[platform].effect` | FFmpeg effect |
| Insert Start | `platform_edits[platform].bumpers.intro` | prepended MP4 |
| Insert End | `platform_edits[platform].bumpers.outro` | appended MP4 |
| CC | caption settings for platform | subtitles on/off |
| Ready | queue/export selection state | render eligibility |

### Format Options

Use the existing platform dimensions:

- `9:16`: TikTok, Shorts, Instagram, `1080x1920`;
- `4:5`: Facebook feed, `1080x1350`;
- `16:9`: YouTube, `1920x1080`.

The dropdown should be data-driven so future presets do not require layout
changes.

### Status Bridge

Add a small status adapter that accepts events from existing operations:

```ts
{
  kind: "idle" | "ai" | "effect" | "insert" | "caption" | "ready" | "error",
  label: string,
  progress?: number,
  tone?: "blue" | "green" | "red" | "neutral"
}
```

This lets camera analysis, AI Director, bumper validation, caption toggles, and
render readiness speak through one consistent surface.

## Motion Stack

Recommended first stack:

- CSS transitions and keyframes for idle, hover, toggles, menus, and Ready.
- Web Animations API for programmatic sequences tied to state updates.

Reason: it keeps the generated local HTML light and dependency-free while the
component contract settles.

Optional later stack:

- GSAP Timeline for more complex chained motion when the component moves from
  prototype to polished production. GSAP timelines are useful for sequencing
  multiple animations under one controller.
- Rive for interactive brand-grade icons only after the final IA/FX/Ready
  behavior is fixed.
- Lottie or dotLottie only for non-interactive decorative animations. Avoid it
  for stateful controls that need app-driven transitions.

Reference docs checked:

- GSAP Timeline: https://gsap.com/docs/v3/GSAP/Timeline/
- MDN Web Animations API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API
- Rive runtimes: https://rive.app/runtimes
- Lottie web: https://github.com/airbnb/lottie-web

## Implementation Phases

### Phase 1 - Freeze The Prototype Contract

- Keep the current spike visually stable.
- Add a short README inside `prototypes/control-bar-spike`.
- Document query states used for visual review.
- Capture screenshots for default, format menu, FX menu, Insert menu, muted,
  AI loading, and Ready.

Acceptance:

- The spike opens by `file://`.
- The public API is documented.
- No app integration yet.

### Phase 2 - Production Asset Wrapper

- Create `tools/cutted/assets/control-bar/`.
- Copy or build the reviewed JS/CSS into production assets.
- Keep asset names deterministic: `control-bar.js` and `control-bar.css`.
- Add fallback behavior if assets are missing.

Acceptance:

- Generated HTML can load the assets locally.
- Missing assets do not break the existing editor.

### Phase 3 - Card Lifecycle Integration

- Mount the control surface only for the active/open card.
- Destroy it when the card closes or is replaced.
- Update it when platform, trim, effects, captions, bumpers, or render state
  change.
- Avoid mounting duplicate bars on repeated card opens.

Acceptance:

- One open card has one control surface.
- Closed cards stay cheap.
- Existing play, pause, trim, and timeline interactions still work.

### Phase 4 - Callback Wiring

- Volume callback updates only the preview player.
- Format callback switches active platform edit.
- AI callback triggers existing camera/AI analysis path.
- FX callback updates the current platform effect.
- Insert callback opens bumper selection/validation for Start or End.
- CC callback updates caption state.
- Ready callback marks the clip/platform as ready for render.
- Cancel callback returns from Ready to editable state.

Acceptance:

- Browser state and exported queue agree after each control change.
- Per-platform edits do not leak between TikTok/Facebook/YouTube.

### Phase 5 - Contextual Status Strip

- Add `status` to the control bar API.
- Emit short messages from AI, FX, Insert, CC, format, and Ready events.
- Show progress for AI/camera analysis when available.
- Show user-safe errors for invalid bumper dimensions or failed analysis.

Acceptance:

- The user can understand what is happening without opening a side panel.
- Error messages are short and do not expose raw payloads.

### Phase 6 - QA And Visual Polish

- Run focused browser checks on default, mobile-ish width, and narrow desktop.
- Verify keyboard navigation and `Escape` behavior.
- Verify `prefers-reduced-motion`.
- Verify screenshots against the spike states.
- Export a queue with FX, CC, format, Insert, and Ready set.
- Render one clip with and without bumpers.

Acceptance:

- No incoherent overlap with video controls or timeline handles.
- Final render still respects platform dimensions, captions, effects, and
  intro/outro bumpers.

## Files Expected To Change Later

Likely implementation files:

- `prototypes/control-bar-spike/README.md`
- `prototypes/control-bar-spike/script.js`
- `prototypes/control-bar-spike/styles.css`
- `tools/cutted/assets/control-bar/control-bar.js`
- `tools/cutted/assets/control-bar/control-bar.css`
- `tools/cutted/scripts/cutted.py`
- `tests/test_cutted_import_ui.py`

Do not mix this integration with unrelated live timeline changes unless the
integration point requires it.

## QA Matrix

| Area | Check |
| --- | --- |
| Visual | default, menu open, muted, AI loading, Ready |
| Layout | desktop, narrow desktop, mobile-ish width |
| Keyboard | tab order, enter/space, escape, focus visible |
| State | platform switch, FX switch, CC toggle, bumper slots |
| Render | no bumper, intro only, outro only, intro + outro |
| Fallback | missing assets, reduced motion, no backdrop-filter |
| Regression | existing timeline, existing render tab, existing effects panel |

## Risks

- The bar can cover timeline handles if mounted too low.
- Ready state can diverge from queue state if it is stored only in UI.
- Insert can confuse users if it looks like importing the main clip instead of
  adding intro/outro bumpers.
- Heavy motion can make the editor feel slow on generated local galleries.
- Multiple open cards can create duplicate event listeners if lifecycle is not
  explicit.

## Mitigations

- Keep app state outside the component.
- Mount one instance per active card and destroy it clearly.
- Use data-driven menu options.
- Start with CSS and Web Animations API before adding animation libraries.
- Gate loops and glows behind reduced-motion support.
- Keep production integration behind a graceful asset fallback.

## Definition Of Done

- The control bar has a documented public API.
- The generated CUTED workspace loads the control surface as local assets.
- The active card shows the bar between video and timeline.
- All controls map to existing app state or documented future callbacks.
- Status strip communicates AI, Insert, FX, CC, and Ready events.
- Exported queue reflects the selected platform, captions, effect, bumpers, and
  ready state.
- Visual and render smoke checks pass.
