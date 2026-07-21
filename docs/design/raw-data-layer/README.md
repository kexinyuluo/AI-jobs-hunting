# Raw data layer — filesystem-as-database for every internet-facing fetch

**Status:** ACCEPTED (owner sign-off 2026-07-21) with **one open question**
(email git policy — see the [decisions index](#decisions-answered-and-one-open)).
Produced by: web research pass → first draft → five independent design
reviews (three angle reviews, two adversarial) → owner answers → this
regeneration. Implementation not started; stage tasks live in
`todo/tasks/`. All docs follow
the writing rules in [docs/design/STYLE.md](../STYLE.md): every section
self-contained, every reference clickable, every concept diagram in both
Mermaid and plain-text form, every decision a self-contained block.

## Problem (why this family of designs exists)

Every internet-facing skill treats fetched data as disposable. The only
cache (`tmp/search_cache/` snapshots) is deliberately a within-session
artifact with a 6-hour lifetime. Three costs follow:

1. **No memory.** A posting rejected last week returns every run; a mailbox
   review re-reads and re-classifies the same messages; nothing can be
   filtered by code against stored metadata when a new need appears.
2. **No bug recovery.** When a classifier is wrong (the known visa
   false-negative bug; the unreliable scraper remote-flag), everything it
   mislabeled is gone — fixed code can never re-run over what we saw.
3. **No timeline.** "What's new since Tuesday", "what did this company post
   this month", "which rejection email closed this application" are
   unanswerable.

**Honesty note from the token-economics review:** the earlier token-usage
program already banked the big single-session token savings. On the
job-search path this layer is roughly **token-neutral** (the arithmetic is
in [the job-postings doc](02-job-postings-pipeline.md#9-honest-token-accounting));
its justification there is bug recovery, durable memory, and code-based
filtering. The genuinely large token savings live in the **email** half
(mailbox re-reads become local queries), which this store core unlocks.

## Design stance

> **We definitely have bugs. The design must make bugs cheap:** keep the raw
> data, make everything else deterministically re-derivable from it, and a
> bug becomes "fix code, rebuild" instead of "data lost".

The principles every document shares:

- **Raw is sacred; derived is disposable.** The raw zone is append-only and
  immutable; everything else can be deleted and rebuilt from it by
  deterministic code.
- **The filesystem is the database.** Partitioned directories, one-line-per-
  record JSONL, per-entity YAML, manifests. A person can `ls` and `cat`
  their way to any answer.
- **Append, never mutate.** History is an event log; "current state" files
  are rebuilt projections, never hand-edited.
- **Versioning is built in; breaking changes rebuild instead of migrate.**
  Matches this repo's no-backward-compatibility stance — and is only
  possible because raw is kept.
- **Facts, opinions, and judgments live in separate channels.** What the
  source said; what our code concluded (stamped with the code version); what
  a human verified (protected from rebuilds).
- **Code filters; AI reads only deltas.** Compact indexes make routine
  questions one script call; AI attention is spent on new information only.
- **All real data lives in the private overlay**, and identifiers in paths
  and manifests are neutral slugs — no real name or address anywhere.
- **The store never blocks and never vouches.** Store failures degrade to
  cold behavior; acting on anything still requires fresh fetches and the
  same verification gates as today. Memory is not freshness.
- **Claims are bounded, not aspirational.** Capture scope, retention's limit
  on rebuildability, lifecycle preconditions, and privacy exposure are
  stated as contracts with limits.

## The documents

| Doc | What it covers | Post-review verdict |
|-----|----------------|---------------------|
| [01 — Store core](01-store-core.md) | The generic contract: five zones, write discipline, the determinism contract, identity pinning, retention with reference counting, agent ergonomics, content-egress rules | **Accepted.** Architecture endorsed by all five reviews; mechanics corrected; all five decisions resolved |
| [02 — Job postings](02-job-postings-pipeline.md) | The first concrete domain: capture at the fetch boundary, stable posting identity, observation timeline (gap-tolerant, on-demand polling), code-only query surface, JD reuse, application linkage, suppressed-row review queue. Closure inference is **not built** (owner decision) | **Accepted.** Implementation plan ready |
| [03 — Provider interfaces](03-provider-interfaces.md) | One abstract mail contract; Outlook and Gmail as fully isolated implementations; conformance testing; the Gmail permission problem and the resulting read-only default | **Accepted** (all four decisions resolved as recommended). Safety mechanisms are explicit deliverables |
| [04 — Email download & categorization](04-email-download-categorization.md) | Incremental mail sync with staleness detection; categorization taxonomy; guarded company→application→role linking; triage for unknowns; the strictest privacy posture in the family | **Accepted with one open question** (git policy — clarification answered in-doc, awaiting the owner's pick) |
| [Execution plan](execution-plan.md) | Staged delivery (one PR per stage) with acceptance gates, including honest benchmark gates | Signed off; stage tasks filed in `todo/tasks/` |

Suggested cold-read order: this page → each doc's "For the human reviewer"
section (~5 minutes each) → the decision blocks you're asked to fill in.

## What it will look like (one picture)

```
private/data/                        # config.data_root() — never in the public repo
├── jobs/
│   ├── raw/greenhouse/2026/07/21/<fetch_id>/manifest.json → _blobs/<sha>.json.zst
│   ├── derived/postings/examplecorp/gh-1234567/{posting.yaml, jd.md, events.jsonl}
│   ├── index/{postings.jsonl, by-day/…}
│   ├── annotations/gh-1234567.yaml        # human-verified facts — survive every rebuild
│   └── state/{cursors/, build-ledger.jsonl, key-registry.yaml, frozen-facts/}
└── email/                                 # same pattern, partitioned per account,
    └── …                                  #   stricter git policy (see the email doc)
```

Every example in this family uses the fictional Jordan-Rivers universe
(`examplecorp`, `profile-01`, `acct-01`) — and the *real* store also uses
neutral slugs in paths and manifests, so nothing identifying ever appears in
a path, manifest, or query output.

## Decisions: answered, and one open

The owner answered the full decision set on 2026-07-21. The authoritative
ADR record is
[design-decisions/raw-data-layer-decisions.md](../../../design-decisions/raw-data-layer-decisions.md);
each design doc carries a "Decisions (resolved)" table showing where every
answer landed in its text.

**Still open (one):**

- **Email git policy** — the owner asked what the tracked data would
  actually look like and what the consequence is; the answer, with concrete
  examples, is inline in
  [the open decision block](04-email-download-categorization.md#q-e-email-git-policy-what-does-the-overlay-repo-track)
  and the question is mirrored in `todo/decisions/email-git-policy.md`.
  Blocks only the git-policy piece of the email sync stage; option A
  (track index headers + annotations only) is the default path meanwhile.

**Answers that changed the design** (beyond accepting recommendations):

- Multi-laptop reality: everything tolerates locally missing raw
  (`not-synced-here` is a normal state) — new store-wide rule in
  [the store core](01-store-core.md#1-zones-and-their-contracts).
- Retention became a **GC expression config** over posting-date and
  last-observed-date filters (AND default, OR/single supported) —
  [the GC config](01-store-core.md#the-gc-config-decided-2026-07-21).
- Suppressed sweep rows get a **review queue** (partial info + raw path;
  optional manual review; never blocks the pipeline) —
  [the suppressed review queue](02-job-postings-pipeline.md#7-capture-policy-what-counts-as-useful-raw).
- Closure inference is **not built at all** (on-demand polling,
  gap-tolerant timelines) —
  [the lifecycle note](02-job-postings-pipeline.md#4b-lifecycle-not-built-decided-2026-07-21).
- The fixture size cap is a **soft threshold** (warn → human may raise a
  configurable limit); neutral identifier slugs gained **mechanical
  AI-error safeguards** (library-allocated only, write-time pattern
  validation); attachments are **metadata-only**; the cutover criterion is
  **dual** (5 clean runs AND ≥300 job-related messages); at-rest protection
  is the private-machines assumption, documented.
- Process folders were restructured by the same sign-off: open decisions
  now live in `todo/decisions/` (the todo-queue convention in `AGENTS.md`).

## How this was produced

1. **Research pass** (web-research agent): Anthropic's agent/context
   engineering guidance; small-scale data-lake architecture critiques;
   event-sourcing versioning literature (rebuild over migrate); Microsoft
   Graph delta-sync and immutable-ID documentation; job-board lifecycle and
   deduplication practice. The non-obvious gotchas it surfaced (same-
   filesystem renames, torn JSONL tails, failed-fetch lifecycle guards,
   HTML-entity normalization before hashing, sync-token expiry as a routine
   path) are inlined where they bind.
2. **First draft** of all six documents.
3. **Five independent reviews:** data-engineering, token-economics/agent
   behavior, human-ergonomics/privacy, and two adversarial reviews (jobs
   layer, email layer) that attacked the drafts against the real fetcher
   and mailbox code. Roughly 60 findings, 14 at blocker severity.
4. **Review revision.** Every finding is either incorporated or explicitly
   deferred; each document ends with a plain-language "What the reviews
   changed" table linking findings to their fixes. The largest changes: a
   fifth storage zone for non-regenerable state; builder-only locking and
   degrade-on-read; a tested determinism contract; stable native-ID
   identity with pinned keys; lifecycle detection gated on preconditions
   instead of shipped broken; the snapshot cache retained; the Gmail
   read-only default; transition-time re-verification for email evidence;
   and the flipped email git policy.
5. **Owner sign-off (2026-07-21).** Every decision answered; the answers
   were folded back into the docs (this regeneration), decided-question
   scaffolding was pruned, and the one open question kept its
   self-contained block with the owner's clarifying question answered
   inline.

## Relationship to existing work

- **Complements the token-usage-modes program** (`docs/design/token-usage-modes/`):
  that program cut instruction and iteration waste; this adds durable
  memory. They overlap on the search path (hence token-neutral there) and
  compose on the email path (where the next real savings live).
- **The snapshot cache stays.** Within-session refiltering and the
  filter-variant audit are its job; cross-run memory is the store's.
- **The application pipeline is untouched** except for one additive
  `meta.yaml` field (the posting's store key) linking applications to
  posting history.
- **Every hard guardrail survives:** draft-only email (structurally
  strengthened), the leak guard (plus new content-egress rules for store
  data), no fabricated postings, the location gate, blacklist/log
  preflights. Several review fixes exist precisely to keep these intact
  through the refactors.

## Human questions / additional tasks

*Owner space — anything written here is picked up by the next agent session
(see the async-collaboration contract in `AGENTS.md`). Questions get
answered in place; tasks get filed into `todo/` and linked back here.*

- (none right now)
