# Current state

- **Last-updated**: 2026-07-22

- **Process layer**: AgentFold restructure in flight as a stacked PR train —
  `message-queue/` + `tasks/` + `memory/` merged (#56); `handbook/` +
  `design/` (#57) and `skills/` + `automation/` (#58) in review; this PR
  adds `templates/`, `roadmap/`, `history/`, and the reconciler.
- **Email program**: design merged (PR #54: `design/application-progress-calendar/`,
  `design/raw-data-layer/03-provider-interfaces.md`, `04-email-download-categorization.md`);
  implementation not started. The live Outlook assistant
  (`skills/outlook-email-assistant/`) is draft-only and working.
- **Job store**: raw-data-layer stages 0–4 shipped (PRs #49–#53) — library,
  capture boundary, builder, pipeline integration, retention/gardener. The
  skip-logs remain the sole search/draft skip authorities (store projection
  question parked).
- **Token-usage modes**: R1+R2 complete and merged (draft legs −29% tokens /
  −27% time at equal blind-graded quality); stage-benchmark fixtures v1 +
  harness live.
- **Tracker**: meta.yaml schema v4 (per-job status + folder rollup) is
  current; v5 (structured progress + calendar) is designed, not built.
- **Quality gates**: CI runs vendor drift, compileall, example render +
  validate, four unit suites, store fixture validation, leak guard, and
  gitleaks; pre-commit mirrors the fast checks + instruction budgets + the
  reconciler.
