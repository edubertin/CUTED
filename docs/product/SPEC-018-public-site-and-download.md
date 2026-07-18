# SPEC-018: Public Site And Windows Download

Status: implemented with known deviations
Date: 2026-07-17
Owner: CUTED
Language: Portuguese (Brazil)

Related:

- [CUTED PRD](PRD.md)
- [Windows Desktop Shell And Free Distribution](PLAN-004-windows-desktop-shell-and-free-distribution.md)
- [Local Beta Installer](SPEC-011-local-beta-installer.md)
- [Public Release Checklist](../operations/PUBLIC_RELEASE_CHECKLIST.md)
- [Public Release Audit](../operations/PUBLIC_RELEASE_AUDIT_2026-07-17.md)
- [Privacy](../../PRIVACY.md)
- [Brand](../../BRAND.md)

## 1. Decision

Create a one-page public CUTED website using OpenAI Sites. The website presents
the real Windows product, explains the local-first workflow, links to the public
GitHub repository, offers a direct contact action, presents CUTED Now as a
public case study, and provides the approved Windows beta download.

The website does not host the CUTED application runtime. It does not upload,
edit, render, or store user videos. CUTED remains a local Windows application.

Publication decision approved by the owner on 2026-07-17:

- the source repository is public;
- the portable build and installer have been physically tested by the owner;
- the first installer can be published as an unsigned public beta;
- GitHub Releases is the only binary authority;
- the website uses the versioned installer and checksum assets;
- the unsigned-build and SmartScreen limitation remains visible beside the
  download action.

## 2. Specialists Consulted

- Workflow: route the request through product spec, visual direction, download
  architecture, and release gates before implementation.
- Product Manager: make trust and product understanding the first conversion;
  use GitHub as the primary CTA until the installer is approved.
- UX Expert: use an editorial, product-led layout based on the real CUTED
  timeline and screenshots; avoid generic AI/SaaS composition.
- Architect: keep GitHub Releases as the only binary authority; fail closed if
  release metadata or checksum validation is unavailable.

## 3. Objective

The website should let a Brazilian creator understand CUTED in less than ten
seconds and answer four questions without reading technical documentation:

1. What does CUTED do?
2. What stays on my computer?
3. How does the workflow turn a long video into social clips?
4. Can I download it safely today?

Secondary goals:

- direct developers and contributors to GitHub;
- provide an intentional contact path;
- establish public trust through transparent beta, privacy, license, and
  release information;
- become the stable public entry point for future Windows releases.

## 4. Audience And Job To Be Done

Primary audience:

- Brazilian creators cutting podcasts, interviews, classes, streams, or long
  videos into short-form content;
- editors and operators producing variants for TikTok, Shorts, Instagram,
  Facebook, and YouTube;
- Windows users who prefer local media processing instead of uploading their
  entire library to a hosted editor.

Job to be done:

> When I have a long video and need several short versions, I want to find,
> refine, and render good moments without moving my entire media library into a
> cloud service.

## 5. Positioning And Message Rules

Primary proposition:

> CUTED is a local-first Windows editor that helps transform long videos into
> social clips while keeping projects, heavy processing, and final renders on
> the user's computer.

Message pillars:

- Local-first: project media and outputs remain local by default.
- Complete workflow: suggest, review, edit, adapt, queue, and render.
- Multi-platform: prepare different aspect ratios and treatments from one cut.
- Optional AI: connected features are not required for every workflow.
- Open source: public code under AGPL-3.0.
- Honest beta: source and installer are public, with limitations stated beside
  the download.

Approved language:

- `Processamento principal local`.
- `Sem upload automatico da sua biblioteca`.
- `Recursos de IA sao opcionais`.
- `Sugestoes de momentos para revisao`.
- `Gera versoes para diferentes plataformas`.
- `Baixar para Windows`.

Do not claim:

- `100% offline`;
- `nada sai do seu computador`;
- `funciona em qualquer PC`;
- `publica diretamente nas redes`;
- `IA encontra os melhores cortes`;
- `qualquer video do YouTube`;
- claims that the unsigned beta is signed, certified, or production-stable.

## 6. Information Architecture

The MVP is one responsive page with anchor navigation.

### 6.1 Header

- Transparent CUTED logo.
- Links: `Produto`, `Como funciona`, `Privacidade`, `Codigo`.
- Release action: `Baixar para Windows`.

The header remains compact and does not hide the first product visual.

### 6.2 Hero

Eyebrow:

> Editor local para Windows - beta open source

H1:

> Transforme videos longos em cortes prontos. No seu computador.

Supporting copy:

> Encontre momentos, ajuste cada formato e renderize para TikTok, Shorts,
> Instagram, Facebook e YouTube. Projetos e processamento pesado permanecem
> locais; recursos de IA sao opcionais.

CTAs:

- Primary: `Baixar CUTED para Windows`.
- Secondary: `Ver no GitHub`.
- Contact: `Falar com o desenvolvedor`.
- Supporting metadata: version, file size, release date, checksum link, and
  known limitations.

The main visual is `docs/images/cuted-social-preview.png`, shown nearly
full-width and without fake browser or device chrome. At 1440 x 900, the first
viewport should show the headline, actions, and a meaningful portion of the
product visual while leaving a hint of the next section.

Trust strip:

> Windows 10/11 - Processamento local - Codigo aberto - Sem conta CUTED

### 6.3 How It Works

Use a timeline-shaped sequence:

1. `Importe`: choose a local video or an authorized link.
2. `Encontre`: review suggested moments and natural cut boundaries.
3. `Refine`: adjust trim, camera, effects, overlays, and captions.
4. `Renderize`: produce platform variants on the user's computer.

Desktop uses a horizontal progression from CUTED blue to CUTED green. Mobile
uses a vertical progression. Every step has a number and text; color alone does
not communicate state.

### 6.4 Inside CUTED

Show the real product in two editorial bands, not generic feature cards:

- `docs/images/cuted-project-home.png`
  - Heading: `Seus projetos, no seu workspace.`
  - Explain recent projects, workspace continuity, and local storage.
- `docs/images/cuted-editor.png`
  - Heading: `Um espaco de decisao para cada corte.`
  - Explain trim, aspect ratio, AI tools, effects, captions, approval, and
    rejection controls.

Images open in an accessible lightbox so interface details remain inspectable
on smaller screens.

### 6.5 Capabilities

Use a concise two-column feature index instead of a grid of equal cards:

- suggested cuts and natural phrase boundaries;
- timeline and trim;
- per-platform variants;
- Smart Camera and local vision;
- captions in Portuguese and English translation on demand;
- text, image, effect, and bumper overlays;
- background render queue;
- recoverable local projects.

Supporting disclosure:

> Alguns recursos conectados podem exigir uma chave configurada pelo proprio
> usuario. A chave nao e fornecida pelo CUTED nem incorporada ao instalador.

### 6.6 CUTED Now Case Study

Present `https://www.tiktok.com/@cutednow` as a public editorial lab whose
published clips are produced with CUTED. The first site release may state that
one clip exceeded 47 thousand views, explicitly timestamped as an observation
from July 2026. Do not present changing follower, like, or view counts as live
product guarantees.

Use the approved `assets/social/cuted-now/approved/` package and the CTA
`Ver @cutednow no TikTok`.

### 6.7 Local-First And Privacy

Heading:

> Seu video nao precisa virar upload.

Visual flow:

```text
Video local -> analise e edicao local -> FFmpeg local -> CUTED Renders
```

Required disclosure:

> Videos, previews, transcricoes, projetos e renders ficam no computador por
> padrao. O CUTED nao exige uma conta hospedada nem envia automaticamente sua
> biblioteca. Quando o usuario ativa um recurso conectado a uma API de IA,
> somente o material necessario para aquela operacao e enviado ao provedor
> configurado.

Link: `Entender privacidade e integracoes`, pointing to `PRIVACY.md` on GitHub.

### 6.8 Open Source And Distribution Status

Heading:

> Codigo aberto e beta publico para Windows.

Required status copy:

> O codigo-fonte e o instalador estao disponiveis publicamente. O instalador e
> gratuito e ainda nao possui assinatura digital, portanto o Windows pode
> exibir um aviso do SmartScreen.

Links:

- Repository: `https://github.com/edubertin/CUTED`.
- Releases: `https://github.com/edubertin/CUTED/releases`.
- Issues: `https://github.com/edubertin/CUTED/issues`.
- License: `https://github.com/edubertin/CUTED/blob/main/LICENSE`.
- Security: `https://github.com/edubertin/CUTED/blob/main/SECURITY.md`.

### 6.9 Final CTA

Heading:

> Seu proximo corte pode comecar local.

Actions:

- `Baixar para Windows`, `Ver no GitHub`, `Falar com o desenvolvedor`.

### 6.10 FAQ

The MVP answers:

- O CUTED ja pode ser baixado?
- O processamento e realmente local?
- Preciso de uma chave de IA?
- O CUTED publica diretamente nas redes?
- Quais versoes do Windows sao suportadas?
- O aplicativo e gratuito?
- Onde reporto bugs ou vulnerabilidades?

### 6.11 Footer

Include GitHub, Releases, Privacy, Security, License, Brand, and Contact. Do not
display the contact email as visible text.

## 7. Contact Behavior

The requested visible action is an icon-plus-label button:

```text
Falar com o desenvolvedor
```

MVP behavior:

```text
mailto:edubertin85@gmail.com?subject=CUTED%20-%20contato
```

Accessibility:

- label remains visible; the email address does not;
- mail icon from the existing icon library;
- `aria-label="Enviar e-mail ao desenvolvedor sobre o CUTED"`;
- visible keyboard focus;
- minimum 44 x 44 px interaction target.

Privacy limitation:

The address is hidden visually but remains present in the page source through
the `mailto:` URL and can be collected by bots. JavaScript obfuscation would
only reduce naive scraping and is not a security boundary.

If the address must not exist in public HTML, replace the MVP link with a
server-side contact form using rate limiting, bot protection, a honeypot, and a
mail delivery provider. That is a separate capability and must not be added
silently during the static MVP.

Bugs should still point to GitHub Issues. Vulnerabilities must point to
`SECURITY.md`, never to a public issue or prefilled email containing private
files, logs, paths, videos, transcripts, or keys.

## 8. Visual Direction

Direction sentence:

> A cinematic, editorial view of a real creative Windows tool, organized around
> the CUTED timeline from blue input to green approved output.

Tokens:

| Role | Value | Use |
| --- | --- | --- |
| Background | `#050505` | Page base |
| Surface | `#0D0D0D` | Quiet content surfaces |
| Raised surface | `#111111` | Navigation and focused panels |
| Primary text | `#E7E7E8` | Headlines and primary copy |
| Secondary text | `#8C8C8F` | Metadata and supporting copy |
| CUTED blue | `#11A2CF` | Input, edit, focus, links |
| Focus blue | `#24DCFF` | Keyboard focus and active interaction |
| CUTED green | `#AFCF2A` | Approval, completion, download |
| Border | `#272727` | Structural boundaries |

Typography:

- Inter or a system sans-serif stack;
- compact, strong headings;
- no artificial futuristic display font;
- letter spacing remains `0`.

Composition rules:

- use full-width editorial bands and unframed product media;
- keep the real product as a first-viewport signal;
- use the logo energy instead of adding decorative orbs or generic gradients;
- reserve glow for blue input and green completion points;
- avoid a split hero, bento grid, pricing cards, invented testimonials,
  marketing metrics, robots, cloud illustrations, and generic AI imagery;
- cards, when genuinely needed, use a maximum 8 px radius;
- motion is restrained and disabled through `prefers-reduced-motion`.

## 9. Asset Plan

Approved sources:

| Asset | Source use |
| --- | --- |
| `assets/brand/cuted-logo-transparent.png` | Header and final brand signature |
| `assets/brand/cuted-symbol-mark-transparent.png` | One timeline transition accent |
| `assets/brand/cuted-app-icon.png` | Favicon and Windows download identity |
| `docs/images/cuted-social-preview.png` | Hero media and initial Open Graph image |
| `docs/images/cuted-project-home.png` | Product Home demonstration |
| `docs/images/cuted-editor.png` | Editor demonstration |

Do not distort, recolor, crop away essential UI, or rebuild the logo as SVG.
Do not use user projects, private paths, real transcripts, or unapproved media.

Implementation copies optimized derivatives into `apps/site/public/` while
preserving the repository assets as the source of truth. The site should not
hotlink first-party images from `raw.githubusercontent.com`.

Future optional asset:

- a silent 45-60 second product demonstration using synthetic or explicitly
  authorized media, with Portuguese captions, poster image, and playback
  controls;
- no autoplay with sound;
- the screenshot flow is the required MVP fallback.

## 10. Site Architecture

Proposed repository surface:

```text
apps/site/
  .openai/hosting.json
  app/
    layout.tsx
    page.tsx
    globals.css
    api/release/windows/route.ts
  public/
    brand/
    product/
    og.png
```

The site is a presentation and release-discovery surface only. It does not add
authentication, a hosted database, video upload, cloud render, payments, or
project persistence.

The OpenAI Sites project was created during the approved implementation phase.
Its `.openai/hosting.json` is stored under `apps/site/`.

## 11. Download Architecture

### 11.1 Authority

GitHub Releases is the only source of public binaries. OpenAI Sites must not
store, copy, proxy, or repackage the installer.

The site may expose a small server endpoint that reads public GitHub release
metadata and returns a normalized contract:

```json
{
  "available": true,
  "version": "v0.1.0-beta.1",
  "publishedAt": "2026-07-17T00:00:00Z",
  "sizeBytes": 308873281,
  "downloadUrl": "https://github.com/.../CUTED-Setup.exe",
  "checksumUrl": "https://github.com/.../CUTED-Setup.exe.sha256",
  "releaseUrl": "https://github.com/edubertin/CUTED/releases/tag/v0.1.0-beta.1"
}
```

Never render the GitHub release body as raw HTML. No GitHub token belongs in
client JavaScript. Public metadata should use edge caching and fail closed.

### 11.2 Release Assets

Use invariant public asset names:

```text
CUTED-Setup.exe
CUTED-Setup.exe.sha256
```

The checksum file format is:

```text
<sha256>  CUTED-Setup.exe
```

Versioned identity remains in the release tag, release title, installer
metadata, application `VERSION`, and changelog.

For a stable non-prerelease, these URLs are valid:

```text
https://github.com/edubertin/CUTED/releases/latest/download/CUTED-Setup.exe
https://github.com/edubertin/CUTED/releases/latest/download/CUTED-Setup.exe.sha256
```

GitHub `releases/latest` does not select releases marked as prereleases. The
first public beta should therefore remain correctly marked as a prerelease and
the site endpoint should select an explicitly approved beta from the public
releases list, then use that release asset's versioned `browser_download_url`.
Do not misclassify a beta as stable only to obtain a shorter URL.

### 11.3 Download States

| State | UI behavior |
| --- | --- |
| No release | No download `href`; show `Download publico em validacao` and an active `Ver Releases` link |
| Invalid release | Disable download when installer, checksum, version, or expected names are missing |
| API unavailable | Fail closed; show `Nao foi possivel confirmar o download` and link to Releases |
| Valid release | Show version, size, date, checksum, limitations, and active download action |
| Download started | Preserve button width; show confirmation through an `aria-live` region |
| Release withdrawn | Short cache expires and the site returns to unavailable state |

The approved implementation state is `Valid release`, using the explicit beta
tag `v2026.07.17-beta.1` and the invariant installer and checksum asset names.

### 11.4 GitHub Limits

GitHub requires each release asset to be under 2 GiB. The latest local CUTED
installer is 343,927,844 bytes, approximately 328 MiB, so it fits this
technical limit.
This size result does not approve public distribution by itself.

If a future build exceeds 2 GiB, do not split the installer for end users and
do not move the binary into OpenAI Sites. Reduce the package, preferably by
continuing the planned ONNX path instead of a full PyTorch distribution.

## 12. Binary Release Gate

The public beta publication was authorized after the owner confirmed a
successful physical installer run. The implementation task still verifies the
following items before activating the public link:

- approved commit on `main` and green CI;
- secret scanning and source audit remain clean;
- portable and installer smoke pass;
- clean Windows machine without Python passes;
- physical WebView2 launch passes;
- local import, Smart Camera, captions, and a real final render pass;
- upgrade and uninstall preserve workspace, settings, and renders;
- installer remains below the GitHub asset limit;
- SHA-256 is calculated and independently verified;
- Python and bundled dependency licenses are present;
- exact FFmpeg version, hash, license, and corresponding source are recorded;
- Ultralytics/AGPL notices match the distributed package;
- code-signing decision is recorded;
- SmartScreen/Defender behavior is tested and documented;
- support guide, known limitations, privacy, and sanitized diagnostics are
  ready;
- release is prepared as draft and every asset is verified before publication.

## 13. Accessibility And Responsive QA

- WCAG 2.2 AA target.
- One `h1`, semantic landmarks, and a `Pular para o conteudo` link.
- Visible 2-3 px focus using `#24DCFF` with offset.
- Minimum 44 x 44 px interactive targets.
- Complete keyboard navigation.
- Text contrast of at least 4.5:1; controls and indicators at least 3:1.
- Product state is never communicated by blue or green alone.
- Lightbox closes with `Esc`, traps focus, and returns focus to its trigger.
- Descriptive alt text for the logo and product screenshots.
- Reflow works at 320 px and 200% zoom.
- High-contrast mode remains understandable.
- `prefers-reduced-motion` disables nonessential movement.
- No auto-playing sound or inaccessible demonstration video.
- Long Portuguese copy and all button labels fit without overlap.

Required review viewports:

- 1440 x 900;
- 1280 x 720;
- 768 x 1024;
- 390 x 844;
- 320 x 568.

## 14. SEO And Sharing

Title:

> CUTED - Editor local de cortes para Windows

Description:

> Transforme videos longos em cortes para redes sociais com um fluxo local de
> edicao, legendas, Smart Camera e render no Windows.

Required metadata:

- canonical Sites URL;
- Portuguese locale;
- Open Graph and X card;
- `docs/images/cuted-social-preview.png` as the initial visual source;
- favicon from `cuted-app-icon.png`;
- no fabricated organization, pricing, review, or download structured data.

During implementation, generate one site-specific `public/og.png` after the
final layout and copy are stable. It must preserve the CUTED brand and may use
the existing social preview as its visual foundation.

## 15. Privacy And Measurement

MVP measurement is privacy-preserving and optional. Do not add advertising
pixels, session replay, fingerprinting, or individual behavioral profiles.

Useful aggregate events after an explicit analytics decision:

- GitHub CTA click;
- Releases CTA click;
- contact click;
- product screenshot interaction;
- download click after release approval.

No analytics capability is included in the first implementation unless it is
separately approved.

## 16. Scope

In scope:

- one public Portuguese page;
- responsive product-led presentation;
- official CUTED brand and safe screenshots;
- GitHub, Issues, Releases, Privacy, Security, License, and Contact links;
- current unavailable download state;
- future release discovery contract;
- SEO and sharing metadata;
- accessible interactions and release-state handling.

Out of scope:

- hosting the CUTED application runtime;
- uploading or editing videos in the website;
- account, login, database, newsletter, or user profiles;
- cloud rendering;
- social network publishing;
- payments or pricing;
- chatbot;
- English localization in the MVP;
- public installer publication before release QA;
- analytics without a separate privacy decision;
- contact form infrastructure in the mailto MVP.

## 17. Acceptance Criteria

Product and content:

- the first viewport communicates CUTED, Windows, video clipping, and
  local-first behavior;
- the real product is visible in the first viewport;
- the visitor understands the four-step workflow without technical docs;
- current GitHub CTA points to the official public repository;
- download status cannot be mistaken for an available binary;
- privacy copy clearly separates local behavior from optional API features;
- the site never claims direct social publishing;
- contact action works without visibly printing the email address;
- license, privacy, security, and contribution paths are reachable.

Visual and experience:

- official assets are used without distortion;
- page avoids generic AI/SaaS visual patterns;
- responsive layouts pass all required viewports;
- keyboard, focus, contrast, reduced-motion, and lightbox behavior pass;
- no private video, transcript, path, project, or user data appears;
- all external links are validated before deployment.

Download:

- the installer `href` points to the approved versioned GitHub Release asset;
- GitHub Releases remains the only binary authority;
- invalid or unavailable release metadata fails closed;
- the valid state shows version, checksum, limitations, and a
  version-consistent download URL;
- binary activation requires every release gate in this spec.

## 18. Implementation Slices

### Slice A: Sites Foundation

- create `apps/site` through the OpenAI Sites initializer;
- persist `.openai/hosting.json` in the site project;
- establish page metadata, tokens, fonts, favicon, and source asset copies;
- open the starter preview before visual implementation, per Sites workflow.

### Slice B: Product Page

- implement header, hero, workflow timeline, product bands, capabilities,
  privacy, distribution status, FAQ, contact, and footer;
- use the approved versioned public beta state;
- build the accessible screenshot lightbox;
- validate responsive layout in the in-app browser.

### Slice C: Release Discovery

- add the normalized public GitHub release endpoint;
- validate approved tag and invariant asset names;
- implement fail-closed states and short caching;
- activate only the owner-approved beta tag and invariant asset names.

### Slice D: Site QA And Publication

- run production build;
- validate copy, links, metadata, accessibility, and visual layout;
- generate and inspect the final Open Graph image;
- save a Sites version and deploy the public page;
- publish only source that matches the approved GitHub binary release.

### Slice E: Windows Download Activation

- rebuild the current Windows binary and installer;
- create and verify the GitHub prerelease with invariant asset names;
- publish under the explicit approval recorded on 2026-07-17;
- confirm the live site resolves the correct versioned download.

## 19. Decisions Closed On 2026-07-17

- The visible contact label is `Falar com o desenvolvedor`; the email remains
  hidden visually behind the `mailto:` action.
- The site is hosted with OpenAI Sites; a custom domain is not required for the
  first release.
- The first binary is intentionally unsigned and the SmartScreen warning is
  disclosed beside the download.
- The first public beta is approved for GitHub Releases.
- The first page uses real screenshots and CUTED Now evidence instead of a
  synthetic demo video.

## 20. Recommended Next Step

Maintain the public beta as a coordinated release surface: keep the source,
GitHub prerelease, checksum, public site, support copy, and known limitations in
sync. Before the next binary, rerun the installer, licensing, clean-machine,
render, uninstall-preservation, and download-link checks.

## 21. Implementation Record

Implemented on 2026-07-17:

- public site: `https://cuted-app.edubertin.chatgpt.site/`;
- repository: `https://github.com/edubertin/CUTED`;
- merge: PR #35, `codex/public-site-release` into `main`;
- release: `v2026.07.17-beta.1`;
- binary authority: versioned GitHub Release assets;
- published assets: `CUTED-Setup.exe` and `CUTED-Setup.exe.sha256`;
- distribution state: free unsigned Windows prerelease with SmartScreen
  limitation disclosed.

Known implementation deviations:

- the site uses explicit versioned URLs for `v2026.07.17-beta.1` in
  `apps/site/app/page.tsx` instead of the normalized dynamic release endpoint;
- installer and checksum names are protected by site tests, but release
  withdrawal does not fail closed automatically;
- withdrawing or replacing the prerelease therefore requires a coordinated
  site update and redeployment;
- dynamic GitHub release discovery remains a future hardening task, not a
  property of the first published site.
