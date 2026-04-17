from __future__ import annotations

import argparse

import pandas as pd

from src.features.beneish_features import build_beneish_features, build_beneish_summary
from src.utils.config import PROCESSED_DATA_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Beneish M-score analysis on annual financials")
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

    beneish_df = build_beneish_features(df)
    summary_df = build_beneish_summary(beneish_df)

    out_dir = PROCESSED_DATA_DIR / ticker
    features_path = out_dir / "annual_beneish_features.csv"
    summary_path = out_dir / "beneish_summary.csv"

    beneish_df.to_csv(features_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    print(f"Saved: {features_path}")
    print(f"Saved: {summary_path}")

    print("\nBeneish summary:")
    print(summary_df.to_string(index=False))

    preview_cols = [
        "fiscal_year",
        "dsri",
        "gmi",
        "aqi",
        "sgi",
        "depi",
        "sgai",
        "lvgi",
        "tata",
        "beneish_input_count",
        "beneish_complete",
        "beneish_mscore",
        "beneish_flag",
        "beneish_label",
    ]
    preview_cols = [c for c in preview_cols if c in beneish_df.columns]

    print("\nBeneish feature preview:")
    print(beneish_df[preview_cols].to_string(index=False))


if __name__ == "__main__":
    main()