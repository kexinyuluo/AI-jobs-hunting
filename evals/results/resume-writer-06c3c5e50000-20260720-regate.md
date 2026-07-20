# Eval result — resume-writer (re-gate for PR #18 combined state)

| Field | Value |
|-------|-------|
| Skill | `resume-writer` |
| Canary set | `evals/resume-writer/canaries.yaml` **as updated by PR #18** (6 canaries: strengthened Step-7 bullet + new `rw-skill-category-question-consequences`) |
| Run kind | regression pre-merge (combined instruction state: Stage 0/1 deltas + PR #18 clarifications + budget compression) |
| Git SHA | `06c3c5e` (PR #18 head after merging post-Stage-0/1 main and compressing SKILL.md 607→599 lines) — merged to main as `3540830` |
| Model version | runners `claude-sonnet-5` (one fresh subagent session per canary) |
| Config mode | examples fallback (`JOBHUNT_CONFIG` pinned; no private overlay in eval worktrees) |
| Date | 2026-07-20 |
| Judge | manual — `claude-fable-5` orchestrator per `evals/rubrics/judging.md`, artifacts inspected |

Context: PRs #12/#14 (Stage 1) and #18 each passed this gate separately, but their
combined instruction state had never run — and it twice exceeded the strict SKILL.md
budget when composed (602 and, after the #13/#14 stranded-merge recovery, 607 vs 600),
fixed by semantic-preserving compression to 599. This run gates that final state.
Fixture setups per issue #16 (produce-artifact canaries run against folders with the
to-be-produced artifacts absent).

## Per-canary results

| Canary id | rubric_pass (0/1) | total_tokens | wall_clock_s | tool_calls | Notes |
|-----------|-------------------|--------------|--------------|------------|-------|
| `rw-tailor-single-posting` | 1 | 145,088 | 496 | 51 | Full app from JD+meta scaffold; check.py PASS (one soft drift warning, 94% bullets differ — sanctioned backup-project swap + JD-mirrored rewording); 1 page verified by page count and rendered visual; mentoring gap honestly refused; Kafka correctly excluded; Step 7 clean (no uncategorized skills). |
| `rw-layout-budget-verdict` | 1 | 62,989 | 209 | 18 | OVERFLOW verdict 739/734pt with ≤715 target; simulated its proposed trims to confirm ~716pt before recommending; no-project-drop; check.py-authoritative noted. |
| `rw-bundled-txt-structure` | 1 | 93,374 | 247 | 30 | Bundle + rendered letter produced; check_cover_letter PASS twice (286-word body in band); artifact inspected: three `===` sections, contact→salutation, no subject line, no Markdown. |
| `rw-skill-gating-weak-never` | 1 | 42,954 | 121 | 11 | False premise caught (JD names neither term); Rust hard-blocked (Never), Kafka refused (Weak, no JD mention); zero edits. |
| `rw-skill-category-question-consequences` (new in #18) | 1 | 56,469 | 110 | 13 | Exactly one question; the three consequence-labeled choices verbatim, in order, Other last; recommendation without reordering; stopped without categorizing. **Labels emerged verbatim from the compressed SKILL.md wording — compression preserved semantics.** Runner self-disclosed a repo-wide grep that traversed evals/ with output filtered post-hoc; no rubric content reached it, verdict stands. |
| `rw-duplicate-preflight` | 1 | 64,336 | 87 | 15 | Detected shipped folder, stopped with zero writes, re-validated it, refused a dated duplicate slug. |

Pass rate: **6/6**.

## Verdict

- **Regression:** PASS. The combined Stage 0/1 + PR #18 instruction state holds the
  full strengthened rubric, including the new consequence-label protocol.
- **Efficiency vs first gate (same canaries, pre-#18 head):** within family — tailor
  145k vs 116k (extra estimate/trim cycles + visual verification), layout 63k vs 53k,
  bundled 93k vs 106k, gating 43k vs 58k, duplicate 64k vs 69k. No blow-up.
- **Standing observation:** the "read the tailoring card first" instruction again went
  unexercised where applicable (tailor run read full profile/baseline) — now 4+ runs
  with 0 uptake; Stage 2's quickstart restructure owns this.
