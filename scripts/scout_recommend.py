"""Rank missing core indicators for the next observation.

Example:
  python scripts/scout_recommend.py --observed water_temperature electrical_conductivity nitrate
Default target year = last data year + 1, so ALL complete years train the model.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.scout.engine import DEFAULT_RIDGE, recommend  # noqa: E402
from app.services.scout.panel import load_annual_median_panel  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--observed", nargs="*", default=[])
    ap.add_argument("--target-year", type=int, default=None)
    ap.add_argument("--ridge", type=float, default=DEFAULT_RIDGE)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    panel = load_annual_median_panel()
    target = a.target_year or (max(panel.years) + 1)
    res = recommend(panel, target, a.observed, ridge=a.ridge)
    if a.json:
        print(json.dumps(res, indent=2))
        return
    ex = res["explanation"]
    print(f"Observed: {res['observed'] or '(none)'}")
    print(f"Training years ({res['n_train_years']}): {res['training_years']}  ridge={res['ridge']}")
    print("\nRank  Indicator                  EIG (nats)")
    for r in res["rankings"]:
        print(f"{r['rank']:>4}  {r['indicator']:<25}  {r['eig']:.4f}")
    print(f"\nRecommended: {res['recommendation']}  (ridge stability: {res['ridge_stability']})")
    print("Top associated:", ", ".join(
        f"{t['indicator']} ({t['correlation']:+.2f})" for t in ex["top_associated_indicators"]))
    print("Limitations:")
    for l in ex["limitations"]:
        print("  -", l)


if __name__ == "__main__":
    main()