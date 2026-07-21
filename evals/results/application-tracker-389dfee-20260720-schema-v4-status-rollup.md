# Eval result — application-tracker

| Field | Value |
|-------|-------|
| Skill | `application-tracker` |
| Canary set | `evals/application-tracker/canaries.yaml` (v4 rewrite, incl. new `at-update-one-role-multi-app`) |
| Run kind | regression pre-merge (schema-v4 per-job status + derived-rollup change) |
| Git SHA | `389dfee` + uncommitted working tree (the v4 change under review; canaries from the same tree) |
| Model version | runner `claude-opus-4-8`; judge `claude-fable-5` |
| Config mode | examples fallback via sandbox config (copy of `examples/applications` per canary; `JOBHUNT_CONFIG` pointed at a per-run scratch config derived from `config.example.yaml`) |
| Date | 2026-07-20 |
| Judge | manual per `evals/rubrics/judging.md` (orchestrating agent judged runner transcripts) |

## Per-canary results

| Canary id | rubric_pass (0/1) | total_tokens | wall_clock_s | tool_calls | Notes (which check failed / efficiency flag) |
|-----------|-------------------|--------------|--------------|------------|----------------------------------------------|
| `at-pipeline-health` | 1 | 39,571 | 92 | 11 | Read-only; folder/rollup status; `--check-metadata` confirmed sync |
| `at-validate-drafted-metadata` | 1 | 37,252 | 52 | 6 | Narrowed with `--statuses drafted` knowing the default is all folders; negative (v3-rejection) case not exercised by fixture |
| `at-enrich-insert-only` | 1 | 43,396 | 112 | 15 | Insert-only diff verified; salary stayed null despite cache band |
| `at-status-move-on-request` | 1 | 38,531 | 72 | 10 | `--update` stamped posting status + status_date, moved folder; ran `--sync-log` itself (stronger than the "remind" wording) |
| `at-update-one-role-multi-app` | 1 | 45,489 | 129 | 13 | `--update-job` on one role only; sibling untouched; folder followed rollup; `[mixed]` rendered. Runner slip: one intermediate read-only `--check-metadata` ran without the sandbox env var (validated the real tree read-only, then re-ran correctly) — no rubric impact |

Pass rate: 5/5.

## Verdict

- **Regression:** PASS. All rubric checks hold on the v4 behavior; no folder was moved without an
  explicit request in any run; no hand-edited YAML anywhere.
- **Efficiency vs baseline:** no prior baseline exists for the v4 canary set (three canaries were
  rewritten and one is new, so previous numbers do not bound these). These numbers stand as the v4
  baseline. Metric source: subagent-harness usage counters (token/wall-clock/tool-call per runner),
  not `logs/metrics.jsonl` — hooks do not fire inside subagent runners; note for comparability with
  future runs.
