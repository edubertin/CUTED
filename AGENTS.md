# CUTED Agent Instructions

## Local Context

Before changing CUTED, read these files in order:

1. `PROJECT.md`
2. `README.md`
3. `docs/README.md`
4. The specific product/architecture docs for the task
5. `docs/qa/REGRESSION_MATRIX.md` before UI/render/pipeline changes
6. `docs/operations/LOCAL_DEV.md` before running local servers or render smoke tests

There are currently no project-local specialist agents. Use global specialists only when the task needs them.

## Product Direction

CUTED is a local Windows app for users, not a hosted web/SaaS product. During
development, it may run as a local web app/browser UI on `127.0.0.1`. The
compiled product should process videos on the user's computer and store project
data locally.

Do not introduce cloud rendering, hosted databases, public auth, multi-user
collaboration, billing, or hosted web deployment unless Eduardo explicitly asks
for that product direction.

Future commercial distribution should be treated as a Windows packaging/release concern, likely involving Inno Setup, MSIX/Microsoft Store evaluation, code signing, local diagnostics, and installer QA.

## Repository Boundaries

- `tools/cutted/` is the current reference implementation. Keep it working until replacement modules have equivalent QA coverage.
- `packaging/` owns Windows executable and installer work.
- `prototypes/` contains spikes. Do not wire a prototype into production behavior unless the task explicitly asks for that integration.
- `assets/` contains safe source assets. Do not store generated video outputs there.
- `channels/` contains social/editorial operations. Treat it as content-like, not application code.
- `samples/` is dev evidence/fixtures only. User projects should live outside the repo.

Do not move folders to `apps/`, `packages/`, `content/`, or `experiments/` just for structure symmetry. Plan migrations first, then make reversible moves on a dedicated branch.

## Commands

Use the system Python when available:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile tools/cutted/scripts/cutted.py
python tools/cutted/scripts/cutted.py launch
python tools/cutted/scripts/cutted.py serve --dir "samples/<sample-folder>" --port 8779
```

If `python` is not available in this Codex desktop session, use the bundled Codex Python discovered via workspace dependencies.

Live timeline checks:

```powershell
cd prototypes/live-timeline
npm ci
npm run build:lib
```

CI runs these checks on Windows:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile tools/cutted/scripts/cutted.py
cd prototypes/live-timeline && npm ci && npm run build:lib
```

## QA Expectations

For docs-only changes, review links and repository status.

For Python behavior changes, run:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile tools/cutted/scripts/cutted.py
```

For Project Home, editor UI, render queue, or visual assets, run targeted tests plus a browser smoke test on an isolated temporary workspace when practical.

For render pipeline changes, run at least one real local render smoke when media and FFmpeg are available. Do not commit generated MP4 outputs.

For packaging changes, prefer a staged path:

1. launcher smoke on dev machine;
2. PyInstaller folder build;
3. installer build;
4. clean Windows machine smoke;
5. uninstall/data-preservation check.

## Safety Rules

- Never read or commit `.env`, `.env.local`, `.env.*.local`, certificates, signing keys, private keys, or credentials.
- Never embed OpenAI keys or any other secret in code, generated HTML, installer files, or docs.
- Do not print raw private paths, transcripts, payloads, or user media metadata unless needed for a local debug report and safe to share.
- Do not commit imported source videos, preview clips, rendered MP4s, captioned outputs, local workspaces, or build artifacts.
- Preserve final renders by default during cleanup, uninstall, and project deletion.
- Prefer Recycle Bin for destructive local project deletion when available.
- Do not push, merge, publish, submit builds, or create releases unless Eduardo explicitly asks in the current message.

## Generated Output Policy

Generated or local-only outputs belong outside Git:

```text
Documents/CUTED Workspace/
Videos/CUTED Renders/
%LOCALAPPDATA%/CUTED/
%USERPROFILE%/.cuted/
packaging/dist/
packaging/build/
prototypes/live-timeline/dist-lib/
prototypes/live-timeline/node_modules/
samples/**/clips/
samples/**/captioned-clips/
samples/**/_source/
samples/**/camera-analysis/
samples/**/*.mp4
```

Only commit small, intentional fixtures, manifests, source assets, docs, scripts, and tests.

## Approval Gates

Ask before:

- moving or deleting folders;
- cleaning user projects or generated media;
- changing installer uninstall behavior;
- changing secret storage;
- adding cloud services or hosted storage;
- changing commercial distribution assumptions;
- packaging or publishing a Windows installer;
- merging to `main` or pushing a branch.

## Current Structure Plan

The desired future structure separates local web development from the compiled
desktop product:

```text
apps/web/
apps/desktop/
packages/cuted-core/
packages/cuted-renderer/
packages/cuted-ai/
packages/cuted-ui/
tools/cutted/
```

`apps/web` is valid for local development. It must not be treated as a hosted
SaaS/deploy target unless Eduardo explicitly changes the product direction.
`apps/desktop` is the future compiled Windows app shell. `tools/cutted/` and
`cutted.py` are legacy compatibility paths; new module/package names should use
the CUTED/Cuted spelling with one `t`.
