# from __future__ import annotations

# import argparse

# import pandas as pd

# from src.models.rolling_zscore_analysis import (
#     add_rolling_zscore_columns,
#     build_rolling_zscore_anomalies_long,
# )
# from src.models.zscore_analysis import (
#     choose_zscore_features,
#     build_zscore_yearly_summary,
# )
# from src.utils.config import PROCESSED_DATA_DIR


# def main() -> None:
#     parser = argparse.ArgumentParser(
#         description="Run rolling 5-year Z-score anomaly analysis on annual financial features"
#     )
#     parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. AAPL")
#     parser.add_argument("--threshold", type=float, default=2.0, help="Absolute z-score threshold")
#     parser.add_argument("--window", type=int, default=5, help="Rolling history window")
#     parser.add_argument("--min-history", type=int, default=4, help="Minimum prior valid points required")
#     args = parser.parse_args()

#     ticker = args.ticker.strip().lower()
#     threshold = float(args.threshold)
#     window = int(args.window)
#     min_history = int(args.min_history)

#     in_path = PROCESSED_DATA_DIR / ticker / "annual_financials_enriched.csv"
#     if not in_path.exists():
#         raise FileNotFoundError(
#             f"Missing file: {in_path}\n"
#             f"Run this first:\n"
#             f"python -m src.pipeline.run_annual_eda --ticker {ticker.upper()}"
#         )

#     df = pd.read_csv(in_path)
#     df = df.sort_values("fiscal_year").reset_index(drop=True)

#     selected_features, feature_report_df = choose_zscore_features(df)

#     scored_df = add_rolling_zscore_columns(
#         df=df,
#         features=selected_features,
#         threshold=threshold,
#         window=window,
#         min_history=min_history,
#     )

#     anomalies_df = build_rolling_zscore_anomalies_long(
#         scored_df=scored_df,
#         features=selected_features,
#         threshold=threshold,
#     )

#     yearly_summary_df = build_zscore_yearly_summary(
#         anomalies_df=anomalies_df,
#         fiscal_years=df["fiscal_year"].tolist(),
#     )

#     out_dir = PROCESSED_DATA_DIR / ticker
#     feature_report_path = out_dir / "rolling_zscore_feature_selection.csv"
#     scored_path = out_dir / "annual_financials_rolling_zscores.csv"
#     anomalies_path = out_dir / "rolling_zscore_anomalies_long.csv"
#     summary_path = out_dir / "rolling_zscore_yearly_summary.csv"

#     feature_report_df.to_csv(feature_report_path, index=False)
#     scored_df.to_csv(scored_path, index=False)
#     anomalies_df.to_csv(anomalies_path, index=False)
#     yearly_summary_df.to_csv(summary_path, index=False)

#     print(f"Saved: {feature_report_path}")
#     print(f"Saved: {scored_path}")
#     print(f"Saved: {anomalies_path}")
#     print(f"Saved: {summary_path}")

#     print("\nSelected features for rolling Z-score:")
#     print(feature_report_df[feature_report_df["selected"]].to_string(index=False))

#     print("\nTop rolling Z-score anomalies:")
#     if anomalies_df.empty:
#         print("No anomalies found at the selected threshold.")
#     else:
#         print(anomalies_df.head(25).to_string(index=False))

#     print("\nYear-wise rolling Z-score summary:")
#     print(yearly_summary_df.to_string(index=False))


# if __name__ == "__main__":
#     main()