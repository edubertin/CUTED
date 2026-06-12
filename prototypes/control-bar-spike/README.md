# CUTED Control Bar Spike

Visual/API spike for the CUTED control surface that will sit between the video
preview and the live timeline.

Open locally:

```text
file:///C:/Users/edube/OneDrive/Documentos/Cuted/prototypes/control-bar-spike/index.html
```

## Public API

```js
const controller = window.createCutedControlBar(container, {
  volume: 75,
  muted: false,
  aspectRatio: "9:16",
  aiStatus: "idle",
  effectStyle: "clean",
  captionsEnabled: true,
  bumpers: {
    intro: null,
    outro: null
  },
  ready: false,
  status: {
    kind: "ai",
    label: "AI analyzing frame safety...",
    progress: 42,
    tone: "blue"
  },
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
    onApproveClick(payload) {},
    onReadyCancel(payload) {},
    onDiscardClick(payload) {}
  }
});

controller.update({ ready: true });
controller.destroy();
```

The production integration should pass `mockBumpers: false`; Start/End clicks
then emit intent only, letting the CUTED app open the real bumper file picker.

## Demo Query States

```text
?formatMenu=open
?fx=open
?insert=open
?muted=on
?ready=on
?ai=loading
?cc=on
?intro=on&outro=on
```
