# SPEC-014 - Project Home And Workspace Lifecycle

## Goal

Turn CUTED from a generated-gallery prototype into a first-class local app with
a clear project lifecycle:

```text
Open CUTED -> Project Home -> New/Open Project -> Edit -> Render local
```

The user should not feel that an old sample was loaded accidentally, that
browser memory leaked into a new job, or that importing remains a permanent tab
inside an active edit session.

## Context

Today CUTED has two operational modes that look similar:

- `serve --dir samples/<sample>` opens a generated static gallery.
- `launch` opens a local workspace shell under `Documents/CUTED Workspace`.

Both routes render the same browser shell and expose `Importar`, `Editar`, and
`Renderizar` tabs. This was useful for MVP validation, but it creates the wrong
mental model for the product.

In the future app, importing is project creation. Once a project exists, the
primary workspace is editing. Returning to import from inside that same project
is not a normal workflow; creating or opening another project is.

## Product Principles

- CUTED opens to a Project Home when no active project is explicitly requested.
- A project is a durable local object, not a browser tab or transient sample.
- New project means no inherited title, cards, visual maps, local state,
  render queue, or previous gallery status.
- Editing is the main project workspace.
- Import is an entry flow, not a permanent tab in an open project.
- Render is an action or flow inside the project, not a top-level navigation
  destination forever.
- Recent projects are helpful, but they must be explicit and manageable.
- Deleting generated work is a destructive project-management action, not a
  side effect of starting a new project.

## Target Information Architecture

```text
CUTED App
  Project Home
    New project
    Open project
    Recent projects
    Manage storage

  Project Workspace
    Edit
    Project switcher
    Render local
    Results
    Settings
```

## Project Home

The first-run and app-start screen should be a dense, production-like project
surface rather than a marketing page.

Primary areas:

- header with CUTED logo and settings;
- `Novo projeto` primary action;
- `Abrir projeto` secondary action;
- recent projects list;
- storage/status footer.

Recent project cards should show:

- project title or source label;
- thumbnail or first frame when available;
- created date and last opened date;
- source duration or clip count;
- render status;
- disk size estimate;
- quick actions: open, reveal folder, more menu.

Empty state:

- copy: "Nenhum projeto ainda";
- primary action: "Novo projeto";
- secondary action: "Abrir pasta de projetos";
- no sample auto-loading unless the build is explicitly a dev/demo mode.

## New Project Flow

`Novo projeto` opens a focused creation/import flow.

Required fields:

- local video file or rights-approved URL;
- final render destination;
- suggestion count;
- duration profile;
- optional editorial context.

Rules:

- the render destination starts empty;
- submission is blocked until a destination is selected;
- importing creates a new project folder before analysis starts;
- the project gets a stable id before the job runs;
- any local browser draft from another project is ignored;
- once import succeeds, CUTED navigates to Edit.

The user should not see old cards, old source titles, old visual maps, old
render results, or previous localStorage state in the new project.

## Project Workspace

The open project should default to Edit.

Top-level tabs should move toward:

```text
Edit
```

with project-level actions rather than tabs:

- project switcher;
- render button;
- settings;
- project menu.

Import should not be reachable as a normal tab once a project is open. If a user
wants different media, they create a new project or explicitly replace source in
a future advanced flow.

Render should become a project action:

```text
Renderizar
  Local
  Results
```

For the current local beta, only `Renderizar local` is in scope. Submit,
calendar, and publishing workflows are intentionally out of this product branch
and should be explored as a separate program when needed.

## Project Switcher

A compact switcher should live near the top-left app chrome, separate from the
clip editing surface.

Suggested menu:

```text
Current project
Recent projects
Open other...
New project
Manage projects
```

Rules:

- switching projects warns only when there are unsaved local edits;
- current project identity is always visible;
- destructive actions are not adjacent to `Open` or `New`;
- ControlBar integration is deferred until the ControlBar branch is ready.

## Manage Projects

The management surface should handle cleanup without forcing users into the file
system.

Project actions:

- open;
- rename;
- duplicate (future);
- reveal folder;
- remove from recent;
- clean cache;
- delete project.

Storage actions:

- clean preview media;
- clean visual maps/camera analysis;
- clean captioned temp files;
- keep final renders by default;
- optional "delete final renders too" checkbox for full deletion.

## Deletion Rules

Deleting a project is destructive because it can remove generated clips,
analysis, edits, and possibly source-derived files.

The UI must:

- show the project name;
- show approximate size;
- list what will be removed;
- keep final renders by default unless the user opts in;
- use a clear button label such as `Excluir projeto`;
- prefer moving to Recycle Bin over permanent deletion when possible;
- never place delete next to the primary open/new action.

## Visual Direction

The app shell should follow the current CUTED language:

- deep black workspace;
- large but restrained CUTED logo presence;
- glass panels with thin borders;
- blue for AI/camera/active direction;
- green for approval, ready state, effects, and successful outcomes;
- white for primary readable controls;
- compact controls built for editing, not landing-page composition;
- status strips that feel like live production equipment;
- icon-first controls when the meaning is familiar;
- no card-heavy marketing hero on app start.

The current live timeline and Control Bar spike define the design direction:

- luminous blue/green state;
- dense control clusters;
- glass + glow only where it communicates state;
- large, confident control surfaces for editor-critical actions;
- motion used for readiness, scanning, loading, and focus changes.

The Control Bar remains a design reference for this work. It should not be
integrated until its branch is explicitly approved.

## Out Of Scope

- cloud login;
- multi-user collaboration;
- paid billing;
- social publishing implementation;
- replacing the current editor internals;
- integrating the in-progress Control Bar branch;
- deleting repo `samples/` automatically.

## Acceptance Criteria

- Launch without a project opens Project Home, not an old sample.
- New project creates a fresh project folder and clean app state.
- After import completes, the user lands in Edit.
- An active project no longer exposes Import as a normal project tab.
- Render is available as a project action.
- Recent projects are visible and reopenable.
- Removing a recent item does not delete files.
- Deleting a project requires explicit confirmation and lists consequences.
- Cache cleanup can free space without deleting final renders.
- Existing sample galleries remain openable for development QA.
