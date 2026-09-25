#!/usr/bin/env python3
"""Inspect a local dataset under data/raw/ (CSV, JSON, or FHIR Observations)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running without install: add backend to path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services.inspection import format_report, inspect_path  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "path",
        type=Path,
        help="File or directory to inspect (prefer paths under data/raw/)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of text",
    )
    args = parser.parse_args()

    try:
        report = inspect_path(args.path)
    except Exception as exc:  # noqa: BLE001 — CLI surface
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
