# from __future__ import annotations

# import numpy as np
# import pandas as pd

# from src.models.zscore_analysis import (
#     DEFAULT_ZSCORE_FEATURES,
#     build_zscore_yearly_summary,
#     choose_zscore_features,
# )


# def rolling_zscore_series(
#     series: pd.Series,
#     window: int = 5,
#     min_history: int = 4,
# ) -> pd.Series:
#     """
#     Compute rolling z-scores using only PREVIOUS observations.

#     Example with window=5:
#     - score for 2015 uses 2010-2014
#     - current year is never included in its own baseline

#     If there is not enough prior history, return NaN for that point.
#     """
#     s = pd.to_numeric(series, errors="coerce")
#     out = pd.Series(np.nan, index=s.index, dtype="float64")

#     for i in range(len(s)):
#         current_value = s.iloc[i]
#         if pd.isna(current_value):
#             continue

#         start = max(0, i - window)
#         history = s.iloc[start:i].dropna()

#         if len(history) < min_history:
#             continue

#         mean = history.mean()
#         std = history.std(ddof=0)

#         if pd.isna(std) or std == 0:
#             continue

#         out.iloc[i] = (current_value - mean) / std

#     return out


# def add_rolling_zscore_columns(
#     df: pd.DataFrame,
#     features: list[str],
#     threshold: float = 2.0,
#     window: int = 5,
#     min_history: int = 4,
# ) -> pd.DataFrame:
#     out = df.copy()
#     out = out.sort_values("fiscal_year").reset_index(drop=True)

#     for feature in features:
#         z_col = f"{feature}_rolling_zscore"
#         flag_col = f"{feature}_rolling_zflag"

#         out[z_col] = rolling_zscore_series(
#             out[feature],
#             window=window,
#             min_history=min_history,
#         )
#         out[flag_col] = out[z_col].abs() >= threshold
#         out[flag_col] = out[flag_col].fillna(False)

#     return out


# def build_rolling_zscore_anomalies_long(
#     scored_df: pd.DataFrame,
#     features: list[str],
#     threshold: float = 2.0,
# ) -> pd.DataFrame:
#     rows = []

#     for _, row in scored_df.iterrows():
#         fiscal_year = row["fiscal_year"]

#         for feature in features:
#             z_col = f"{feature}_rolling_zscore"
#             z_value = row.get(z_col, np.nan)
#             raw_value = row.get(feature, np.nan)

#             if pd.notna(z_value) and abs(float(z_value)) >= threshold:
#                 rows.append(
#                     {
#                         "fiscal_year": fiscal_year,
#                         "feature": feature,
#                         "value": raw_value,
#                         "zscore": float(z_value),
#                         "abs_zscore": abs(float(z_value)),
#                         "method": "rolling_5y",
#                     }
#                 )

#     if not rows:
#         return pd.DataFrame(
#             columns=["fiscal_year", "feature", "value", "zscore", "abs_zscore", "method"]
#         )

#     out = pd.DataFrame(rows)
#     out = out.sort_values(
#         by=["abs_zscore", "fiscal_year", "feature"],
#         ascending=[False, True, True],
#     ).reset_index(drop=True)

#     return out

# # do not use this code , it was a experiment to understand the context of the files. The above code is the actual code for compare_zscore_methods.py, which compares the outputs of global vs rolling Z-score analyses and identifies any differences in risk levels assigned to each fiscal year. The below code snippets are from related files that perform the Z-score analyses and generate the yearly summaries that this comparison relies on.   