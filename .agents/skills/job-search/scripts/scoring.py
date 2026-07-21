"""Filtering and scoring of postings against a job-matching profile."""
from __future__ import annotations

import re

from common import JobPosting, normalize, term_matches
from job_metadata import extract_required_yoe_details
from visa import classify_visa, visa_tags

_US_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west virginia", "wisconsin", "wyoming",
}
_US_STATE_ABBR = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}
_US_HUBS = {
    "san francisco", "bay area", "silicon valley", "mountain view", "palo alto",
    "menlo park", "sunnyvale", "santa clara", "san jose", "cupertino", "oakland",
    "redwood city", "san mateo", "seattle", "bellevue", "redmond", "kirkland",
    "new york", "brooklyn", "boston", "cambridge", "austin", "dallas", "houston",
    "denver", "boulder", "chicago", "atlanta", "miami", "los angeles",
    "san diego", "portland", "phoenix", "raleigh", "durham", "pittsburgh",
    "philadelphia", "minneapolis", "nashville", "salt lake", "washington, d",
}
_US_TOKENS = ("united states", "usa", "u.s.", "u.s.a", "remote - us", "remote, us",
              "remote (us", "us remote", "united states of america")
_FOREIGN_TOKENS = (
    "united kingdom", " uk", "uk)", "u.k", "london", "england", "scotland",
    "ireland", "dublin", "germany", "berlin", "munich", "hamburg", "cologne",
    "frankfurt", "karlsruhe", "nuremberg", "bremen", "stuttgart", "canada",
    "toronto", "vancouver", "montreal", "france", "paris", "india",
    "bangalore", "bengaluru", "hyderabad", "pune", "mumbai", "delhi", "chennai",
    "singapore", "australia", "sydney", "melbourne", "netherlands", "amsterdam",
    "spain", "madrid", "barcelona", "portugal", "lisbon", "poland", "warsaw",
    "brazil", "sao paulo", "mexico", "japan", "tokyo", "korea", "china",
    "israel", "tel aviv", "emea", "apac", "latam", "europe", "zurich", "geneva",
    "sweden", "stockholm", "denmark", "copenhagen", "romania", "bucharest",
    "philippines", "manila", "argentina", "colombia", "nigeria", "kenya",
    "new zealand", "vietnam", "indonesia", "malaysia", "dubai", "abu dhabi",
)


def is_foreign(nloc: str) -> bool:
    return any(tok in nloc for tok in _FOREIGN_TOKENS)


def is_us(original_loc: str, nloc: str) -> bool:
    if any(tok in nloc for tok in _US_TOKENS):
        return True
    if any(re.search(rf"\b{re.escape(s)}\b", nloc) for s in _US_STATE_NAMES):
        return True
    if any(h in nloc for h in _US_HUBS):
        return True
    # uppercase 2-letter state abbreviation in the original string (e.g. ", CA")
    if any(ab in _US_STATE_ABBR for ab in re.findall(r"\b[A-Z]{2}\b", original_loc or "")):
        return True
    return False


def title_ok(posting: JobPosting, profile: dict) -> bool:
    titles = profile.get("titles", {}) or {}
    ntitle = normalize(posting.title)
    include = titles.get("include") or []
    exclude = titles.get("exclude") or []
    # Strip known non-level phrases before applying excludes, so their words don't
    # trip a rule — e.g. "Member of Technical Staff" must survive the "staff" exclude.
    ntitle_excl = ntitle
    for phrase in titles.get("exclude_neutralize") or []:
        ntitle_excl = ntitle_excl.replace(normalize(phrase), " ")
    if exclude and any(term_matches(t, ntitle_excl) for t in exclude):
        return False
    if include:
        return any(term_matches(t, ntitle) for t in include)
    return True


def location_ok(posting: JobPosting, profile: dict) -> bool:
    loc_cfg = profile.get("location", {}) or {}
    nloc = normalize(posting.location)
    preferred = loc_cfg.get("preferred") or []
    remote = posting.remote in ("remote", "hybrid")
    allow_remote = loc_cfg.get("allow_remote", True)
    require = loc_cfg.get("require_match")
    us_only = loc_cfg.get("us_only")

    if not require and not us_only:
        return True

    # Foreign roles are dropped first — this wins over remote / preferred("remote") /
    # US-abbrev false positives (e.g. "Germany (Remote)", "CA-Ontario-Toronto").
    if is_foreign(nloc):
        return False

    # Strict mode: only preferred cities or remote.
    if require:
        if allow_remote and remote:
            return True
        return any(term_matches(p, nloc) for p in preferred)

    # US-only gate: keep US-based, preferred, or (non-foreign) remote.
    if any(term_matches(p, nloc) for p in preferred):
        return True
    if is_us(posting.location, nloc):
        return True
    return bool(allow_remote and remote)


def visa_ok(posting: JobPosting, profile: dict) -> bool:
    """Apply the profile's visa policy. Fills posting.visa_label/hits as a side effect."""
    label, hits = classify_visa(posting.description or posting.title)
    posting.visa_label = label
    posting.visa_hits = hits
    visa = profile.get("visa", {}) or {}
    if not visa.get("needs_sponsorship"):
        return True
    policy = visa.get("policy", "exclude_negative")
    if policy == "require_positive":
        return label == "yes"
    return label != "no"          # exclude_negative (default): keep yes + unclear


def date_ok(posting: JobPosting, max_age_days: float | None) -> bool:
    if max_age_days is None:
        return True
    if posting.age_days is None:      # unknown date -> keep, flag in reasons
        return True
    return posting.age_days <= max_age_days


def parse_min_required_years(text: str | None) -> int | float | None:
    """Return only a high-confidence general minimum YOE.

    Preferred or tool-specific/contextual YOE may still be shown in metadata, but
    it is not safe to use as a hard search filter.
    """
    details = extract_required_yoe_details(text)
    return details.get("min") if details.get("confidence") == "high" else None


def experience_ok(posting: JobPosting, profile: dict) -> bool:
    """Drop postings whose stated minimum YOE exceeds profile max_years_experience."""
    cap = profile.get("max_years_experience")
    if cap is None:
        return True
    blob = " ".join(
        x for x in (posting.description, posting.title) if x
    )
    stated_min = parse_min_required_years(blob)
    if stated_min is None:
        return True
    return stated_min <= int(cap)


def comp_ok(posting: JobPosting, profile: dict) -> bool:
    """Drop postings whose stated salary is clearly annual and below the floor.

    Fires only when ``profile["comp"]["min_base"]`` is set AND the posting states a
    salary whose upper bound reads as an annual USD figure below the floor. A range
    that reaches the floor at its top is kept (it *can* pay enough). No stated salary,
    small numbers (< 15k — per-hour/per-month or a parse artifact, not a plausible
    annual salary), and unparseable values are all kept: the floor never guesses.
    """
    floor = (profile.get("comp") or {}).get("min_base")
    if not floor:
        return True
    s = posting.salary_range
    if not isinstance(s, dict):
        return True
    hi, lo = s.get("max"), s.get("min")
    top = hi if isinstance(hi, (int, float)) else lo
    if not isinstance(top, (int, float)) or top < 15000:
        return True
    return top >= float(floor)


# --------------------------------------------------------------------------- #
# AI-native / AI-transitioning company signal
# --------------------------------------------------------------------------- #
def ai_company_hits(posting: JobPosting, profile: dict) -> list[str]:
    """AI-native/AI-transitioning signals found in the JD (title + description).

    A JD-text heuristic that works on EVERY source (company boards + Indeed/
    LinkedIn hits), unlike the registry tag which only covers curated boards.
    Signals come from `profile["ai_company"]["signals"]`.
    """
    cfg = profile.get("ai_company", {}) or {}
    signals = cfg.get("signals") or []
    if not signals:
        return []
    blob = normalize((posting.title or "") + " " + (posting.description or ""))
    return [s for s in signals if term_matches(s, blob)]


def ai_company_ok(posting: JobPosting, profile: dict,
                  is_ai_native_company: bool = False) -> bool:
    """Hard-filter to AI-native/AI-transitioning employers when configured.

    Only active when `ai_company.require` is truthy (set by `--ai-native-only` or
    the profile). A posting passes if its company is a registry AI-native employer
    OR its JD carries at least one AI-company signal. Default (soft) mode keeps
    everything and lets `score_posting` apply the boost instead.
    """
    cfg = profile.get("ai_company", {}) or {}
    if not cfg.get("require"):
        return True
    return is_ai_native_company or bool(ai_company_hits(posting, profile))


# --------------------------------------------------------------------------- #
# Level / experience fit
# --------------------------------------------------------------------------- #
# Google-equivalent numeric bands per normalized seniority word. Mirrors
# job_metadata.GENERIC_GOOGLE_EQUIVALENTS so the level-fit penalty speaks the
# same scale as the discovery table's "Level (Google eq.)" column.
_LEVEL_BANDS = {
    "intern": (2.0, 2.8), "entry": (3.0, 3.8), "mid": (4.0, 4.8),
    "senior": (5.0, 5.8), "staff": (6.0, 6.8), "senior_staff": (7.0, 7.8),
    "principal": (8.0, 8.8), "distinguished": (9.0, 10.0),
}


def target_level_band(profile: dict) -> tuple[float, float] | None:
    """Desired Google-equivalent level range spanning every `seniority.target` word.

    Returns ``(low, high)`` or ``None`` when no recognized target is configured
    (so the caller skips the level-fit penalty entirely). ``senior staff`` and
    ``senior_staff`` are both accepted.
    """
    target = (profile.get("seniority", {}) or {}).get("target") or []
    bands = [_LEVEL_BANDS[key] for t in target
             if (key := normalize(t).replace(" ", "_")) in _LEVEL_BANDS]
    if not bands:
        return None
    return min(b[0] for b in bands), max(b[1] for b in bands)


def level_fit_delta(posting: JobPosting, band: tuple[float, float] | None,
                    weight: float) -> tuple[float, str | None]:
    """Non-positive score adjustment for how far a posting sits outside `band`.

    Overlapping (in-band) or unknown levels are not penalized. Distance is in
    Google-ladder steps (~1.0 per level), scaled by `weight`.
    """
    if band is None or weight <= 0:
        return 0.0, None
    level = posting.job_level or {}
    low, high = level.get("min"), level.get("max")
    if low is None and high is None:
        return 0.0, None
    lo = float(low if low is not None else high)
    hi = float(high if high is not None else low)
    b_lo, b_hi = band
    if hi < b_lo:                       # under-leveled (e.g. entry role for a senior search)
        dist, kind = b_lo - hi, "under-leveled"
    elif lo > b_hi:                     # over-leveled (e.g. staff+ role for a senior search)
        dist, kind = lo - b_hi, "over-leveled"
    else:
        return 0.0, None                # overlaps the target band -> good fit
    penalty = round(dist * weight, 1)
    return -penalty, f"{kind} (-{penalty:g})"


def score_posting(posting: JobPosting, profile: dict,
                  sponsor_index: dict | None = None,
                  is_ai_native_company: bool = False) -> None:
    """Compute posting.score and posting.reasons in place.

    `is_ai_native_company` is precomputed by the caller (search_jobs) from the
    registry AI-native tag set, so scoring.py stays free of a registry import.
    """
    kw = profile.get("keywords", {}) or {}
    ntitle = normalize(posting.title)
    ndesc = normalize(posting.description)
    score = 0.0
    reasons: list[str] = []

    strong = [k for k in (kw.get("strong") or []) if term_matches(k, ntitle + " " + ndesc)]
    good = [k for k in (kw.get("good") or []) if term_matches(k, ndesc)]
    neg = [k for k in (kw.get("negative") or []) if term_matches(k, ntitle + " " + ndesc)]

    for k in strong:
        bump = 8 if term_matches(k, ntitle) else 4
        score += bump
    for k in good:
        score += 1.5
    for k in neg:
        score -= 4
    if strong:
        reasons.append("strong: " + ", ".join(strong[:6]))
    if good:
        reasons.append("skills: " + ", ".join(good[:6]))
    if neg:
        reasons.append("mismatch: " + ", ".join(neg[:6]))

    # Seniority hint
    sen_cfg = profile.get("seniority", {}) or {}
    target = [s.lower() for s in sen_cfg.get("target", [])]
    if "staff" in target and term_matches("staff", ntitle):
        score += 4; reasons.append("staff-level title")
    elif "senior" in target and (term_matches("senior", ntitle) or term_matches("sr", ntitle)):
        score += 3; reasons.append("senior-level title")

    # Level fit: demote roles whose parsed Google-equivalent level sits outside the
    # target seniority band, so a "senior" search isn't topped by staff+/entry roles.
    # Reuses the level parsed by enrich_posting_metadata; `fit_weight: 0` disables it.
    fit_delta, fit_note = level_fit_delta(
        posting, target_level_band(profile), float(sen_cfg.get("fit_weight", 6.0)))
    if fit_delta:
        score += fit_delta
        reasons.append("level " + fit_note)

    # YOE fit (opt-in): demote roles asking materially more experience than the
    # candidate has. Active only when the profile states `years_experience`.
    cand_yoe = profile.get("years_experience")
    if cand_yoe is not None:
        req_min = (posting.required_yoe or {}).get("min")
        if req_min is not None and float(req_min) > float(cand_yoe):
            over = float(req_min) - float(cand_yoe)
            penalty = round(over * float(sen_cfg.get("yoe_fit_weight", 1.0)), 1)
            if penalty:
                score -= penalty
                reasons.append(f"yoe over-reach +{over:g}y (-{penalty:g})")

    # Visa
    if posting.visa_label == "yes":
        score += 15; reasons.append("visa: sponsorship stated (" + ", ".join(posting.visa_hits[:3]) + ")")
    elif posting.visa_label == "unclear":
        reasons.append("visa: not stated (verify)")
    tags = visa_tags(posting.description)
    if "h1b_transfer_friendly" in tags:
        score += 5; reasons.append("h1b transfer friendly")

    # AI-native / AI-transitioning company signal (boost; hard-filter is optional
    # and handled by ai_company_ok). Rewards "infra role AT an AI-native company".
    ai_cfg = profile.get("ai_company", {}) or {}
    if ai_cfg:
        hits = ai_company_hits(posting, profile)
        if hits:
            per = float(ai_cfg.get("boost_per_hit", 2))
            cap = float(ai_cfg.get("max_boost", 10))
            score += min(cap, per * len(hits))
            reasons.append("ai-signal: " + ", ".join(hits[:5]))
        if is_ai_native_company:
            score += float(ai_cfg.get("company_boost", 6))
            reasons.append("ai-native company")

    # Employer sponsorship history (optional DOL enrichment)
    if sponsor_index:
        key = _norm_company(posting.company)
        rec = sponsor_index.get(key)
        if rec:
            h1b = rec.get("h1b", 0); perm = rec.get("perm", 0)
            if h1b or perm:
                score += min(10, (h1b + perm * 2) / 20.0)
                reasons.append(f"DOL: {h1b} H-1B / {perm} PERM filings")

    # Location
    loc_cfg = profile.get("location", {}) or {}
    nloc = normalize(posting.location)
    if any(term_matches(p, nloc) for p in (loc_cfg.get("preferred") or [])):
        score += 5; reasons.append(f"location: {posting.location}")
    if posting.remote in ("remote", "hybrid"):
        score += 3; reasons.append(posting.remote)

    # Recency (mild boost for very fresh)
    if posting.age_days is not None and posting.age_days <= 1:
        score += 3; reasons.append("posted <24h")

    posting.score = round(score, 1)
    posting.reasons = reasons


def _norm_company(name: str) -> str:
    n = normalize(name)
    for suffix in (" inc", " llc", " ltd", " corp", " corporation", " labs",
                   " technologies", " technology", " ai", " io", " the "):
        n = n.replace(suffix, " ")
    return " ".join(n.split())
