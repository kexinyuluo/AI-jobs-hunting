"""Backfill a `location` field into every application's meta.yaml.

Reads each application's job-description file(s) (`source/JD-*.md`), extracts the
posting `Location:` line(s), and records them in `meta.yaml`:

- Single-role application  -> a top-level `location: "<loc>"`.
- Multi-role application    -> a `location: "<loc>"` inside each `jobs:` entry
  (read from that entry's `jd_file`).

Insertion is done as targeted text edits (not a YAML round-trip) so existing
formatting, quoting, and comments are preserved. Idempotent: an application (or
job entry) that already has a `location` is left untouched. Applications whose
JD has no `Location:` line are reported so their location can be filled in by
hand.

Usage:
    python .agents/skills/application-tracker/scripts/backfill_location.py                 # all status folders
    python .agents/skills/application-tracker/scripts/backfill_location.py --statuses drafted
    python .agents/skills/application-tracker/scripts/backfill_location.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

# Self-contained skill: this script lives in the application-tracker skill's
# scripts/ folder alongside its _vendor/ copies of the pure toolkit modules. Put
# both the script folder and its _vendor/ on sys.path so the vendored config and
# location modules import regardless of the working directory.
_HERE = Path(__file__).resolve().parent
for _p in (_HERE, _HERE / "_vendor"):
    if str(_p) not in sys.path and _p.is_dir():
        sys.path.insert(0, str(_p))

import config
from location import extract_jd_locations

# The applications root comes from config (config.yaml holds the real path), so
# the scanned folders — and thus behavior — are unchanged no matter where this
# self-contained script lives.
APPLICATIONS_DIR = config.applications_root()
# On-disk status folders (numbered so a file browser lists applications/ in order).
STATUS_FOLDERS = ["6_drafted", "5_applied", "4_in_progress", "3_rejected", "2_ignored"]
SOURCE_DIRNAME = "source"


def _yaml_dq(value: str) -> str:
    """Render a value as a YAML double-quoted scalar."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _source_dir(app_dir: Path) -> Path:
    src = app_dir / SOURCE_DIRNAME
    return src if src.is_dir() else app_dir


def _jd_files(app_dir: Path) -> list[Path]:
    folder = _source_dir(app_dir)
    return [
        p for p in sorted(folder.glob("*.md"))
        if p.name.lower() == "jd.md" or p.name.lower().startswith("jd-")
    ]


def _locations_from_jd(path: Path) -> str:
    try:
        locs = extract_jd_locations(path.read_text())
    except OSError:
        return ""
    seen: list[str] = []
    for loc in locs:
        if loc not in seen:
            seen.append(loc)
    return " / ".join(seen)


def _combined_jd_location(app_dir: Path) -> str:
    seen: list[str] = []
    for jd in _jd_files(app_dir):
        for loc in _locations_from_jd(jd).split(" / "):
            loc = loc.strip()
            if loc and loc not in seen:
                seen.append(loc)
    return " / ".join(seen)


def _insert_after(lines: list[str], idx: int, new_line: str) -> list[str]:
    return lines[: idx + 1] + [new_line] + lines[idx + 1 :]


def backfill_single(text: str, loc: str) -> str | None:
    """Insert a top-level `location:` after the `role:` (or `company:`) line."""
    lines = text.splitlines()
    role_idx = next((i for i, ln in enumerate(lines)
                     if re.match(r"^role\s*:", ln)), None)
    if role_idx is None:
        role_idx = next((i for i, ln in enumerate(lines)
                         if re.match(r"^company\s*:", ln)), None)
    if role_idx is None:
        return None
    new_line = f"location: {_yaml_dq(loc)}"
    out = _insert_after(lines, role_idx, new_line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def backfill_jobs(text: str, meta: dict, app_dir: Path) -> tuple[str | None, list[str]]:
    """Insert a `location:` into each `jobs:` entry, read from its `jd_file`."""
    lines = text.splitlines()
    missing: list[str] = []
    jobs = meta.get("jobs") or []
    src = _source_dir(app_dir)

    # Insert bottom-up so earlier line indexes stay valid.
    insertions: list[tuple[int, str]] = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        if str(job.get("location") or "").strip():
            continue  # already present
        jd_file = str(job.get("jd_file") or "").strip()
        role = str(job.get("role") or "?")
        if not jd_file:
            missing.append(f"{role} (no jd_file)")
            continue
        loc = _locations_from_jd(src / jd_file)
        if not loc:
            missing.append(f"{role} (no Location in {jd_file})")
            continue
        # Find the `jd_file:` line for this entry (values are unique per job).
        pat = re.compile(r"^(\s*)jd_file\s*:\s*['\"]?" + re.escape(jd_file))
        line_idx = next((i for i, ln in enumerate(lines) if pat.match(ln)), None)
        if line_idx is None:
            missing.append(f"{role} (jd_file line not found)")
            continue
        indent = pat.match(lines[line_idx]).group(1)
        insertions.append((line_idx, f"{indent}location: {_yaml_dq(loc)}"))

    if not insertions:
        return (None, missing)
    for idx, new_line in sorted(insertions, key=lambda x: x[0], reverse=True):
        lines = _insert_after(lines, idx, new_line)
    return ("\n".join(lines) + ("\n" if text.endswith("\n") else ""), missing)


def process_app(app_dir: Path, dry_run: bool) -> dict:
    meta_path = app_dir / "meta.yaml"
    result = {"slug": app_dir.name, "action": "skip", "detail": ""}
    if not meta_path.exists():
        result["detail"] = "no meta.yaml"
        return result
    text = meta_path.read_text()
    try:
        meta = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        result["action"] = "error"
        result["detail"] = f"unparseable meta.yaml: {exc}"
        return result

    is_multi = isinstance(meta.get("jobs"), list) and meta.get("jobs")

    if is_multi:
        new_text, missing = backfill_jobs(text, meta, app_dir)
        if new_text is None:
            result["detail"] = ("all jobs already have location"
                                if not missing else "; ".join(missing))
            if missing:
                result["action"] = "needs-manual"
            return result
        detail = "added per-job location"
        if missing:
            detail += f"; MISSING: {'; '.join(missing)}"
            result["action"] = "partial"
        else:
            result["action"] = "updated"
        result["detail"] = detail
    else:
        if str(meta.get("location") or "").strip():
            result["detail"] = "location already present"
            return result
        loc = _combined_jd_location(app_dir)
        if not loc:
            result["action"] = "needs-manual"
            result["detail"] = "no Location line in JD(s)"
            return result
        new_text = backfill_single(text, loc)
        if new_text is None:
            result["action"] = "error"
            result["detail"] = "no role/company anchor to insert after"
            return result
        result["action"] = "updated"
        result["detail"] = f"location = {loc}"

    # Verify the edited YAML still parses before writing.
    try:
        yaml.safe_load(new_text)
    except yaml.YAMLError as exc:
        result["action"] = "error"
        result["detail"] = f"edit broke YAML: {exc}"
        return result
    if not dry_run:
        meta_path.write_text(new_text)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--statuses", default=",".join(STATUS_FOLDERS),
                        help="Comma-separated status folders (default: all).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report changes without writing.")
    args = parser.parse_args()

    statuses = [s.strip() for s in args.statuses.split(",") if s.strip()]
    counts: dict[str, int] = {}
    manual: list[dict] = []
    for status in statuses:
        status_dir = APPLICATIONS_DIR / status
        if not status_dir.is_dir():
            continue
        for app_dir in sorted(status_dir.iterdir()):
            if not app_dir.is_dir() or app_dir.name.startswith("."):
                continue
            res = process_app(app_dir, args.dry_run)
            counts[res["action"]] = counts.get(res["action"], 0) + 1
            tag = res["action"].upper()
            if res["action"] in ("updated", "partial", "needs-manual", "error"):
                print(f"[{tag}] {res['slug']}: {res['detail']}")
            if res["action"] in ("needs-manual", "partial", "error"):
                manual.append(res)

    print("\n" + "=" * 60)
    print("Summary:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    if manual:
        print(f"\n{len(manual)} application(s) need manual location entry:")
        for m in manual:
            print(f"  - {m['slug']}: {m['detail']}")
    if args.dry_run:
        print("\n(dry-run — no files written)")


if __name__ == "__main__":
    main()
