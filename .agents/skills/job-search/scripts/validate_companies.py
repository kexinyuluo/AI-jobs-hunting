#!/usr/bin/env python3
"""Validate that every company token in companies.yaml is still reachable.

Usage: .venv/bin/python .agents/skills/job-search/scripts/validate_companies.py
Prints OK/FAIL with job counts. Use when adding companies or if fetches break.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

from sources import fetch_company

SKILL_DIR = Path(__file__).resolve().parents[1]


def main() -> int:
    registry = yaml.safe_load((SKILL_DIR / "companies.yaml").read_text()) or {}
    all_entries = registry.get("companies", [])
    # Identity-only rows (no `ats`, e.g. blacklist-only companies) are never polled,
    # so skip them here — only poll entries have a board to validate.
    companies = [c for c in all_entries if isinstance(c, dict) and c.get("ats")]
    skipped = len(all_entries) - len(companies)
    bad = 0
    for c in companies:
        try:
            n = len(fetch_company(c))
            status = "OK  " if n else "EMPTY"
            if not n:
                bad += 1
            print(f"{status} {c['name']:<18} {c['ats']}:{c['token']}  ({n} jobs)")
        except Exception as exc:  # noqa: BLE001
            bad += 1
            print(f"FAIL {c['name']:<18} {c['ats']}:{c['token']}  {exc}")
    print(f"\n{len(companies) - bad}/{len(companies)} companies reachable"
          + (f" ({skipped} identity-only rows skipped)." if skipped else "."))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
