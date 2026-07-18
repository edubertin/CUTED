# Release Evidence - 2026.07.17 Beta 1

## Identity

- Tag: `v2026.07.17-beta.1`
- Name: `CUTED 2026.07.17 Beta 1`
- State: public GitHub prerelease
- Published: 2026-07-17
- Source commit: `2591d78393bc8aa285e945e676800a5018c987fd`
- Release: `https://github.com/edubertin/CUTED/releases/tag/v2026.07.17-beta.1`
- Public site: `https://cuted-app.edubertin.chatgpt.site/`

## Assets

| Asset | Size | Purpose |
| --- | ---: | --- |
| `CUTED-Setup.exe` | 343,927,844 bytes | Windows installer |
| `CUTED-Setup.exe.sha256` | 82 bytes | Published checksum sidecar |

Installer SHA-256:

```text
5428600dbd3b3c6e42685e59a0bc1878250608cda9ef9cb2a7c8aae47a4dabc8
```

GitHub Releases is the only binary authority. The public site links to the
versioned release asset and does not host or proxy the installer.

## Verification

- PR #35 merged the public site and release integration into `main`.
- CI, CodeQL, and Gitleaks passed on the merge commit.
- The installer and checksum use the invariant release asset names.
- The installer digest reported by GitHub matches the value above.
- The release is marked as a prerelease rather than stable.

## Known Limitations

- The installer is not digitally signed and Windows may show SmartScreen.
- Clean-machine, full render, Smart Camera, upgrade, and uninstall-preservation
  checks remain required hardening evidence before a stable release.
- Future releases must repeat licensing, checksum, dependency, installer, and
  public-link validation instead of inheriting this approval automatically.
- The first site uses explicit versioned release URLs. Removing the GitHub
  asset does not automatically disable the site CTA until the site is updated.

## Withdrawal

If the binary must be withdrawn, remove or unpublish the GitHub Release asset
and immediately update and redeploy the public site to disable the fixed CTA.
Dynamic fail-closed release discovery is documented for future hardening but
is not present in the first published site.
