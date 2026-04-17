from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.preprocessing.companyfacts_to_annuals import (
    build_annual_financials_wide,
    extract_annual_metric_rows,
)
from src.utils.config import PROCESSED_DATA_DIR, RAW_DATA_DIR


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build clean annual financial tables from SEC companyfacts.json"
    )
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. AAPL")
    args = parser.parse_args()

    ticker = args.ticker.strip().lower()

    companyfacts_path = RAW_DATA_DIR / ticker / "companyfacts.json"
    if not companyfacts_path.exists():
        raise FileNotFoundError(
            f"Missing file: {companyfacts_path}\n"
            f"Run fetch first:\n"
            f"python -m src.pipeline.fetch_company_data --ticker {ticker.upper()}"
        )

    companyfacts = load_json(companyfacts_path)

    long_df = extract_annual_metric_rows(companyfacts)
    if long_df.empty:
        raise RuntimeError("No annual financial facts were extracted from companyfacts.json")

    wide_df = build_annual_financials_wide(companyfacts, long_df)

    out_dir = PROCESSED_DATA_DIR / ticker
    out_dir.mkdir(parents=True, exist_ok=True)

    long_path = out_dir / "annual_facts_long.csv"
    wide_path = out_dir / "annual_financials.csv"

    long_df.to_csv(long_path, index=False)
    wide_df.to_csv(wide_path, index=False)

    print(f"Saved: {long_path}")
    print(f"Saved: {wide_path}")

    print("\nAnnual facts preview:")
    print(long_df.head(20).to_string(index=False))

    print("\nAnnual financials preview:")
    print(wide_df.to_string(index=False))

    print("\nCoverage by metric:")
    coverage = long_df.groupby("metric")["fy"].nunique().sort_values(ascending=False)
    print(coverage.to_string())


if __name__ == "__main__":
    main()