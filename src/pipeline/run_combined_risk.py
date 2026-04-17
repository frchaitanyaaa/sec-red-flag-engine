from __future__ import annotations

import argparse

import pandas as pd

from src.models.combined_risk import (
    build_combined_focus_years,
    build_combined_risk_summary,
)
from src.utils.config import PROCESSED_DATA_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Run combined quantitative risk layer")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. AAPL")
    args = parser.parse_args()

    ticker = args.ticker.strip().lower()
    out_dir = PROCESSED_DATA_DIR / ticker

    zscore_path = out_dir / "zscore_yearly_summary.csv"
    beneish_path = out_dir / "beneish_summary.csv"
    iforest_path = out_dir / "iforest_summary.csv"

    for path in [zscore_path, beneish_path, iforest_path]:
        if not path.exists():
            raise FileNotFoundError(f"Missing required file: {path}")

    zscore_df = pd.read_csv(zscore_path)
    beneish_df = pd.read_csv(beneish_path)
    iforest_df = pd.read_csv(iforest_path)

    summary_df = build_combined_risk_summary(
        zscore_summary_df=zscore_df,
        beneish_summary_df=beneish_df,
        iforest_summary_df=iforest_df,
    )
    focus_df = build_combined_focus_years(summary_df)

    summary_path = out_dir / "combined_risk_summary.csv"
    focus_path = out_dir / "combined_risk_focus_years.csv"

    summary_df.to_csv(summary_path, index=False)
    focus_df.to_csv(focus_path, index=False)

    print(f"Saved: {summary_path}")
    print(f"Saved: {focus_path}")

    print("\nCombined risk summary:")
    print(summary_df.to_string(index=False))

    print("\nFocus years (at least one method triggered):")
    if focus_df.empty:
        print("No triggered years found.")
    else:
        print(focus_df.to_string(index=False))


if __name__ == "__main__":
    main()