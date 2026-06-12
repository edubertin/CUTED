import { Application, Container, Graphics } from "pixi.js";
import "./timeline.css";

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
    startX: 60,
    startY: 98
  },
  mobile: {
    endX: 0,
    endY: 73,
    startX: 44,
    startY: 78
  }
};

export type LayerKind = "camera" | "effect";
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

export interface TimelineKeyframe {
  id: string;
  layer: LayerKind;
  time: number;
  label: string;
  editable: boolean;
  intensity: number;
}

export interface LiveTimelineSnapshot {
  duration: number;
  trimStart: number;
  trimEnd: number;
  playhead: number;
  playing: boolean;
  muted: boolean;
  volume: number;
  peaks: readonly number[];
  keyframes: readonly TimelineKeyframe[];
}

interface TimelineState extends LiveTimelineSnapshot {
  volumeOpen: boolean;
  volumeEnabled: boolean;
  inspectorEnabled: boolean;
  mode: TimelineMode;
  activeHandle: TrimSide | null;
  inspectorOpen: boolean;
  selectedKeyframeId: string | null;
  hoveredKeyframeId: string | null;
}

export interface LiveTimelineCallbacks {
  onKeyframeOpen?: (keyframe: TimelineKeyframe) => void;
  onPlayToggle?: (playing: boolean) => void;
  onSeek?: (time: number) => void;
  onTrimChange?: (trim: { start: number; end: number; side: TrimSide }) => void;
  onVolumeChange?: (volume: number, muted: boolean) => void;
}

export interface LiveTimelineOptions {
  callbacks?: LiveTimelineCallbacks;
  duration?: number;
  keyframes?: readonly TimelineKeyframe[];
  logoUrl?: string;
  muted?: boolean;
  peaks?: readonly number[];
  playhead?: number;
  playing?: boolean;
  selectedKeyframeId?: string | null;
  showInspector?: boolean;
  showVolume?: boolean;
  trimEnd?: number;
  trimStart?: number;
  volume?: number;
}

export interface LiveTimelineController {
  destroy: () => void;
  getSnapshot: () => LiveTimelineSnapshot;
  update: (options: LiveTimelineOptions) => void;
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
  trimReadout: HTMLElement | null;
  playheadReadout: HTMLElement | null;
}

let elements: TimelineElements;
let state: TimelineState;
let activeCallbacks: LiveTimelineCallbacks = {};
let lastPlaybackTick = performance.now();
let lastRenderTick = performance.now();
let audioContext: AudioContext | null = null;
let cutPulse: CutPulse | null = null;
let snapPulse: SnapPulse | null = null;
const cutParticles: CutParticle[] = [];
const playheadTrail: PlayheadTrace[] = [];

export async function createLiveTimeline(container: HTMLElement, options: LiveTimelineOptions = {}): Promise<LiveTimelineController> {
  activeCallbacks = options.callbacks ?? {};
  container.innerHTML = liveTimelineMarkup(options.logoUrl ?? "", options.showVolume ?? true);
  elements = readElements(container);
  state = createInitialState(options);
  resetRuntimeEffects();

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

  return {
    destroy() {
      app.destroy(true);
      container.innerHTML = "";
    },
    getSnapshot() {
      return snapshotFromState(state);
    },
    update(nextOptions) {
      activeCallbacks = nextOptions.callbacks ?? activeCallbacks;
      applyOptionsToState(state, nextOptions);
      renderTimeline();
    }
  };
}

function liveTimelineMarkup(logoUrl: string, showVolume: boolean): string {
  return `<div class="timeline-shell" id="timeline-shell">
    <div class="timeline-canvas" id="timeline-canvas"></div>
    <button class="playhead-control" id="playhead-control" type="button" aria-label="Tocar preview">
      <span id="playhead-glyph" aria-hidden="true"></span>
    </button>
    <div class="volume-popover" id="volume-popover"${showVolume ? " hidden" : " hidden data-disabled=\"true\""}>
      <input id="volume-slider" type="range" min="0" max="100" value="72" aria-label="Volume" />
      <button id="mute-button" type="button" aria-label="Mutar">VOL</button>
    </div>
    <button class="trim-handle trim-handle--start" id="start-handle" type="button" aria-label="Cortar inicio">
      <img id="start-logo" alt="" src="${escapeAttribute(logoUrl)}" />
      <span class="trim-blade trim-blade--start" aria-hidden="true"></span>
    </button>
    <button class="trim-handle trim-handle--end" id="end-handle" type="button" aria-label="Cortar fim">
      <img id="end-logo" alt="" src="${escapeAttribute(logoUrl)}" />
      <span class="trim-blade trim-blade--end" aria-hidden="true"></span>
    </button>
    <aside class="keyframe-popover" id="keyframe-popover" aria-label="Inspector do keyframe" hidden>
      <div class="keyframe-popover__aura" aria-hidden="true"></div>
      <div class="keyframe-popover__lens" aria-hidden="true"></div>
      <div class="keyframe-popover__beam"></div>
      <div class="keyframe-popover__top">
        <span id="popover-meta">Camera</span>
        <strong id="popover-title">Punch-in</strong>
      </div>
      <div class="keyframe-popover__meter">
        <i id="popover-meter"></i>
      </div>
      <div class="keyframe-popover__actions">
        <button type="button" aria-label="Modo">M</button>
        <button type="button" aria-label="Forca">I</button>
        <button type="button" aria-label="Tempo">~</button>
      </div>
    </aside>
  </div>`;
}

function createInitialState(options: LiveTimelineOptions): TimelineState {
  const duration = Math.max(options.duration ?? 72, 0.3);
  const trimStart = clamp(options.trimStart ?? 3.8, 0, duration);
  const trimEnd = clamp(options.trimEnd ?? 67.2, trimStart + 0.3, duration);
  return {
    duration,
    trimStart,
    trimEnd,
    playhead: clamp(options.playhead ?? 18, trimStart, trimEnd),
    playing: options.playing ?? false,
    muted: options.muted ?? false,
    volume: clamp(options.volume ?? 0.72, 0, 1),
    volumeOpen: false,
    volumeEnabled: options.showVolume ?? true,
    inspectorEnabled: options.showInspector ?? true,
    mode: "idle",
    activeHandle: null,
    inspectorOpen: false,
    selectedKeyframeId: options.selectedKeyframeId ?? "cam-2",
    hoveredKeyframeId: null,
    peaks: options.peaks ?? createPeaks(128),
    keyframes: options.keyframes ?? createDemoKeyframes()
  };
}

function createDemoKeyframes(): readonly TimelineKeyframe[] {
  return [
    createKeyframe("cam-1", "camera", 7.1, "Centro seguro", true, 0.35),
    createKeyframe("cam-2", "camera", 14.5, "Punch-in", true, 0.72),
    createKeyframe("cam-3", "camera", 29.1, "Reacao", true, 0.62),
    createKeyframe("cam-4", "camera", 46.2, "Grupo", true, 0.44),
    createKeyframe("cam-5", "camera", 61.5, "Corte", false, 0.9),
    createKeyframe("fx-1", "effect", 10.2, "Glow leve", true, 0.38),
    createKeyframe("fx-2", "effect", 21.4, "VHS", true, 0.7),
    createKeyframe("fx-3", "effect", 36.9, "Filme antigo", true, 0.52),
    createKeyframe("fx-4", "effect", 54.4, "Impacto", true, 0.82)
  ];
}

function resetRuntimeEffects(): void {
  lastPlaybackTick = performance.now();
  lastRenderTick = performance.now();
  cutPulse = null;
  snapPulse = null;
  cutParticles.splice(0);
  playheadTrail.splice(0);
}

function snapshotFromState(source: TimelineState): LiveTimelineSnapshot {
  return {
    duration: source.duration,
    trimStart: source.trimStart,
    trimEnd: source.trimEnd,
    playhead: source.playhead,
    playing: source.playing,
    muted: source.muted,
    volume: source.volume,
    peaks: source.peaks,
    keyframes: source.keyframes
  };
}

function applyOptionsToState(target: TimelineState, options: LiveTimelineOptions): void {
  target.duration = Math.max(options.duration ?? target.duration, 0.3);
  target.trimStart = clamp(options.trimStart ?? target.trimStart, 0, target.duration);
  target.trimEnd = clamp(options.trimEnd ?? target.trimEnd, target.trimStart + 0.3, target.duration);
  target.playhead = clamp(options.playhead ?? target.playhead, target.trimStart, target.trimEnd);
  target.playing = options.playing ?? target.playing;
  target.muted = options.muted ?? target.muted;
  target.volume = clamp(options.volume ?? target.volume, 0, 1);
  target.volumeEnabled = options.showVolume ?? target.volumeEnabled;
  target.inspectorEnabled = options.showInspector ?? target.inspectorEnabled;
  target.peaks = options.peaks ?? target.peaks;
  target.keyframes = options.keyframes ?? target.keyframes;
  if (Object.prototype.hasOwnProperty.call(options, "selectedKeyframeId")) {
    target.selectedKeyframeId = options.selectedKeyframeId ?? null;
  }
}

function readElements(root: ParentNode): TimelineElements {
  return {
    shell: requireElement(root, "timeline-shell", HTMLElement),
    canvasHost: requireElement(root, "timeline-canvas", HTMLElement),
    startHandle: requireElement(root, "start-handle", HTMLElement),
    endHandle: requireElement(root, "end-handle", HTMLElement),
    startLogo: requireElement(root, "start-logo", HTMLImageElement),
    endLogo: requireElement(root, "end-logo", HTMLImageElement),
    popover: requireElement(root, "keyframe-popover", HTMLElement),
    popoverTitle: requireElement(root, "popover-title", HTMLElement),
    popoverMeta: requireElement(root, "popover-meta", HTMLElement),
    popoverMeter: requireElement(root, "popover-meter", HTMLElement),
    playheadControl: requireElement(root, "playhead-control", HTMLButtonElement),
    playheadGlyph: requireElement(root, "playhead-glyph", HTMLElement),
    volumePopover: requireElement(root, "volume-popover", HTMLElement),
    volumeSlider: requireElement(root, "volume-slider", HTMLInputElement),
    muteButton: requireElement(root, "mute-button", HTMLButtonElement),
    trimReadout: optionalElement(root, "trim-readout", HTMLElement),
    playheadReadout: optionalElement(root, "playhead-readout", HTMLElement)
  };
}

function requireElement<T extends HTMLElement>(root: ParentNode, id: string, ctor: { new (): T }): T {
  const element = root.querySelector(`#${id}`);
  if (!(element instanceof ctor)) {
    throw new Error(`Missing expected element: ${id}`);
  }
  return element;
}

function optionalElement<T extends HTMLElement>(root: ParentNode, id: string, ctor: { new (): T }): T | null {
  const element = root.querySelector(`#${id}`);
  return element instanceof ctor ? element : null;
}

function escapeAttribute(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll("\"", "&quot;").replaceAll("<", "&lt;");
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
  const height = Math.max(host.clientHeight, 150);
  const compact = width < 700 || height < 210;
  const railX = compact ? 70 : 76;
  const railWidth = Math.max(width - railX * 2, compact ? 180 : 420);
  const railY = compact ? 40 : Math.round(height * 0.26);
  const railHeight = compact ? Math.max(height - 72, 76) : Math.round(height * 0.56);
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
  const { left, right } = timelineVisualBounds(m);
  const top = m.railY - 22;
  const bottom = m.railY + m.railHeight + 22;
  g.roundRect(left, m.railY - 34, right - left, m.railHeight + 68, 18)
    .fill({ color: COLORS.blue, alpha: 0.025 + energy * 0.04 });
  g.moveTo(left, top).lineTo(right, top)
    .stroke({ color: COLORS.blue, alpha: 0.44 + energy, width: 2 });
  g.moveTo(left, bottom).lineTo(right, bottom)
    .stroke({ color: COLORS.green, alpha: 0.36 + energy * 0.7, width: 2 });
  g.moveTo(left, top + 14).lineTo(left + 34, top + 14)
    .stroke({ color: COLORS.white, alpha: 0.14, width: 1 });
  g.moveTo(right - 34, bottom - 14).lineTo(right, bottom - 14)
    .stroke({ color: COLORS.white, alpha: 0.12, width: 1 });
}

function drawInactiveMasks(g: Graphics, m: TimelineMetrics, s: TimelineState, pulse: number): void {
  const startX = timeToX(s.trimStart, m, s.duration);
  const endX = timeToX(s.trimEnd, m, s.duration);
  const { left, right } = timelineVisualBounds(m);
  g.rect(left, m.railY - 22, Math.max(startX - left, 0), m.railHeight + 44).fill({ color: COLORS.black, alpha: 0.32 });
  g.rect(endX, m.railY - 22, Math.max(right - endX, 0), m.railHeight + 44).fill({ color: COLORS.black, alpha: 0.32 });
  g.roundRect(startX, m.railY - 21, endX - startX, m.railHeight + 42, 7)
    .fill({ color: COLORS.blue, alpha: 0.025 });
  drawSelectionTexture(g, m, startX, endX, pulse);
  g.moveTo(startX, m.railY - 22).lineTo(endX, m.railY - 22)
    .stroke({ color: COLORS.blue, alpha: 0.12, width: 5 });
  g.moveTo(startX, m.railY + m.railHeight + 22).lineTo(endX, m.railY + m.railHeight + 22)
    .stroke({ color: COLORS.green, alpha: 0.16 + Math.sin(pulse * 1.8) * 0.03, width: 5 });
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
  const { left, right } = timelineVisualBounds(m);
  g.moveTo(left, m.waveformY).lineTo(right, m.waveformY).stroke({ color: COLORS.white, alpha: 0.1, width: 1 });
}

function drawRail(g: Graphics, m: TimelineMetrics, s: TimelineState, y: number, color: number, alpha: number, pulse: number): void {
  const startX = timeToX(s.trimStart, m, s.duration);
  const endX = timeToX(s.trimEnd, m, s.duration);
  const { left, right } = timelineVisualBounds(m);
  g.moveTo(left, y).lineTo(right, y).stroke({ color: COLORS.rail, alpha: 1, width: 7 });
  g.moveTo(left, y).lineTo(right, y).stroke({ color, alpha: 0.24 + Math.sin(pulse * 1.4) * 0.03, width: 3 });
  g.moveTo(startX, y).lineTo(endX, y).stroke({ color, alpha: 0.16, width: 13 });
  g.moveTo(startX, y).lineTo(endX, y).stroke({ color, alpha: alpha + Math.sin(pulse * 2) * 0.06, width: 3 });
}

function timelineVisualBounds(m: TimelineMetrics): { left: number; right: number } {
  const padding = m.width < 760 ? HANDLE_ANCHOR.mobile.startX : HANDLE_ANCHOR.desktop.startX;
  return {
    left: clamp(m.railX - padding, 0, m.width),
    right: clamp(m.railX + m.railWidth + padding, 0, m.width)
  };
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
    activeCallbacks.onPlayToggle?.(state.playing);
    playUiTone(state.playing ? "play" : "pause", state);
    render();
  });
  elements.playheadControl.addEventListener("contextmenu", (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (!state.volumeEnabled) return;
    state.volumeOpen = !state.volumeOpen;
    render();
  });
  elements.volumeSlider.addEventListener("input", () => {
    state.volume = clamp(Number(elements.volumeSlider.value) / 100, 0, 1);
    state.muted = state.volume === 0;
    activeCallbacks.onVolumeChange?.(state.volume, state.muted);
    playUiTone("volume", state);
    render();
  });
  elements.muteButton.addEventListener("click", (event) => {
    event.stopPropagation();
    state.muted = !state.muted;
    activeCallbacks.onVolumeChange?.(state.volume, state.muted);
    playUiTone("mute", state);
    render();
  });
}

function bindShellInteractions(elements: TimelineElements, state: TimelineState, render: () => void): void {
  elements.shell.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    if (isHandleTarget(event.target)) return;
    if (isTransportTarget(event.target)) return;
    state.playing = false;
    state.inspectorOpen = false;
    if (state.volumeEnabled) state.volumeOpen = false;
    state.mode = "scrubbing";
    state.playhead = xToTime(event.clientX, getMetrics(elements.canvasHost), state.duration);
    activeCallbacks.onPlayToggle?.(false);
    activeCallbacks.onSeek?.(state.playhead);
    render();
  });
  elements.shell.addEventListener("pointermove", (event) => {
    if (isHandleTarget(event.target)) return;
    if (isPointerNearTrim(event.clientX, event.clientY, elements, state)) {
      state.hoveredKeyframeId = null;
      elements.shell.classList.remove("is-over-keyframe");
      render();
      return;
    }
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
    if (
      isHandleTarget(event.target) ||
      isPointerNearTrim(event.clientX, event.clientY, elements, state)
    ) {
      event.stopPropagation();
      return;
    }
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
    state.trimStart = clamp(time, 0, state.trimEnd - 2);
    state.playhead = Math.max(state.playhead, state.trimStart);
    activeCallbacks.onTrimChange?.({ start: state.trimStart, end: state.trimEnd, side: "start" });
    render();
  };
  const updateEnd = (clientX: number): void => {
    const time = xToTime(clientX, getMetrics(elements.canvasHost), state.duration);
    state.trimEnd = clamp(time, state.trimStart + 2, state.duration);
    state.playhead = Math.min(state.playhead, state.trimEnd);
    activeCallbacks.onTrimChange?.({ start: state.trimStart, end: state.trimEnd, side: "end" });
    render();
  };
  bindRightButtonTrimDrag(elements.startHandle, "start", state, updateStart, render);
  bindRightButtonTrimDrag(elements.endHandle, "end", state, updateEnd, render);
}

function bindRightButtonTrimDrag(
  handle: HTMLElement,
  side: TrimSide,
  state: TimelineState,
  update: (clientX: number) => void,
  render: () => void
): void {
  handle.addEventListener("contextmenu", (event) => {
    event.preventDefault();
    event.stopPropagation();
  });
  handle.addEventListener("pointerdown", (event) => {
    if (event.button !== 2) return;
    event.preventDefault();
    event.stopPropagation();
    handle.setPointerCapture?.(event.pointerId);
    startTrimDrag(handle, side, state);
    render();
    let moved = false;

    const move = (moveEvent: PointerEvent): void => {
      if (moveEvent.pointerId !== event.pointerId) return;
      moveEvent.preventDefault();
      moveEvent.stopPropagation();
      moved = true;
      update(moveEvent.clientX);
      emitCutParticles(side, state, elements);
    };
    const finish = (finishEvent: PointerEvent): void => {
      if (finishEvent.pointerId !== event.pointerId) return;
      finishEvent.preventDefault();
      finishEvent.stopPropagation();
      window.removeEventListener("pointermove", move);
      window.removeEventListener("pointerup", finish);
      window.removeEventListener("pointercancel", finish);
      handle.releasePointerCapture?.(event.pointerId);
      finishTrimDrag(handle, side, state, moved);
      render();
    };

    window.addEventListener("pointermove", move);
    window.addEventListener("pointerup", finish);
    window.addEventListener("pointercancel", finish);
  });
}

function startTrimDrag(handle: HTMLElement, side: TrimSide, state: TimelineState): void {
  handle.classList.add("is-dragging");
  state.playing = false;
  state.mode = "trimming";
  state.activeHandle = side;
  state.inspectorOpen = false;
  activeCallbacks.onPlayToggle?.(false);
  if (state.volumeEnabled) state.volumeOpen = false;
}

function finishTrimDrag(handle: HTMLElement, side: TrimSide, state: TimelineState, moved: boolean): void {
  handle.classList.remove("is-dragging");
  if (moved) {
    triggerCutPulse(side, state);
    playUiTone("cut", state);
  }
  state.mode = "idle";
  state.activeHandle = null;
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

function isPointerNearTrim(clientX: number, clientY: number, elements: TimelineElements, state: TimelineState): boolean {
  const m = getMetrics(elements.canvasHost);
  const rect = elements.canvasHost.getBoundingClientRect();
  const x = clientX - rect.left;
  const y = clientY - rect.top;
  const startX = timeToX(state.trimStart, m, state.duration);
  const endX = timeToX(state.trimEnd, m, state.duration);
  const withinRail = y >= m.railY - 48 && y <= m.railY + m.railHeight + 48;
  return withinRail && (Math.abs(x - startX) <= 42 || Math.abs(x - endX) <= 42);
}

function openInspector(keyframe: TimelineKeyframe, state: TimelineState, render: () => void): void {
  if (state.mode === "trimming") return;
  state.playing = false;
  state.volumeOpen = false;
  state.selectedKeyframeId = keyframe.id;
  state.inspectorOpen = state.inspectorEnabled;
  state.mode = "editing";
  activeCallbacks.onPlayToggle?.(false);
  activeCallbacks.onKeyframeOpen?.(keyframe);
  render();
}

function selectedKeyframe(state: TimelineState): TimelineKeyframe | null {
  return state.keyframes.find((keyframe) => keyframe.id === state.selectedKeyframeId) ?? null;
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
  const y = Math.max(m.railY - 26, 24);
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
  elements.popover.hidden = !s.inspectorEnabled || !s.inspectorOpen || keyframe === null;
  if (!s.inspectorEnabled || !s.inspectorOpen || keyframe === null) return;
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
  if (elements.trimReadout) {
    elements.trimReadout.textContent = `${formatTime(state.trimStart)} - ${formatTime(state.trimEnd)}`;
  }
  if (elements.playheadReadout) {
    elements.playheadReadout.textContent = formatTime(state.playhead);
  }
}

function updateTransportControls(state: TimelineState, elements: TimelineElements): void {
  elements.playheadControl.classList.toggle("is-playing", state.playing);
  elements.playheadControl.classList.toggle("is-muted", state.muted);
  elements.playheadControl.setAttribute("aria-label", state.playing ? "Pausar preview" : "Tocar preview");
  elements.playheadGlyph.dataset.state = state.playing ? "pause" : "play";
  elements.volumePopover.hidden = !state.volumeEnabled || !state.volumeOpen;
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
  return target instanceof Element && Boolean(target.closest(".playhead-control, .volume-popover"));
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
