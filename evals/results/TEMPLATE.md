<!--
One-page result-recording template. Copy to evals/results/<skill>-<git-sha>-<date>.md and fill.
Results are per-machine (network/board state + local model dependent). Tracked for now; may be
gitignored later. Pull tokens/wall-clock from: .venv/bin/python scripts/metrics/report.py --by-sha
-->
# Eval result — <skill>

| Field | Value |
|-------|-------|
| Skill | `<skill>` |
| Canary set | `evals/<skill>/canaries.yaml` |
| Run kind | regression baseline / regression pre-merge / A/B |
| Git SHA | `<12-char sha>` |
| Model version | `<claude model id>` |
| Config mode | examples fallback (config.yaml unset) / private overlay mounted |
| Date | `YYYY-MM-DD` |
| Judge | manual / skill-creator comparator / `<judge model + rubric>` |

## Per-canary results

| Canary id | rubric_pass (0/1) | total_tokens | wall_clock_s | tool_calls | Notes (which check failed / efficiency flag) |
|-----------|-------------------|--------------|--------------|------------|----------------------------------------------|
| `<id>` | | | | | |
| `<id>` | | | | | |
| `<id>` | | | | | |
| `<id>` | | | | | |

Pass rate: `<n_pass>/<n_total>`.

## Verdict

- **Regression:** PASS / FAIL. If FAIL, which canary(ies) + which check regressed, and whether it
  blocks the merge (rubric fail OR large efficiency blow-up vs baseline).
- **Efficiency vs baseline (if comparing):** token / wall-clock / tool-call deltas per canary
  (mean + median from `report.py --by-sha`).

## A/B section (only for run kind = A/B)

- **Pre-registered primary metric:** `<e.g. total_tokens>` — registered on `<date>` BEFORE runs.
- **Variants:** A = `<sha/branch>`, B = `<sha/branch>`. Model pinned: `<model id>`.
- **n paired runs:** `<5-10>`.
- **Efficiency (quantitative):** per-canary paired deltas; overall mean/median delta on the
  primary metric.
- **Quality (directional, blind pairwise):** `<e.g. B preferred 6/8, 2 ties>` — direction only,
  NO significance claim. Judge kappa on calibration set: `<>= 0.6>`.
- **Ship decision:** ship winner as a normal single-purpose commit / no change.
