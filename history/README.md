# history/ — one folder per working session

Every top-level session that did real work leaves a folder under
`conversations/`, named `<YYYY-MM-DD>-<kebab-slug>/`, containing at minimum
a `handover.md` (template: `templates/handover.md`) — one screen, plain
language, for a human who was away. Depth never goes in the handover; it
goes in the task folder and the handover links there. The reconciler's
`handover-present` check files a repair item for any folder that lacks one.

Optional extras per folder: `artifacts/` (small session outputs worth
keeping that belong to no task).

Retention: conversation folders are prunable once their content is fully
reflected in tasks/memory (git history is the archive); durable learnings
are promoted to `memory/` first.
