# PLAN-003 - Editor Entry And Import Loading Fixes

## Workflow Read

Context understood:

- Eduardo observed two UX regressions while testing a local imported project.
- The app is still a local web UI during development, but remains a future
  Windows desktop product.
- The fix belongs to the generated local workspace, not to hosted web
  deployment.

Request type: spec plus implementation pipeline.

Risk level: medium. The changes are small, but they touch first-run editor
state, loading feedback, generated HTML, and browser smoke behavior.

Recommended mode:

1. Spec lock.
2. Local implementation.
3. Targeted unit tests.
4. Browser smoke on a local project.

Approval needed before changes: no for local implementation; yes before commit,
push, PR, merge, installer, or destructive cleanup.

## Problems

### Problem 1 - SEO Loading Step Starts Done

During import loading, the SEO/publication intelligence step appears green
before it has participated in the loading sequence.

Expected behavior:

- `SEO` starts idle like every later step.
- It becomes active only after `Previews`.
- It turns done/green only when the `publish` stage actually completes.
- Then `Editor` becomes active.

Current evidence:

- Backend import progress emits `publish` after preview rendering in
  `tools/cutted/scripts/cutted.py`.
- Home loading HTML already contains `<li data-import-step="publish">SEO</li>`.
- Frontend `importStageOrder` currently omits `publish`, so the step index logic
  can mark it incorrectly relative to `editor`.

Likely root cause:

```text
importStageOrder = prepare, media, audio, analysis, suggestions, previews, editor
loading UI has: prepare, media, audio, analysis, suggestions, previews, publish, editor
```

The UI sequence and emitted progress sequence are out of sync.

### Problem 2 - First Edit Card Opens Automatically

After import completes and CUTED enters the `Editar` workspace, the first clip
dropdown/card appears open by default.

Expected behavior:

- All clip cards start closed.
- No preview video loads until the user opens a card.
- The user decides which clip to inspect first.
- Opening one card still closes any other open card and loads only that preview.

Current evidence:

- `card_html(moment)` adds `open` when `moment.rank == 1`.
- Startup JS calls `activateCard(card)` for cards that are already open.
- The spec now says all Edit cards should start closed after import.

## Product Rules

- Loading feedback must be sequential and honest. No step should look complete
  before its own work has happened.
- Green means complete, ready, or positive completion. It should not mean "will
  happen later."
- The editor should not assume which cut the user wants to open first.
- Closed cards should remain cheap: no video preview source loaded by default.

## Implementation Pipeline

### Phase 0 - Baseline

Files to inspect:

- `tools/cutted/scripts/cutted.py`
- `tests/test_cutted_import_ui.py`
- `docs/qa/REGRESSION_MATRIX.md`
- `docs/product/SPEC-001-review-workspace.md`

Baseline checks:

```powershell
python tests/test_cutted_import_ui.py
python -m py_compile tools/cutted/scripts/cutted.py
```

If system `python` is unavailable in Codex Desktop, use the bundled Codex
Python path from workspace dependencies.

### Phase 1 - Spec Lock

Keep these expected behaviors documented:

- `docs/product/SPEC-001-review-workspace.md`: Edit cards start closed after
  import.
- `docs/qa/REGRESSION_MATRIX.md`: SEO loading step participates between
  Previews and Editor.
- This plan: implementation checklist and QA path.

### Phase 2 - Fix SEO Loading Sequence

Implementation target:

- Frontend loading JS inside `project_home_js(...)` in
  `tools/cutted/scripts/cutted.py`.

Expected code change:

```js
const importStageOrder = [
  "prepare",
  "media",
  "audio",
  "analysis",
  "suggestions",
  "previews",
  "publish",
  "editor"
];
```

Also verify:

- `emit_import_progress("publish", ...)` remains after preview rendering and
  before editor assembly.
- `project_home_import_loading_html(...)` keeps the `publish` list item between
  `previews` and `editor`.
- `updateImportSteps(stage)` handles unknown stages defensively so a future step
  cannot make all steps appear done.

Recommended hardening:

```js
const currentIndex = importStageOrder.includes(stage)
  ? importStageOrder.indexOf(stage)
  : 0;
```

### Phase 3 - Fix Closed Edit Entry

Implementation target:

- `card_html(moment)` in `tools/cutted/scripts/cutted.py`.
- Startup card bootstrap in the generated JS in the same file.

Expected code change:

- Remove the rank-based `open_attr`.
- Generate every edit card as closed by default.
- Keep the existing summary click behavior that toggles a card.
- Keep `activateCard(card)` only as a response to a user-opened or already
  explicitly-restored card.

Important constraint:

- Do not remove `activateCard(card)` entirely; it still owns the single active
  preview behavior after a card opens.

### Phase 4 - Tests

Add or update tests in `tests/test_cutted_import_ui.py`.

Suggested tests:

1. `test_import_loading_stage_order_includes_publish_before_editor`

Expected assertions:

- generated page JS contains `const importStageOrder`;
- `"publish"` appears before `"editor"`;
- loading HTML contains `data-import-step="publish"`;
- `updateImportSteps` does not treat an unknown stage as the last known step.

2. `test_edit_cards_start_closed_after_import`

Expected assertions:

- `card_html(Moment(rank=1, ...))` does not include `<details ... open>`;
- `card_html(Moment(rank=2, ...))` also stays closed;
- generated JS still contains the click path that toggles `card.open` and calls
  `activateCard(card)`.

3. Existing tests to preserve:

- control surface slot exists in cards;
- only active/open cards display live timeline;
- workspace opens the Edit surface by default.

### Phase 5 - Browser Smoke

Use the current local dev server or launch a fresh isolated workspace:

```powershell
python tools/cutted/scripts/cutted.py launch --no-browser
```

Smoke path:

1. Start from Project Home.
2. Import or recover a small local project.
3. Watch the loading rail:
   - Project -> Media -> Audio -> Analysis -> Cuts -> Previews -> SEO -> Editor.
4. Confirm `SEO` is not green before the `publish` stage.
5. Confirm `SEO` becomes active after Previews.
6. Confirm after navigation to Edit all clip cards are closed.
7. Open one card and confirm only that card loads preview media.
8. Open another card and confirm the first card closes.

Browser checks:

- No console errors.
- No horizontal overflow.
- Video source is absent on closed cards and present only after opening one
  card.

### Phase 6 - QA Commands

Minimum:

```powershell
python tests/test_cutted_import_ui.py
python -m unittest discover -s tests -p "test_*.py"
python -m py_compile tools/cutted/scripts/cutted.py
```

If the change also touches live timeline or extracted control bar assets:

```powershell
cd prototypes/live-timeline
npm ci
npm run build:lib
```

### Phase 7 - GitHub Path

Only when Eduardo asks to prepare on GitHub:

1. Review `git status` and diff.
2. Create branch `codex/editor-entry-import-loading-fixes`.
3. Stage only scoped files.
4. Run the QA commands above.
5. Commit with a message like:

```text
Fix import loading order and closed editor entry
```

6. Push and open a draft PR.

## Acceptance Criteria

- SEO loading step starts idle.
- SEO loading step becomes active only after Previews.
- SEO loading step turns green/done only before Editor starts.
- Edit workspace loads with all clip cards closed.
- Opening a card remains explicit user action.
- Only one card preview is active at a time.
- Existing render, caption, platform, control surface, and live timeline tests
  still pass.

## Out Of Scope

- Redesigning the import loading screen.
- Reworking the control bar.
- Changing AI provider behavior.
- Changing publish metadata generation.
- Moving files into `apps/` or `packages/`.
- Creating commits, PRs, or release artifacts without an explicit request.
