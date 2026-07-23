# memory/lessons/ — what failure taught, scoped by area

One subfolder per non-skill area (`harness/`, `store/`, `publish/`, …), one
file per lesson. **Skill-specific lessons do NOT live here** — each skill's
`LESSONS.md` is the lessons zone for that skill, read when the skill runs.

Rules (shared with the per-skill zones):

- A lesson is scoped: it is read only when working in its area. A lesson
  that applies everywhere is promoted into the relevant contract
  (`AGENTS.md` or a skill's `SKILL.md`) and deleted here — one home per fact.
- Merge before adding — extend an existing lesson rather than filing a
  near-duplicate. The gardener's `lessons-report` flags stale/duplicate
  entries.

Schema: copy `templates/memory/lesson.md` (validated by `automation/reconcile/reconcile.py`).
