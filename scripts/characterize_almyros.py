#!/usr/bin/env python3
"""Characterize normalized Almyros observations (Phase 2B)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services.characterize_almyros import (  # noqa: E402
    run_characterization,
    write_analysis_summary,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-csv",
        type=Path,
        default=None,
        help="Normalized Almyros CSV (default: data/processed/almyros/observations.csv)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Characterization output directory "
        "(default: data/processed/almyros/characterization)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print summary as JSON",
    )
    args = parser.parse_args()

    summary = run_characterization(input_csv=args.input_csv, output_dir=args.output_dir)
    write_analysis_summary(summary)

    if args.json:
        payload = {
            k: v
            for k, v in summary.items()
            if k not in ("profile", "readiness")
        }
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(
            f"Characterized {summary['row_count']} rows / "
            f"{summary['indicator_count']} indicators"
        )
        print(f"Output: {summary['output_dir']}")
        print(f"Provenance: {summary['provenance_path']}")
        print(
            "Readiness — "
            f"candidate={len(summary['candidates'])}, "
            f"limited={len(summary['limited'])}, "
            f"exclude={len(summary['excluded'])}"
        )
        print(f"scale_anomaly rows: {summary['scale_anomaly_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
