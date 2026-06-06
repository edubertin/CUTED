# SPEC-005: CUTED Liquid UI

## Objective

Create a clean, professional design language for the CUTED browser workspace
using the official logo palette, restrained glass controls, and less redundant
interface copy.

## Principles

- The video is the product surface. Controls should support it, not compete
  with it.
- Glass appears on functional chrome: header, flow tabs, preview transport,
  segmented presets, floating layer menus, inspectors, and render actions.
- Dense content stays readable with dark neutral panels.
- Primary actions use the metal white token. Selection and approved states use
  brand green. Technical/import progress can use brand blue.
- Copy is terse. Professional users do not need repeated explanations on every
  screen.

## Components

### Buttons

All buttons inherit a shared base: compact height, rounded control radius,
tokenized background, visible focus ring, and subtle hover transition.

Variants:

- Primary: white/black, for submit and render.
- Quiet: dark glass/neutral, for secondary actions.
- Active: brand green tint, for selected presets and approved choices.
- Danger: dark red, only for destructive layer actions.
- Icon: square/circular transport controls.

### Preview Transport

The format strip and player controls live in a responsive control dock above the
video. The strip stays on the first row, transport and volume on the second row,
both centered and constrained to the current preview width.

### Panels

Tool panels, import, render, and overlay inspectors use a shared panel radius,
border, and surface treatment. Panels avoid nested-card visual noise.

### Text

Primary interface labels should be one to three words when possible. Repeated
status text should collapse into compact state labels like `Sem destino`,
`Em edicao`, `Fila`, `Renderizar`, and `Nada na fila`.

## Accessibility And QA

- Maintain visible focus outlines for keyboard users.
- Keep all text readable against dark and glass backgrounds.
- Verify desktop and mobile widths for overflow.
- Ensure overlay drag/resize, preview play, volume, format switching, import,
  and render flows are unchanged.
