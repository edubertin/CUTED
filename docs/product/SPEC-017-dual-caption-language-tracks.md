# SPEC-017 - Dual Caption Language Tracks

## Goal

Let CUTED prepare Portuguese and English caption tracks during import, then let
the editor switch the visible and rendered Closed Caption language with one
simple `PT-BR / EN` toggle.

The feature should make bilingual caption output feel immediate in the editor
without turning the import form into a language-configuration screen.

## Context

CUTED is primarily aimed at Brazilian creators and operators. The default import
experience should therefore continue to produce Brazilian Portuguese captions and
Portuguese AI publishing copy. At the same time, many clips can be reused for
international audiences when English captions are available.

The current import flow already carries a `language` field into YouTube caption
selection, hosted transcription, local transcription, and generated
`caption_segments`. The recent language correction made new imports default to
`pt`. This spec extends that direction by preparing a second caption track
instead of asking the user to choose the caption language before import.

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
- During import, generate a secondary `en` caption track for each selected clip.
- Store both tracks in `moments.json`.
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

English captions are prepared after selected moments exist. The MVP should not
translate the entire long-form source; it should translate only the selected
clip caption segments.

Preferred order:

1. If an English YouTube caption track can be aligned safely to the same selected
   moment windows, use it.
2. Otherwise, translate the selected Portuguese caption segments to English.
3. Keep the original segment timestamps.
4. Require the translated track to preserve the same segment count and order.
5. If translation fails, mark `en` as unavailable and keep import successful.

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
- `EN` is disabled when the English track is not ready.
- Disabled `EN` should explain the state with a short tooltip or status line:
  `English captions were not generated for this import.`
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

### Step 2 - Import-Time EN Track

- After selected moments have PT-BR caption segments, generate `en` tracks.
- Use OpenAI translation when configured.
- Return deterministic `unavailable` metadata when translation is not possible.
- Write both tracks into `moments.json`.

### Step 3 - Editor Toggle

- Add the `PT-BR / EN` toggle in Closed Caption controls.
- Store active language in browser state.
- Update preview caption text from `caption_tracks`.
- Disable `EN` if the track status is not `ready`.

### Step 4 - Queue And Render

- Include `caption_language` and `caption_tracks` in queue rows.
- Resolve `caption_segments` from the selected language before final render.
- Ensure final MP4 subtitles use the selected language.

### Step 5 - QA

- Add tests for track contract generation.
- Add tests for import metadata and translation fallback.
- Add UI tests for the toggle being present and disabled/enabled correctly.
- Add render tests that `caption_language = en` burns English segments.
- Run the standard Python suite and a browser smoke test.

## Acceptance Criteria

- A new Portuguese import has `caption_tracks.pt-BR.status = ready`.
- A new import with OpenAI configured has `caption_tracks.en.status = ready` for
  selected clips when translation succeeds.
- A new import without translation support still completes and records
  `caption_tracks.en.status = unavailable`.
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
| AI import | Import Portuguese source with OpenAI configured | `moments.json` includes ready `pt-BR` and `en` caption tracks |
| AI import | Import without translation support | PT-BR captions work and EN is marked unavailable |
| Closed Caption | Toggle from PT-BR to EN | Preview captions change language without resetting edits |
| Closed Caption | EN unavailable | EN segment is disabled with a clear status |
| Finalize | Render queue with EN selected | Final MP4 burns English captions |
| Compatibility | Open older project without `caption_tracks` | Captions render from legacy `caption_segments` |

## Risks

- Translation cost increases with clip count.
- Translated captions may be longer than Portuguese captions and require careful
  wrapping.
- AI translation must preserve segment count; otherwise timing can drift.
- Old local server processes can make UI changes appear missing.
- Browser state may preserve a stale active language if not scoped per project.

## Open Questions

- Should caption language eventually be per platform instead of per clip?
- Should imported English YouTube captions be preferred over AI translation when
  both exist?
- Should users be able to regenerate EN captions after editing PT-BR text?
- Should the final filename include the caption language suffix when EN is used?

## Specialist Notes

Product recommendation: prepare both tracks during import and keep PT-BR as the
default. This gives users an international output path without adding import
friction.

UX recommendation: use a two-option segmented toggle in Closed Caption. Avoid a
dropdown and avoid `Auto` in the MVP.

Engineering recommendation: duplicate text tracks, not video files. Keep
timestamps stable and resolve the selected track only at preview/export/render
boundaries.

QA recommendation: treat timing preservation and backwards compatibility as the
highest-risk areas.

