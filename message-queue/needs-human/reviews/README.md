# message-queue/needs-human/reviews/ — things awaiting (optional) human eyes

One file per item an agent thinks the owner may want to look at: a design
doc awaiting a read, a data-quality queue worth a glance (e.g. the job
store's suppressed-postings queue), a risky change that shipped with a
"sanity-check me" note. **Everything here is optional** — nothing blocks on
a review, and declining to look is a valid resolution.

## File format

Copy `templates/queue/review.md` and fill the blanks — the template is the
single source of truth for this schema (validated by
`automation/reconcile/reconcile.py`).
