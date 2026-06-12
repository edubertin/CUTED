import type { LiveTimelineOptions, TimelineKeyframe } from "./liveTimeline";

export interface CuttedCameraFrame extends Record<string, unknown> {
  confidence?: number | string | null;
  key?: number | string | null;
  part?: number | string | null;
  source?: number | string | null;
  strength?: number | string | null;
  time?: number | string | null;
}

export interface CuttedEffectFrame extends Record<string, unknown> {
  intensity?: number | string | null;
  key?: number | string | null;
  label?: number | string | null;
  time?: number | string | null;
}

export interface CuttedTimelineModel {
  cameraPath: readonly CuttedCameraFrame[];
  duration: number;
  effectKeyframes?: readonly CuttedEffectFrame[];
  muted?: boolean;
  playhead?: number;
  selectedCameraIndex?: number | null;
  trimEndPosition: number;
  trimStart: number;
  volume?: number;
  waveformPayload?: unknown;
}

export function createLiveTimelineOptionsFromCuttedModel(model: CuttedTimelineModel): LiveTimelineOptions {
  const duration = positiveNumber(model.duration, 0.3);
  const cameraKeyframes = cuttedCameraPathToKeyframes(model.cameraPath, duration);
  const effectKeyframes = cuttedEffectFramesToKeyframes(model.effectKeyframes ?? [], duration);
  const selected = selectedCameraId(model.selectedCameraIndex, cameraKeyframes);
  return {
    duration,
    keyframes: [...cameraKeyframes, ...effectKeyframes],
    muted: model.muted,
    peaks: cuttedWaveformPayloadToPeaks(model.waveformPayload),
    playhead: clampNumber(model.playhead ?? model.trimStart, 0, duration),
    selectedKeyframeId: selected,
    trimEnd: clampNumber(model.trimEndPosition, 0, duration),
    trimStart: clampNumber(model.trimStart, 0, duration),
    volume: model.volume
  };
}

export function cuttedCameraPathToKeyframes(
  frames: readonly CuttedCameraFrame[],
  duration: number
): readonly TimelineKeyframe[] {
  const safeDuration = positiveNumber(duration, 0.3);
  return frames.map((frame, index) => {
    return {
      id: `camera-${index}`,
      layer: "camera",
      time: clampNumber(numberValue(frame.time) ?? 0, 0, safeDuration),
      label: cameraFrameLabel(frame, index),
      editable: true,
      intensity: frameIntensity(frame, 0.68)
    };
  });
}

export function cuttedEffectFramesToKeyframes(
  frames: readonly CuttedEffectFrame[],
  duration: number
): readonly TimelineKeyframe[] {
  const safeDuration = positiveNumber(duration, 0.3);
  return frames.map((frame, index) => {
    const label = stringValue(frame.label) ?? stringValue(frame.key) ?? `Efeito ${index + 1}`;
    return {
      id: `effect-${index}`,
      layer: "effect",
      time: clampNumber(numberValue(frame.time) ?? 0, 0, safeDuration),
      label,
      editable: true,
      intensity: clampNumber(numberValue(frame.intensity) ?? 0.62, 0, 1)
    };
  });
}

export function cuttedWaveformPayloadToPeaks(payload: unknown): readonly number[] {
  const source = waveformSource(payload);
  if (source.length === 0) return [];
  const max = Math.max(...source.map((value) => Math.abs(value)), 0.001);
  return source.map((value) => clampNumber(Math.abs(value) / max, 0.08, 1));
}

function selectedCameraId(index: number | null | undefined, keyframes: readonly TimelineKeyframe[]): string | null {
  if (index === null || index === undefined) return null;
  return keyframes[index]?.id ?? null;
}

function waveformSource(payload: unknown): readonly number[] {
  if (Array.isArray(payload)) return numericArray(payload);
  if (!isRecord(payload)) return [];
  const peaks = payload.peaks;
  if (Array.isArray(peaks)) return numericArray(peaks);
  const samples = payload.samples;
  if (Array.isArray(samples)) return numericArray(samples);
  return [];
}

function numericArray(values: readonly unknown[]): readonly number[] {
  return values.flatMap((value) => {
    const number = numberValue(value);
    return number === null ? [] : [number];
  });
}

function cameraFrameLabel(frame: CuttedCameraFrame, index: number): string {
  const part = stringValue(frame.part);
  const key = stringValue(frame.key);
  const source = stringValue(frame.source);
  if (part) return part;
  if (key) return key;
  if (source) return source.replace(/^ai-director-/, "");
  return `Camera ${index + 1}`;
}

function frameIntensity(frame: CuttedCameraFrame, fallback: number): number {
  const strength = numberValue(frame.strength);
  if (strength !== null) return clampNumber(strength / 100, 0.18, 1);
  const confidence = numberValue(frame.confidence);
  if (confidence !== null) return clampNumber(confidence, 0.18, 1);
  return fallback;
}

function numberValue(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function stringValue(value: unknown): string | null {
  if (typeof value === "string" && value.trim()) return value.trim();
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  return null;
}

function positiveNumber(value: number, fallback: number): number {
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function clampNumber(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
