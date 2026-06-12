# ADR-0005 Local Project Memory And Cleanup

## Status

Proposed

## Context

CUTED is moving from generated review pages toward a local beta app. The current
prototype stores some UI state in browser `localStorage` and stores generated
media in folders such as `samples/<sample>` or a local workspace directory.

That creates two product risks:

- a new session can look like it inherited old work;
- cleanup is unclear because browser state, generated previews, analysis cache,
  source media, and final renders are not represented as one user-facing
  project.

The product needs an explicit local project model before the app shell becomes
the normal entrypoint.

## Decision

Introduce a durable local project catalog and treat each import as a project.

Default runtime layout:

```text
Documents/
  CUTED Workspace/
    projects/
      <project-id>/
        project.json
        moments.json
        project-state.json
        index.html
        clips/
        frames/
        waveforms/
        overlay-assets/
        camera-analysis/
        captioned-clips/
        _source/

Videos/
  CUTED Renders/
    <project-id>/
      *.mp4

%LOCALAPPDATA%/
  CUTED/
    projects.json
    cuted-launch.lock
    logs/
```

The project folder is the source of truth for project content. The browser may
cache UI state for responsiveness, but it must be scoped by project id and must
not define project identity.

## Project Catalog

`projects.json` should store lightweight metadata only:

```json
{
  "version": 1,
  "recent": [
    {
      "id": "20260612-143012-example",
      "title": "Podcast example",
      "path": "C:/Users/.../Documents/CUTED Workspace/projects/20260612-143012-example",
      "created_at": "2026-06-12T14:30:12-03:00",
      "last_opened_at": "2026-06-12T15:02:44-03:00",
      "status": "ready",
      "clip_count": 10,
      "render_count": 3,
      "size_bytes": 123456789
    }
  ]
}
```

The catalog must not contain secrets, transcripts in full, raw provider payloads,
or private media content.

## Project State

`project-state.json` should replace global browser state over time.

It should include:

- selected clips and statuses;
- trim values;
- active resolution/platform edits;
- camera paths and director plans;
- overlays and image asset references;
- bumper references;
- caption settings;
- render queue state.

It should not include:

- OpenAI API keys;
- large base64 image/video payloads after materialization;
- browser-only layout flags that are safe to forget.

## Browser State

Use browser storage only as a short-term cache.

Rules:

- key by project id, not just `cutted-state`;
- clear or ignore unrelated project keys when opening a project;
- always hydrate from project files when possible;
- write back to project state during meaningful edits;
- allow recovery from localStorage only as a fallback when project save fails.

## Cleanup Model

Project cleanup has three levels:

```text
Remove from recents
  Catalog-only. Files remain on disk.

Clean project cache
  Removes generated temporary artifacts, keeping project metadata and final
  renders.

Delete project
  Moves the project folder to Recycle Bin when possible. Final renders are kept
  by default unless the user opts in to delete them too.
```

Cache cleanup may remove:

- preview clips;
- frames;
- waveforms;
- visual maps and camera-analysis cache;
- caption temp files;
- unused overlay materializations;
- old logs scoped to the project.

Cache cleanup must not remove:

- `project.json`;
- `moments.json`;
- `project-state.json`;
- user-selected source media outside the workspace;
- final rendered MP4s by default.

## Sample Folders

Repository `samples/` remain development fixtures and QA evidence.

The app should not treat repo samples as user projects unless opened explicitly
in dev mode. User-facing project history should prefer
`Documents/CUTED Workspace/projects`.

## Consequences

Positive:

- CUTED launch becomes predictable.
- New project is truly clean.
- Users can return to previous work intentionally.
- Cleanup can free disk space without surprising deletion.
- Future installer behavior becomes easier to explain and test.

Negative:

- Requires migration code from current `localStorage` and generated HTML state.
- Requires a project catalog API.
- Requires careful QA around deletion and cache cleanup.
- Existing samples need a compatibility path for development.

## Validation

- Launch with no active project opens Project Home.
- Create new project twice; the second project does not inherit first project
  title, cards, state, visual maps, render queue, or localStorage.
- Open recent project restores its cards and edits.
- Remove from recents leaves files on disk.
- Clean cache keeps final renders and project metadata.
- Delete project asks for explicit confirmation and moves files to Recycle Bin
  when available.
- Repo samples remain openable with `serve --dir` for QA.
