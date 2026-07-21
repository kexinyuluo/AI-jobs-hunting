# Store stage 5 — email track (provider contract, sync, categorization, cutover)

- **Status**: todo
- **Priority**: P2 (someday)
- **Area**: harness
- **Source**: raw-data-layer sign-off 2026-07-21; plan: docs/design/raw-data-layer/execution-plan.md

## Goal

Ship this stage green (CI + leak guard) as one focused PR (the owner's
delivery preference: small stacked PRs, one stage each). The execution plan
is the narrative source of truth; this file carries the checklist.

## Context

Sequenced after the jobs core proves the pattern. Substages per
docs/design/raw-data-layer/execution-plan.md: 5a provider contract +
conformance (route allowlists primary, folder-walking checker that
demonstrably fails a planted send-capable provider fixture, pre-commit
paths updated, rename to `email-assistant` no alias); 5b download-emails
sync (full-resync-first with inventory-diff tombstoning, per-account state,
provider-immutable-ID keys, staleness tripwire, Inbox+Sent+Drafts,
attachment METADATA only); 5c categorization + linking (ATS vendor-domain
denylist, company-gated tokens, derivation tracking, triage queues,
by-application reverse index, git-ignored evidence sidecar); 5d store-first
review + reconciliation with transition-time re-verification, cutover on
the dual criterion (5 clean runs AND ≥300 job-related messages). Gmail
lands read-only afterwards.

Open dependency: email git policy (todo/decisions/email-git-policy.md) —
blocks only the git-policy piece of 5b; default path is option A.

## Definition of done

- [ ] 5a: conformance green on synthetic mailbox; one read-only `--live` run; every existing draft-only test preserved; the new folder-walking checker demonstrably fails a planted send-capable provider fixture; pre-commit paths updated; skill renamed with no alias.
- [ ] 5b: full resync + inventory-diff tombstoning proven before delta lands; staleness tripwire fires on an induced wedged sync (test); attachment metadata captured, content never (test).
- [ ] 5c: vendor-domain denylist enforced at registry-write time (test); by-application reverse index answers in one read.
- [ ] 5d: cutover only after 5 consecutive zero-mismatch intersection runs AND ≥300 job-related messages through both paths; transition-time re-verification tested against the adversarial wrong-application scenarios; token savings measured and recorded.
- [ ] Email git policy resolved (todo/decisions/email-git-policy.md) before the 5b git-policy piece lands.
