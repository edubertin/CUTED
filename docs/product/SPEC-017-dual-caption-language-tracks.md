# SPEC-017 - Dual Caption Language Tracks

## Goal

Let CUTED prepare Portuguese captions during import, then let the editor generate
English captions on demand for a specific clip when the user chooses `EN` in the
Closed Caption toggle.

The feature should keep import fast for Brazilian users while still offering a
clear bilingual output path when English captions are actually needed.

## Context

CUTED is primarily aimed at Brazilian creators and operators. The default import
experience should therefore continue to produce Brazilian Portuguese captions and
Portuguese AI publishing copy. At the same time, many clips can be reused for
international audiences when English captions are available.

The current import flow already carries a `language` field into YouTube caption
selection, hosted transcription, local transcription, and generated
`caption_segments`. New imports default to `pt`. The first version prepared a
second English track during import, but real YouTube imports showed that this
made long imports wait on multiple hosted translation calls after previews were
already ready. This spec now moves English generation out of the import critical
path.

## Product Decision

Use a compact language toggle inside the Closed Caption area:

```text
Closed Caption    PT-BR | EN
```

Default selection: `PT-BR`.

The toggle changes:

- caption text shown in the browser preview;
- caption text sent to the final render queue;
- subtitle text burned into the final MP4.
- when `EN` is selected for a clip that has no English track yet, the editor
  generates only that clip's English captions and then switches to them.

The toggle does not change:

- the CUTED app UI language;
- AI publishing copy language;
- clip selection scoring;
- source media or generated preview clips.

AI publishing metadata remains Brazilian Portuguese in this first version unless
a future spec explicitly separates publishing language.

## Users

- Brazilian creators who edit primarily in Portuguese but want an English output
  option.
- Operators preparing multiple social exports from the same imported source.
- Reviewers who need to compare whether English captions still fit the clip
  timing before rendering.

## MVP Scope

- Keep Project Home import defaulted to Portuguese.
- During import, generate a primary `pt-BR` caption track.
- During import, mark the secondary `en` caption track as not generated.
- Generate a secondary `en` caption track only when the user selects `EN` for
  that specific clip.
- Store generated tracks in `moments.json` and refresh the embedded editor data.
- Keep legacy `caption_segments` populated from the primary `pt-BR` track.
- Add a compact `PT-BR / EN` segmented toggle in the Closed Caption controls.
- Switching the toggle updates visible caption preview without reimporting.
- Export/finalize includes the selected caption language.
- Final render burns captions from the selected track.
- If English generation is unavailable, keep the toggle visible but disable `EN`
  with a clear unavailable state.

## Out Of Scope

- Translating the full source video before clip selection.
- Translating the whole CUTED interface.
- Changing AI publishing metadata away from PT-BR.
- Adding more languages than PT-BR and EN.
- Realtime translation while the video plays.
- User-editable per-line translation UI.
- Cloud rendering, hosted storage, login, or collaboration.
- Reprocessing old projects automatically.

## Import Behavior

### Primary Track

The import keeps Portuguese as the canonical transcript language.

For YouTube sources:

1. Try `pt-orig,pt` captions first.
2. If captions are unavailable, transcribe with `language=pt`.
3. Produce candidate clips and `caption_segments` from this track.

For local files:

1. Transcribe with `language=pt`.
2. Produce candidate clips and `caption_segments` from this track.

### English Track

English captions are generated on demand after the selected moment exists and
the editor is open. The MVP should not translate the entire long-form source and
should not translate all selected clips during import. It should translate only
the current clip's caption segments when the user requests `EN`.

Preferred order:

1. If `caption_tracks.en.status = ready`, switch immediately.
2. Otherwise, POST the clip rank and `gallery_path` to the local caption track
   generation endpoint.
3. Translate the selected Portuguese caption segments to English.
4. Keep the original segment timestamps.
5. Require the translated track to preserve the same segment count and order.
6. Persist the generated track back into `moments.json` and the editor's
   embedded `window.CUTTED_DATA`.
7. If translation fails, keep `PT-BR` active and keep the project editable.

The translated English text should be natural, concise, and suitable for burned
short-form captions. It should not add explanations or change meaning.

## Data Contract

### `moments.json`

Each moment may include `caption_tracks`.

```json
{
  "rank": 1,
  "caption_segments": [
    { "start": 0.0, "end": 2.4, "text": "Legenda em portugues." }
  ],
  "caption_language_default": "pt-BR",
  "caption_tracks": {
    "pt-BR": {
      "label": "PT-BR",
      "status": "ready",
      "source": "youtube-caption",
      "segments": [
        { "start": 0.0, "end": 2.4, "text": "Legenda em portugues." }
      ]
    },
    "en": {
      "label": "EN",
      "status": "ready",
      "source": "translation",
      "segments": [
        { "start": 0.0, "end": 2.4, "text": "English caption." }
      ]
    }
  }
}
```

Supported track statuses:

```text
ready
unavailable
error
```

Compatibility rule: `caption_segments` remains the primary PT-BR track so older
render and queue paths still work.

### `caption-queue.json`

Queue rows should include the selected caption language and the available tracks.

```json
{
  "rank": 1,
  "caption_language": "en",
  "caption_tracks": {
    "pt-BR": { "status": "ready", "segments": [] },
    "en": { "status": "ready", "segments": [] }
  },
  "caption_segments": []
}
```

Queue rule: `caption_segments` should be the resolved active track at export
time, while `caption_tracks` preserves the alternatives for debugging and future
edits.

### `platform_edits`

If caption language becomes platform-specific, store it under the active
platform edit:

```json
{
  "platform_edits": {
    "tiktok": { "caption_language": "pt-BR" },
    "youtube": { "caption_language": "en" }
  }
}
```

MVP rule: one active caption language per clip is acceptable. Per-platform
caption language can be added without changing the track contract.

## UI Requirements

- Place the toggle inside the existing Closed Caption controls, not in Project
  Home.
- Use a segmented control with two fixed choices: `PT-BR` and `EN`.
- `PT-BR` is selected by default.
- `EN` is clickable when the clip has Portuguese caption segments.
- If English is not ready yet, clicking `EN` shows a generation status and calls
  the local API for that clip.
- If English cannot be generated, keep `PT-BR` active and show a short error.
- Switching language updates captions in preview immediately.
- Switching language must not reset trim, camera, effects, overlays, or selected
  platforms.
- The selected language should be included when the clip enters the render queue.

## Translation Rules

- Preserve segment timestamps exactly.
- Preserve segment count and order.
- Translate only speech content, not UI labels.
- Do not add commentary, explanations, hashtags, or publishing copy.
- Keep captions short enough for the existing caption wrapping system.
- Normalize punctuation for burned captions.
- If a translation line is too long, let caption wrapping split it visually; do
  not change timing during translation.
- If the model cannot return a safe aligned translation, mark the English track
  unavailable instead of blocking import.

## Local-First And Privacy Rules

- Do not store raw provider payloads.
- Do not expose API keys to browser JavaScript.
- Do not send source videos for translation; send only selected caption text when
  hosted translation is required.
- Keep generated tracks inside the local project folder.
- Import must succeed with PT-BR captions even if EN generation fails.

## Implementation Plan

### Step 1 - Contract Helpers

- Add helpers to normalize caption language keys.
- Add helpers to build a default `caption_tracks` object from existing
  `caption_segments`.
- Add helpers to resolve the active caption segments from a queue row.
- Keep `caption_segments` backwards compatible.

### Step 2 - Import-Time Track Defaults

- After selected moments have PT-BR caption segments, write only the default
  `pt-BR` ready track.
- Write deterministic `en` metadata as `unavailable` / `not_generated`.
- Do not call hosted translation during import.

### Step 3 - Editor Toggle

- Add the `PT-BR / EN` toggle in Closed Caption controls.
- Store active language in browser state.
- Update preview caption text from `caption_tracks`.
- Enable `EN` when the clip can generate English from PT-BR segments.

### Step 4 - On-Demand EN Generation

- Add `POST /api/caption-tracks/translate`.
- Request body: `gallery_path`, `rank`, `language = en`.
- Resolve the project folder through the existing local gallery path guard.
- Translate only the requested clip.
- Lock by project/rank/language so repeated clicks do not duplicate calls.
- Persist `moments.json` and the embedded editor data in `index.html`.

### Step 5 - Queue And Render

- Include `caption_language` and `caption_tracks` in queue rows.
- Resolve `caption_segments` from the selected language before final render.
- Ensure final MP4 subtitles use the selected language.

### Step 6 - QA

- Add tests for track contract generation.
- Add tests that import metadata does not trigger English translation.
- Add tests for on-demand translation persistence.
- Add UI tests for the toggle being present and enabled for generation.
- Add render tests that `caption_language = en` burns English segments.
- Run the standard Python suite and a browser smoke test.

## Acceptance Criteria

- A new Portuguese import has `caption_tracks.pt-BR.status = ready`.
- A new import does not call English translation before opening the editor.
- A new import records `caption_tracks.en.status = unavailable` or equivalent
  not-generated metadata.
- Clicking `EN` on a clip with PT-BR segments generates only that clip's English
  caption track.
- Reloading the project keeps the generated English caption track.
- `caption_segments` remains populated for backwards compatibility.
- The Closed Caption panel shows a `PT-BR / EN` toggle.
- `PT-BR` is selected by default.
- Choosing `EN` changes preview caption text without changing trim, camera,
  effect, overlay, or platform state.
- Rendering with `caption_language = en` burns English captions.
- Rendering with `caption_language = pt-BR` burns Portuguese captions.
- Existing projects without `caption_tracks` still render from
  `caption_segments`.
- AI publishing hook, title, description, and hashtags remain PT-BR.

## QA Matrix Additions

| Area | Check | Expected Result |
| --- | --- | --- |
| AI import | Import Portuguese source with OpenAI configured | Import opens with PT-BR ready and EN not generated |
| AI import | Import without translation support | PT-BR captions work and EN is marked unavailable |
| Closed Caption | Click EN on a PT-BR clip | Only that clip generates EN, then preview changes language |
| Closed Caption | EN generation fails | PT-BR stays active with a clear status |
| Finalize | Render queue with EN selected | Final MP4 burns English captions |
| Compatibility | Open older project without `caption_tracks` | Captions render from legacy `caption_segments` |

## Risks

- Translation cost increases only with clips where the user requests EN.
- Translated captions may be longer than Portuguese captions and require careful
  wrapping.
- AI translation must preserve segment count; otherwise timing can drift.
- Old local server processes can make UI changes appear missing.
- Browser state may preserve a stale active language if not scoped per project.
- Updating both `moments.json` and embedded `index.html` must stay consistent
  until the editor loads project data from JSON directly.

## Open Questions

- Should caption language eventually be per platform instead of per clip?
- Should imported English YouTube captions be preferred over AI translation when
  both exist?
- Should users be able to regenerate EN captions after editing PT-BR text?
- Should the final filename include the caption language suffix when EN is used?

## Specialist Notes

Product recommendation: keep import PT-BR-first and generate EN only when the
operator asks for it on a clip. This protects import speed and still gives users
an international output path.

UX recommendation: use a two-option segmented toggle in Closed Caption. Avoid a
dropdown and avoid `Auto` in the MVP.

Engineering recommendation: duplicate text tracks, not video files. Keep
timestamps stable and resolve the selected track only at preview/export/render
boundaries.

QA recommendation: treat timing preservation and backwards compatibility as the
highest-risk areas.
