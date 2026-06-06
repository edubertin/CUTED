# SPEC-003: AI Ingestion and Clip Diversity

## Objective

Make AI imports reliable for long videos and keep generated clip suggestions
meaningfully diverse across the source timeline.

## Current Problem

Two failure modes were observed during local imports:

- OpenAI clip selection can choose several near-duplicate windows from the same
  strong timeline region.
- YouTube videos without usable captions can fall back to downloading the full
  audio file, and large audio uploads can exceed the OpenAI transcription
  request limit.

## Product Rules

- The requested suggestion count means distinct clip ideas, not repeated trims of
  the same moment.
- AI-selected clips must pass deterministic guardrails before they become review
  cards.
- YouTube captions are preferred when available because they avoid transcription
  upload cost and size limits.
- Audio sent to hosted transcription must be compressed or chunked before it can
  exceed the configured safe upload limit.
- Import failures should explain the step that failed without exposing secrets or
  raw provider payloads.

## Clip Diversity Requirements

- Candidate pools sent to AI should be prefiltered for timeline diversity.
- Final AI selections must reject candidates with excessive overlap.
- Final AI selections must reject candidates with highly similar transcript text.
- Missing slots after rejection should be filled from diverse local candidates.
- Prompt metadata should include a coarse timeline cluster identifier, but code
  remains the source of truth for enforcing diversity.

## Ingestion Requirements

- `yt-dlp` should use a JavaScript runtime when configured or discoverable.
- Captions should be attempted before audio download for YouTube imports.
- Hosted transcription should check file size before upload.
- Oversized audio should be compressed to a lower-bitrate mono audio file.
- Audio that remains oversized after compression should be split into smaller
  chunks and timestamp offsets should be restored after transcription.

## Configuration

```text
CUTED_OPENAI_UPLOAD_LIMIT_MB=22
CUTED_OPENAI_CHUNK_SECONDS=600
CUTED_YTDLP_JS_RUNTIME=node:C:\path\to\node.exe
CUTED_YTDLP_EXTRA_ARGS=
```

## Acceptance Criteria

- A 10-clip import should not return multiple clips that overlap most of the same
  source window.
- The problematic `20260605-215749-watch` transcript produces a diverse candidate
  pool with maximum overlap below the configured threshold.
- A large audio file is not sent directly to OpenAI when it exceeds the safe
  upload limit.
- `yt-dlp` command construction can include a JS runtime without requiring UI
  changes.
- Existing local and OpenAI import paths continue to produce `moments.json` and
  `index.html`.
