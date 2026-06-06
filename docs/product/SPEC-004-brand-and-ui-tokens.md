# SPEC-004: Brand And UI Tokens

## Objective

Define the CUTED brand assets and first UI color token set for the browser
review workspace.

## Brand Assets

- Source logo: `assets/brand/cuted-logo-official.png`.
- Transparent logo: `assets/brand/cuted-logo-transparent.png`.
- Generated galleries must copy the transparent logo to
  `assets/brand/cuted-logo-transparent.png` beside the generated `index.html`.
- The browser header must use the transparent logo, not a recreated SVG or a
  black-background raster.

## Palette

The initial palette is derived from the official logo and current workspace
surfaces:

| Token | Value | Use |
| --- | --- | --- |
| `--color-brand-blue` | `#11A2CF` | Technical/focus accent, future progress states |
| `--color-brand-green` | `#AFCF2A` | Selected/approved/active edit states |
| `--color-brand-white` | `#E7E7E8` | Primary action surfaces and logo metal white |
| `--color-brand-black` | `#050505` | App background |
| `--color-metal-gray` | `#68686A` | Secondary metadata and neutral emphasis |
| `--color-surface` | `#0D0D0D` | Cards |
| `--color-surface-raised` | `#111111` | Panels and opened cards |
| `--color-surface-muted` | `#151515` | Chips and quiet controls |
| `--color-surface-control` | `#191919` | Buttons and segmented controls |
| `--color-border` | `#272727` | Default borders |
| `--color-border-strong` | `#333333` | Inputs and controls |

## CUTED Liquid UI Tokens

The editor uses a restrained glass layer inspired by Apple Liquid Glass, but
adapted for a professional dark video workspace. Glass surfaces are reserved
for navigation, transport controls, segmented controls, modals, and compact
toolbars. Video content, timelines, and generated media remain visually stable
and mostly opaque.

| Token | Use |
| --- | --- |
| `--glass-bg` | Default translucent control surface |
| `--glass-bg-strong` | Higher opacity glass for menus and active panels |
| `--glass-border` | Hairline edge for glass controls |
| `--glass-highlight` | Top/internal highlight for dimensional controls |
| `--glass-shadow` | Floating control shadow |
| `--control-bg` | Quiet button background |
| `--control-hover` | Hover/focus button background |
| `--control-active` | Selected segmented state |
| `--radius-control` | Button and chip radius |
| `--radius-panel` | Panels, cards, and menus |

## Application Rules

- Keep the interface predominantly black/neutral so video previews remain the
  primary content.
- Use green for selected, active, approved, or export-ready states.
- Use blue sparingly for technical progress and future import/AI feedback.
- Use white/black for primary actions with high contrast.
- Avoid new decorative glows in the application chrome; the logo already
  carries the brand energy.
- Do not hardcode new component colors when a token exists.
- Use glass sparingly. Prefer it for controls that float above the workspace,
  not for dense content or the video canvas.
- Every glass surface needs a solid fallback through background opacity and a
  visible border so readability survives browsers with weaker `backdrop-filter`
  support.
- Button labels should be short. Longer guidance belongs in tooltips, empty
  states, or product documentation.

## Acceptance Criteria

- The app header renders the transparent PNG logo.
- The transparent logo has a real alpha channel and no black rectangular
  background.
- The title under the logo stays centered and visually separated from the logo.
- The main workspace CSS exposes the brand tokens in `:root`.
- Core UI surfaces, buttons, selected states, cards, panels, and tabs use the
  token set or documented neutral derivatives.
- Transport controls, segmented controls, tool panels, overlay menus, import,
  and render views share the same button and glass token system.
- The generated interface avoids repeated instructional copy in primary
  working surfaces.
