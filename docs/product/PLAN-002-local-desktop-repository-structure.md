# PLAN-002 - Local Desktop Repository Structure

## Objective

Align CUTED's repository direction with the current product decision: CUTED can
run as a local web app/browser UI during development, but the compiled product
is a local Windows desktop app. It is not a hosted web app.

This plan is intentionally structural. It does not move files by itself.

## Current Assessment

The repository is healthy for the current stage:

- `tools/cutted/` holds the reference implementation.
- `docs/` has strong product, architecture, QA, and operations context.
- `packaging/` already owns Windows executable and installer planning.
- `prototypes/` contains UI spikes that can inform the local app shell.
- `assets/` contains versioned source assets.
- `channels/` contains social/editorial operations.
- `samples/` is local dev evidence and currently has no tracked files.

The main mismatch is naming and future-boundary language. `apps/web` is useful
for the local development UI, but it must not be interpreted as hosted SaaS.
The distribution model is Windows desktop/local.

## Product Assumptions

- Heavy processing should run on the user's computer.
- Source media and generated project files should stay local by default.
- The first sellable product is Windows-first.
- The development UI can run as a web app locally.
- Microsoft Store/MSIX can be evaluated later, after the local installer path is
  reliable.
- Cloud render, hosted database, auth, team collaboration, and billing are out of
  scope until explicitly reopened.

## Target Repository Shape

Do not create these folders until there is implementation pressure. This is the
target grammar for future extraction:

```text
repo/
  AGENTS.md
  PROJECT.md
  README.md
  apps/
    web/
    desktop/
  packages/
    cuted-core/
    cuted-renderer/
    cuted-ai/
    cuted-ui/
  tools/
    cutted/
  docs/
  assets/
  content/
  fixtures/
  infra/
  experiments/
  packaging/
```

Intent:

- `apps/desktop/`: packaged Windows app shell, launcher, local app composition,
  installer-facing entrypoints.
- `apps/web/`: local development browser UI. It can run on `127.0.0.1`, but is
  not a hosted deployment target.
- `packages/cuted-core/`: project model, data contracts, queue logic, platform
  presets, safe path rules.
- `packages/cuted-renderer/`: FFmpeg graph construction, render jobs, manifests,
  output copying.
- `packages/cuted-ai/`: OpenAI/local provider adapters, transcription,
  selection, cost ledger, visual director integration.
- `packages/cuted-ui/`: reusable local editor UI assets/components, timeline,
  control surfaces.
- `tools/cutted/`: legacy/reference CLI and bridge until all extracted modules
  are proven.
- `content/`: future home for `channels/` if social operations grow.
- `experiments/`: future home for `prototypes/` if spike volume grows.
- `fixtures/`: small safe test fixtures only; no private media.
- `infra/`: only if release infrastructure grows beyond tool-native files.

## What Should Not Move Yet

- Do not move `tools/cutted/scripts/cutted.py` until package boundaries are
  tested.
- Do not move `packaging/`; it already has a clear responsibility.
- Do not move `channels/` until there is a broader content migration.
- Do not move `prototypes/` until docs and CI references can be updated in the
  same branch.
- Do not create empty `apps/` or `packages/` folders just to match the target.

## Recommended Phases

### Phase 0 - Context Alignment

Status: complete for the root context files; keep them current as the product
changes.

- Add `PROJECT.md`.
- Add root `AGENTS.md`.
- Record that `apps/web` means local development UI, while `apps/desktop` means
  compiled Windows product shell.
- Keep current folders stable.

Acceptance:

- A new Codex thread can understand the product direction in under five minutes.
- Local Windows direction is explicit.
- Generated output policy is explicit.

### Phase 1 - ADR Correction

ADR-0001 now carries a local web plus desktop-direction note. Before a real code
migration, either update it fully or add a new ADR that clarifies the split
between `apps/web` and `apps/desktop`.

New decision:

```text
apps/desktop
apps/web
packages/cuted-core
packages/cuted-renderer
packages/cuted-ai
packages/cuted-ui
tools/cutted
```

Acceptance:

- No durable doc presents hosted web as the normal product target.
- Local browser UI is described as a development/runtime surface.
- Desktop is described as the compiled distribution surface.

### Phase 2 - Stabilize Local Project State

Before code extraction, finish the local project model:

- `project.json`
- `project-state.json`
- project-scoped browser cache
- render manifests
- cleanup rules
- diagnostics-safe metadata

Acceptance:

- Two projects do not share browser state.
- Clearing browser storage does not destroy meaningful edits.
- Project cleanup preserves final renders by default.

### Phase 3 - Extract Core Contracts

Create packages only when code starts moving:

- `packages/cuted-core`
- tests for project/catalog/queue/path rules
- typed data-contract documentation or schemas

Acceptance:

- The reference script can call the package or share fixtures with it.
- Behavior remains covered by existing tests.

### Phase 4 - Extract Renderer

Move FFmpeg/render logic behind package boundaries after contracts are stable.

Acceptance:

- A render queue can be processed without generated HTML assumptions.
- Existing overlay/caption/camera/bumpers regression cases still pass.

### Phase 5 - Local Web And Desktop App Shells

Introduce `apps/web` and `apps/desktop` only when the app shell needs its own
source boundary.

Acceptance:

- `apps/web` can run the local development UI.
- `cuted.exe launch` or equivalent starts the local app.
- User workspace defaults outside the repo.
- Installer-facing assets and version metadata are clear.

### Phase 6 - Content And Experiment Cleanup

Only after product code boundaries settle:

- consider moving `channels/` to `content/tiktok/`;
- consider moving `prototypes/` to `experiments/`;
- update docs and CI in the same branch.

Acceptance:

- No broken docs, CI paths, or asset references.
- Moves are reversible and reviewed separately from behavior changes.

## Microsoft / Windows Commercial Path

Treat Microsoft distribution as a release channel, not an architecture change.

Near term:

- Inno Setup or portable `onedir` beta.
- Unsigned/private tester workflow documented.
- No auto-update unless explicitly scoped.

Later:

- Code signing.
- MSIX/Microsoft Store feasibility.
- Store privacy and data disclosures.
- License review for FFmpeg, H.264/AAC, Ultralytics/AGPL, OpenCV, yt-dlp, and
  any bundled models.
- Installer/update/uninstall QA on clean Windows machines.

## Risks

- Premature package split could slow current MVP iteration.
- Leaving all behavior inside one Python script makes onboarding harder over
  time.
- `apps/web` naming could mislead future agents toward cloud/web assumptions if
  not documented as local development only.
- Bundling YOLO/PyTorch may make the Windows installer too large for commercial
  distribution.
- Generated media can grow quickly and must stay outside Git.

## Next Safe Action

Create or update documentation first:

1. Keep `PROJECT.md` and `AGENTS.md` current.
2. Use this plan as the repository-structure map.
3. Write a full follow-up ADR before moving code into `apps/web`,
   `apps/desktop`, or `packages/*`.

No folder migration is recommended until after the ADR correction and project
state persistence work are reviewed.
