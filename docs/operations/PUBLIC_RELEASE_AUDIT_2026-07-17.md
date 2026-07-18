# Public Release Audit - 2026-07-17

## Decision

The CUTED source repository is approved to proceed through pull request, CI,
merge and public visibility. Windows binaries are not approved for public
release yet.

## Post-Audit Publication Decision

This decision records the audit state before the owner completed the physical
installer validation. Later on 2026-07-17, the owner confirmed the tested
Windows build and explicitly approved the first unsigned public beta. The
decision is captured in `SPEC-018` and supersedes only the binary-publication
gate above; the evidence and open risks in this audit remain historically
accurate.

The resulting public state is:

- repository and source are public;
- PR #35 is merged into `main` with CI, CodeQL, and Gitleaks passing;
- prerelease `v2026.07.17-beta.1` is published with `CUTED-Setup.exe` and its
  SHA-256 sidecar;
- the public site points to the versioned GitHub Release;
- the installer is intentionally unsigned and may trigger SmartScreen.

See [Release Evidence - 2026.07.17 Beta 1](RELEASE-2026.07.17-BETA.1.md).

## Source Repository Evidence

- Gitleaks 8.30.1 scanned 198 commits with zero findings.
- The only initial matches were the documented `vertical_9_16` preset; the
  allowlist is limited to that exact non-secret value.
- Only `.env.example` is tracked. Local env files remain ignored and were not
  read during the audit.
- No tracked video, model, executable, installer or archive was found.
- No generated build, release artifact or Actions artifact is published.
- All 116 completed GitHub Actions logs were scanned with zero findings.
- The only absolute local path found in historical PR metadata was sanitized.
- Repository history is approximately 14 MiB and contains no large user media.
- Existing workflows do not receive application secrets.
- Public documentation, privacy, security, contribution, conduct, copyright,
  trademark and third-party notices are present.

## Verification Evidence

- 228 Python tests passed, including bind, Host, Origin, session, static-read and
  script-context injection coverage.
- Python compilation passed.
- Timeline TypeScript/Vite library build passed.
- npm audit reports zero known vulnerabilities.
- YAML parsing and Markdown local-link checks passed.
- PyInstaller `onedir` build passed.
- Packaged smoke test passed, including local session enforcement.
- The portable build is 1.22 GiB and includes 71 Python license directories.
- Inno Setup produced a 294.6 MiB installer and SHA-256 sidecar.

## Binary Release Gates Still Open

- clean Windows machine without Python;
- physical WebView2 launch and complete import/edit/render;
- Smart Camera verification with real media;
- upgrade and uninstall data-preservation test;
- complete corresponding-source bundle for FFmpeg and enabled GPL libraries;
- code-signing decision and SmartScreen/Defender test;
- final installer support metadata and public download page.

These were the open gates at audit time. The owner subsequently accepted the
remaining unsigned-beta limitations and authorized the first prerelease. They
remain hardening requirements for later stable releases unless separately
closed with new evidence.

Owner approval does not waive third-party license obligations. The missing
FFmpeg/GPL corresponding-source evidence applies to the currently published
beta and remains an active distribution-compliance risk that must be resolved,
not deferred to a later release.
