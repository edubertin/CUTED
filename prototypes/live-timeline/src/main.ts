import cutedLogoUrl from "../../../assets/brand/cuted-logo-transparent.png";
import { createLiveTimeline, type LiveTimelineSnapshot, type TimelineKeyframe } from "./liveTimeline";

const mount = document.getElementById("timeline-demo");
const trimReadout = document.getElementById("trim-readout");
const playheadReadout = document.getElementById("playhead-readout");

if (!(mount instanceof HTMLElement)) {
  throw new Error("Missing timeline demo mount.");
}

const keyframes: readonly TimelineKeyframe[] = [
  { id: "cam-1", layer: "camera", time: 7.1, label: "Centro seguro", editable: true, intensity: 0.35 },
  { id: "cam-2", layer: "camera", time: 14.5, label: "Punch-in", editable: true, intensity: 0.72 },
  { id: "cam-3", layer: "camera", time: 29.1, label: "Reacao", editable: true, intensity: 0.62 },
  { id: "cam-4", layer: "camera", time: 46.2, label: "Grupo", editable: true, intensity: 0.44 },
  { id: "cam-5", layer: "camera", time: 61.5, label: "Corte", editable: false, intensity: 0.9 },
  { id: "fx-1", layer: "effect", time: 10.2, label: "Glow leve", editable: true, intensity: 0.38 },
  { id: "fx-2", layer: "effect", time: 21.4, label: "VHS", editable: true, intensity: 0.7 },
  { id: "fx-3", layer: "effect", time: 36.9, label: "Filme antigo", editable: true, intensity: 0.52 },
  { id: "fx-4", layer: "effect", time: 54.4, label: "Impacto", editable: true, intensity: 0.82 }
];

let controller: Awaited<ReturnType<typeof createLiveTimeline>> | null = null;

controller = await createLiveTimeline(mount, {
  duration: 72,
  keyframes,
  logoUrl: cutedLogoUrl,
  playhead: 18,
  selectedKeyframeId: "cam-2",
  trimEnd: 67.2,
  trimStart: 3.8,
  callbacks: {
    onSeek: () => syncControllerReadout(controller),
    onTrimChange: () => syncControllerReadout(controller)
  }
});

syncReadout(controller.getSnapshot());

function syncControllerReadout(activeController: Awaited<ReturnType<typeof createLiveTimeline>> | null): void {
  if (activeController) syncReadout(activeController.getSnapshot());
}

function syncReadout(snapshot: LiveTimelineSnapshot): void {
  if (trimReadout) {
    trimReadout.textContent = `${formatTime(snapshot.trimStart)} - ${formatTime(snapshot.trimEnd)}`;
  }
  if (playheadReadout) {
    playheadReadout.textContent = formatTime(snapshot.playhead);
  }
}

function formatTime(totalSeconds: number): string {
  const seconds = Math.round(totalSeconds);
  const minutes = Math.floor(seconds / 60);
  return `${String(minutes).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
}
