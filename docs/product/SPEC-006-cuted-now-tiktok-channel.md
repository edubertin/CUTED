# SPEC-006: CUTED Now TikTok Channel

## Objective

Define the implementation plan for `CUTED Now`, a TikTok channel that acts as a
public content lab for CUTED. The channel publishes timely short-form clips
about current market, creator, platform, and internet moments while collecting
performance evidence for future product decisions.

## Context

`CUTED Now` is not only a marketing profile for the app. It is a fast editorial
testing surface:

- source timely topics from YouTube, TikTok, creator news, AI, technology, and
  market conversations;
- generate short clips through CUTED;
- publish native TikTok outputs;
- measure what topics, hooks, overlays, captions, and formats perform;
- feed learning back into CUTED's product and render workflow.

The current account is:

```text
https://www.tiktok.com/@cutednow
```

## Workflow Classification

- Request type: product/design/operations plan.
- Risk level: medium when local-only; high when changing TikTok account state or
  publishing.
- Recommended mode: spec first, then implementation in small approved steps.
- External approval gate: profile edits, uploads, posts, deletes, account
  settings, analytics export, or any authenticated TikTok action.

## Current Profile Setup

- Handle: `@cutednow`
- Display name: `CUTED Now`
- Bio: `O agora em cortes rapidos. Feito com CUTED.`
- Avatar: `assets/social/cuted-now/approved/avatar.png`
- Published videos: none yet.

## Positioning

### Channel Promise

Fast cuts about what is happening now.

### Bio Options

Current bio:

```text
O agora em cortes rapidos. Feito com CUTED.
```

Alternative:

```text
Cortes rapidos sobre o que esta acontecendo agora. Feito com CUTED.
```

### Editorial Voice

- direct;
- current;
- curious;
- slightly urgent, but not sensationalist;
- no over-explaining the app in every video;
- CUTED appears as the system behind the channel, not as the only subject.

## Content Pillars

### Now

Timely clips about events that are actively being discussed.

Examples:

- "O que acabou de mudar no YouTube?"
- "Esse recurso de IA apareceu agora."
- "O mercado reagiu a isso."

### Market

Creator economy, AI, tech platforms, monetization, tools, apps, and launch
signals.

### Platform Watch

Changes, controversies, features, and experiments from TikTok, YouTube,
Instagram, Twitch, X, and other creator platforms.

### Explained Cut

A strong third-party clip with a minimal editorial frame that makes the point
clear and useful.

### CUTED Lab

Occasional behind-the-scenes proof that the clip was created with CUTED:
render, caption, overlay, camera reframe, and platform variation tests.

## Repository Structure

Channel operation lives in:

```text
channels/tiktok/cuted-now/
  README.md
  profile.md
  content/
    backlog.md
    calendar.md
  experiments/
    metrics.csv
    post-template.json
  posts/
```

Approved visual assets live in:

```text
assets/social/cuted-now/approved/
```

Draft visual assets live in:

```text
assets/social/cuted-now/drafts/
```

## Visual Identity

### Existing Brand Anchors

- Logo: `assets/brand/cuted-logo-transparent.png`
- Approved avatar: `assets/social/cuted-now/approved/avatar.png`
- Brand blue: `#11A2CF`
- Brand green: `#AFCF2A`
- Brand white: `#E7E7E8`
- Brand black: `#050505`

### TikTok Adaptation

The TikTok profile should feel sharper and more immediate than the app UI:

- use the CUTED black/metal base;
- reserve blue/green for motion lines, active states, and watermark accents;
- avoid heavy UI chrome over the video;
- make the first frame readable without sound;
- keep watermarks small and consistent.

Do not use the older blue/red `CE/D` style avatar for CUTED Now. Do not use gray
watermark slabs; use transparent black capsules instead.

## Approved Asset Package

Approved files:

- `avatar.png`
- `avatar-preview.png`
- `watermark-light.png`
- `watermark-dark.png`
- `cover-template-1080x1920.png`
- `lower-third-1080x1920.png`
- `end-card-1080x1920.png`
- `frame-agora-1080x1920.png`
- `frame-market-1080x1920.png`
- `frame-platform-watch-1080x1920.png`
- `frame-cuted-lab-1080x1920.png`

## Video Format Defaults

- Platform: TikTok.
- Size: `1080x1920`.
- Duration target: 18-42 seconds for early tests.
- Captions: always enabled.
- Hook: visible in first 1-2 seconds.
- Watermark: present but secondary.
- Ending: no heavy outro unless the clip needs brand closure.

## Production Workflow

1. Pick a timely topic.
2. Confirm source rights and risk.
3. Generate clips in CUTED.
4. Choose a content pillar.
5. Select one hook style.
6. Apply the relevant overlay/caption template.
7. Export TikTok preset.
8. Review the final video visually and with sound off.
9. Publish only after explicit approval.
10. Record metrics at 1 hour, 24 hours, and 7 days.

## Hook Test Matrix

### Hook Types

- `question`: "Voce viu isso?"
- `statement`: "Isso muda o jogo para criadores."
- `contrast`: "Todo mundo olhou para X, mas o ponto real era Y."
- `receipts`: "Olha esse trecho."
- `speed`: "Em 20 segundos: o que aconteceu."

### First Batch

For the first 14 days, test no more than three hook types at once:

- question;
- statement;
- receipts.

## Publishing Cadence

### First 14 Days

- 2-4 posts per day when there is enough source material.
- Review every 3 days.
- Keep a small set of controlled variations.
- Do not chase every trend if it breaks the channel's identity.

### After Initial Learning

- double down on the strongest two pillars;
- retire low-retention formats;
- add one new test variable per week.

## Measurement Contract

Each post should be logged in `channels/tiktok/cuted-now/experiments/metrics.csv`
with:

```text
post_id
posted_at
source_url
source_type
rights_status
pillar
topic
hook_type
duration_seconds
caption_style
watermark_style
overlay_style
hashtags
views_1h
views_24h
views_7d
likes_24h
comments_24h
shares_24h
saves_24h
followers_gained_24h
retention_avg
completion_rate
notes
```

Use `channels/tiktok/cuted-now/experiments/post-template.json` for per-post
metadata before publishing.

## Success Criteria

- The account has a complete profile and consistent visual identity.
- Each published post can be traced back to a source, pillar, hook, and template.
- Metrics are collected consistently enough to compare formats.
- The best-performing formats produce product insights for CUTED.
- The channel can publish quickly without losing basic rights and quality checks.

## TikTok Account Access Protocol

Authenticated TikTok work should start read-only.

Allowed after login without extra approval:

- inspect profile state;
- inspect existing posts;
- inspect analytics and settings;
- summarize visible account health;
- identify missing setup items.

Requires explicit approval in the current message:

- change profile name, bio, avatar, link, category, privacy, or settings;
- upload drafts;
- publish posts;
- delete posts or comments;
- reply to comments;
- connect business tools;
- change account security or permissions;
- export or store private analytics outside the repository.

The user handles credentials and two-factor authentication directly in the
browser. Passwords, tokens, backup codes, and private cookies must not be shared
in chat or committed to the repository.

## External Research Path

Before publishing trend-dependent videos, check current platform context through
TikTok Creative Center or equivalent trend discovery:

- trending hashtags;
- trending songs/sounds;
- videos rising in the relevant region;
- creator/platform topic velocity.

Treat trend data as directional, not as the final editorial decision.

## Implementation Tasks

1. Maintain the TikTok asset package.
2. Keep account profile changes documented in `channels/tiktok/cuted-now/profile.md`.
3. Record post metadata and metrics for each published clip.
4. Produce the first 10-video test backlog.
5. Render the first batch with consistent templates.
6. Publish approved videos.
7. Review 24-hour results and adjust the matrix.

## Open Questions

- Should `CUTED Now` post only in Portuguese at first?
- Which topics are allowed or disallowed for rights, politics, sensitive news,
  and creator drama?
- Should metrics remain local CSV/JSON, move to Google Sheets, or become a
  future app analytics table?
