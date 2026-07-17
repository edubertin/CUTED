# SPEC-007: OpenAI Settings and Local Cost Ledger

## Objective

Add an in-app settings surface for OpenAI credentials, model selection, connection
testing, and local cost visibility without exposing secrets to browser storage or
committing credentials.

## Scope

- Add a settings button near `Novo projeto`.
- Store the OpenAI API key only in ignored local configuration.
- Store non-secret model/provider preferences in a local user settings file.
- Show whether an OpenAI key is configured without returning the full key.
- Test OpenAI connectivity on demand.
- Track local estimated spend from CUTED-triggered OpenAI calls.

## Out of Scope

- Billing reconciliation with the OpenAI dashboard.
- Multi-user auth, team billing, or hosted secret management.
- Support for non-OpenAI providers in the first UI version.
- Automatic budget enforcement.

## Local Files

- Secret key: `%USERPROFILE%\.cuted\.env.cuted.local`.
- User settings: `%USERPROFILE%\.cuted\settings.json`.
- Usage ledger: `%USERPROFILE%\.cuted\usage-ledger.json`.

`CUTED_HOME` may override the `%USERPROFILE%\.cuted` data directory for tests or
advanced local debugging. The legacy repository `.env.cuted.local` remains a
read fallback for development compatibility, but new saves from the app write to
the user data directory. The UI never writes the token to `localStorage`.

## API Endpoints

```text
GET  /api/settings/openai
POST /api/settings/openai
POST /api/settings/openai/test
GET  /api/usage/local
```

## Cost Rules

The ledger is an estimate for local operator feedback. It records:

- Responses API input, cached input, and output tokens when usage is returned.
- Transcription duration for OpenAI audio transcription.
- Model name, operation, timestamp, and pricing source.

The OpenAI dashboard remains the source of truth for actual billing.

## Acceptance Criteria

- A user can paste and save an OpenAI token from the app.
- The saved token is not visible in page HTML, localStorage, diagnostics, or API
  responses.
- A user can test the connection without starting an import.
- Imports can use the saved OpenAI settings.
- The settings panel shows local estimated total and latest usage event.
- Checks pass without requiring a live OpenAI token.
