# Store stage 4 — GC config, retention enforcement, gardener routine

- **Status**: todo
- **Priority**: P2 (someday)
- **Area**: harness
- **Source**: raw-data-layer sign-off 2026-07-21; plan: docs/design/raw-data-layer/execution-plan.md

## Goal

Ship this stage green (CI + leak guard) as one focused PR (the owner's
delivery preference: small stacked PRs, one stage each). The execution plan
is the narrative source of truth; this file carries the checklist.

## Context

Implement the owner's GC expression config
(docs/design/raw-data-layer/01-store-core.md → "The GC config"):
independent posting-date and last-observed-date filters, AND default,
OR/single supported; refcount-gated blob deletion; frozen-facts snapshots
before pruning; per-manifest tombstones; `pruned` vs `not-synced-here` vs
`corrupt` never conflated. Gardener store routine (sizes, orphans, refcount
audit, manifest-less dirs, torn tails, stale locks, cursor/queue ages,
annotation-conflict backlog, not-synced-here counts), dry-run by default.
No at-rest encryption tooling (owner decision: private machines,
user-protected).

Acceptance: gardener dry-run clean on the real store; prune → rebuild
carries frozen facts forward with zero errors and zero husks.

## Definition of done

- [ ] GC expression config parses AND/OR/single filters over both dates; unit-tested against crafted manifests.
- [ ] Prune → rebuild carries frozen facts forward: zero errors, zero husks (test on real store copy).
- [ ] Refcount audit: a blob referenced by any keep-class manifest is never deleted (test).
- [ ] Gardener store routine dry-run clean on the real store; reports all listed dimensions incl. not-synced-here counts.
