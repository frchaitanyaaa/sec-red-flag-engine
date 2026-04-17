from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.features.annual_features import (
    add_growth_features,
    add_ratio_features,
    build_anomaly_hints,
    build_missingness_report,
    build_summary_stats,
)
from src.utils.config import PROCESSED_DATA_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EDA on annual financials")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. AAPL")
    args = parser.parse_args()

    ticker = args.ticker.strip().lower()
    in_path = PROCESSED_DATA_DIR / ticker / "annual_financials.csv"

    if not in_path.exists():
        raise FileNotFoundError(
            f"Missing file: {in_path}\n"
            f"Run this first:\n"
            f"python -m src.pipeline.build_annual_financials --ticker {ticker.upper()}"
        )

    df = pd.read_csv(in_path)
    df = df.sort_values("fiscal_year").reset_index(drop=True)

    enriched_df = add_growth_features(df)
    enriched_df = add_ratio_features(enriched_df)

    missingness_df = build_missingness_report(enriched_df)
    summary_df = build_summary_stats(enriched_df)
    anomaly_hints_df = build_anomaly_hints(enriched_df, yoy_threshold=0.25)

    out_dir = PROCESSED_DATA_DIR / ticker
    enriched_path = out_dir / "annual_financials_enriched.csv"
    missingness_path = out_dir / "annual_missingness_report.csv"
    summary_path = out_dir / "annual_summary_stats.csv"
    hints_path = out_dir / "annual_anomaly_hints.csv"

    enriched_df.to_csv(enriched_path, index=False)
    missingness_df.to_csv(missingness_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    anomaly_hints_df.to_csv(hints_path, index=False)

    print(f"Saved: {enriched_path}")
    print(f"Saved: {missingness_path}")
    print(f"Saved: {summary_path}")
    print(f"Saved: {hints_path}")

    print("\nMissingness report:")
    print(missingness_df.to_string(index=False))

    print("\nTop anomaly hints (|YoY| >= 25%):")
    if anomaly_hints_df.empty:
        print("No anomaly hints found with the current threshold.")
    else:
        print(anomaly_hints_df.head(25).to_string(index=False))

    preview_cols = [
        "fiscal_year",
        "revenue",
        "revenue_yoy",
        "net_income",
        "net_income_yoy",
        "receivables",
        "receivables_yoy",
        "current_ratio",
        "liabilities_to_assets",
        "cfo_to_net_income",
        "net_margin",
    ]
    preview_cols = [c for c in preview_cols if c in enriched_df.columns]

    print("\nEnriched annual preview:")
    print(enriched_df[preview_cols].to_string(index=False))


if __name__ == "__main__":
    main()



#for understanding the context of this file, see the related files below:
#Interpretation: In 2013, the company's depreciation expense was roughly 106% of what it was in 2012 (a 6% increase). This is a relatively stable metric compared to some of the lower values in your list
#i have added absolue values of yoy changes to the anomaly hints to help identify large changes in magnitude regardless of direction. You can adjust the threshold as needed to find more or fewer hints.