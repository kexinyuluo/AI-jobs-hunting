<!--
Pre-merge regression gate for feat/render-pipeline-speed (Items 1-4: canary #16 repair,
pdf_convert detect+retry, parallel PDF conversion, render.py pre-flight one-page estimate gate,
+ SKILL/LESSONS wording). Behavioral SKILL/LESSONS + render-behavior edits -> full 7-canary run.
-->
# Eval result — resume-writer

| Field | Value |
|-------|-------|
| Skill | `resume-writer` — full current 7-canary set |
| Canary set | `evals/resume-writer/canaries.yaml` |
| Run kind | regression pre-merge (behavioral edits on `feat/render-pipeline-speed`) |
| Git SHA | `25f465e2e9ad` (branch head; all 7 canaries run against it) |
| Model version | `claude-sonnet-5` (one fresh subject subagent per canary; Agent-tool `sonnet` runner) |
| Config mode | examples fallback (`config.yaml` unset). Artifact-producing canaries use an ISOLATED temp-config tree per their setup (issue #16 repair for `rw-tailor-single-posting`; the multi-experience isolated-tree setup for `rw-multi-experience-baseline`); read-only canaries use `config.example.yaml`. No private overlay. |
| Date | `2026-07-21` |
| Judge | manual — orchestrator per `evals/rubrics/judging.md`; every artifact inspected; each subject's `git status --porcelain` self-audit verified (zero tracked-file writes, `private/` untouched). |

## Per-canary results

| Canary id | rubric_pass | total_tokens | wall_clock_s | tool_calls | Notes (subject = fresh sonnet subagent) |
|-----------|-------------|--------------|--------------|------------|------------------------------------------|
| `rw-tailor-single-posting` | 1 | 123,040 | 474 | 32 | **Item 1 repair validated:** isolated fresh-tailoring scaffold exercised the FULL path (did NOT stop at the duplicate guard). Pre-flight ran (no dup/blacklist, `Remote (US)` location match); `cp` baseline→tailored.yaml; locked fields byte-identical (diff), 5 project titles all `[draft]`, no inventions; all deliverables produced; est 739pt borderline OVERFLOW — render.py gate correctly did NOT abort (Item 4 noise band); check.py "all checks passed (0 warnings)"; resume + cover both 1 page; Step-7 queue legitimately empty (all JD skills Approved). |
| `rw-layout-budget-verdict` | 1 | 54,394 | 67 | 6 | Ran `estimate_layout.py` read-only BEFORE any render; verdict 739pt vs ~734pt budget with the bands, correctly flagged as borderline (within ±12pt noise), recommended shortening longest bullets (never drop a project), and stated check.py is the authoritative gate. Cited the updated LESSONS ~739pt borderline note. No render, no edits, tree clean. |
| `rw-multi-experience-baseline` | 1 | 116,317 | 537 | 44 | Canonical ordered `employers:` — both employers (Northwind Systems, Blue Lantern Labs) preserved with count/order/fields; all direct role bullets kept as bullets (no 4-6-project restructuring); extra-employer overhead counted in the estimate (tuned SPARSE 628→OK 685pt via honest lengthening); both employers verified in the 1-page PDF via text extraction; check.py "all checks passed (2 non-blocking warnings: 47% drift, ~1.2in trailing whitespace < 1.5in fail line)"; all artifacts in the isolated `_test_application_` tree. **Live-observed:** its render ran the two PDF conversions as two concurrent `soffice` processes with distinct `-env:UserInstallation` profiles (Item 3). |
| `rw-bundled-txt-structure` | 1 | 98,407 | 240 | 29 | One `..._Application_<role>.txt` at root; three `===`-underlined sections in order (COVER LETTER / WHY THIS COMPANY & ROLE / PAST EXPERIENCE); COVER LETTER = name+contact then salutation, NO subject line, 2 body paras (115/117 w, 268 total), plain text, "Sincerely,"+name; claims traced to tailored.yaml (no fabrication); cover DOCX+PDF rendered, `check_cover_letter` passed (only WARN = intentionally-unrendered resume PDF, out of scope). |
| `rw-skill-gating-weak-never` | 1 | 66,464 | 97 | 12 | Rust=Never (declined outright), Kafka=Weak (withheld — verified the JD text mentions NEITHER term, catching the false premise); confirmed all other JD skills resolve to Approved so nothing uncategorized was silently added and no Step 7 owed; no fabricated proficiency; zero writes. |
| `rw-skill-category-question-batch` | 1 | 56,000 | 64 | 7 | Confirmed OpenTelemetry + WebAssembly absent from all three lists; ONE batch, TWO single-select questions (one per skill), the three consequence-labeled choices in exact order + Other last (recommendation allowed, order preserved); "Weak or Selective" treated as the user-facing alias for stored `Weak` (no rename/new category); did not categorize; zero writes. |
| `rw-duplicate-preflight` | 1 | 56,548 | 55 | 7 | Scanned the log (absent) + every `applications/<status>/<slug>/` folder; detected the existing `example-corp-senior-software-engineer` folder as an exact company+role match; STOPPED without a second folder/slug, offered to refresh; did not rely on the (absent) log alone; zero writes. |

Pass rate: **7/7**.

## Verdict

- **Gate: PASS.** All seven canaries' `primary_metric` (`rubric_pass`) = 1; no listed `failure_mode`
  observed. No efficiency blow-up (token/tool counts are in line with — and several below — the prior
  gate record at `4a1d589`/`8d4c06c`; the two full-tailoring canaries are naturally the heaviest).
- **This branch's behavioral edits are covered:**
  - **Item 4 (render.py pre-flight estimate gate + SKILL Step 5.5/6 + LESSONS wording)** — exercised
    directly by `rw-layout-budget-verdict` (correct two-part verdict, borderline handling) and by
    both full-tailoring canaries, whose renders hit the shipped borderline (est 739pt) and were
    correctly NOT aborted while check.py stayed authoritative. The gate's noise-band design (abort
    only when est exceeds budget by more than one rendered line) is confirmed in real runs.
  - **Item 1 (canary-fixture repair, GH #16)** — `rw-tailor-single-posting` now runs the full
    fresh-tailoring path in an isolated scaffold instead of collapsing onto `rw-duplicate-preflight`'s
    stop; both canaries pass and no longer overlap. This is the one sanctioned canary-setup change
    (its whole purpose), recorded here per the eval-gate rules; no rubric intent was weakened.
  - **Items 2-3 (pdf_convert detect+retry; parallel conversion)** — implementation-level, but every
    rendering canary produced valid, non-trivial 1-page PDFs, and `rw-multi-experience-baseline`'s
    render was observed running two concurrent isolated-profile `soffice` processes — the parallel
    path working end-to-end inside a faithful skill run.
- **Isolation:** every subject's `git status --porcelain` self-audit was empty; the orchestrator
  re-verified the tracked tree is clean (all canary writes landed in the gitignored `tmp/canary/**`
  trees); `examples/**` and `private/**` untouched.

## Notes on method

- Efficiency numbers are each subject subagent's own usage (`subagent_tokens` / `duration_ms` /
  `tool_uses`), not `logs/metrics.jsonl` (no per-SHA metrics hook fires for subagent runs) — recorded,
  not scored into `rubric_pass`.
- Method (b) per `evals/README.md`: fresh subject per canary, verbatim prompt, setup applied by the
  orchestrator (isolated temp configs for the artifact-producing canaries), no rubric shown to the
  subject (no coaching), judged against `expected_behavior` with artifacts inspected.
