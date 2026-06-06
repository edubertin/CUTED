# SPEC-002: AI Processing Tab

## Objective

Plan the migration from a Codex-operated CUTED skill into an in-app processing
tab. The user should be able to start analysis, monitor progress, and review
generated clips inside CUTED without manually asking Codex to run the skill.

## Current State

Processing is currently driven by `tools/cutted/scripts/cutted.py` through
commands such as:

- `analyze`
- `serve`
- `caption-selected`
- `render-selected`

This is effective for MVP validation, but it makes Codex the operational
interface. The next product step is to move the job controls into the app.

## Proposed User Flow

1. User opens the AI Processing tab.
2. User chooses a local video or provides a rights-approved URL.
3. User chooses language, target platforms, clip count, and optional quality
   settings.
4. User starts processing.
5. UI shows job status: queued, ingesting, transcribing, analyzing, rendering
   previews, ready, failed, or cancelled.
6. When ready, CUTED opens the Review Workspace with generated clip cards.
7. User edits and finalizes outputs normally.

## Functional Requirements

- Start a processing job from the UI.
- Show progress for long-running steps.
- Cancel or retry a failed job.
- Persist generated output folder metadata.
- Surface errors in user-safe language.
- Keep model/provider configuration out of source code.
- Preserve a local-first path.

## AI Provider Requirements

The provider should be abstracted behind an internal interface. Candidate
providers may include local transcription, OpenAI APIs, or another configured
provider later. The product should not bind the UI directly to one provider.

Minimum provider operations:

- transcribe audio
- generate or normalize segments
- score highlight candidates
- optionally summarize clip rationale

Provider output is not the final quality gate. The local pipeline must enforce
clip diversity, upload-size limits, and safe fallbacks before writing review
cards. See [SPEC-003](SPEC-003-ai-ingestion-and-clip-diversity.md).

## API Shape Draft

```text
POST /api/processing/jobs
GET  /api/processing/jobs/:jobId
POST /api/processing/jobs/:jobId/cancel
POST /api/finalize
GET  /api/assets/:assetId
```

## Job States

```text
queued
ingesting
transcribing
analyzing
rendering_previews
ready
failed
cancelled
```

## Acceptance Criteria

- A user can initiate analysis without Codex commands.
- The app shows progress during long-running work.
- The output of the processing tab can feed the existing Review Workspace.
- AI-selected suggestions are filtered so near-duplicate timeline windows do not
  fill the review workspace.
- Oversized audio is compressed or chunked before hosted transcription.
- Failures keep enough diagnostic information for developers without exposing
  secrets, full private payloads, or credentials.
- Provider credentials are read from environment or secure local configuration.

## Open Questions

- Which provider should be used first for hosted AI?
- Should local transcription remain the default for privacy and cost control?
- What is the target maximum video length for the MVP?
- Should processing be synchronous for local MVP or job-queued from day one?
