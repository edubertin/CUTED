# PLAN-004 - Windows Desktop Shell And Free Distribution

Status: implemented; first unsigned public beta published on 2026-07-17
Date: 2026-07-02
Related:
- [SPEC-011 Local Beta Installer](SPEC-011-local-beta-installer.md)
- [PLAN-002 Local Desktop Repository Structure](PLAN-002-local-desktop-repository-structure.md)
- [Windows Executable Plan](../../packaging/PLANO-EXECUTAVEL-WINDOWS.md)

## Goal

Turn CUTED from a local browser workflow into a real Windows desktop app that
can be installed, opened from the Start Menu, used without terminal commands,
and eventually downloaded from a public landing page.

The app is planned as a free product. Free distribution lowers commercial
pricing pressure, but it does not remove packaging, license, privacy, security,
or Windows trust requirements.

## Decision

Use the current Python engine and local web UI, but present them through a
native Windows desktop shell.

Recommended stack:

```text
Inno Setup installer
  -> PyInstaller onedir runtime
  -> cuted.exe launcher
  -> local server bound to 127.0.0.1
  -> pywebview / WebView2 desktop window
  -> browser fallback for development and recovery
```

This keeps the product local-first and avoids a rewrite while removing the
"localhost in a browser tab" feeling from the user-facing app.

## Why This Path

- It preserves the working Python engine, FFmpeg pipeline, project workspace,
  and render behavior.
- It avoids the size and extra runtime cost of Electron.
- It avoids a Tauri/Rust sidecar migration before the frontend is separated.
- It lets the current installer work continue instead of restarting packaging.
- It keeps MSIX/Microsoft Store as a later distribution channel, not a blocker.

## Implementation Roadmap

### Phase 1 - Desktop Shell Flag

Status: implemented.

Add a `launch --desktop-shell` mode. In this mode CUTED starts the local server
and opens a native desktop window through pywebview/WebView2. If pywebview or
WebView2 cannot start, the app falls back to the external browser unless
`--no-browser` is set.

Acceptance:

- `python tools/cutted/scripts/cutted.py launch --desktop-shell` opens the
  current workspace in a desktop window when dependencies are installed.
- `python tools/cutted/scripts/cutted.py launch` keeps the existing browser dev
  behavior.
- Packaged `cuted.exe` without arguments requests desktop shell by default.
- Existing `launch --no-browser` smoke tests still work.

### Phase 2 - Packaged Desktop Runtime

Status: packaged build and automatic smoke passed on the dev machine on
2026-07-02.

Build the current PyInstaller `onedir` package with pywebview included.

Acceptance:

- `dist/CUTED/cuted.exe` opens CUTED as a desktop app on the dev machine.
- A clean machine without Python can launch, import a short MP4, and render one
  final video.
- Failure to initialize WebView2 produces a safe fallback or support message.
- `cuted.exe desktop-shell-check --json` reports pywebview/edgechromium
  readiness during package smoke tests.

Dev-machine evidence:

- `packaging/build.ps1` produced
  `%LOCALAPPDATA%/cuted-build/dist/CUTED`.
- `packaging/smoke-test.ps1` passed against the packaged app, including
  FFmpeg, YOLO model, pywebview/edgechromium preflight, local API, and workspace
  bootstrap.

Remaining before distribution:

- run the same smoke on a clean Windows machine without Python;
- manually double-click `cuted.exe` and verify the WebView2 desktop window;
- import one short MP4 and render one final video from the packaged app.
- configure an OpenAI key through the app settings and verify import/AI actions
  without exposing the key in browser storage, diagnostics, or repo files.

### Phase 3 - Installer UX

Status: installer compiled and silent install smoke passed on the dev machine on
2026-07-02.

Update the Inno Setup installer and beta guide around the desktop app behavior.

Acceptance:

- Start Menu shortcut opens the desktop shell, not the default browser.
- Optional desktop shortcut behaves the same.
- Uninstall preserves `Documents/CUTED Workspace`, `Videos/CUTED Renders`, and
  `%USERPROFILE%\.cuted`.
- The guide explains Windows SmartScreen and WebView2 runtime expectations.
- `packaging/build-installer.ps1` compiles the installer from the portable
  build into `%LOCALAPPDATA%/cuted-build/installer` when Inno Setup is present.

Dev-machine evidence:

- Inno Setup 6.7.3 installed per-user through the official `JRSoftware.InnoSetup`
  winget package.
- `packaging/build-installer.ps1` produced
  `%LOCALAPPDATA%/cuted-build/installer/CUTED-Setup-2026.07.02.exe`.
- The installer ran silently with `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART
  /CURRENTUSER`.
- The installed app reported desktop shell readiness and served a temporary
  workspace through the local API.

### Phase 4 - Public Download Readiness

Status: first unsigned beta published on 2026-07-17 after explicit owner
approval. Remaining clean-Windows, real-render, uninstall-preservation,
licensing, and signing evidence must be reevaluated before a stable release.

Prepare a public release path for a free app.

Acceptance:

- Code signing decision recorded.
- License notices bundled and visible.
- Privacy/support page explains that processing is local and source videos stay
  on the user's machine unless the user chooses an AI/API feature.
- Support diagnostics explain app/tool readiness without collecting API keys,
  source media, full transcripts, or raw provider payloads.
- Download page includes version, changelog, checksum, and known limitations.

### Phase 5 - Public GitHub Readiness

Status: implemented on 2026-07-17. The repository, public site, and prerelease
are live; GitHub Releases remains the only binary authority.

Before changing repository visibility, audit the repo and history.

Acceptance:

- Secret scan and generated-media audit completed.
- Large private media, local projects, transcripts, outputs, models, and build
  artifacts are absent from Git history or explicitly handled.
- License files are complete for the open-source/public state.
- Public README explains the free app scope and local-first runtime.

## Specialist Notes

### Architecture

Keep the shell thin. The desktop layer should supervise the local server and
window lifecycle, not absorb render, AI, or project-state logic.

### Development

The first implementation slice should be reversible: optional dependency,
explicit `--desktop-shell` flag, packaged default in `cuted_launcher.py`, and
browser fallback.

### QA

Test three modes separately:

- dev browser: `launch`;
- headless smoke: `launch --no-browser`;
- desktop app: `launch --desktop-shell`.

Clean-machine testing remains mandatory before sharing an installer.

### Security And Privacy

Keep the server on `127.0.0.1`. Mutating local API calls require an HttpOnly
session cookie, loopback `Host`, and matching loopback `Origin`. Diagnostics
must not collect source videos, full transcripts, API keys, cookies, or private
file contents.

## Risks

| Risk | Mitigation |
| --- | --- |
| WebView2 unavailable or broken | Browser fallback now; installer/runtime check later |
| pywebview/PyInstaller hidden imports | Build smoke plus explicit collection in `cuted.spec` |
| App still feels web inside the shell | Later UI polish: native title, app icon, no browser chrome, desktop shortcuts |
| Free app still has license duties | Keep third-party notices and review FFmpeg/Ultralytics/yt-dlp before public release |
| Public GitHub exposes private history | Separate public-readiness audit before visibility change |

## Out Of Scope For This Roadmap

- Cloud rendering.
- User accounts, billing, subscriptions, or hosted projects.
- Microsoft Store submission.
- Rewriting the app in Tauri, Electron, .NET, or native UI.
- Moving current code into `apps/desktop` before the shell is proven.
