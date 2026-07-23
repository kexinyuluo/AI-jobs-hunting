# message-queue/needs-agent/retries/ — mechanical repair queue

Repair work filed by automated checks (the reconciler, CI, a failed job) —
one finding per file, deterministically named `<check-id>--<subject-slug>.md`
so re-runs update the same file instead of duplicating it. This queue is how
the repo converges: an invariant breaks → a check files it here → the next
session fixes it.

## Rules

- Any session picks up items touching the area it is already working in.
- Never delete an item without fixing it or explicitly rejecting it in the
  file (a rejection states why the finding is wrong or accepted).
- Items are idempotent and **regenerable** — the filing check re-creates a
  wrongly-deleted item on its next run, and garbage-collects items whose
  finding has cleared.

## File format

`templates/queue/retry.md` is the schema; the reconciler writes these
items itself with deterministic `<check>--<subject-slug>.md` names.
