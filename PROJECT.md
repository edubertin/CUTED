# Project

## Identity

- Product: CUTED
- Status: local-first Windows desktop public beta
- Audience: creators and operators turning long-form videos into short-form clips
- Business goal: ship a free, open-source Windows app that runs heavy video processing on the user's computer instead of in a cloud web app

## Current State

- Active phase: public Windows beta with a first-class local desktop shell and public product site
- Production status: source and unsigned Windows installer are public as a prerelease
- Release status: `v2026.07.17-beta.1` is published through GitHub Releases; build and installer tooling live under `packaging/`
- Open decisions:
  - When code signing should be added to reduce SmartScreen friction.
  - Whether a future stable distribution should add MSIX/Microsoft Store alongside the direct Inno Setup download.
  - How much desktop-shell polish is required before the first stable release.
  - Whether YOLO/PyTorch remains in the public package or is replaced by a smaller ONNX route.
  - When to split the current reference implementation into app/package boundaries.
  - How much local project state should move from browser `localStorage` into `project-state.json` before a stable release.

## Product Direction

CUTED is not planned as a hosted web/SaaS product. During development it can
and should run as a local web app/browser UI because that keeps iteration fast.
For users, the compiled product surface should be packaged and distributed as a
Windows desktop app. The core reasons are large media files, heavy FFmpeg/render
work, local vision processing, privacy, and avoiding early cloud infrastructure
costs.

The target runtime is:

```text
Development
  local web app/browser UI
  local server on 127.0.0.1

Compiled product
  Windows desktop launcher/app package
  local launcher
  local server on 127.0.0.1
  local browser/editor UI
  local workspace under Documents/CUTED Workspace
  final renders under Videos/CUTED Renders
```

Future Microsoft distribution should be treated as a Windows packaging/release path, not as a cloud hosting path.

## Stack

- App/runtime: Python 3.12 reference implementation in `tools/cutted/scripts/cutted.py`
- UI: generated local HTML/CSS/JS plus extracted prototype assets
- Rendering: FFmpeg via local subprocess
- Vision: local OpenCV fallback, YOLO visual map path when available
- AI: optional OpenAI API configuration; never embedded in code
- Development surface: local web app/browser UI
- Compiled user surface: Windows desktop app that opens/hosts the local browser/editor UI
- Packaging: PyInstaller/Inno Setup plan under `packaging/`
- CI: GitHub Actions on Windows
- Database: none in production cloud; local JSON/project files are the working data store
- Hosting: no hosted product runtime; the presentation/download site runs on OpenAI Sites and binaries remain on GitHub Releases
- Observability: local logs and planned diagnostics bundle

## Repository Map

- `tools/cutted/`: current reference implementation and local Codex skill copy.
- `tools/cutted/scripts/cutted.py`: analyzer, local API, Project Home, render pipeline, camera analysis, generated UI.
- `tools/cutted/assets/`: extracted local UI assets copied into generated workspaces.
- `docs/`: durable product, architecture, QA, and operations documentation.
- `packaging/`: Windows executable and installer plans/scripts.
- `prototypes/`: UI/runtime spikes that inform the local app shell.
- `assets/brand/`: source brand assets.
- `assets/social/`: versioned social/channel assets.
- `apps/site/`: public presentation and download page; it does not host the CUTED runtime.
- `channels/`: editorial/channel operations for CUTED Now; may later move to `content/`.
- `tests/`: Python regression tests for the current reference implementation.
- `samples/`: local development fixtures/evidence only; generated videos must not be committed.
- `.github/`: CI workflow.

## Target Structure Plan

Do not move folders just for symmetry. CUTED currently fits the standard as an existing project with documented exceptions.

Recommended future shape when extraction is justified:

```text
apps/web/                # local development UI, never a hosted SaaS target
apps/desktop/            # Windows launcher/app shell when separated from the script
packages/cuted-core/     # data contracts, project model, queue logic
packages/cuted-renderer/ # FFmpeg rendering and manifest behavior
packages/cuted-ai/       # provider adapters, transcription, cost ledger
packages/cuted-ui/       # reusable local editor UI assets/components
tools/cutted/            # legacy reference CLI and migration bridge until retired
content/tiktok/          # optional future home for channel operations
experiments/             # optional future home for prototypes after migration
```

`apps/web` is valid for the local development UI. It should not imply hosted
deployment, cloud render, web auth, or SaaS. `apps/desktop` is the compiled
Windows product shell, and `packages/cuted-ui` should hold reusable UI code
when extraction is justified. Existing `tools/cutted/` and `cutted.py` names are
legacy compatibility paths; future module and package names should use
CUTED/Cuted with one `t`.

## Commands

- Start sample server: `python tools/cutted/scripts/cutted.py serve --dir "samples/<sample-folder>" --port 8779`
- Launch local app shell: `python tools/cutted/scripts/cutted.py launch`
- Python tests: `python -m unittest discover -s tests -p "test_*.py"`
- Compile script: `python -m py_compile tools/cutted/scripts/cutted.py`
- Live timeline install: `cd prototypes/live-timeline && npm ci`
- Live timeline build: `cd prototypes/live-timeline && npm run build:lib`
- CI-equivalent local check: run Python tests, script compile, and live timeline build.

If `python` is not available on this Windows machine, use the bundled Codex Python path shown by the local workspace dependency tool.

## Required Docs Before Implementation

- Product overview: `docs/product/PRD.md`
- Data contracts: `docs/architecture/DATA_CONTRACTS.md`
- Render pipeline: `docs/architecture/RENDER_PIPELINE.md`
- Engine extraction: `docs/architecture/ADR-0006-cuted-engine-incremental-extraction.md`
- Local project model: `docs/architecture/ADR-0005-local-project-memory-and-cleanup.md`
- Project Home plan: `docs/product/PLAN-001-project-home-clean-workspace-implementation.md`
- Desktop structure plan: `docs/product/PLAN-002-local-desktop-repository-structure.md`
- Local beta installer: `docs/product/SPEC-011-local-beta-installer.md`
- Windows packaging plan: `packaging/PLANO-EXECUTAVEL-WINDOWS.md`
- QA matrix: `docs/qa/REGRESSION_MATRIX.md`
- Local dev runbook: `docs/operations/LOCAL_DEV.md`

## Safety

- Secrets: never read or commit `.env`, `.env.local`, `.env.*.local`, API keys, certificates, private keys, or installer signing material.
- User data: source videos, transcripts, generated previews, camera analysis, final MP4s, and local project folders are private user data unless explicitly created as safe fixtures.
- Generated outputs: keep generated media in `Documents/CUTED Workspace`, `Videos/CUTED Renders`, local archives, or ignored folders.
- Repo samples: use only for dev evidence/fixtures; do not make repo `samples/` the default user workspace.
- Destructive actions: project deletion, cache cleanup, build cleanup, and installer uninstall behavior require explicit confirmation and must preserve final renders by default.
- Public binary releases: the first unsigned beta is published with its limitations disclosed. Its FFmpeg/GPL version, hash, license, and corresponding-source evidence is still an active compliance gap and must be regularized for the current distribution. Reassess Ultralytics/AGPL, H.264/AAC patent exposure, code signing, Microsoft Store/MSIX requirements, privacy disclosures, support diagnostics, and all dependency obligations before each later release.

## Next Implementation Slice

The next repository-structure slice should be documentation and boundary alignment, not file moves:

1. Keep `tools/cutted` as the reference implementation.
2. Keep the ADR-0001 desktop/local-web note current, and write a full replacement ADR before a real code migration.
3. Finish project-scoped state persistence before splitting packages.
4. Move channel operations to `content/` only when social operations grow.
5. Move prototypes to `experiments/` only when a migration branch can update docs and CI together.
