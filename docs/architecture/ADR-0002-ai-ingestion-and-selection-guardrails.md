# ADR-0002: AI Ingestion and Selection Guardrails

## Status

Accepted

## Context

CUTED is moving from a Codex-operated skill into an in-app AI processing flow.
Hosted AI can help choose stronger clips, but provider output is not enough to
guarantee product-level quality. A local import produced repeated suggestions
from two short timeline regions, and another import hit an OpenAI request size
limit when a full YouTube audio file was uploaded for transcription.

## Decision

CUTED will keep deterministic guardrails in the local pipeline:

- AI receives a more diverse candidate pool instead of many near-identical
  windows.
- AI selections are filtered after the response for overlap and transcript
  similarity.
- Missing slots are filled from diverse local candidates.
- YouTube captions remain the preferred transcript source.
- Oversized audio is compressed and, if needed, split into chunks before hosted
  transcription.
- `yt-dlp` can be configured with a JavaScript runtime to improve YouTube
  extraction reliability.

The AI provider ranks and explains editorial choices; the application enforces
timeline diversity, upload limits, and stable data contracts.

## Consequences

- The app should produce fewer duplicate clip suggestions.
- Some AI-selected candidates may be rejected after provider response.
- Large videos become more reliable but may take longer because compression and
  chunked transcription add local FFmpeg work.
- Configuration remains environment-based and does not expose provider keys in
  source code.
