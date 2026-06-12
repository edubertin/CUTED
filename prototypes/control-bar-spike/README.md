# CUTED Control Bar Spike

Visual/API spike for the CUTED control surface that will sit between the video
preview and the live timeline.

Open locally:

```text
file:///C:/Users/edube/OneDrive/Documentos/Cuted/prototypes/control-bar-spike/index.html
```

## Public Contract

The spike exposes one browser global:

```js
const controller = window.createCutedControlBar(container, options);
```

The component is intentionally state-light. Production should keep the active
card/platform edit as the source of truth, pass state into the bar, and listen
for user intent through callbacks or the `statechange` event.

## Options

```js
const controller = window.createCutedControlBar(container, {
  volume: 75,
  muted: false,
  aspectRatio: "9:16",
  aiStatus: "idle",
  effectStyle: "clean",
  captionsEnabled: false,
  bumpers: {
    intro: null,
    outro: null
  },
  ready: false,
  discarded: false,
  status: null,
  mockBumpers: true,
  callbacks: {
    onVolumeChange(payload) {},
    onFormatChange(payload) {},
    onAiClick(payload) {},
    onAiStatusChange(payload) {},
    onEffectClick(payload) {},
    onEffectStyleChange(payload) {},
    onInsertClick(payload) {},
    onBumperClick(payload) {},
    onBumperRemove(payload) {},
    onBumperChange(payload) {},
    onCaptionToggle(payload) {},
    onApproveClick(state) {},
    onDiscardClick(state) {},
    onReadyCancel(state) {},
    onStateChange(state) {}
  }
});
```

Use `mockBumpers: false` in production. Start/End clicks should emit intent and
let the CUTED app open the real bumper file picker.

## State

```js
{
  volume: 75,
  muted: false,
  aspectRatio: "9:16",
  aiStatus: "idle", // "idle" | "loading" | "active"
  effectStyle: "clean", // "clean" | "vhs" | "film" | "grain"
  captionsEnabled: false,
  bumpers: {
    intro: null, // or { slot: "intro", label: "start-bumper.mp4", duration: 1.8 }
    outro: null
  },
  ready: false,
  discarded: false,
  status: {
    kind: "ai",
    label: "AI analyzing frame safety...",
    progress: 42,
    persistent: false,
    tone: "blue" // "blue" | "green" | "red" | "neutral"
  }
}
```

`ready` and `discarded` are persistent locked states. When either one is active,
the editing controls are visually and functionally locked. The small right-side
X restores editing.

## Controller Methods

```js
controller.getState();
controller.update(nextState);
controller.setStatus(status, holdMs);
controller.clearStatus();
controller.setReady(true);
controller.setDiscarded(true);
controller.reset(nextState);
controller.subscribe(listener);
controller.destroy();
```

`subscribe(listener)` returns an unsubscribe function. The same state is also
emitted as a bubbling DOM event:

```js
container.addEventListener("cuted-control-bar:statechange", event => {
  console.log(event.detail);
});
```

## Demo Query States

```text
?formatMenu=open
?fx=open
?insert=open
?muted=on
?ready=on
?discarded=on
?ai=loading
?cc=on
?intro=on&outro=on
?status=error
```

## Production Asset Target

When approved, copy/adapt this spike into:

```text
tools/cutted/assets/control-bar/control-bar.js
tools/cutted/assets/control-bar/control-bar.css
```

The generated review workspace already expects copied assets under:

```text
assets/control-bar/control-bar.js
assets/control-bar/control-bar.css
```
