from __future__ import annotations

import argparse

import pandas as pd

from src.models.isolation_forest_analysis import (
    build_iforest_anomalies_long,
    build_iforest_feature_matrix,
    build_iforest_summary,
    build_iforest_yearly_output,
    run_isolation_forest,
)
from src.utils.config import PROCESSED_DATA_DIR


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Isolation Forest anomaly analysis on annual financial features"
    )
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. AAPL")
    parser.add_argument(
        "--contamination",
        default="0.15",
        help="Contamination value, e.g. 0.15 or auto",
    )
    parser.add_argument("--n-estimators", type=int, default=200, help="Number of trees")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    ticker = args.ticker.strip().lower()

    contamination_raw = str(args.contamination).strip().lower()
    contamination: float | str
    if contamination_raw == "auto":
        contamination = "auto"
    else:
        contamination = float(contamination_raw)

    in_path = PROCESSED_DATA_DIR / ticker / "annual_financials_enriched.csv"
    if not in_path.exists():
        raise FileNotFoundError(
            f"Missing file: {in_path}\n"
            f"Run this first:\n"
            f"python -m src.pipeline.run_annual_eda --ticker {ticker.upper()}"
        )

    df = pd.read_csv(in_path)
    df = df.sort_values("fiscal_year").reset_index(drop=True)

    X, selected_features, feature_report_df = build_iforest_feature_matrix(df)

    _, model_output_df = run_isolation_forest(
        X=X,
        contamination=contamination,
        n_estimators=int(args.n_estimators),
        random_state=int(args.random_state),
    )

    scored_df = build_iforest_yearly_output(df, model_output_df)
    anomalies_df = build_iforest_anomalies_long(scored_df, selected_features)
    summary_df = build_iforest_summary(scored_df)

    out_dir = PROCESSED_DATA_DIR / ticker
    feature_report_path = out_dir / "iforest_feature_report.csv"
    matrix_path = out_dir / "iforest_feature_matrix.csv"
    scored_path = out_dir / "annual_financials_iforest.csv"
    anomalies_path = out_dir / "iforest_anomalies_long.csv"
    summary_path = out_dir / "iforest_summary.csv"

    feature_report_df.to_csv(feature_report_path, index=False)
    X.to_csv(matrix_path, index=False)
    scored_df.to_csv(scored_path, index=False)
    anomalies_df.to_csv(anomalies_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    print(f"Saved: {feature_report_path}")
    print(f"Saved: {matrix_path}")
    print(f"Saved: {scored_path}")
    print(f"Saved: {anomalies_path}")
    print(f"Saved: {summary_path}")

    print("\nIsolation Forest feature report:")
    print(feature_report_df.to_string(index=False))

    print("\nIsolation Forest anomalies:")
    if anomalies_df.empty:
        print("No outliers found with the selected contamination setting.")
    else:
        print(anomalies_df.to_string(index=False))

    print("\nIsolation Forest year-wise summary:")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()