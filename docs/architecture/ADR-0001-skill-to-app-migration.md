# ADR-0001: Migrate CUTED From Skill Workflow to App Workflow

## Status

Proposed

## Context

CUTED currently works through a local Codex skill and a large Python script. This
has been useful for rapid MVP iteration, but the product direction is to expose
processing directly in the application. The user should not need to ask Codex to
run commands in order to analyze a video.

## Decision

CUTED should keep the current local-first behavior while gradually extracting
the workflow into explicit app and package boundaries.

Proposed future boundaries:

```text
apps/web
packages/cuted-core
packages/cuted-renderer
packages/cuted-ai
packages/cuted-ui
tools/cutted
```

The current `tools/cutted` implementation remains the reference implementation
until the replacement modules are proven with equivalent QA coverage. The
`tools/cutted` and `cutted.py` names are legacy compatibility paths; new package
and module names should use CUTED/Cuted with one `t`.

## Consequences

Positive:

- The product can offer an in-app AI processing tab.
- Data/render contracts become reusable outside Codex.
- The UI can evolve without editing a generated HTML blob inside a script.
- Rendering and AI provider choices can be tested independently.

Negative:

- Migration introduces temporary duplication.
- Contracts must be documented carefully to avoid regressions.
- Existing generated samples may not map perfectly to future app state.

## Migration Principles

- Keep local render working throughout migration.
- Extract contracts before extracting code.
- Add regression tests around overlays, platform edits, captions, and final
  render before replacing behavior.
- Keep secrets out of source code.
- Preserve compatibility with existing `samples/` where practical.

## Revisit When

- The AI Processing tab has a working endpoint.
- The web app has its own persistent state model.
- Renderer package can process a queue without depending on generated HTML.
- The old skill path is no longer required for normal operation.
