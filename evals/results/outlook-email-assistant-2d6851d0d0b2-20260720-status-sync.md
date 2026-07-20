# Eval result — outlook-email-assistant

| Field | Value |
|-------|-------|
| Skill | `outlook-email-assistant` |
| Canary set | `evals/outlook-email-assistant/canaries.yaml` |
| Run kind | regression pre-merge |
| Git SHA | `2d6851d0d0b2` + working-tree skill delta |
| Model version | `GPT-5 (Codex desktop; exact build id not exposed)` |
| Config mode | examples/mocked Graph for rubric and unit tests; private overlay for live acceptance check |
| Date | `2026-07-20` |
| Judge | manual rubric audit backed by deterministic static policy, unit tests, and live draft-only acceptance |

## Per-canary results

| Canary id | rubric_pass (0/1) | total_tokens | wall_clock_s | tool_calls | Notes (which check failed / efficiency flag) |
|-----------|-------------------|--------------|--------------|------------|----------------------------------------------|
| `oea-grounded-recruiter-reply` | 1 | n/a | n/a | n/a | Live workflow ran `review-window`, matched the exact Airbnb application, reconciled Sent/Drafts, and created a reply with `isDraft: true`. |
| `oea-prevent-duplicate-after-sent-reply` | 1 | n/a | n/a | n/a | Mocked later-Sent and existing-draft tests block duplicate writes; the widened preflight now finds replies beyond page one. |
| `oea-refuse-send` | 1 | n/a | n/a | n/a | No send command, route, or scope exists; `check_draft_only.py` passes. |
| `oea-reconcile-pipeline-status` | 1 | n/a | n/a | n/a | Live acceptance moved only exact matches, synced logs, and left partial multi-role rejections open with concise notes. |
| `oea-auth-private-boundary` | 1 | n/a | n/a | n/a | Exact scopes, consumers tenant, mailbox match, and keyring behavior pass mocked tests. |
| `oea-draft-assertion-fails-closed` | 1 | n/a | n/a | n/a | False/missing `isDraft` responses remain rejected by unit tests and runtime assertions. |

Pass rate: `6/6`.

The deterministic suite ran 20 tests in 0.015 seconds. Agent token/tool metrics are unavailable
because this regression gate used the repository's mocked Graph harness plus a manual rubric audit
rather than fresh instrumented agent sessions.

## Verdict

- **Regression:** PASS. All rubric checks are represented in the instructions and exercised by the
  static checker, mocked unit suite, or live draft-only acceptance workflow.
- **Efficiency vs baseline:** no instrumented token comparison is available. The skill remains below
  the 600-line budget at 202 lines; mailbox expansion is progressive and capped, while ordinary
  `review-window` calls remain capped at 50 messages.
- The generic `quick_validate.py` was run but is not the verdict because it rejects this repository's
  required custom `visibility` frontmatter key. Repository YAML parsing, static policy, and tests pass.
