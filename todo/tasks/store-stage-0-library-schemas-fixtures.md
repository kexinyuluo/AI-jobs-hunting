# Store stage 0 — shared store library, schemas, fixtures

- **Status**: done (shipped in PR #49) — delete in the next merged PR that touches todo/
- **Priority**: P1 (this round)
- **Area**: harness
- **Source**: raw-data-layer sign-off 2026-07-21; plan: docs/design/raw-data-layer/execution-plan.md

## Goal

Ship this stage green (CI + leak guard) as one focused PR (the owner's
delivery preference: small stacked PRs, one stage each). The execution plan
is the narrative source of truth; this file carries the checklist.

## Context

Build `scripts/shared/store/` per the store-core contract
(docs/design/raw-data-layer/01-store-core.md): five zones incl. `state/`,
same-dir atomic writes + torn-tail tolerance, content-addressed blobs
(sha256 of uncompressed bytes, verify-on-read, refcounts), manifest
envelope v1 (fetch groups + over-capture fields), build ledger +
materialization sequence, header-record JSONL indexes, pinned-key registry,
builder-only fail-fast lock, canonical serializer, lowercase slugs +
library-only neutral-identifier allocation (strict write-time pattern
validation), `store_show.py` resolver, taxonomies, JSON Schemas +
zone-aware `validate_store.py`, migrations scaffold (annotations/state
only). Config: `paths.data_root`. Fixture store under `examples/data/`
(script-generated, synthetic-only, example.com senders) with the decided
**soft 100 KB threshold** (exceed → human-visible warning; human-approved
configurable raise; never a silent grow or hard block).

Owner-decision specifics that MUST be tested: missing-raw tolerance
(manifest present, blob absent = `not-synced-here`, informational — the
owner runs multiple laptops with manually-synced raw); crash-injection
atomicity; ledger set-difference incl. the started-before/committed-after
fetch; idempotent event appends; incremental==rebuild equivalence;
byte-identical rebuild determinism; annotation-orphan hard-fail;
key-registry pinning; leak-guard proof (seeded token under private/data/
never reaches public tree).

## Definition of done

- [x] All listed modules exist under `scripts/shared/store/` and are vendored cleanly (`sync_vendored.py --check` green).
- [x] CI green: unit suite incl. crash-injection, torn-tail, refcount, ledger set-difference, idempotent events, incremental==rebuild, determinism, annotation-orphan hard-fail, key-registry pinning, missing-raw (`not-synced-here`) tolerance.
- [x] `validate_store.py examples/data/` green; over-threshold fixture triggers the warning path (test), never a silent grow or hard block.
- [x] Leak-guard proof test green (seeded token under `private/data/` never reaches the public tree).
- [x] Zero behavior change to any skill (existing suites untouched and green).
