# Contributing

Thanks for helping improve the job-hunting toolkit. This is the **public**
`jobs-finder-toolkit` repository, Apache-2.0. It ships timeless tooling and a
fictional "Jordan Rivers" example candidate under `examples/` — never anyone's
real data.

## Dev setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

No `config.yaml` is needed to contribute: with none present, every tool falls
back to the tracked `config.example.yaml` and the `examples/` Jordan Rivers
fixture. (For PDF rendering, install LibreOffice — see `README.md`.)

Optionally wire the tracked git hooks (drift check + compile on commit) in one
idempotent, stdlib-only step:

```bash
python scripts/bootstrap_overlay.py        # installs hooks/pre-commit + hooks/pre-push
```

## Running the checks

Run these before opening a PR (all must pass; CI runs them too):

```bash
# Publish leak-guard + exporter unit tests
.venv/bin/python -m unittest discover -s scripts/publish/tests

# Instruction-file size budget (strict)
.venv/bin/python scripts/metrics/instruction_budget.py --strict

# Public leak guard — must be COMPLETELY CLEAN (exit 0, zero findings)
.venv/bin/python scripts/publish/check_public.py

# Link / symlink / vendor-drift check
.venv/bin/python scripts/maintenance/gardener/gardener.py verify-links
```

Vendored copies must stay in sync; after editing a canonical `scripts/shared/`
module, regenerate with `.venv/bin/python scripts/vendoring/sync_vendored.py` (the
pre-commit hook and CI both fail on drift).

## Eval gate for skill-instruction changes

Any PR that touches a skill's instruction files — `.agents/skills/*/SKILL.md`,
`LESSONS.md`, or `reference.md` — **must run that skill's canaries** in
`evals/<skill>/` and report the results in the PR description (see
`evals/README.md` for how). Instruction edits are delta-only, and consolidation
must not drop a domain edge case.

## No personal data — ever

This tree is PUBLIC. Never add real names, emails, phone numbers, employer or
school names, home paths, or any other personal identity — in code, docs,
comments, tests, or example data. Use the fictional Jordan Rivers fixture.

The CI **leak guard (`scripts/publish/check_public.py`) is blocking**: it scans
tracked files (text and `.docx`/`.pdf` content) for structural PII and private
paths, and any finding fails the build. Fork PRs run it tokenless (structural +
path checks only), which a clean tree passes by design.

## Extra-careful review areas

Changes under **`scripts/publish/`**, **`.github/`**, and **`hooks/`** are the
repo's leak defenses (the guard, the exporter, CI, and the pre-push gate). PRs
touching them get extra-careful review — keep those changes small, well-explained,
and covered by the tests in `scripts/publish/tests/`.

This is a single-maintainer repo, so there is no `CODEOWNERS` file; the maintainer
reviews every PR.
