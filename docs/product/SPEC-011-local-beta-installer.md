# SPEC-011: Local Beta Installer

## Objective

Ship CUTED Phase 1 as a complete local beta that non-technical friends can
install, open, process videos, render final clips, and find their exported files
without using Codex, Python commands, Docker, or a cloud render server.

## Context

CUTED is currently local-first. The browser workspace generates JSON state, the
local Python server receives `/api/finalize`, and FFmpeg renders outputs into
the generated job folder. This keeps media private and avoids early cloud costs
from uploading source videos, storing preview assets, rendering multiple MP4
variants, and serving final downloads.

The current prototype still requires command-line operation:

```powershell
python tools/cutted/scripts/cutted.py serve --dir "samples/<sample-folder>" --port 8779
```

Phase 1 should replace that operator workflow with a simple install-and-open
desktop experience.

## Agents Consulted

- Workflow: treat this as a medium/high-risk implementation plan because it
  touches packaging, local filesystem behavior, user installation, and support.
- Product Manager: keep the MVP ruthlessly focused on local beta validation,
  not SaaS, billing, collaboration, or cloud rendering.
- Architect: preserve the local render pipeline and isolate the future
  installer/app shell from the current reference implementation.
- Developer: prefer the shortest reliable packaging path before a larger app
  migration.
- QA Engineer: define smoke checks for installer, first run, render, cleanup,
  and recoverability.

## Recommendation

Build Phase 1 as a Windows-first local installer.

Primary path:

```text
CUTED Installer
  -> installs CUTED local runtime
  -> bundles or locates FFmpeg
  -> starts a local server on 127.0.0.1
  -> opens the CUTED workspace in the browser
  -> stores jobs in the user's CUTED Workspace
  -> exports final MP4 files to CUTED Renders
```

Do not build a cloud SaaS render path in Phase 1.

## Phase 1 Scope

### In Scope

- Windows beta installer for friends.
- One-click launch shortcut.
- Local workspace folder outside the git repository.
- Local import flow for video files.
- Local processing using the existing `cutted.py` implementation.
- Local gallery server on `127.0.0.1`.
- Automatic browser open after launch.
- Final exports copied to a clear user-facing folder.
- Basic cleanup controls for large temporary files.
- Installer/readme support instructions.
- Smoke tests and release checklist.

### Out of Scope

- Public web app with login.
- Cloud render workers.
- Multi-user collaboration.
- Billing or subscriptions.
- Social platform publishing.
- Mac installer.
- Mobile app.
- Automatic cloud backup of source videos.
- Uploading raw source videos to object storage.

## Target User Flow

1. User downloads `CUTED Setup.exe`.
2. User installs CUTED.
3. User opens CUTED from Start Menu or Desktop shortcut.
4. CUTED starts the local server.
5. CUTED opens `http://127.0.0.1:<port>/`.
6. User imports a local video.
7. CUTED creates a job folder under `Documents/CUTED Workspace`.
8. User reviews/edit clips in the browser workspace.
9. User renders selected outputs.
10. Final MP4 files appear under `Videos/CUTED Renders/<job>/`.
11. User can open the render folder from the UI.

## Proposed Folder Layout

```text
Documents/
  CUTED Workspace/
    jobs/
      <job-id>/
        import-request.json
        moments.json
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
    <job-id>/
      clip-001-tiktok-captioned.mp4
      clip-001-youtube-captioned.mp4
```

`_source/`, preview clips, waveforms, and camera-analysis caches are local
workspace artifacts. Final MP4s are the user-facing deliverables.

## Technical Plan

### Step 1: Stabilize Local Runtime Entrypoint

Create a small launcher entrypoint around the current script.

Responsibilities:

- choose a free localhost port;
- create the CUTED workspace folders;
- start the local server;
- open the default browser;
- write a local runtime log;
- show a user-safe error when FFmpeg or dependencies fail.

Suggested command shape:

```powershell
cuted.exe launch
```

### Step 2: Separate Workspace From Repository Samples

Add a first-run default:

```text
Documents/CUTED Workspace/jobs
Videos/CUTED Renders
```

The repo `samples/` folder should remain development evidence, not the default
runtime location for friends.

### Step 3: Add Import-To-Workspace Flow

Use the existing local import behavior, but ensure the generated job folder is
created under the user workspace and records:

```text
source_path
output_path
created_at
preset
clip_count
duration_profile
```

### Step 4: Bundle FFmpeg Strategy

Pick one Phase 1 approach:

- Preferred for non-technical testers: bundle FFmpeg with the installer.
- Fallback: if bundling is blocked, download or locate FFmpeg during setup with
  a clear support message.

The launcher should never require the user to edit PATH manually.

### Step 5: Package The Python Runtime

Evaluate PyInstaller first because the existing implementation is Python-first.

Expected output:

```text
dist/CUTED/
  cuted.exe
  ffmpeg/
  assets/
  runtime files
```

If PyInstaller becomes brittle with OpenCV/Whisper/YT-DLP dependencies, fallback
to a folder-based portable runtime before attempting a full desktop rewrite.

### Step 6: Build Windows Installer

Use a simple Windows installer after the portable build works.

Options:

- Inno Setup: practical for a Windows beta installer.
- NSIS: also viable.
- MSIX: better later, but can add signing and packaging complexity.

Installer responsibilities:

- install app files;
- create Start Menu shortcut;
- optionally create Desktop shortcut;
- avoid requiring admin when possible;
- include uninstall support.

### Step 7: Add Cleanup Controls

Because video jobs can become very large, Phase 1 needs a simple cleanup model:

- keep final renders by default;
- allow deleting preview/source/cache files per job;
- warn before deleting source-derived workspace artifacts;
- show approximate job size in the UI or support screen.

Minimum beta acceptable version: document a manual cleanup folder and add a
launcher/support command to open the workspace.

### Step 8: Add Beta Support Diagnostics

Add a support bundle command:

```powershell
cuted.exe diagnostics
```

It should collect safe metadata only:

- app version;
- Windows version;
- FFmpeg availability;
- workspace path;
- latest job ids;
- sanitized recent logs;
- no source videos;
- no full transcripts by default;
- no API keys or secrets.

### Step 9: Release Checklist

Before sending to friends:

- install on a clean Windows machine;
- launch without Python installed;
- import one local MP4;
- generate clips;
- open review workspace;
- render one TikTok output;
- verify final MP4 path under `Videos/CUTED Renders`;
- restart app and reopen existing job;
- run cleanup on a job copy;
- uninstall and verify user renders are not deleted.

## Feasibility In Current Codex Session

With only a small amount of remaining GPT/Codex usage in this thread, completing
the entire Phase 1 installer implementation end-to-end is not realistic. The
full implementation needs packaging experiments, dependency bundling, clean
machine testing, installer iteration, and render smoke tests.

What is realistic now:

- save this implementation plan;
- identify the first implementation slice;
- start a new focused thread for the Windows portable launcher;
- then turn the portable build into an installer after it runs locally.

## Recommended Implementation Slices

### Slice A: Portable Local Launcher

Goal: `cuted.exe launch` opens CUTED locally without manual Python commands.

Deliverables:

- launcher entrypoint;
- workspace folder creation;
- free-port selection;
- browser open;
- logs;
- minimal smoke test.

### Slice B: Workspace Import Defaults

Goal: generated jobs no longer default to repo `samples/`.

Deliverables:

- `Documents/CUTED Workspace/jobs`;
- `Videos/CUTED Renders`;
- import metadata;
- UI copy/path validation.

### Slice C: Portable Build

Goal: build a folder-based portable CUTED runtime.

Deliverables:

- PyInstaller or equivalent build script;
- bundled runtime assets;
- FFmpeg strategy;
- launch test on the development machine.

### Slice D: Installer

Goal: produce `CUTED Setup.exe`.

Deliverables:

- installer script;
- shortcuts;
- uninstall behavior;
- clean-machine QA checklist.

### Slice E: Beta Hardening

Goal: reduce support pain before sending to friends.

Deliverables:

- cleanup command or UI;
- diagnostics command;
- user-facing quickstart;
- known issues doc.

## Decision

Proceed with Phase 1 as a Windows-first local installer path, starting with a
portable launcher. Defer cloud login/render until after friends validate the
local workflow and the team has real data on job size, render time, failure
rate, and support burden.

