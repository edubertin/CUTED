# CUTED

CUTED is an early AI-assisted video clipping workspace.

This repository currently stores generated samples, review pages, rendered clips,
caption artifacts, and brand assets used to validate the product workflow before
the main application code is organized here.

## Current Contents

- `assets/brand/`: brand images for channel/profile use.
- `samples/`: generated clipping experiments with review HTML, frames, clips,
  caption queues, subtitles, and rendered outputs.
- `tools/cutted/`: versioned copy of the local CUTED skill used to generate
  galleries, serve the local finalize API, and render captioned outputs.

## Local Gallery Server

Use the CUTED server when testing the interactive final render flow:

```powershell
python tools/cutted/scripts/cutted.py serve --dir "samples/<sample-folder>" --port 8779
```

The static `index.html` still works for review, but `Finalizar videos` requires
the local server because the browser cannot run FFmpeg by itself.

## Current Stage

Prototype with a local render loop. The current focus is validating the
end-to-end clipping, per-video camera reframing, effects, calls-to-action,
captions, and final video review workflow before extracting a fuller application
structure.

The current camera MVP uses local FFmpeg crop/scale presets only. OpenCV itself
does not add API cost; future cost would come only from optional cloud APIs or
paid model hosting if automatic face/speaker detection moves outside the local
machine.
