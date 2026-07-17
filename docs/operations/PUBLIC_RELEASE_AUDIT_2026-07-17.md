# Public Release Audit - 2026-07-17

## Decision

The CUTED source repository is approved to proceed through pull request, CI,
merge and public visibility. Windows binaries are not approved for public
release yet.

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

The local installer is evidence only. It must not be attached to a GitHub
Release until these gates pass.
