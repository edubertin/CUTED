# CUTED PRD

## Summary

CUTED is an AI-assisted video clipping workspace for turning long-form videos
into short-form social clips. The current MVP runs locally: it analyzes a source
video, suggests candidate clips, renders preview media, opens a browser review
workspace, and lets the user trim, caption, compose overlays, choose platform
presets, and finalize rendered MP4 outputs.

## Problem

Short-form editors need to create several platform-specific versions from the
same clip. A single idea may need different framing, text, logo placement,
captions, effects, and output dimensions for TikTok, Shorts, Instagram,
Facebook, and YouTube. The previous flow loaded too many videos and separated
editing tools across screens, which made the local prototype heavy and slowed
iteration.

## Product Goals

- Let a user review suggested clips quickly without loading every video at once.
- Make each clip editable inside one collapsible workspace.
- Preserve per-platform edits so a user can tune TikTok, Shorts, Instagram,
  Facebook, and YouTube independently.
- Render the final queue using the latest saved edit state.
- Keep the MVP local-first until the AI processing tab and backend boundaries
  are specified.
- Build documentation that supports a future monorepo structure.

## Non Goals

- Public publishing to social platforms.
- Multi-user collaboration.
- Cloud rendering infrastructure.
- Billing, teams, permissions, or production auth.
- Replacing the local FFmpeg path before the migration is designed.

## Primary Users

- Content creators cutting long-form podcast, interview, stream, or lecture
  content into social clips.
- Operators who need to process many clips and export multiple platform formats.
- Product/development reviewers validating the future CUTED application flow.

## Current MVP Journey

1. User runs the local CUTED analyzer against a local video or approved YouTube
   test URL.
2. CUTED generates candidate clips, frames, metadata, and an `index.html`
   gallery.
3. User serves the sample folder through `cutted.py serve`.
4. User expands one clip card at a time.
5. User edits trim, camera, effects, text/image overlays, captions, transcript,
   and platform presets.
6. User selects export destinations through the export dock.
7. User finalizes the queue.
8. The local API renders MP4 outputs into `captioned-clips/`.
9. User reviews and downloads final videos from the Final tab.

## Success Criteria

- A clip can be edited without opening all preview videos at once.
- Platform presets retain their own layer/camera/effect state.
- Final render includes text overlays, image overlays, captions, effects, trim,
  camera reframing, and the selected output dimensions.
- A user can restart the local server and continue from saved generated files.
- The documentation gives a new developer enough context to modify the MVP
  without reverse engineering the full script.

## Open Product Questions

- Which AI provider should power the future in-app processing tab?
- Should source video and generated artifacts remain local by default?
- Should cloud processing be opt-in per job or configured per workspace?
- What is the minimum progress/status model for long-running processing jobs?
- Which sample artifacts should be committed, ignored, or archived as fixtures?
