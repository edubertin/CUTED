# PLAN-005 - Beta Polish: OpenAI Key, Diagnostics, And Tester Guide

Status: implemented
Date: 2026-07-02
Related:
- [SPEC-007 OpenAI Settings and Local Cost Ledger](SPEC-007-openai-settings-and-cost-ledger.md)
- [SPEC-011 Local Beta Installer](SPEC-011-local-beta-installer.md)
- [PLAN-004 Windows Desktop Shell And Free Distribution](PLAN-004-windows-desktop-shell-and-free-distribution.md)
- [Windows Executable Plan](../../packaging/PLANO-EXECUTAVEL-WINDOWS.md)

## Goal

Close the small beta-readiness gaps found after the installer build:

- keep OpenAI keys out of the repository and browser storage;
- add a safe diagnostics command for tester support;
- align the beta guide with the new desktop shell path;
- keep clean-machine and full physical render QA explicit.

## Implementation Plan

### Phase 1 - OpenAI Key Storage

Status: implemented.

New saves from the settings panel write the OpenAI key to the CUTED user data
directory:

```text
%USERPROFILE%\.cuted\.env.cuted.local
```

`CUTED_HOME` can still override the CUTED data directory for tests or advanced
local debugging.

Compatibility:

- CUTED still reads the legacy repository `.env.cuted.local` after the user data
  secret file, so current dev setups do not break.
- API responses report whether a key exists, but do not return the key.
- UI/browser storage does not receive the key.

### Phase 2 - Safe Diagnostics

Status: implemented.

Add:

```powershell
cuted.exe diagnostics --json
cuted.exe diagnostics --out "<path>\cuted-diagnostics.json"
```

The report includes safe operational metadata only:

- app version and packaged/dev mode;
- Python/Windows runtime summary;
- whether settings, usage ledger, OpenAI key file, FFmpeg, FFprobe, and desktop
  shell are available;
- OpenAI provider/model names and key configured boolean.

The report must not include API keys, source videos, transcripts, raw provider
payloads, cookies, private media, or full support logs.
The diagnostics command also avoids loading secret env files; it reports key
configuration through environment/file-existence flags only.

### Phase 3 - Tester Guide Alignment

Status: implemented.

Update the beta guide so the user-facing flow is:

```text
Install -> open CUTED from Start Menu/Desktop -> desktop app window opens ->
configure OpenAI key in settings -> import -> edit -> render
```

The external browser remains only a fallback for development/support.

### Phase 4 - Remaining Manual QA

Status: pending.

Before sharing the installer with testers:

- manually open the installed app through Start Menu or Desktop shortcut;
- verify the WebView2 desktop window visually;
- configure an OpenAI key through the settings panel;
- run one real import with a chosen render destination;
- generate English captions on demand for one clip;
- render one final MP4 and inspect it;
- run the installer on a clean Windows machine without Python;
- uninstall and verify user renders are preserved.

## Acceptance Criteria

- New OpenAI keys are written under CUTED user data, not into the repository.
- Existing dev `.env.cuted.local` remains readable for compatibility.
- Diagnostics output is useful for support and sanitized for privacy.
- The beta guide describes the desktop shell as the main experience.
- Tests pass without requiring a live OpenAI key.

## Risks

| Risk | Mitigation |
| --- | --- |
| Existing dev key appears missing | Keep legacy repo `.env.cuted.local` as a read fallback |
| Diagnostics leaks sensitive data | Only emit booleans, versions, and availability flags |
| Tester still sees browser fallback | Keep guide clear that browser is fallback/support only |
| Installer shared too early | Keep clean-machine/manual render QA pending in PLAN-004 |
