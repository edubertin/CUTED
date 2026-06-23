# ADR-0006: CUTED Engine Incremental Extraction

## Status

Proposed

## Context

The current CUTED engine lives mostly in `tools/cutted/scripts/cutted.py`.
That script is still the reference implementation and must remain runnable, but
it has grown into a mixed surface:

- command-line entrypoints;
- local HTTP server and `/api/*` handlers;
- project catalog and local workspace behavior;
- import, transcription, YouTube, and OpenAI helpers;
- Smart Camera, visual map, OpenCV, YOLO, and AI Director logic;
- FFmpeg render, captions, overlays, bumpers, and publish cover generation;
- generated HTML, CSS, and JavaScript for the local browser UI.

This shape was useful for MVP speed, but it now makes review, packaging, and
feature work harder. The extraction must not break the local Windows direction,
existing sample galleries, current CLI commands, or render QA.

## Decision

Extract the engine gradually while keeping `cutted.py` as a compatibility
facade until replacement modules have equivalent coverage.

New code should use the CUTED spelling with one `t` in module and future package
names. Existing literal paths such as `tools/cutted/` and `cutted.py` remain
legacy compatibility paths until a dedicated migration branch renames them.

The first extraction is a low-risk contracts module:

```text
tools/cutted/scripts/cuted_contracts.py
```

It owns pure data contracts and preset maps used by the current engine:

- clip/transcript dataclasses;
- platform and resolution presets;
- camera, effect, and overlay presets;
- caption event/window contracts.

`tools/cutted/scripts/cutted.py` imports and re-exports those names so current
tests and callers that reference `CUTTED.Moment`, `CUTTED.PLATFORM_PRESETS`, or
similar symbols continue to work.

## Target Direction

Future extraction should prefer these one-`t` package names when real package
boundaries are introduced:

```text
packages/cuted-core/
packages/cuted-renderer/
packages/cuted-ai/
packages/cuted-ui/
```

Suggested order:

1. `cuted-core`: contracts, presets, project metadata, queue normalization, safe
   paths, and pure helpers.
2. `cuted-renderer`: FFmpeg graph construction, caption rendering, overlays,
   bumpers, manifests, and render job primitives.
3. `cuted-ai`: OpenAI/local provider adapters, transcription, selection,
   publish intelligence, local cost ledger, and AI Director payload validation.
4. `cuted-ui`: generated browser assets, Project Home shell, editor HTML/CSS/JS,
   and reusable control surfaces.
5. `apps/web` and `apps/desktop`: only when the local app shell needs dedicated
   source boundaries.

## Migration Rules

- Keep `python tools/cutted/scripts/cutted.py ...` working during migration.
- Keep `tools/cutted` as the reference implementation until modules prove
  equivalent behavior.
- Do not rename folders or commands in the same branch as behavioral extraction.
- Extract pure logic before extracting side-effectful server, file, FFmpeg, or
  OpenAI behavior.
- Re-export moved symbols from `cutted.py` while tests and legacy callers still
  import the script directly.
- Run Python tests and `py_compile` after behavior-affecting moves.
- Run a real local render smoke before changing render graph behavior.

## Consequences

Positive:

- New work can target smaller modules without reading the full engine.
- Contracts become reusable by future app/package boundaries.
- Refactors can preserve CLI compatibility while reducing risk.
- Future package names align with the product spelling: CUTED/Cuted, one `t`.

Negative:

- The bridge period creates temporary duplication of import surfaces.
- Tests may still import `cutted.py` until they are migrated to module-level
  contracts.
- Renaming legacy paths remains a separate migration with packaging risk.

## Validation

- `python -m py_compile tools/cutted/scripts/cuted_contracts.py tools/cutted/scripts/cutted.py`
- `python -m unittest discover -s tests -p "test_*.py"`

## Revisit When

- The renderer can process a queue without generated HTML assumptions.
- Project state has moved from browser-only storage to project files.
- The local desktop shell owns startup/launch behavior separately from the
  reference script.
- Packaging no longer needs to load `cutted.py` dynamically.
