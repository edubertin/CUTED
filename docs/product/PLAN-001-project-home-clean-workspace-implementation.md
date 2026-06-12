# PLAN-001 - Project Home And Clean Workspace Implementation

## Objective

Implement the project lifecycle described in SPEC-014 and ADR-0005 while
preserving the current local render pipeline.

The first implementation should make CUTED feel like a real local app:

```text
Open app -> see projects -> create/open project -> edit -> render
```

No old sample or stale browser state should appear unless the user explicitly
opens that project.

## Design Direction

Follow the current CUTED app language:

- black workspace;
- CUTED blue for AI/camera/active system state;
- CUTED green for ready/effects/positive completion;
- glass panels and thin luminous borders;
- dense editor-first layouts;
- status strips and project cards that feel operational, not decorative;
- no marketing hero screen;
- no nested card piles.

Use the live timeline and Control Bar spike as visual references only. Do not
integrate the Control Bar branch in this plan.

## Phase 0 - Safety And Baseline

Scope:

- preserve current `serve --dir samples/...` behavior;
- preserve current generated galleries;
- keep Control Bar branch untouched;
- add tests around current launch and empty workspace behavior before changing
  it.

Checks:

- `python tests/test_cutted_import_ui.py`;
- current local gallery opens;
- current `launch --no-browser` still creates a workspace shell.

## Phase 1 - Project Catalog Foundation

Goal:

Add a local project catalog without changing the editor UI yet.

Implementation:

- create catalog helpers around `%LOCALAPPDATA%/CUTED/projects.json`;
- create project metadata schema;
- add read/write tests;
- add size estimation helper;
- add safe path validation so project operations stay inside the configured
  workspace unless explicitly opening an existing folder.

Data:

```text
project id
title
path
created_at
last_opened_at
status
clip_count
render_count
size_bytes
thumbnail
```

Acceptance:

- catalog creates when missing;
- corrupt catalog falls back safely and logs a warning;
- adding/opening a project updates `last_opened_at`;
- no secrets or transcripts are stored in catalog.

## Phase 2 - Project Home Shell

Goal:

Make `launch` open a Project Home when no project is selected.

Implementation:

- generate an empty Project Home HTML state;
- replace default `body[data-tab=edit]` for launch with a home state;
- add recent project list;
- add `Novo projeto` and `Abrir projeto` actions;
- keep Settings accessible from Home;
- add empty state copy and storage footer.

Visual:

- centered logo lockup;
- compact operational project cards;
- blue primary "Novo projeto";
- subdued "Abrir projeto";
- no old cards;
- no Import/Edit/Render tabs on Home.

Acceptance:

- app launch does not show old sample content;
- no recent projects shows a clean empty state;
- recent projects render from catalog;
- repo sample server behavior remains unchanged.

## Phase 3 - Clean New Project Flow

Goal:

`Novo projeto` creates a true new project and starts import from that project
context.

Implementation:

- create project folder before import job starts;
- write `project.json` with source/output/import settings;
- write imported outputs under the new project folder;
- scope browser storage by project id;
- after import completes, navigate to project Edit.

UX:

- New project form replaces permanent Import tab;
- destination folder remains required;
- progress states are clear: queued, ingesting, transcribing, analyzing,
  rendering previews, ready, failed;
- failed jobs stay in project history with retry/open-folder actions.

Acceptance:

- two new projects do not share state;
- old title/maps/render queue do not appear;
- import success opens Edit;
- failed import does not poison future project state.

## Phase 4 - Project Workspace Navigation

Goal:

Remove the old tab mental model from active projects.

Implementation:

- active project opens directly in Edit;
- hide/remove `Importar` from project workspace;
- convert `Renderizar` into a project action;
- add project switcher near top-left chrome;
- add project menu: rename, reveal folder, manage project.

Current beta compatibility:

- generated sample galleries may still show tabs during transition;
- new app launch path uses the new shell.

Acceptance:

- active project has no normal route back to Import;
- render action remains discoverable;
- project identity is visible;
- switching projects loads the selected project id/state.

## Phase 5 - Render Flow And Results

Goal:

Move render from a tab to a focused flow.

Implementation:

- `Renderizar` opens a panel/drawer/modal;
- show local render options;
- show queue summary;
- show rendered results after completion;
- keep `/api/finalize` contract initially;
- keep `/api/finalize-results` restore behavior.

Future reserved:

- `Submit` or publish flow can share this entrypoint later.

Acceptance:

- render flow works from Edit;
- results restore after restart;
- final render path is visible;
- render does not require visiting a separate top-level tab.

## Phase 6 - Manage Projects And Cleanup

Goal:

Give users control over old work and disk usage.

Implementation:

- add Manage Projects view;
- show size per project;
- add `Remove from recents`;
- add `Clean cache`;
- add `Delete project`;
- use Recycle Bin when available;
- keep final renders by default;
- require explicit opt-in to delete final renders too.

Safety:

- destructive actions are visually separated;
- delete modal names the project and estimated size;
- action label says exactly what happens;
- no generic "Are you sure?" copy.

Acceptance:

- remove from recents leaves folder intact;
- clean cache preserves metadata and final renders;
- delete asks for confirmation;
- delete cannot target paths outside known project folders without explicit
  handling;
- QA can verify no repo files are deleted accidentally.

## Phase 7 - Persistence Migration

Goal:

Move from global `localStorage` to project-scoped persistence.

Implementation:

- introduce `project-state.json`;
- hydrate editor from project state;
- save meaningful edits back to project state;
- keep localStorage as temporary cache keyed by project id;
- add migration fallback for existing generated galleries.

Acceptance:

- reload restores edits from project files;
- clearing browser storage does not destroy saved project edits;
- opening a second project does not inherit the first project state.

## Phase 8 - Visual Polish And Control Bar Readiness

Goal:

Make the app shell visually coherent with the live timeline and future Control
Bar.

Implementation:

- extract shared app shell tokens;
- align project cards, switcher, render flow, and dialogs with CUTED glass
  language;
- use blue/green status semantics consistently;
- keep dense editor surfaces;
- prepare integration slots for Control Bar without importing it.

Acceptance:

- Home, Edit, Render flow, and Manage Projects feel like the same product;
- mobile layout remains usable;
- destructive actions remain visibly distinct;
- Control Bar can later replace the current control strip without redesigning
  project navigation.

## QA Plan

Smoke:

- launch opens Project Home;
- create project from local file;
- import completes and opens Edit;
- render one output;
- restart app and reopen the project;
- create second project and confirm no inherited state;
- remove first project from recents;
- reopen it through folder;
- clean cache and verify final renders remain;
- delete a disposable project and verify confirmation.

Regression:

- existing `serve --dir samples/...` still opens sample galleries;
- live timeline still loads in generated cards;
- `/api/finalize-results` still restores completed renders;
- OpenAI settings do not leak into catalog;
- repo `samples/` are never deleted by user project cleanup.

## Recommended First Slice

Start with phases 1 and 2:

1. project catalog helpers;
2. Project Home shell for `launch`;
3. recent projects list from catalog;
4. tests around clean launch and catalog persistence.

This gives the app the right front door without touching the editor internals or
the in-progress Control Bar.
