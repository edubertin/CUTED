# CUTED Documentation

This folder is the durable project documentation for CUTED. It captures the
current local MVP, the contracts that connect the browser editor to the render
pipeline, and the planned migration from a Codex skill workflow into a first
class application workflow.

## Reading Order

1. [Product PRD](product/PRD.md)
2. [Review Workspace Spec](product/SPEC-001-review-workspace.md)
3. [AI Processing Tab Spec](product/SPEC-002-ai-processing-tab.md)
4. [AI Ingestion and Clip Diversity Spec](product/SPEC-003-ai-ingestion-and-clip-diversity.md)
5. [Data Contracts](architecture/DATA_CONTRACTS.md)
6. [Render Pipeline](architecture/RENDER_PIPELINE.md)
7. [Skill to App Migration ADR](architecture/ADR-0001-skill-to-app-migration.md)
8. [AI Ingestion and Selection Guardrails ADR](architecture/ADR-0002-ai-ingestion-and-selection-guardrails.md)
9. [CUTED Now TikTok Channel Spec](product/SPEC-006-cuted-now-tiktok-channel.md)
10. [OpenAI Settings and Local Cost Ledger Spec](product/SPEC-007-openai-settings-and-cost-ledger.md)
11. [QA Regression Matrix](qa/REGRESSION_MATRIX.md)
12. [Local Development Runbook](operations/LOCAL_DEV.md)

## Current Source of Truth

The product is still in prototype form. Today, the executable source of truth is
split across:

- `README.md`: short repository orientation.
- `tools/cutted/SKILL.md`: workflow and feature behavior.
- `tools/cutted/scripts/cutted.py`: local analyzer, gallery generator, local API,
  and FFmpeg render pipeline.
- `samples/`: generated review pages, videos, frames, captions, render outputs,
  and QA evidence.
- `channels/`: channel operations, editorial backlogs, post templates, and
  metrics logs for social publishing experiments.
- `assets/social/`: approved and draft social channel assets.

The docs in this folder should become the primary source of truth before the
code is split into app and package boundaries.

## Documentation Principles

- Document the current behavior before redesigning it.
- Keep product rules separate from implementation details.
- Keep render/data contracts explicit because browser state and FFmpeg output
  depend on the same JSON structures.
- Treat generated samples as evidence, not as long-term product architecture.
- Capture architectural decisions as ADRs before large migrations.
