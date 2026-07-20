# Private overlay

This toolkit is designed to be published **publicly** while everything tied to a
real person or a real job hunt stays **private**. It ships as two layers:

1. **PUBLIC toolkit repo** — timeless, general tooling only: the scripts, the five
   public skills, the company registry (identity only), a fake example candidate
   ("Jordan Rivers") under `examples/`, and `config.example.yaml`. Nothing here is
   tied to a real person or a dated posting.
2. **PRIVATE overlay repo** — its **own git repo**, synced to a private GitHub
   remote, holding your real data: profile, resume baseline, reference DOCX,
   applications, interviews, the private `coding-interview` skill, `config.yaml`,
   `.cursor/rules/private-skills.mdc`, and your real job-search profile YAML(s).

The overlay **mounts into a git-ignored `private/` directory** inside a public
checkout (**`private/` is the canonical mount; `personal/` is kept as a legacy
alias** — `.gitignore` ignores both), and `config.yaml`'s `paths.*` point the
toolkit at the overlay's data. Because `private/` (and the other private paths) are
git-ignored in the public repo, your real data is never committed to the public toolkit.

## How the layering works

- The exported public repo's `.gitignore` ignores `private/`, `config.yaml`,
  `.cursor/rules/private-skills.mdc`, every per-skill
  `.agents/skills/*/references_private/` folder, and the private product folders
  (`applications/`, `interviews/`, `templates/`, `.agents/inputs/`,
  `.agents/skills/coding-interview/`). So you can work **in place** in a public
  checkout: drop your private files at those paths (or under `private/` and point
  `config.yaml` at them) and git will refuse to track them. This layered source
  checkout may carry private products on a private branch; the public exporter
  excludes those paths before publishing.
- **Per-skill private notes.** Any candidate-specific skill guidance that used to be
  baked into a `SKILL.md` (real lead-project ordering, real metrics, personal
  anecdotes) lives in a git-ignored `references_private/` folder inside that skill
  (e.g. `.agents/skills/resume-writer/references_private/`). Each `SKILL.md` reads it
  when present (its "Before You Start" **Personalization** stanza) and otherwise falls
  back to the generic examples. The exporter prunes these folders and the leak guard
  fails on any tracked file under one.
- **Guard tokens are config-derived.** `scripts/publish/check_public.py` hardcodes no
  identity; it derives its personal-token set from `config.yaml`, an optional
  `private/leak_tokens.txt`, and the `JOBHUNT_PERSONAL_TOKENS` env var, and scans both
  text and `.docx`/`.pdf` content.
- The public skill router `.cursor/rules/shared-skills.mdc` (tracked) lists only
  the public skills. The private `coding-interview` skill is registered by
  `.cursor/rules/private-skills.mdc`, which the overlay supplies (see the template
  at `docs/overlay-templates/private-skills.mdc`) and which is git-ignored in the
  public repo — so it is discoverable **only** when the overlay is mounted.
- `config.yaml`'s `paths.*` are resolved **relative to the config file's
  directory**, so you can point them at `private/…` (or anywhere) and swap the
  fake example candidate for your real one without editing any tooling.

## Suggested overlay layout

Keep the overlay as its own git repo (private). A clean layout that maps onto the
`config.yaml` `paths.*` keys:

```
my-jobhunt-overlay/            # private git repo (mounts at ./private/)
├── config.yaml                # your real identity + paths (copied from config.example.yaml)
├── leak_tokens.txt            # -> private/leak_tokens.txt (extra publish-guard tokens)
├── job-search/
│   └── blacklist.yaml         # -> private/job-search/blacklist.yaml (registry skip rules)
├── profile/
│   ├── profile.md             # -> paths.profile_md
│   ├── baseline.yaml          # -> paths.baseline_yaml
│   ├── company-levels.yaml    # -> paths.company_levels_yaml (optional; defaults here)
│   ├── applications-log.yaml  # auto-generated (job-search skip list)
│   └── company-search-log.yaml
├── templates/
│   └── reference.docx         # -> paths.reference_docx
├── applications/              # your real applications (-> paths.applications_root)
│   └── 1_discoveries/         # discoveries dir; keep fresh scans in current/, aged ones in archive/
│       ├── current/           # -> paths.discoveries_dir
│       └── archive/
├── interviews/                # your real interview prep
├── skills/
│   ├── coding-interview/      # the PRIVATE skill (SKILL.md + products)
│   └── references_private/    # per public skill: candidate-specific notes/examples,
│                              # symlinked/copied into .agents/skills/<skill>/references_private/
├── job-search-profiles/
│   ├── my-default.yaml        # your real search profile(s)
│   └── my-smb.yaml
└── cursor-rules/
    └── private-skills.mdc     # copied from docs/overlay-templates/private-skills.mdc
```

`private/leak_tokens.txt` is one token per line (blank / `#` lines ignored) — put
identity attributes NOT stored in `config.yaml` here (extra handles, school, GPA,
title, current/former employers, internal product and distinctive project names).
`private/job-search/blacklist.yaml` holds identity-only rows (`name` + optional
`aliases` + a `blacklist:` reason) that `registry.py` merges into the company registry
so personal skip rules never live in the public `companies.yaml`.

## Setup steps

Starting from a fresh public checkout (clone of the public toolkit repo):

1. **Mount the overlay.** Clone (or symlink) your private overlay into the
   git-ignored `private/` path of the public checkout:

   ```bash
   git clone git@github.com:you/my-jobhunt-overlay.git private
   # or, if the overlay already lives elsewhere:
   ln -s /abs/path/to/my-jobhunt-overlay private
   ```

2. **Create `config.yaml`.** Copy the example and edit the `paths.*` to point at
   your overlay data (paths resolve relative to the config file's directory):

   ```bash
   cp config.example.yaml config.yaml
   ```

   ```yaml
   # config.yaml (illustrative — real values live only in your overlay)
   candidate:
     name: "Jordan Rivers"
     contact_line: "City, ST • jordan.rivers@example.com • linkedin.com/in/jordanrivers"
     name_slug: "Jordan_Rivers"
     title_slug: "Software_Engineer"
   paths:
     profile_md: "private/profile/profile.md"
     baseline_yaml: "private/profile/baseline.yaml"
     company_levels_yaml: "private/profile/company-levels.yaml"
     reference_docx: "private/templates/reference.docx"
     applications_root: "private/applications"
     discoveries_dir: "private/applications/1_discoveries/current"
   job_search:
     default_profile: "my-default"
   ```

   `config.yaml` is git-ignored in the public repo, so your real identity never
   gets committed. (If you prefer, point `paths.*` at in-place folders like
   `applications/` — those are git-ignored too.)

3. **Mount the private skill.** Make the overlay's `coding-interview` skill visible
   at the canonical skills path, then register its router:

   ```bash
   ln -s ../../private/skills/coding-interview .agents/skills/coding-interview
   cp docs/overlay-templates/private-skills.mdc .cursor/rules/private-skills.mdc
   ```

   Both `.agents/skills/coding-interview/` and `.cursor/rules/private-skills.mdc`
   are git-ignored in the public repo, so the private skill stays out of public
   history while remaining discoverable whenever the overlay is mounted.

4. **Add your real job-search profile(s).** Drop them next to the example profile
   and point `config.job_search.default_profile` at one:

   ```bash
   cp private/job-search-profiles/my-default.yaml \
      .agents/skills/job-search/profiles/my-default.yaml
   ```

   (The `.agents/skills/job-search/profiles/` folder keeps `example.yaml`,
   `_TEMPLATE.yaml`, and `README.md` public; any `<label>.yaml` you add here is
   your own — keep personal profiles in the overlay and out of the public repo.)

## Producing / refreshing the public repo

Maintainers regenerate the clean public repo from the combined working checkout
with the allowlist exporter — it copies only public paths, prunes `references_private/`,
scrubs files containing personal tokens (text AND `.docx`/`.pdf` content), and
**always** runs the leak guard against the copied tree as the final gate. `--git-init`
additionally commits the clean export:

```bash
.venv/bin/python scripts/publish/export_public.py --dest /path/to/public --git-init
```

The leak guard (`scripts/publish/check_public.py`) fails the publish if any private
skill, `private/` path, tracked `references_private/` file, or personal-identity token
(in a path, text content, or extracted `.docx`/`.pdf` content) is present. Its tokens
are derived at runtime from `config.yaml` + `private/leak_tokens.txt` +
`JOBHUNT_PERSONAL_TOKENS` (nothing hardcoded). Run it any time against a checkout — in
the combined repo it reads the real tokens from your `config.yaml`:

```bash
.venv/bin/python scripts/publish/check_public.py
```
