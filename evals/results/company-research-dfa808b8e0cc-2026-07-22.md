# Eval result — company-research

| Field | Value |
|-------|-------|
| Skill | `company-research` |
| Canary set | `evals/company-research/canaries.yaml` |
| Run kind | regression pre-merge |
| Git SHA | `dfa808b8e0cc` + current working-tree skill/canary delta |
| Model version | `gpt-5.6-sol-xhigh` |
| Config mode | examples fallback (`config.yaml` absent, `JOBHUNT_CONFIG` unset) |
| Date | `2026-07-22` |
| Judge | `gpt-5.6-sol-xhigh` + shared strict rubric, with generated-artifact inspection |

## Per-canary results

| Canary id | rubric_pass (0/1) | total_tokens | wall_clock_s | tool_calls | Notes |
|-----------|-------------------|--------------|--------------|------------|-------|
| `cr-full-research-structure` | 1 | unavailable | 1622 | unavailable | Complete 15-file structure; new cold-reader check passed; no failure mode. |
| `cr-product-cold-reader` | 1 | unavailable | 1241 | 13 | All five focused checks passed; two 404 probes and one noisy HTML fetch were avoidable. |
| `cr-moat-5whys` | 1 | unavailable | 403 | 31 | All four checks passed; 22 calls were targeted evidence searches. |
| `cr-question-bank` | 1 | unavailable | 1347 | 24 | All three checks passed; 16 network fetches included two 404s. |
| `cr-honest-scaffolding-fictional` | 1 | unavailable | 132 | 9 | All three checks passed; no facts fabricated. |

Pass rate: `5/5`.

## Verdict

- **Regression: PASS.** Every expected-behavior bullet passed and no listed failure mode occurred.
- **Efficiency:** Session token metrics were unavailable and there is no same-model baseline, so a
  quantitative non-regression claim is not possible. The focused product canary completed in 13
  tool calls; its three avoidable fetches are a sourcing-path issue, not evidence that the new
  product-explanation instructions expanded the required research scope.
- **Artifacts:** Each canary ran in a separate local isolated worktree. Generated eval artifacts
  were inspected in place and were not merged into this checkout.
