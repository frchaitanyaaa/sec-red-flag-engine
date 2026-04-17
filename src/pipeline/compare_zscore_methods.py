from __future__ import annotations

import argparse

import pandas as pd

from src.utils.config import PROCESSED_DATA_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare global vs rolling Z-score outputs")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. AAPL")
    args = parser.parse_args()

    ticker = args.ticker.strip().lower()
    out_dir = PROCESSED_DATA_DIR / ticker

    global_summary_path = out_dir / "zscore_yearly_summary.csv"
    rolling_summary_path = out_dir / "rolling_zscore_yearly_summary.csv"

    if not global_summary_path.exists():
        raise FileNotFoundError(
            f"Missing file: {global_summary_path}\n"
            f"Run:\n"
            f"python -m src.pipeline.run_zscore_analysis --ticker {ticker.upper()}"
        )

    if not rolling_summary_path.exists():
        raise FileNotFoundError(
            f"Missing file: {rolling_summary_path}\n"
            f"Run:\n"
            f"python -m src.pipeline.run_rolling_zscore_analysis --ticker {ticker.upper()}"
        )

    global_df = pd.read_csv(global_summary_path).rename(
        columns={
            "anomaly_count": "global_anomaly_count",
            "max_abs_zscore": "global_max_abs_zscore",
            "features_triggered": "global_features_triggered",
            "risk_level": "global_risk_level",
        }
    )

    rolling_df = pd.read_csv(rolling_summary_path).rename(
        columns={
            "anomaly_count": "rolling_anomaly_count",
            "max_abs_zscore": "rolling_max_abs_zscore",
            "features_triggered": "rolling_features_triggered",
            "risk_level": "rolling_risk_level",
        }
    )

    comparison_df = global_df.merge(rolling_df, on="fiscal_year", how="outer")
    comparison_df = comparison_df.sort_values("fiscal_year").reset_index(drop=True)

    comparison_df["risk_changed"] = (
        comparison_df["global_risk_level"].fillna("") != comparison_df["rolling_risk_level"].fillna("")
    )

    comparison_path = out_dir / "zscore_method_comparison.csv"
    comparison_df.to_csv(comparison_path, index=False)

    print(f"Saved: {comparison_path}")

    print("\nMethod comparison:")
    print(comparison_df.to_string(index=False))

    changed_df = comparison_df[comparison_df["risk_changed"]].copy()
    print("\nYears where risk label changed between methods:")
    if changed_df.empty:
        print("None")
    else:
        print(changed_df.to_string(index=False))


if __name__ == "__main__":
    main()



# do not use this code , it was a experiment to understand the context of the files. The above code is the actual code for compare_zscore_methods.py, which compares the outputs of global vs rolling Z-score analyses and identifies any differences in risk levels assigned to each fiscal year. The below code snippets are from related files that perform the Z-score analyses and generate the yearly summaries that this comparison relies on.   