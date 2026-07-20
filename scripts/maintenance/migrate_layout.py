"""Migrate application folders to the source/ layout + bundled application .txt.

For every application folder under applications/<status>/<slug>/ this:
  1. Creates a source/ subfolder and moves the generation inputs/intermediates into
     it: JD files (renaming a legacy jd.md to JD-<job-title>.md), tailored.yaml, and
     the resume/cover-letter DOCX files.
  2. Bundles the standalone cover-letter and why-fit .txt files into a single
     copy-paste-friendly Application .txt at the folder root, with a synthesized
     "Past experience" section drawn from the tailored resume content. The cover
     letter's company/role subject line is dropped (the new cover letter starts with
     the name + contact, then the salutation).
  3. Leaves the final resume/cover PDFs, meta.yaml, and notes.md at the folder root.

Idempotent: re-running skips folders already migrated. Purely reorganizes files and
merges existing prose — it never fabricates content.

Usage:
    python scripts/maintenance/migrate_layout.py            # migrate every status folder
    python scripts/maintenance/migrate_layout.py --status drafted
    python scripts/maintenance/migrate_layout.py --dry-run
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

# Repo-only dev tool (NOT a distributed skill): migrate_layout.py lives in
# scripts/maintenance/, so the repo root is two parents up. It reuses the
# canonical shared modules (scripts/shared) for config/layout AND the
# resume-writer skill's cover_letter for parse_cover_letter, so it puts both on
# sys.path (plus the skill's _vendor/ so cover_letter and the check it imports can
# resolve config/layout/location). A repo-relative reach into the sibling skill is
# acceptable here because this tool is never vendored or distributed.
REPO_ROOT = Path(__file__).resolve().parents[2]
_SHARED = REPO_ROOT / "scripts" / "shared"
_RESUME_WRITER = REPO_ROOT / ".agents" / "skills" / "resume-writer" / "scripts"
for _p in (_RESUME_WRITER / "_vendor", _RESUME_WRITER, _SHARED):
    if _p.is_dir() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import config
from config import application_stem
from layout import source_dir, tailored_path
from cover_letter import parse_cover_letter

# Candidate-identity-derived resume stem from config (config.yaml holds the real
# value, so behavior is preserved).
RESUME_STEM = config.resume_stem()
APPLICATIONS_DIR = REPO_ROOT / "applications"
# On-disk status folders (numbered so a file browser lists applications/ in order).
STATUS_FOLDERS = ["6_drafted", "5_applied", "4_in_progress", "3_rejected", "2_ignored"]

BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _strip_bold(text: str) -> str:
    return BOLD_RE.sub(r"\1", text or "").strip()


def slugify_role(role: str) -> str:
    """Turn a job title into a filename slug: lowercase, hyphens, no punctuation."""
    cleaned = re.sub(r"[^0-9A-Za-z]+", " ", role or "").strip().lower()
    return "-".join(cleaned.split()) or "role"


def _load_yaml(path: Path) -> dict:
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except (OSError, yaml.YAMLError):
        return {}


def _jd_target_name(app_dir: Path, meta: dict) -> str:
    """Filename for a legacy jd.md renamed to the JD-<job-title>.md convention."""
    role = meta.get("role", "")
    if not role and isinstance(meta.get("jobs"), list) and meta["jobs"]:
        role = meta["jobs"][0].get("role", "")
    if not role:
        # Derive from the slug: <company>-<role>-<YYYYMMDD>
        parts = app_dir.name.rsplit("-", 1)
        stem = parts[0] if len(parts) == 2 and parts[1].isdigit() else app_dir.name
        role = stem.split("-", 1)[1] if "-" in stem else stem
    return f"JD-{slugify_role(role)}.md"


def _reconstruct_cover(parsed: dict) -> str:
    """Rebuild a clean cover-letter block (name + contact, salutation, body, close)
    with the company/role subject line removed."""
    out = list(parsed["header"])  # name + contact line(s) only
    if parsed["salutation"]:
        out += ["", parsed["salutation"]]
    for para in parsed["paragraphs"]:
        out += ["", para]
    if parsed["closing"]:
        out += [""] + parsed["closing"]
    return "\n".join(out).strip()


def _synth_past_experience(app_dir: Path) -> str:
    """Plain-English 'past experience' answer drawn from the tailored resume."""
    data = _load_yaml(tailored_path(app_dir))
    if not data:
        return "(Add a plain-English summary of relevant past experience here.)"
    emps = data.get("employers") or ([data["employer"]] if data.get("employer") else [])
    paras = []
    summary = " ".join(_strip_bold(b) for b in data.get("summary_bullets", []))
    if emps:
        e = emps[0]
        header = f"{e.get('role', '')} at {e.get('company', '')} ({e.get('dates', '')})."
        paras.append((header + " " + summary).strip())
    elif summary:
        paras.append(summary)
    for e in emps:
        for proj in e.get("projects", []):
            title = _strip_bold(proj.get("title", ""))
            bullets = " ".join(_strip_bold(b) for b in proj.get("bullets", []))
            if title and bullets:
                paras.append(f"{title}: {bullets}")
    return "\n\n".join(paras)


def _bundle_section(title: str, body: str) -> str:
    body = (body or "").strip() or "(to be written)"
    return f"{title}\n{'=' * len(title)}\n\n{body}"


def migrate(app_dir: Path, dry_run: bool = False) -> str:
    src = source_dir(app_dir)
    meta = _load_yaml(app_dir / "meta.yaml")
    label = _load_yaml(tailored_path(app_dir)).get("target_position", "")
    actions = []

    def move(srcp: Path, dstp: Path):
        actions.append(f"mv {srcp.relative_to(app_dir)} -> "
                       f"{dstp.relative_to(app_dir)}")
        if not dry_run:
            dstp.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(srcp), str(dstp))

    # 1. Move generation inputs/intermediates into source/.
    for md in sorted(app_dir.glob("*.md")):
        low = md.name.lower()
        if low == "jd.md":
            move(md, src / _jd_target_name(app_dir, meta))
        elif low.startswith("jd-"):
            move(md, src / md.name)
        # notes.md and anything else stays at the root.

    root_tailored = app_dir / "tailored.yaml"
    if root_tailored.exists():
        move(root_tailored, src / "tailored.yaml")

    for docx in sorted(list(app_dir.glob(f"{RESUME_STEM}*.docx"))
                       + list(app_dir.glob("*Cover_Letter*.docx"))):
        move(docx, src / docx.name)

    # Legacy pre-RESUME_STEM naming: resume.docx -> source/<stem>.docx,
    # resume.pdf -> <stem>.pdf (kept at root as the final PDF).
    legacy_docx = app_dir / "resume.docx"
    if legacy_docx.exists():
        move(legacy_docx, src / f"{RESUME_STEM}.docx")
    legacy_pdf = app_dir / "resume.pdf"
    if legacy_pdf.exists() and not (app_dir / f"{RESUME_STEM}.pdf").exists():
        move(legacy_pdf, app_dir / f"{RESUME_STEM}.pdf")

    # 2. Bundle cover-letter + why-fit .txt (+ synthesized past experience).
    bundle_path = app_dir / f"{application_stem(label)}.txt"
    cover_txts = sorted(app_dir.glob("*Cover_Letter*.txt"))
    why_txts = sorted(app_dir.glob("*Why_Fit*.txt"))
    if not bundle_path.exists() and (cover_txts or why_txts):
        cover_body = ""
        if cover_txts:
            cover_body = _reconstruct_cover(parse_cover_letter(cover_txts[0].read_text()))
        why_body = why_txts[0].read_text().strip() if why_txts else ""
        past_body = _synth_past_experience(app_dir)
        bundle = "\n\n\n".join([
            _bundle_section("COVER LETTER", cover_body),
            _bundle_section("WHY THIS COMPANY & ROLE", why_body),
            _bundle_section("PAST EXPERIENCE", past_body),
        ]) + "\n"
        actions.append(f"write {bundle_path.name}")
        if not dry_run:
            bundle_path.write_text(bundle)
        for old in cover_txts + why_txts:
            actions.append(f"rm {old.name}")
            if not dry_run:
                old.unlink()

    return "; ".join(actions) if actions else ""


def main():
    ap = argparse.ArgumentParser(description="Migrate application folders to source/ layout")
    ap.add_argument("--status", choices=STATUS_FOLDERS, default=None,
                    help="Only migrate one status folder (default: all)")
    ap.add_argument("--dry-run", action="store_true", help="Print actions, change nothing")
    args = ap.parse_args()

    statuses = [args.status] if args.status else STATUS_FOLDERS
    migrated, skipped = 0, 0
    for status in statuses:
        status_dir = APPLICATIONS_DIR / status
        if not status_dir.is_dir():
            continue
        for app_dir in sorted(status_dir.iterdir()):
            if not app_dir.is_dir() or app_dir.name.startswith("."):
                continue
            actions = migrate(app_dir, dry_run=args.dry_run)
            if actions:
                migrated += 1
                print(f"[{status}/{app_dir.name}] {actions}")
            else:
                skipped += 1
    verb = "would migrate" if args.dry_run else "migrated"
    print(f"\n{verb} {migrated} folder(s); {skipped} already up to date.",
          file=sys.stderr)


if __name__ == "__main__":
    main()
