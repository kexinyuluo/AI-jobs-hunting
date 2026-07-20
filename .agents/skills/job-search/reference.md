# Job Search — Data Sources & Heuristics Reference

Detailed reference for the `job-search` skill. Read this when adding sources,
debugging fetchers, or tuning visa detection. Endpoints verified 2026-07-10.

## Supported ATS APIs (public, no auth for reads)

### Greenhouse
- List + descriptions: `https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true`
- Fields used: `title`, `location.name`, `absolute_url`, `first_published`,
  `updated_at`, `content` (HTML, **double entity-encoded** — `strip_html` decodes twice).
- Posted date: prefer `first_published`, fall back to `updated_at`.

### Ashby
- List: `https://api.ashbyhq.com/posting-api/job-board/{token}?includeCompensation=true`
- Fields used: `title`, `location`, `secondaryLocations`, `publishedAt` (ISO w/ ms),
  `descriptionPlain` (plain text), `isRemote`, `workplaceType`, `jobUrl`, `applyUrl`,
  `isListed` (skip when `false`).

### Lever
- List: `https://api.lever.co/v0/postings/{token}?mode=json`
- Fields used: `text` (title), `categories.location`, `descriptionPlain`,
  `createdAt` (epoch **ms**), `workplaceType`, `hostedUrl`.

### SmartRecruiters
- List: `https://api.smartrecruiters.com/v1/companies/{token}/postings?limit=100`
- Detail (for description): `.../postings/{id}` → `jobAd.sections.*.text`.
- Fields used: `name`, `releasedDate`, `location.{city,region,country,remote,hybrid}`.
- Note: description requires a per-posting detail call (slower).

## Finding a company's board token

The token is the slug in the company careers URL:
- `boards.greenhouse.io/<token>` or `job-boards.greenhouse.io/<token>`
- `jobs.ashbyhq.com/<token>`
- `jobs.lever.co/<token>`
- `jobs.smartrecruiters.com/<token>`

Tokens are not always the obvious name (e.g. Glean → `gleanwork`, Scale AI →
`scaleai`, Together AI → `togetherai`, Cursor → `cursor` not `anysphere`). Probe:

```bash
curl -s "https://boards-api.greenhouse.io/v1/boards/<guess>/jobs" | head -c 200
curl -s "https://api.ashbyhq.com/posting-api/job-board/<guess>"    | head -c 200
```

## Cross-company aggregators (span many employers per query)

Implemented in `aggregators.py`. Company boards give the best signal for specific
targets; aggregators give market-wide breadth. All normalize into `JobPosting` and
feed the same filter/score pipeline.

### Keyless (default: jobicy, remoteok, themuse)
| Source | Endpoint | Notes |
|--------|----------|-------|
| Jobicy | `https://jobicy.com/api/v2/remote-jobs?count=100&geo=usa` | US remote; `jobDescription` HTML; `pubDate`. |
| RemoteOK | `https://remoteok.com/api` (User-Agent required) | Full dump; first row is a legal notice (skipped); `date`/`epoch`. |
| The Muse | `https://www.themuse.com/api/public/jobs?page=N&category=...` | US-heavy; `contents` HTML; `publication_date`; no server-side keyword search (client-filtered). |
| Arbeitnow | `https://www.arbeitnow.com/api/job-board-api?page=N` | **EU/Germany-heavy — opt-in only**; `visa_sponsorship=true` filter; `created_at` (unix s). |

### Keyed (STAGE 2, opt-in via env vars) — includes LinkedIn/Indeed coverage
Listed in a profile's `sources.extended_aggregators`; they run only under `--stage 2`
and are skipped quietly when their key env vars are absent (`keyed_available`).
| Source | Env vars | Recency param | Notes |
|--------|----------|---------------|-------|
| Adzuna | `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `ADZUNA_COUNTRY` (def us) | `max_days_old` | `what`/`where` keyword+location; aggregates many boards. |
| JSearch | `RAPIDAPI_KEY` (subscribe to JSearch on RapidAPI) | `date_posted` = today/3days/week/month | **Aggregates LinkedIn + Indeed + Glassdoor** via one key; `query` keyword. |

### JobSpy scraper (site-tiered across the two stages)
Scrapes Indeed / Google / LinkedIn / Glassdoor / ZipRecruiter directly
(`pip install python-jobspy`; already in the repo venv). It is split by site tier:

- **Reliable sites (`sources.jobspy.reliable_sites`, default `[indeed, google]`) run in
  STAGE 1** — free, fast (~1–2s per term×location), rarely rate-limited.
- **Extended sites (`sources.jobspy.extended_sites`, default `[linkedin]`) run in
  STAGE 2** — LinkedIn is slow, often **429/blocks**, and lists no description unless
  `linkedin_fetch_description: true`.

Location config: `sources.jobspy.locations` is a **list** of
`{location, distance, is_remote}` dicts — one scrape per entry. `distance` is a radius
in **miles** (Indeed/LinkedIn/Glassdoor/Zip honor it; Google ignores it). Example: one
entry `{location: "City, ST", distance: 40, is_remote: false}` covers the whole metro
(the anchor city plus its surrounding suburbs) and a second
`{location: "United States", is_remote: true}` adds a US-remote pass. A bare
`jobspy.location` (single string) still works as a fallback. `results_wanted`, `max_terms`
(cap query-terms × locations × sites — each combo is one scrape), and `country_indeed`
tune volume. Recency via `hours_old` (derived from `max_age_days`). Enable with
`sources.jobspy.enabled: true` or `--jobspy`; disable per run with `--no-jobspy`. Helpers:
`build_jobspy_tasks(query_terms, jobspy_cfg, sites, max_age_days)` and `keyed_available(name)`.

### Why not a direct LinkedIn/Indeed API
Neither offers a free public job-search API for third parties (partner/publisher
programs only). Use **JobSpy** (Indeed/Google free in stage 1, LinkedIn/Glassdoor in
stage 2) or **JSearch** (RapidAPI aggregator, stage 2) instead.

## AI-native / AI-transitioning company signal (`scoring.py`)

Encodes "infra role AT an AI-native company (or one transitioning to AI)". Config in the
profile's `ai_company` block. Two signals feed both an optional filter and the score:

- **`ai_company_hits(posting, profile)`** — JD-text heuristic: `ai_company.signals`
  phrases found in title+description (LLM, frontier/foundation model, GenAI, inference/
  training infra, agentic, GPU cluster, ML/AI platform, RAG, vector database, …). Works
  on EVERY source, incl. aggregator hits from companies not in the registry.
- **Registry AI-native tag** — the caller flags a posting whose company resolves (via
  `registry.tagged_keys(ai_company.company_tags)`, default `ai-lab`/`ai-infra`/`ai-native`)
  to a tagged employer; passed to `score_posting(is_ai_native_company=...)`.
- **`ai_company_ok(...)`** — hard-filter, active only when `ai_company.require` is truthy
  (`--ai-native-only`): keep a posting iff it's a registry AI-native employer OR its JD has
  ≥1 signal. Default (soft) mode keeps everything and applies only the boost.

## US / location gate

`location.us_only: true` (set in the active profile) keeps a posting if it is
US-based, matches a preferred city, or is non-foreign remote; it drops clearly-foreign
roles (e.g. "Berlin", "London, UK", "CA-Ontario-Toronto"). This matters when you need
US work authorization / sponsorship. Detection uses US state names + uppercase 2-letter
state abbreviations (from the original string) + major US hubs, and a foreign-token
list that is checked **first** so it wins over remote/abbreviation false positives.
Set `us_only: false` to allow global results, or `require_match: true` for a hard
preferred-cities/remote filter.

## Recency filter

`posted_at` is normalized to UTC from each source's timestamp
(`first_published` / `publishedAt` / `createdAt` / `releasedDate`).
`max_age_days` drops anything older. Postings with an **unknown** date are kept
and flagged (rare) rather than dropped.

## Visa sponsorship heuristic

`visa.py` classifies the JD text into `yes` / `no` / `unclear`:

- **`no`** — an explicit denial matches (e.g. "no sponsorship", "unable to sponsor",
  "authorized to work … without sponsorship", "US citizens only", "green card required").
  Negatives are kept deliberately specific so ordinary "must be authorized to work"
  boilerplate — which even sponsoring employers use — does **not** trigger a reject.
- **`yes`** — an explicit offer matches (e.g. "we sponsor", "H-1B sponsorship",
  "visa sponsorship available", "green card sponsorship", "PERM process", "cap-exempt").
- **`unclear`** — neither; most postings. Under `policy: exclude_negative` these are
  kept; under `require_positive` they are dropped.

Soft tags (`visa_tags`): `h1b_transfer_friendly` (mentions transfer / cap-exempt),
`green_card_mentioned`. These add scoring boosts, not filters.

**This is a text heuristic. Always confirm sponsorship with the employer.**

## Optional DOL sponsorship enrichment

`build_sponsor_index.py` parses DOL OFLC disclosure XLSX files into
`data/sponsors.json` = `{normalized_employer: {"h1b": n, "perm": n}}`.

- Source page: https://www.dol.gov/agencies/eta/foreign-labor/performance
- LCA file (H-1B/H-1B1/E-3): `LCA_Disclosure_Data_FY<YYYY>_Q<n>.xlsx` (large, ~80MB)
- PERM file (green card): `PERM_Disclosure_Data_FY<YYYY>.xlsx`
- Employer name join is fuzzy (`_norm_company` strips Inc/LLC/Labs/AI/etc.); matches
  are approximate — treat the boost as a weak signal, not proof.

## Scoring summary (see `scoring.py`)

| Signal | Effect |
|--------|--------|
| Strong keyword in title | +8 each |
| Strong keyword in description | +4 each |
| Good keyword in description | +1.5 each |
| Negative keyword (honest mis-fit) | −4 each |
| AI-native company (registry tag) | +`company_boost` (default +6) |
| AI-company JD signal | +`boost_per_hit` each (default +2), capped at `max_boost` (default +10) |
| Staff/Senior title (if targeted) | +3–4 |
| Visa `yes` | +15 |
| `h1b_transfer_friendly` tag | +5 |
| DOL employer history (if index present) | up to +10 |
| Preferred location | +5 |
| Remote/hybrid | +3 |
| Posted < 24h | +3 |

## Adding more sources

New aggregators (e.g. USAJobs, Careerjet, Jooble, Findwork, HN "Who is hiring" via
the Algolia API) can be added by writing a fetcher in `aggregators.py` that returns
`JobPosting` objects and registering it in `KEYLESS`/`KEYED`. Read any credentials
from environment variables (never commit keys). The existing filter/score pipeline
then applies automatically.
