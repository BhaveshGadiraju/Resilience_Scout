#!/usr/bin/env python3
"""Normalize Almyros OAH FHIR FSH observations into analysis-ready long-format tables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services.normalize_almyros import (  # noqa: E402
    run_normalization,
    write_analysis_summary,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fsh-dir",
        type=Path,
        default=None,
        help="Directory containing Almyros-related .fsh files (default: data/raw/.../github_fsh)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: data/processed/almyros)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print summary as JSON",
    )
    args = parser.parse_args()

    summary = run_normalization(fsh_dir=args.fsh_dir, output_dir=args.output_dir)
    write_analysis_summary(summary)

    if args.json:
        # hashes are fine in JSON
        print(json.dumps(summary, indent=2, default=str))
    else:
        print(
            f"Normalized {summary['source_observation_count']} Almyros observations "
            f"→ {summary['row_count']} long-format rows"
        )
        print(f"CSV: {summary['csv_path']}")
        if summary.get("parquet_path"):
            print(f"Parquet: {summary['parquet_path']}")
        print(f"Provenance: {summary['provenance_path']}")
        print(f"scale_anomaly rows: {summary['scale_anomaly_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
