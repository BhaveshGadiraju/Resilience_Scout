"""Run the leakage-safe historical replay and write analysis/scout_engine/*."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.scout.backtest import run_backtest, write_outputs  # noqa: E402
from app.services.scout.engine import DEFAULT_RIDGE  # noqa: E402
from app.services.scout.panel import load_annual_median_panel  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k-missing", nargs="+", type=int, default=[3, 4])
    ap.add_argument("--ridge", type=float, default=DEFAULT_RIDGE)
    ap.add_argument("--out", default=str(ROOT / "analysis" / "scout_engine"))
    a = ap.parse_args()

    panel = load_annual_median_panel()
    print("complete core years:", panel.complete_years())
    res = run_backtest(panel, k_missing_values=tuple(a.k_missing), ridge=a.ridge)
    write_outputs(res, a.out)
    print(res["by_strategy"].to_string(index=False))
    print("\nRidge sensitivity:")
    print(res["ridge_table"].to_string(index=False))
    print("\nScout top-1 agreement across folds:",
          res["summary"]["scout_top1_agreement_across_folds"])
    print("Wrote", a.out)


if __name__ == "__main__":
    main()