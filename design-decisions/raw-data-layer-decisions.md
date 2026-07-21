# Raw-data-layer design family: owner decisions (sign-off round 1)

- **Status**: decided (one item deliberately left open — see bottom)
- **Date**: 2026-07-21
- **Decided by**: owner, answering the self-contained decision blocks in
  `docs/design/raw-data-layer/` (v2, post-review)

## Context

The raw-data-layer family (store core, job postings, provider interfaces,
email download) reached owner review with 18 decision blocks. The owner
answered them inline in the docs; this ADR is the durable record. The design
docs fold every answer into their text and keep only compact
"Decisions (resolved)" tables; the full original option analyses live in
git history of those docs.

## Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | Overlay git tracking (jobs store) | Track `derived/`, `index/`, `annotations/`, `state/`; gitignore `raw/`. **New requirement:** all implementations tolerate locally missing raw — multi-laptop setup, raw synced manually, `not-synced-here` is a normal state |
| 2 | Raw retention | A **GC expression config**, not fixed day-counts: independent filters on posting/reposting date and last-observed date, combined with AND by default, OR or single-filter supported (e.g. "posting date > 90 d AND last observed > 30 d") |
| 3 | Builder lock contention | Fail fast |
| 4 | Public fixture-store size | 100 KB **soft threshold**: exceeding warns a human; human approval can raise the (configurable) threshold |
| 5 | Neutral identifier slugs | Yes — with mechanical safeguards so AI can't err: library-allocated slugs only, strict write-time pattern validation, leak-guard coverage of mapped real values |
| 6 | Materialize gate-suppressed sweep rows | No — record each in a **review queue** (partial info + raw manifest path) for optional manual review; never blocks the pipeline |
| 7 | Search/application logs as store projections | Defer — open item at `todo/decisions/logs-as-store-projections.md`. Same answer ordered the **process-folder restructure**: open decisions live under `todo/` (see `design-decisions/process-folders-v2-todo-queue.md`) |
| 8 | Scheduled board polling | No — on-demand polling; timelines are gap-tolerant; closure inference is not built at all |
| 9 | Skill rename | `outlook-email-assistant` → `email-assistant` at refactor time, no alias |
| 10 | Multi-account | Partition every store zone by account from day one; implement single-account first |
| 11 | Live conformance runs | Allowed, read-only, behind explicit `--live`, never CI |
| 12 | Gmail permission posture | Read-only (`gmail.readonly`); revisit only if Gmail drafting becomes a real daily need |
| 13 | Email sync folder scope | Inbox + Sent + Drafts |
| 14 | Store-first cutover criterion | **Dual**: 5 consecutive zero-mismatch comparison runs AND ≥300 job-related messages processed through both paths |
| 15 | Raw of `unrelated`-classified mail | Keep |
| 16 | At-rest encryption | None built. Documented assumption: private machines, user is responsible for protecting raw data (owner's clarifying question answered in the doc: FileVault already covers the one relevant scenario) |
| 17 | Email attachments | Content never captured; **metadata captured** (filename, size, content type, provider attachment ID) |

## Left open (deliberately)

- **Email git policy** — the owner asked what tracked data would look like
  and what the consequence is; answered with concrete examples inside the
  decision block in
  `docs/design/raw-data-layer/04-email-download-categorization.md`, question
  re-posed, mirrored at `todo/decisions/email-git-policy.md`. Default path
  while open: option A (track index headers + annotations only).

## Consequences

- Stage tasks filed under `todo/tasks/store-stage-{0..5}.md`; only the
  email git-policy piece of stage 5b is decision-blocked.
- The lifecycle/closure-inference spec was pruned from doc 02 (recoverable
  from git history); reviving it requires a new `todo/decisions/` item.
- Decisions 1, 2, 4, 5, 6, 7, 8, 14, 16, 17 changed the design beyond the
  recommended options (the rest accepted recommendations as-is); the docs' "Decisions (resolved)" tables link each
  answer to the section that implements it.
