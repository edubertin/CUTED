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

const HANDLE_ANCHOR = {
  desktop: {
    endX: 0,
    endY: 98,
    startX: 76,
    startY: 104
  },
  mobile: {
    endX: 0,
    endY: 73,
    startX: 55,
    startY: 78
  }
};

type LayerKind = "camera" | "effect";
type TimelineMode = "idle" | "editing" | "playing" | "scrubbing" | "trimming";
type TrimSide = "start" | "end";

interface CutParticle {
  color: number;
  life: number;
  maxLife: number;
  size: number;
  vx: number;
  vy: number;
  x: number;
  y: number;
}

interface CutPulse {
  age: number;
  color: number;
  time: number;
}

interface PlayheadTrace {
  age: number;
  strength: number;
  time: number;
}

interface SnapPulse {
  age: number;
  color: number;
  keyframeTime: number;
  side: TrimSide;
  trimTime: number;
}

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
  volumeStepper: HTMLElement;
  volumeDown: HTMLButtonElement;
  volumeUp: HTMLButtonElement;
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
let lastRenderTick = performance.now();
let audioContext: AudioContext | null = null;
let cutPulse: CutPulse | null = null;
let snapPulse: SnapPulse | null = null;
const cutParticles: CutParticle[] = [];
const playheadTrail: PlayheadTrace[] = [];

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
  const delta = clamp((now - lastRenderTick) / 1000, 0.001, 0.04);
  lastRenderTick = now;
  updatePlayback(now, state);
  updatePlayheadTrail(delta, state);
  const pulse = now / 1000;
  graphics.clear();
  drawFrame(graphics, metrics, pulse);
  drawInactiveMasks(graphics, metrics, state, pulse);
  drawWaveform(graphics, metrics, state, pulse);
  drawRails(graphics, metrics, state, pulse);
  drawInspectorFocus(graphics, metrics, state, pulse);
  drawMagneticField(graphics, metrics, state, pulse);
  drawKeyframes(graphics, metrics, state, pulse);
  drawInspectorTether(graphics, metrics, state, pulse);
  drawSnapRitual(graphics, metrics, state, delta, pulse);
  drawPlayheadTrail(graphics, metrics, state);
  drawPlayhead(graphics, metrics, state, pulse);
  drawCutPulse(graphics, metrics, state, delta);
  drawCutParticles(graphics, cutParticles, delta);
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
    volumeStepper: requireElement("volume-stepper", HTMLElement),
    volumeDown: requireElement("volume-down", HTMLButtonElement),
    volumeUp: requireElement("volume-up", HTMLButtonElement),
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
  drawSelectionTexture(g, m, startX, endX, pulse);
  g.roundRect(startX - 2, m.railY - 23, endX - startX + 4, m.railHeight + 46, 9)
    .stroke({ color: COLORS.blue, alpha: 0.18, width: 4 });
  if (s.mode === "trimming") {
    const handleX = s.activeHandle === "start" ? startX : endX;
    const color = s.activeHandle === "start" ? COLORS.blue : COLORS.green;
    g.circle(handleX, m.waveformY, 64 + Math.sin(pulse * 4) * 5).fill({ color, alpha: 0.055 });
  }
}

function drawSelectionTexture(g: Graphics, m: TimelineMetrics, startX: number, endX: number, pulse: number): void {
  const top = m.railY - 17;
  const bottom = m.railY + m.railHeight + 17;
  const textureWidth = Math.max(endX - startX, 0);
  for (let offset = 12; offset < textureWidth; offset += 18) {
    const x = startX + offset;
    const shimmer = 0.5 + Math.sin(pulse * 1.2 + offset * 0.11) * 0.5;
    g.moveTo(x, top).lineTo(x + 18, bottom)
      .stroke({ color: COLORS.white, alpha: 0.012 + shimmer * 0.01, width: 1 });
  }
  for (let offset = 24; offset < textureWidth; offset += 46) {
    const x = startX + offset;
    const y = top + ((offset * 7) % Math.max(bottom - top, 1));
    g.circle(x, y, 1.1).fill({ color: COLORS.blue, alpha: 0.07 });
  }
}

function drawWaveform(g: Graphics, m: TimelineMetrics, s: TimelineState, pulse: number): void {
  const step = m.railWidth / Math.max(s.peaks.length - 1, 1);
  const playheadX = timeToX(s.playhead, m, s.duration);
  const startX = timeToX(s.trimStart, m, s.duration);
  const endX = timeToX(s.trimEnd, m, s.duration);
  const activeX = s.activeHandle === "start" ? startX : endX;
  const volumeEnergy = s.muted ? 0.42 : 0.72 + s.volume * 0.38;
  s.peaks.forEach((peak, index) => {
    const x = m.railX + index * step;
    const drift = Math.sin(pulse * 2.8 + index * 0.18) * 0.06;
    const trimPressure = s.mode === "trimming" ? clamp(1 - Math.abs(x - activeX) / 140, 0, 1) : 0;
    const height = peak * 78 * (1 + drift + trimPressure * 0.22);
    const proximity = clamp(1 - Math.abs(x - playheadX) / 118, 0, 1);
    const playingBoost = s.playing ? proximity * 0.34 : 0;
    const alpha = (isInsideTrim(x, m, s) ? 0.64 + playingBoost + trimPressure * 0.2 : 0.18) * volumeEnergy;
    if (index % 3 === 0 && isInsideTrim(x, m, s)) {
      g.roundRect(x - 3.8, m.waveformY - height * 0.5 - 2, 7.6, height + 4, 4)
        .fill({ color: COLORS.green, alpha: (0.06 + playingBoost * 0.16 + trimPressure * 0.08) * volumeEnergy });
    }
    if (trimPressure > 0.02) {
      g.circle(x, m.waveformY, 10 + trimPressure * 22).fill({ color: COLORS.white, alpha: trimPressure * 0.012 });
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

function drawInspectorFocus(g: Graphics, m: TimelineMetrics, s: TimelineState, pulse: number): void {
  const keyframe = selectedKeyframe(s);
  if (!s.inspectorOpen || keyframe === null) return;
  const x = timeToX(keyframe.time, m, s.duration);
  const y = keyframe.layer === "camera" ? m.cameraY : m.effectY;
  const color = keyframe.layer === "camera" ? COLORS.blue : COLORS.green;
  const breathe = 0.5 + Math.sin(pulse * 2.4) * 0.5;
  g.roundRect(m.railX - 16, m.railY - 22, m.railWidth + 32, m.railHeight + 44, 10)
    .fill({ color: COLORS.black, alpha: 0.18 });
  g.circle(x, y, 76 + breathe * 16).fill({ color, alpha: 0.05 });
  g.circle(x, y, 32 + breathe * 8).stroke({ color, alpha: 0.18, width: 2 });
  g.moveTo(x - 46, y).lineTo(x + 46, y).stroke({ color, alpha: 0.32, width: 2 });
}

function drawMagneticField(g: Graphics, m: TimelineMetrics, s: TimelineState, pulse: number): void {
  if (s.mode !== "trimming" || s.activeHandle === null) return;
  const activeTime = s.activeHandle === "start" ? s.trimStart : s.trimEnd;
  const keyframe = nearestTrimKeyframe(activeTime, s);
  if (keyframe === null) return;
  const handleX = timeToX(activeTime, m, s.duration);
  const keyframeX = timeToX(keyframe.time, m, s.duration);
  const y = keyframe.layer === "camera" ? m.cameraY : m.effectY;
  const distance = Math.abs(keyframeX - handleX);
  const pull = clamp(1 - distance / 120, 0, 1);
  const color = keyframe.layer === "camera" ? COLORS.blue : COLORS.green;
  if (pull <= 0) return;
  g.moveTo(handleX, m.waveformY)
    .bezierCurveTo(handleX + (keyframeX - handleX) * 0.28, m.waveformY, keyframeX - 18, y, keyframeX, y)
    .stroke({ color: COLORS.white, alpha: 0.16 * pull, width: 7 * pull });
  g.moveTo(handleX, m.waveformY)
    .bezierCurveTo(handleX + (keyframeX - handleX) * 0.28, m.waveformY, keyframeX - 18, y, keyframeX, y)
    .stroke({ color, alpha: (0.24 + Math.sin(pulse * 8) * 0.05) * pull, width: 2 });
  g.circle(keyframeX, y, 20 + pull * 24).fill({ color, alpha: 0.04 * pull });
}

function nearestTrimKeyframe(activeTime: number, s: TimelineState): TimelineKeyframe | null {
  return s.keyframes.reduce<TimelineKeyframe | null>((best, keyframe) => {
    if (!keyframe.editable) return best;
    const distance = Math.abs(keyframe.time - activeTime);
    if (distance > 7) return best;
    if (best === null) return keyframe;
    return distance < Math.abs(best.time - activeTime) ? keyframe : best;
  }, null);
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

function drawInspectorTether(g: Graphics, m: TimelineMetrics, s: TimelineState, pulse: number): void {
  const keyframe = selectedKeyframe(s);
  if (!s.inspectorOpen || keyframe === null) return;
  const x = timeToX(keyframe.time, m, s.duration);
  const y = keyframe.layer === "camera" ? m.cameraY : m.effectY;
  const target = inspectorAnchorPoint(keyframe, m, s);
  const color = keyframe.layer === "camera" ? COLORS.blue : COLORS.green;
  const phase = 0.5 + Math.sin(pulse * 5.4) * 0.5;
  g.moveTo(x, y)
    .bezierCurveTo(x, y - 42, target.x - 48, target.y + 28, target.x, target.y)
    .stroke({ color: COLORS.white, alpha: 0.1 + phase * 0.05, width: 9 });
  g.moveTo(x, y)
    .bezierCurveTo(x, y - 42, target.x - 48, target.y + 28, target.x, target.y)
    .stroke({ color, alpha: 0.34 + phase * 0.12, width: 2 });
  g.circle(x, y, 20 + phase * 10).fill({ color, alpha: 0.035 + phase * 0.025 });
}

function inspectorAnchorPoint(keyframe: TimelineKeyframe, m: TimelineMetrics, s: TimelineState): { x: number; y: number } {
  const x = timeToX(keyframe.time, m, s.duration);
  const y = keyframe.layer === "camera" ? m.cameraY : m.effectY;
  return {
    x: clamp(x, 134, m.width - 134),
    y: clamp(y - 22, 24, m.height - 58)
  };
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

function drawPlayheadTrail(g: Graphics, m: TimelineMetrics, s: TimelineState): void {
  playheadTrail.forEach((trace) => {
    const fade = clamp(1 - trace.age / 0.7, 0, 1) * trace.strength;
    const x = timeToX(trace.time, m, s.duration);
    const height = m.railHeight + 44;
    g.moveTo(x, m.railY - 22).lineTo(x, m.railY - 22 + height)
      .stroke({ color: COLORS.blue, alpha: fade * 0.16, width: 10 });
    g.moveTo(x, m.waveformY).lineTo(x - 34 * fade, m.waveformY)
      .stroke({ color: COLORS.white, alpha: fade * 0.12, width: 2 });
    g.circle(x, m.waveformY, 16 + fade * 28).fill({ color: COLORS.blue, alpha: fade * 0.018 });
  });
}

function drawSnapRitual(g: Graphics, m: TimelineMetrics, s: TimelineState, delta: number, pulse: number): void {
  if (snapPulse === null) return;
  snapPulse.age += delta;
  const fade = clamp(1 - snapPulse.age / 0.62, 0, 1);
  if (fade <= 0) {
    snapPulse = null;
    return;
  }
  const keyframeX = timeToX(snapPulse.keyframeTime, m, s.duration);
  const trimX = timeToX(snapPulse.trimTime, m, s.duration);
  const keyframe = snappedKeyframeByTime(snapPulse.keyframeTime, s);
  const y = keyframe?.layer === "effect" ? m.effectY : m.cameraY;
  const elastic = Math.sin(snapPulse.age * 30) * 4 * fade;
  g.circle(keyframeX, y, 22 + snapPulse.age * 70).stroke({ color: snapPulse.color, alpha: 0.42 * fade, width: 2 });
  g.circle(keyframeX, y, 7 + fade * 4).fill({ color: COLORS.white, alpha: 0.18 * fade });
  g.moveTo(trimX, m.waveformY + elastic).lineTo(keyframeX, y - elastic)
    .stroke({ color: COLORS.white, alpha: 0.2 * fade, width: 5 * fade });
  g.moveTo(trimX, m.waveformY + elastic).lineTo(keyframeX, y - elastic)
    .stroke({ color: snapPulse.color, alpha: 0.48 * fade, width: 2 });
  g.circle(trimX, m.waveformY, 30 + snapPulse.age * 92).stroke({ color: snapPulse.color, alpha: 0.22 * fade, width: 2 });
}

function drawCutPulse(g: Graphics, m: TimelineMetrics, s: TimelineState, delta: number): void {
  if (cutPulse === null) return;
  cutPulse.age += delta;
  const alpha = clamp(1 - cutPulse.age / 0.46, 0, 1);
  const x = timeToX(cutPulse.time, m, s.duration);
  const radius = 22 + cutPulse.age * 210;
  if (alpha <= 0) {
    cutPulse = null;
    return;
  }
  g.circle(x, m.waveformY, radius).stroke({ color: cutPulse.color, alpha: alpha * 0.3, width: 2 });
  g.moveTo(x, m.railY - 30).lineTo(x, m.railY + m.railHeight + 30)
    .stroke({ color: COLORS.white, alpha: alpha * 0.36, width: 1 });
}

function drawCutParticles(g: Graphics, particles: CutParticle[], delta: number): void {
  for (let index = particles.length - 1; index >= 0; index -= 1) {
    const particle = particles[index];
    particle.life += delta;
    if (particle.life >= particle.maxLife) {
      particles.splice(index, 1);
      continue;
    }
    particle.x += particle.vx * delta;
    particle.y += particle.vy * delta;
    particle.vx *= 0.988;
    particle.vy *= 0.988;
    const alpha = 1 - particle.life / particle.maxLife;
    g.circle(particle.x, particle.y, particle.size * alpha).fill({ color: particle.color, alpha: alpha * 0.72 });
  }
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

function updatePlayheadTrail(delta: number, state: TimelineState): void {
  for (let index = playheadTrail.length - 1; index >= 0; index -= 1) {
    playheadTrail[index].age += delta;
    if (playheadTrail[index].age > 0.7) {
      playheadTrail.splice(index, 1);
    }
  }
  if (!state.playing) return;
  const newest = playheadTrail[playheadTrail.length - 1];
  if (newest && Math.abs(newest.time - state.playhead) < 0.08) return;
  playheadTrail.push({ age: 0, strength: state.muted ? 0.42 : state.volume, time: state.playhead });
  if (playheadTrail.length > 18) {
    playheadTrail.splice(0, playheadTrail.length - 18);
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
  elements.volumeDown.addEventListener("click", (event) => {
    event.stopPropagation();
    stepVolume(-0.1, state, render);
  });
  elements.volumeUp.addEventListener("click", (event) => {
    event.stopPropagation();
    stepVolume(0.1, state, render);
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
      gsap.set(handle, { x: 0, y: 0 });
      handle.classList.add("is-dragging");
      state.playing = false;
      state.mode = "trimming";
      state.activeHandle = side;
      state.inspectorOpen = false;
      state.volumeOpen = false;
    },
    onDrag() {
      update(this.pointerX);
      emitCutParticles(side, state, elements);
      gsap.set(handle, { x: 0, y: 0 });
    },
    onRelease() {
      handle.classList.remove("is-dragging");
      triggerCutPulse(side, state);
      playUiTone(triggerSnapRitual(side, state) ? "snap" : "cut", state);
      state.mode = "idle";
      state.activeHandle = null;
      gsap.set(handle, { x: 0, y: 0 });
    }
  });
}

function emitCutParticles(side: TrimSide, state: TimelineState, elements: TimelineElements): void {
  const m = getMetrics(elements.canvasHost);
  const time = side === "start" ? state.trimStart : state.trimEnd;
  const x = timeToX(time, m, state.duration);
  const color = side === "start" ? COLORS.blue : COLORS.green;
  const direction = side === "start" ? -1 : 1;
  for (let count = 0; count < 3; count += 1) {
    cutParticles.push(createCutParticle(x, m.waveformY, color, direction));
  }
  if (cutParticles.length > 96) {
    cutParticles.splice(0, cutParticles.length - 96);
  }
}

function createCutParticle(x: number, y: number, color: number, direction: number): CutParticle {
  const spread = (Math.random() - 0.5) * 90;
  return {
    color,
    life: 0,
    maxLife: 0.34 + Math.random() * 0.26,
    size: 1.6 + Math.random() * 2.8,
    vx: direction * (70 + Math.random() * 190),
    vy: spread,
    x,
    y: y + (Math.random() - 0.5) * 78
  };
}

function triggerCutPulse(side: TrimSide, state: TimelineState): void {
  cutPulse = {
    age: 0,
    color: side === "start" ? COLORS.blue : COLORS.green,
    time: side === "start" ? state.trimStart : state.trimEnd
  };
}

function triggerSnapRitual(side: TrimSide, state: TimelineState): boolean {
  const keyframe = nearestSnappedKeyframe(side, state);
  if (keyframe === null) return false;
  snapPulse = {
    age: 0,
    color: keyframe.layer === "camera" ? COLORS.blue : COLORS.green,
    keyframeTime: keyframe.time,
    side,
    trimTime: side === "start" ? state.trimStart : state.trimEnd
  };
  return true;
}

function nearestSnappedKeyframe(side: TrimSide, state: TimelineState): TimelineKeyframe | null {
  const trimTime = side === "start" ? state.trimStart : state.trimEnd;
  return state.keyframes.reduce<TimelineKeyframe | null>((best, keyframe) => {
    if (!keyframe.editable || Math.abs(keyframe.time - trimTime) > 0.34) return best;
    if (best === null) return keyframe;
    return Math.abs(keyframe.time - trimTime) < Math.abs(best.time - trimTime) ? keyframe : best;
  }, null);
}

function snappedKeyframeByTime(time: number, state: TimelineState): TimelineKeyframe | null {
  return state.keyframes.find((keyframe) => Math.abs(keyframe.time - time) < 0.01) ?? null;
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
  const anchor = m.width < 760 ? HANDLE_ANCHOR.mobile : HANDLE_ANCHOR.desktop;
  setHandlePosition(elements.startHandle, startX - anchor.startX, m.waveformY - anchor.startY);
  setHandlePosition(elements.endHandle, endX - anchor.endX, m.waveformY - anchor.endY);
}

function placePlayheadControl(m: TimelineMetrics, s: TimelineState, elements: TimelineElements): void {
  const x = timeToX(s.playhead, m, s.duration);
  const y = m.railY - 46;
  elements.playheadControl.style.left = `${x - 16}px`;
  elements.playheadControl.style.top = `${y - 16}px`;
  elements.volumeStepper.style.left = `${x - 31}px`;
  elements.volumeStepper.style.top = `${m.railY + m.railHeight + 26}px`;
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
  elements.popover.style.setProperty("--intensity", String(keyframe.intensity));
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
  elements.volumeStepper.classList.toggle("is-muted", state.muted);
  elements.volumeStepper.style.setProperty("--volume", String(state.muted ? 0 : state.volume));
  elements.volumePopover.hidden = !state.volumeOpen;
  elements.volumeSlider.value = String(Math.round(state.volume * 100));
  elements.muteButton.textContent = state.muted ? "MUTE" : "VOL";
  elements.muteButton.classList.toggle("is-muted", state.muted);
}

function updateShellMode(state: TimelineState, elements: TimelineElements): void {
  elements.shell.dataset.mode = state.mode;
  elements.shell.dataset.activeHandle = state.activeHandle ?? "";
  elements.shell.dataset.focus = state.inspectorOpen ? "keyframe" : "";
}

function isHandleTarget(target: EventTarget | null): boolean {
  return target instanceof Element && Boolean(target.closest(".trim-handle"));
}

function isTransportTarget(target: EventTarget | null): boolean {
  return target instanceof Element && Boolean(target.closest(".playhead-control, .volume-popover, .volume-stepper"));
}

function stepVolume(delta: number, state: TimelineState, render: () => void): void {
  state.volume = clamp(state.volume + delta, 0, 1);
  state.muted = state.volume === 0;
  state.volumeOpen = false;
  playUiTone("volume", state);
  render();
}

function playUiTone(kind: "cut" | "loop" | "mute" | "pause" | "play" | "snap" | "volume", state: TimelineState): void {
  if (state.muted && kind !== "mute") return;
  audioContext ??= new AudioContext();
  if (audioContext.state === "suspended") {
    void audioContext.resume();
  }
  const oscillator = audioContext.createOscillator();
  const gain = audioContext.createGain();
  const frequency = { cut: 760, loop: 520, mute: 190, pause: 240, play: 420, snap: 880, volume: 660 }[kind];
  oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
  oscillator.type = kind === "cut" || kind === "snap" ? "triangle" : "sine";
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
