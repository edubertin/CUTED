import { Application, Container, Graphics } from "pixi.js";
import { gsap } from "gsap";
import { Draggable } from "gsap/Draggable";
import cutedLogoUrl from "../../../assets/brand/cuted-logo-transparent.png";
import "./timeline.css";

gsap.registerPlugin(Draggable);

const COLORS = {
  blue: 0x11a2cf,
  green: 0xafcf2a,
  white: 0xe7e7e8,
  black: 0x050505,
  surface: 0x0d0d0d,
  rail: 0x1b1f20
};

type LayerKind = "camera" | "effect";
type TimelineMode = "idle" | "editing" | "playing" | "scrubbing" | "trimming";
type TrimSide = "start" | "end";

interface TimelineKeyframe {
  id: string;
  layer: LayerKind;
  time: number;
  label: string;
  editable: boolean;
  intensity: number;
}

interface TimelineState {
  duration: number;
  trimStart: number;
  trimEnd: number;
  playhead: number;
  playing: boolean;
  muted: boolean;
  volume: number;
  volumeOpen: boolean;
  mode: TimelineMode;
  activeHandle: TrimSide | null;
  inspectorOpen: boolean;
  selectedKeyframeId: string | null;
  hoveredKeyframeId: string | null;
  peaks: readonly number[];
  keyframes: readonly TimelineKeyframe[];
}

interface TimelineMetrics {
  width: number;
  height: number;
  railX: number;
  railY: number;
  railWidth: number;
  railHeight: number;
  cameraY: number;
  effectY: number;
  waveformY: number;
}

interface TimelineElements {
  shell: HTMLElement;
  canvasHost: HTMLElement;
  startHandle: HTMLElement;
  endHandle: HTMLElement;
  startLogo: HTMLImageElement;
  endLogo: HTMLImageElement;
  popover: HTMLElement;
  popoverTitle: HTMLElement;
  popoverMeta: HTMLElement;
  popoverMeter: HTMLElement;
  playheadControl: HTMLButtonElement;
  playheadGlyph: HTMLElement;
  volumePopover: HTMLElement;
  volumeSlider: HTMLInputElement;
  muteButton: HTMLButtonElement;
  trimReadout: HTMLElement;
  playheadReadout: HTMLElement;
}

const elements = readElements();
elements.startLogo.src = cutedLogoUrl;
elements.endLogo.src = cutedLogoUrl;

const state: TimelineState = {
  duration: 72,
  trimStart: 3.8,
  trimEnd: 67.2,
  playhead: 18,
  playing: false,
  muted: false,
  volume: 0.72,
  volumeOpen: false,
  mode: "idle",
  activeHandle: null,
  inspectorOpen: false,
  selectedKeyframeId: "cam-2",
  hoveredKeyframeId: null,
  peaks: createPeaks(128),
  keyframes: [
    createKeyframe("cam-1", "camera", 7.1, "Centro seguro", true, 0.35),
    createKeyframe("cam-2", "camera", 14.5, "Punch-in", true, 0.72),
    createKeyframe("cam-3", "camera", 29.1, "Reacao", true, 0.62),
    createKeyframe("cam-4", "camera", 46.2, "Grupo", true, 0.44),
    createKeyframe("cam-5", "camera", 61.5, "Corte", false, 0.9),
    createKeyframe("fx-1", "effect", 10.2, "Glow leve", true, 0.38),
    createKeyframe("fx-2", "effect", 21.4, "VHS", true, 0.7),
    createKeyframe("fx-3", "effect", 36.9, "Filme antigo", true, 0.52),
    createKeyframe("fx-4", "effect", 54.4, "Impacto", true, 0.82)
  ]
};

let lastPlaybackTick = performance.now();
let audioContext: AudioContext | null = null;

const app = new Application();
await app.init({
  resizeTo: elements.canvasHost,
  backgroundAlpha: 0,
  antialias: true,
  autoDensity: true,
  resolution: Math.min(window.devicePixelRatio, 2)
});

elements.canvasHost.appendChild(app.canvas);

const scene = new Container();
const graphics = new Graphics();
scene.addChild(graphics);
app.stage.addChild(scene);

const renderTimeline = (): void => {
  const metrics = getMetrics(elements.canvasHost);
  const now = performance.now();
  updatePlayback(now, state);
  const pulse = now / 1000;
  graphics.clear();
  drawFrame(graphics, metrics, pulse);
  drawInactiveMasks(graphics, metrics, state, pulse);
  drawWaveform(graphics, metrics, state, pulse);
  drawRails(graphics, metrics, state, pulse);
  drawKeyframes(graphics, metrics, state, pulse);
  drawPlayhead(graphics, metrics, state, pulse);
  placeHandles(metrics, state, elements);
  placePlayheadControl(metrics, state, elements);
  updateReadouts(state, elements);
  updateTransportControls(state, elements);
  updatePopover(metrics, state, elements);
  updateShellMode(state, elements);
};

app.ticker.add(renderTimeline);
bindShellInteractions(elements, state, renderTimeline);
bindHandleDrag(elements, state, renderTimeline);
bindTransportControls(elements, state, renderTimeline);
renderTimeline();

function readElements(): TimelineElements {
  return {
    shell: requireElement("timeline-shell", HTMLElement),
    canvasHost: requireElement("timeline-canvas", HTMLElement),
    startHandle: requireElement("start-handle", HTMLElement),
    endHandle: requireElement("end-handle", HTMLElement),
    startLogo: requireElement("start-logo", HTMLImageElement),
    endLogo: requireElement("end-logo", HTMLImageElement),
    popover: requireElement("keyframe-popover", HTMLElement),
    popoverTitle: requireElement("popover-title", HTMLElement),
    popoverMeta: requireElement("popover-meta", HTMLElement),
    popoverMeter: requireElement("popover-meter", HTMLElement),
    playheadControl: requireElement("playhead-control", HTMLButtonElement),
    playheadGlyph: requireElement("playhead-glyph", HTMLElement),
    volumePopover: requireElement("volume-popover", HTMLElement),
    volumeSlider: requireElement("volume-slider", HTMLInputElement),
    muteButton: requireElement("mute-button", HTMLButtonElement),
    trimReadout: requireElement("trim-readout", HTMLElement),
    playheadReadout: requireElement("playhead-readout", HTMLElement)
  };
}

function requireElement<T extends HTMLElement>(id: string, ctor: { new (): T }): T {
  const element = document.getElementById(id);
  if (!(element instanceof ctor)) {
    throw new Error(`Missing expected element: ${id}`);
  }
  return element;
}

function createKeyframe(
  id: string,
  layer: LayerKind,
  time: number,
  label: string,
  editable: boolean,
  intensity: number
): TimelineKeyframe {
  return { id, layer, time, label, editable, intensity };
}

function createPeaks(count: number): readonly number[] {
  return Array.from({ length: count }, (_, index) => {
    const wave = Math.sin(index * 0.39) * 0.38 + Math.sin(index * 0.13) * 0.24;
    const accent = index % 17 === 0 ? 0.3 : 0;
    return clamp(0.22 + Math.abs(wave) + accent, 0.16, 1);
  });
}

function getMetrics(host: HTMLElement): TimelineMetrics {
  const width = Math.max(host.clientWidth, 320);
  const height = Math.max(host.clientHeight, 230);
  const compact = width < 700;
  const railX = compact ? 82 : 118;
  const railWidth = Math.max(width - railX * 2, compact ? 180 : 420);
  const railY = Math.round(height * 0.22);
  const railHeight = Math.round(height * 0.56);
  return {
    width,
    height,
    railX,
    railY,
    railWidth,
    railHeight,
    cameraY: railY + 44,
    waveformY: railY + Math.round(railHeight * 0.5),
    effectY: railY + railHeight - 44
  };
}

function drawFrame(g: Graphics, m: TimelineMetrics, pulse: number): void {
  const energy = 0.18 + Math.sin(pulse * 1.4) * 0.05;
  g.roundRect(m.railX - 28, m.railY - 34, m.railWidth + 56, m.railHeight + 68, 18)
    .fill({ color: COLORS.blue, alpha: 0.025 + energy * 0.04 });
  g.roundRect(m.railX - 16, m.railY - 22, m.railWidth + 32, m.railHeight + 44, 10)
    .fill({ color: COLORS.black, alpha: 0.72 })
    .stroke({ color: COLORS.blue, alpha: 0.72, width: 2 });
  g.roundRect(m.railX - 7, m.railY - 13, m.railWidth + 14, m.railHeight + 26, 7)
    .stroke({ color: COLORS.white, alpha: 0.1, width: 1 });
  g.moveTo(m.railX - 4, m.railY - 12).lineTo(m.railX + m.railWidth + 4, m.railY - 12)
    .stroke({ color: COLORS.white, alpha: 0.12, width: 1 });
}

function drawInactiveMasks(g: Graphics, m: TimelineMetrics, s: TimelineState, pulse: number): void {
  const startX = timeToX(s.trimStart, m, s.duration);
  const endX = timeToX(s.trimEnd, m, s.duration);
  g.rect(m.railX - 16, m.railY - 22, startX - m.railX + 16, m.railHeight + 44).fill({ color: COLORS.black, alpha: 0.58 });
  g.rect(endX, m.railY - 22, m.railX + m.railWidth - endX + 16, m.railHeight + 44).fill({ color: COLORS.black, alpha: 0.58 });
  g.roundRect(startX, m.railY - 21, endX - startX, m.railHeight + 42, 7)
    .fill({ color: COLORS.blue, alpha: 0.025 })
    .stroke({ color: COLORS.green, alpha: 0.2 + Math.sin(pulse * 1.8) * 0.04, width: 1 });
  g.roundRect(startX - 2, m.railY - 23, endX - startX + 4, m.railHeight + 46, 9)
    .stroke({ color: COLORS.blue, alpha: 0.18, width: 4 });
  if (s.mode === "trimming") {
    const handleX = s.activeHandle === "start" ? startX : endX;
    const color = s.activeHandle === "start" ? COLORS.blue : COLORS.green;
    g.circle(handleX, m.waveformY, 64 + Math.sin(pulse * 4) * 5).fill({ color, alpha: 0.055 });
  }
}

function drawWaveform(g: Graphics, m: TimelineMetrics, s: TimelineState, pulse: number): void {
  const step = m.railWidth / Math.max(s.peaks.length - 1, 1);
  const playheadX = timeToX(s.playhead, m, s.duration);
  const volumeEnergy = s.muted ? 0.42 : 0.72 + s.volume * 0.38;
  s.peaks.forEach((peak, index) => {
    const x = m.railX + index * step;
    const drift = Math.sin(pulse * 2.8 + index * 0.18) * 0.06;
    const height = peak * 78 * (1 + drift);
    const proximity = clamp(1 - Math.abs(x - playheadX) / 118, 0, 1);
    const playingBoost = s.playing ? proximity * 0.34 : 0;
    const alpha = (isInsideTrim(x, m, s) ? 0.64 + playingBoost : 0.18) * volumeEnergy;
    if (index % 3 === 0 && isInsideTrim(x, m, s)) {
      g.roundRect(x - 3.8, m.waveformY - height * 0.5 - 2, 7.6, height + 4, 4)
        .fill({ color: COLORS.green, alpha: (0.06 + playingBoost * 0.16) * volumeEnergy });
    }
    g.roundRect(x - 2.2, m.waveformY - height * 0.5, 4.4, height, 3).fill({ color: COLORS.green, alpha });
  });
}

function drawRails(g: Graphics, m: TimelineMetrics, s: TimelineState, pulse: number): void {
  drawRail(g, m, s, m.cameraY, COLORS.blue, 0.92, pulse);
  drawRail(g, m, s, m.effectY, COLORS.green, 0.86, pulse + 0.6);
  g.moveTo(m.railX, m.waveformY).lineTo(m.railX + m.railWidth, m.waveformY).stroke({ color: COLORS.white, alpha: 0.1, width: 1 });
}

function drawRail(g: Graphics, m: TimelineMetrics, s: TimelineState, y: number, color: number, alpha: number, pulse: number): void {
  const startX = timeToX(s.trimStart, m, s.duration);
  const endX = timeToX(s.trimEnd, m, s.duration);
  g.moveTo(m.railX, y).lineTo(m.railX + m.railWidth, y).stroke({ color: COLORS.rail, alpha: 1, width: 7 });
  g.moveTo(startX, y).lineTo(endX, y).stroke({ color, alpha: 0.16, width: 13 });
  g.moveTo(startX, y).lineTo(endX, y).stroke({ color, alpha: alpha + Math.sin(pulse * 2) * 0.06, width: 3 });
}

function drawKeyframes(g: Graphics, m: TimelineMetrics, s: TimelineState, pulse: number): void {
  s.keyframes.forEach((keyframe) => {
    const x = timeToX(keyframe.time, m, s.duration);
    const y = keyframe.layer === "camera" ? m.cameraY : m.effectY;
    const color = keyframe.layer === "camera" ? COLORS.blue : COLORS.green;
    const muted = keyframe.time < s.trimStart || keyframe.time > s.trimEnd;
    drawKeyframe(g, x, y, color, keyframe, {
      hovered: s.hoveredKeyframeId === keyframe.id,
      selected: s.selectedKeyframeId === keyframe.id,
      muted,
      pulse
    });
  });
}

function drawKeyframe(
  g: Graphics,
  x: number,
  y: number,
  color: number,
  keyframe: TimelineKeyframe,
  visual: { hovered: boolean; selected: boolean; muted: boolean; pulse: number }
): void {
  const isCamera = keyframe.layer === "camera";
  const height = isCamera ? 52 : 44;
  const width = isCamera ? 13 : 11;
  const visibility = visual.muted ? 0.34 : 1;
  const aura = visual.selected ? 0.36 + Math.sin(visual.pulse * 3) * 0.08 : visual.hovered ? 0.24 : 0.08;
  const haloPad = visual.selected ? 12 : visual.hovered ? 10 : 8;
  g.roundRect(x - width - haloPad, y - height * 0.5 - haloPad, width * 2 + haloPad * 2, height + haloPad * 2, 9)
    .fill({ color, alpha: aura * 0.22 * visibility });
  g.roundRect(x - width - 4, y - height * 0.5 - 4, width * 2 + 8, height + 8, 7)
    .stroke({ color, alpha: aura * visibility, width: 2 });
  g.roundRect(x - width, y - height * 0.5, width * 2, height, 4)
    .fill({ color: COLORS.black, alpha: keyframe.editable ? 0.84 : 0.5 })
    .stroke({ color, alpha: (visual.selected ? 1 : 0.84) * visibility, width: visual.selected ? 3 : 2 });
  g.roundRect(x - width + 4, y - height * 0.5 + 4, Math.max(width * 2 - 8, 4), 5, 3)
    .fill({ color: COLORS.white, alpha: keyframe.editable ? 0.2 : 0.08 });
  g.circle(x, y - height * 0.5 - 9, visual.selected ? 3.4 : 2.4)
    .fill({ color, alpha: (keyframe.editable ? 0.9 : 0.42) * visibility });
}

function drawPlayhead(g: Graphics, m: TimelineMetrics, s: TimelineState, pulse: number): void {
  const x = timeToX(s.playhead, m, s.duration);
  const glow = (s.playing ? 0.24 : 0.14) + Math.sin(pulse * 4) * 0.05;
  if (s.playing) {
    g.circle(x, m.waveformY, 68 + Math.sin(pulse * 3) * 6).fill({ color: COLORS.blue, alpha: 0.035 });
    g.moveTo(x - 26, m.waveformY).lineTo(x + 26, m.waveformY).stroke({ color: COLORS.white, alpha: 0.2, width: 2 });
  }
  g.moveTo(x, m.railY - 31).lineTo(x, m.railY + m.railHeight + 31).stroke({ color: COLORS.blue, alpha: glow, width: s.playing ? 16 : 12 });
  g.moveTo(x, m.railY - 31).lineTo(x, m.railY + m.railHeight + 31).stroke({ color: COLORS.white, alpha: 0.8, width: 2 });
  g.circle(x, m.railY - 31, 9 + Math.sin(pulse * 4) * 1.2).fill({ color: COLORS.white, alpha: 0.08 });
  g.circle(x, m.railY - 31, 5).fill({ color: COLORS.white, alpha: 0.95 });
}

function updatePlayback(now: number, state: TimelineState): void {
  const elapsed = (now - lastPlaybackTick) / 1000;
  lastPlaybackTick = now;
  if (!state.playing) return;
  state.playhead += elapsed;
  if (state.playhead >= state.trimEnd) {
    state.playhead = state.trimStart;
    playUiTone("loop", state);
  }
}

function bindTransportControls(elements: TimelineElements, state: TimelineState, render: () => void): void {
  elements.playheadControl.addEventListener("click", (event) => {
    event.stopPropagation();
    state.playing = !state.playing;
    state.mode = state.playing ? "playing" : "idle";
    state.inspectorOpen = false;
    if (state.playhead < state.trimStart || state.playhead > state.trimEnd) {
      state.playhead = state.trimStart;
    }
    playUiTone(state.playing ? "play" : "pause", state);
    render();
  });
  elements.playheadControl.addEventListener("contextmenu", (event) => {
    event.preventDefault();
    event.stopPropagation();
    state.volumeOpen = !state.volumeOpen;
    render();
  });
  elements.volumeSlider.addEventListener("input", () => {
    state.volume = clamp(Number(elements.volumeSlider.value) / 100, 0, 1);
    state.muted = state.volume === 0;
    playUiTone("volume", state);
    render();
  });
  elements.muteButton.addEventListener("click", (event) => {
    event.stopPropagation();
    state.muted = !state.muted;
    playUiTone("mute", state);
    render();
  });
}

function bindShellInteractions(elements: TimelineElements, state: TimelineState, render: () => void): void {
  elements.shell.addEventListener("pointerdown", (event) => {
    if (isHandleTarget(event.target)) return;
    if (isTransportTarget(event.target)) return;
    state.playing = false;
    state.inspectorOpen = false;
    state.volumeOpen = false;
    state.mode = "scrubbing";
    state.playhead = xToTime(event.clientX, getMetrics(elements.canvasHost), state.duration);
    render();
  });
  elements.shell.addEventListener("pointermove", (event) => {
    if (isHandleTarget(event.target)) return;
    const keyframe = nearestKeyframe(event.clientX, event.clientY, elements, state);
    state.hoveredKeyframeId = keyframe?.id ?? null;
    elements.shell.classList.toggle("is-over-keyframe", Boolean(keyframe));
    render();
  });
  elements.shell.addEventListener("pointerleave", () => {
    state.hoveredKeyframeId = null;
    elements.shell.classList.remove("is-over-keyframe");
    render();
  });
  elements.shell.addEventListener("contextmenu", (event) => {
    event.preventDefault();
    const keyframe = nearestKeyframe(event.clientX, event.clientY, elements, state);
    if (keyframe?.editable) openInspector(keyframe, state, render);
    if (!keyframe) {
      state.inspectorOpen = false;
      state.mode = "idle";
      render();
    }
  });
}

function bindHandleDrag(elements: TimelineElements, state: TimelineState, render: () => void): void {
  const updateStart = (clientX: number): void => {
    const time = xToTime(clientX, getMetrics(elements.canvasHost), state.duration);
    state.trimStart = clamp(snapTrimTime(time, "start", state), 0, state.trimEnd - 2);
    state.playhead = Math.max(state.playhead, state.trimStart);
    render();
  };
  const updateEnd = (clientX: number): void => {
    const time = xToTime(clientX, getMetrics(elements.canvasHost), state.duration);
    state.trimEnd = clamp(snapTrimTime(time, "end", state), state.trimStart + 2, state.duration);
    state.playhead = Math.min(state.playhead, state.trimEnd);
    render();
  };
  createDraggable(elements.startHandle, "start", state, updateStart);
  createDraggable(elements.endHandle, "end", state, updateEnd);
}

function createDraggable(
  handle: HTMLElement,
  side: TrimSide,
  state: TimelineState,
  update: (clientX: number) => void
): void {
  Draggable.create(handle, {
    type: "x",
    trigger: handle,
    onPress() {
      handle.classList.add("is-dragging");
      state.playing = false;
      state.mode = "trimming";
      state.activeHandle = side;
      state.inspectorOpen = false;
      state.volumeOpen = false;
    },
    onDrag() {
      update(this.pointerX);
    },
    onRelease() {
      handle.classList.remove("is-dragging");
      state.mode = "idle";
      state.activeHandle = null;
      gsap.set(handle, { x: 0 });
    }
  });
}

function nearestKeyframe(clientX: number, clientY: number, elements: TimelineElements, state: TimelineState): TimelineKeyframe | null {
  const m = getMetrics(elements.canvasHost);
  const rect = elements.canvasHost.getBoundingClientRect();
  const x = clientX - rect.left;
  const y = clientY - rect.top;
  return state.keyframes.find((keyframe) => {
    const kx = timeToX(keyframe.time, m, state.duration);
    const ky = keyframe.layer === "camera" ? m.cameraY : m.effectY;
    return Math.abs(kx - x) <= 18 && Math.abs(ky - y) <= 42;
  }) ?? null;
}

function openInspector(keyframe: TimelineKeyframe, state: TimelineState, render: () => void): void {
  state.playing = false;
  state.volumeOpen = false;
  state.selectedKeyframeId = keyframe.id;
  state.inspectorOpen = true;
  state.mode = "editing";
  render();
}

function selectedKeyframe(state: TimelineState): TimelineKeyframe | null {
  return state.keyframes.find((keyframe) => keyframe.id === state.selectedKeyframeId) ?? null;
}

function snapTrimTime(time: number, side: TrimSide, state: TimelineState): number {
  const candidates = state.keyframes
    .filter((keyframe) => keyframe.time > state.trimStart && keyframe.time < state.trimEnd)
    .map((keyframe) => keyframe.time);
  const nearest = candidates.reduce<number | null>((best, candidate) => {
    if (best === null) return candidate;
    return Math.abs(candidate - time) < Math.abs(best - time) ? candidate : best;
  }, null);
  if (nearest === null || Math.abs(nearest - time) > 0.9) return time;
  return side === "start" ? nearest - 0.12 : nearest + 0.12;
}

function placeHandles(m: TimelineMetrics, s: TimelineState, elements: TimelineElements): void {
  const startX = timeToX(s.trimStart, m, s.duration);
  const endX = timeToX(s.trimEnd, m, s.duration);
  setHandlePosition(elements.startHandle, startX - 96, m.waveformY - 106);
  setHandlePosition(elements.endHandle, endX - 34, m.waveformY - 106);
}

function placePlayheadControl(m: TimelineMetrics, s: TimelineState, elements: TimelineElements): void {
  const x = timeToX(s.playhead, m, s.duration);
  const y = m.railY - 46;
  elements.playheadControl.style.left = `${x - 16}px`;
  elements.playheadControl.style.top = `${y - 16}px`;
  elements.volumePopover.style.left = `${clamp(x - 74, 12, m.width - 160)}px`;
  elements.volumePopover.style.top = `${y + 26}px`;
}

function setHandlePosition(handle: HTMLElement, x: number, y: number): void {
  handle.style.left = `${x}px`;
  handle.style.top = `${y}px`;
}

function updatePopover(m: TimelineMetrics, s: TimelineState, elements: TimelineElements): void {
  const keyframe = selectedKeyframe(s);
  elements.popover.hidden = !s.inspectorOpen || keyframe === null;
  if (!s.inspectorOpen || keyframe === null) return;
  const x = timeToX(keyframe.time, m, s.duration);
  const y = keyframe.layer === "camera" ? m.cameraY : m.effectY;
  const left = clamp(x - 118, 16, m.width - 252);
  const top = clamp(y - 136, 14, m.height - 160);
  elements.popover.dataset.layer = keyframe.layer;
  elements.popover.style.left = `${left}px`;
  elements.popover.style.top = `${top}px`;
  elements.popoverTitle.textContent = keyframe.label;
  elements.popoverMeta.textContent = keyframe.layer === "camera" ? "Camera keyframe" : "Effect keyframe";
  elements.popoverMeter.style.width = `${Math.round(keyframe.intensity * 100)}%`;
}

function updateReadouts(state: TimelineState, elements: TimelineElements): void {
  elements.trimReadout.textContent = `${formatTime(state.trimStart)} - ${formatTime(state.trimEnd)}`;
  elements.playheadReadout.textContent = formatTime(state.playhead);
}

function updateTransportControls(state: TimelineState, elements: TimelineElements): void {
  elements.playheadControl.classList.toggle("is-playing", state.playing);
  elements.playheadControl.classList.toggle("is-muted", state.muted);
  elements.playheadControl.setAttribute("aria-label", state.playing ? "Pausar preview" : "Tocar preview");
  elements.playheadGlyph.dataset.state = state.playing ? "pause" : "play";
  elements.volumePopover.hidden = !state.volumeOpen;
  elements.volumeSlider.value = String(Math.round(state.volume * 100));
  elements.muteButton.textContent = state.muted ? "MUTE" : "VOL";
  elements.muteButton.classList.toggle("is-muted", state.muted);
}

function updateShellMode(state: TimelineState, elements: TimelineElements): void {
  elements.shell.dataset.mode = state.mode;
  elements.shell.dataset.activeHandle = state.activeHandle ?? "";
}

function isHandleTarget(target: EventTarget | null): boolean {
  return target instanceof Element && Boolean(target.closest(".trim-handle"));
}

function isTransportTarget(target: EventTarget | null): boolean {
  return target instanceof Element && Boolean(target.closest(".playhead-control, .volume-popover"));
}

function playUiTone(kind: "loop" | "mute" | "pause" | "play" | "volume", state: TimelineState): void {
  if (state.muted && kind !== "mute") return;
  audioContext ??= new AudioContext();
  if (audioContext.state === "suspended") {
    void audioContext.resume();
  }
  const oscillator = audioContext.createOscillator();
  const gain = audioContext.createGain();
  const frequency = { loop: 520, mute: 190, pause: 240, play: 420, volume: 660 }[kind];
  oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
  oscillator.type = "sine";
  gain.gain.setValueAtTime(0.0001, audioContext.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.018 * Math.max(state.volume, 0.18), audioContext.currentTime + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.075);
  oscillator.connect(gain);
  gain.connect(audioContext.destination);
  oscillator.start();
  oscillator.stop(audioContext.currentTime + 0.08);
}

function isInsideTrim(x: number, m: TimelineMetrics, s: TimelineState): boolean {
  return x >= timeToX(s.trimStart, m, s.duration) && x <= timeToX(s.trimEnd, m, s.duration);
}

function timeToX(time: number, metrics: TimelineMetrics, duration: number): number {
  return metrics.railX + clamp(time / duration, 0, 1) * metrics.railWidth;
}

function xToTime(clientX: number, metrics: TimelineMetrics, duration: number): number {
  const rect = elements.canvasHost.getBoundingClientRect();
  return clamp(((clientX - rect.left - metrics.railX) / metrics.railWidth) * duration, 0, duration);
}

function formatTime(totalSeconds: number): string {
  const seconds = Math.round(totalSeconds);
  const minutes = Math.floor(seconds / 60);
  return `${String(minutes).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
