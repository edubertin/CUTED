# SPEC-016 - AI Briefing Microphone

## Goal

Let a user speak a short editorial briefing while creating a new project, then
turn that audio into editable text for the existing AI context field.

The feature should reduce the blank-textarea problem without turning New Project
into a voice assistant or a mandatory setup flow.

## Context

The Project Home New Project form already has a microphone affordance beside
the AI context field, but it currently only reports that audio transcription is
a future phase. The previous Camera Lab spike showed that asking users to fill
too much context up front creates friction. A short voice note is a better fit:
users can say what they want while the intent is fresh, review the text, and
continue.

## Product Rules

- The app UI for this feature is English.
- The microphone transcription language defaults to auto-detect, independent
  from the app UI language.
- Voice briefing is optional.
- Manual typing remains the primary fallback.
- The microphone never starts without explicit browser permission.
- Audio transcription never starts an import automatically.
- The user can edit or delete the transcript before import.
- Raw audio is temporary by default and is deleted after transcription.
- Only the final text and lightweight metadata may enter project metadata.
- The local project catalog must not store raw audio or full transcript text.

## MVP Scope

- Add a record/stop interaction to the AI Briefing panel.
- Capture audio in the browser with `getUserMedia` and `MediaRecorder`.
- Send the recorded audio blob to a local CUTED endpoint on `127.0.0.1`.
- Transcribe via the configured local backend:
  - OpenAI when an API key is configured;
  - local `faster-whisper` when available;
  - clear fallback error when neither path is available.
- Insert the returned text into `context_prompt`.
- Show states for ready, recording, transcribing, applied, and error.

## Out Of Scope

- Realtime transcription.
- Speech-to-speech assistant behavior.
- Voice commands for operating the UI.
- Saving a history of raw audio files.
- Cloud rendering, hosted storage, login, or collaboration.
- Translating the entire existing editor UI in this same slice.

## Data Contract

The existing import payload remains compatible:

```json
{
  "context_prompt": "final text used by the AI"
}
```

When microphone metadata is persisted in a future project file, use:

```json
{
  "ai_context": {
    "source": "microphone",
    "text": "editable transcript",
    "language": "auto",
    "provider": "openai",
    "model": "gpt-4o-mini-transcribe",
    "audio_seconds": 24.2,
    "created_at": "2026-06-20T12:00:00Z"
  }
}
```

For the first implementation, `context_prompt` is the source of truth used by
analysis. Metadata can be returned by the endpoint without being required by
the import job.

## Local API

```text
POST /api/ai-context/audio?language=auto
Content-Type: audio/webm;codecs=opus
```

Response:

```json
{
  "ok": true,
  "context": {
    "text": "Prioritize sharp hooks and practical advice.",
    "language": "auto",
    "provider": "openai",
    "model": "gpt-4o-mini-transcribe",
    "audio_seconds": 18.4
  },
  "warnings": []
}
```

## Security And Privacy

- Limit request size.
- Accept only audio media types expected from `MediaRecorder`.
- Write audio to a temporary local draft path.
- Delete the temporary file in a `finally` block.
- Never expose OpenAI keys to browser JavaScript.
- Record OpenAI transcription usage in the local cost ledger.
- Do not log raw transcript payloads or audio bytes.

## Acceptance Criteria

- Clicking the microphone starts browser permission and recording when allowed.
- Clicking again stops recording and starts transcription.
- Recording state is visually distinct.
- Successful transcription fills the AI briefing textarea.
- Existing typed text is preserved and appended to, not silently replaced.
- Transcription failure leaves the typed textarea usable.
- Import remains blocked only by missing source media, not by mic failure.
- OpenAI transcription uses the backend key only.
- Raw microphone audio is deleted after the request completes.
- Project Home tests cover the microphone UI and endpoint affordance.
