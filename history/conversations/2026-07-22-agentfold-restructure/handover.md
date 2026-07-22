# Handover — agentfold-restructure

- **Date**: 2026-07-22
- **Task(s)**: 2026-07-22-agentfold-restructure

## What happened

- The owner approved a full AgentFold-pattern restructure (scope Q&A in
  session; ADR: `memory/decisions/agentfold-restructure.md`), shipped as a
  stacked PR train: #56 (queues/tasks/memory — merged), #57 (handbook +
  design), #58 (skills/ + automation/), and the harness-components PR
  (templates/, roadmap/, history/, reconciler — this one).
- The private overlay was mirrored in two commits of its own.

## Where things stand

- #56 merged; #57/#58/harness PR in review, each verified locally (full
  test battery + leak guard + verify-links + reconciler green).
- Next: email execution plan Stage 1 (provider contract,
  `tasks/0_backlog/2026-07-22-email-provider-contract`) then Stage 2
  (tracker schema v5 + calendar).

## Needs your attention

- [private decision: benchmark drafts promote-or-delete](../../../private/message-queue/needs-human/decisions/benchmark-drafts-promote-or-delete.md)
  — still awaiting your answer ("leave parked" chosen this session, so the
  7 drafts stay frozen as the quality baseline).
- Merge order: #57 → #58 → harness PR (each stacked on the previous).
