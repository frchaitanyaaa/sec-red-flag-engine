from __future__ import annotations

import numpy as np
import pandas as pd


GROWTH_COLUMNS = [
    "revenue",
    "net_income",
    "total_assets",
    "current_assets",
    "current_liabilities",
    "total_liabilities",
    "receivables",
    "ppe",
    "depreciation",
    "sga",
    "cfo",
]


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    num = pd.to_numeric(numerator, errors="coerce")
    den = pd.to_numeric(denominator, errors="coerce")
    out = num / den
    out = out.replace([np.inf, -np.inf], np.nan)
    return out


def add_growth_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out.sort_values("fiscal_year").reset_index(drop=True)

    for col in GROWTH_COLUMNS:
        if col in out.columns:
            out[f"{col}_yoy"] = out[col].pct_change()

    return out


def add_ratio_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if {"current_assets", "current_liabilities"}.issubset(out.columns):
        out["current_ratio"] = safe_divide(out["current_assets"], out["current_liabilities"])

    if {"total_liabilities", "total_assets"}.issubset(out.columns):
        out["liabilities_to_assets"] = safe_divide(out["total_liabilities"], out["total_assets"])

    if {"cfo", "net_income"}.issubset(out.columns):
        out["cfo_to_net_income"] = safe_divide(out["cfo"], out["net_income"])

    if {"receivables", "revenue"}.issubset(out.columns):
        out["receivables_to_revenue"] = safe_divide(out["receivables"], out["revenue"])

    if {"sga", "revenue"}.issubset(out.columns):
        out["sga_to_revenue"] = safe_divide(out["sga"], out["revenue"])

    if {"revenue", "total_assets"}.issubset(out.columns):
        out["asset_turnover"] = safe_divide(out["revenue"], out["total_assets"])

    if {"net_income", "revenue"}.issubset(out.columns):
        out["net_margin"] = safe_divide(out["net_income"], out["revenue"])

    if {"cfo", "revenue"}.issubset(out.columns):
        out["cfo_to_revenue"] = safe_divide(out["cfo"], out["revenue"])

    return out


def build_missingness_report(df: pd.DataFrame) -> pd.DataFrame:
    report = pd.DataFrame(
        {
            "column": df.columns,
            "missing_count": df.isna().sum().values,
            "missing_pct": (df.isna().mean().values * 100).round(2),
        }
    )
    return report.sort_values(["missing_count", "column"], ascending=[False, True]).reset_index(drop=True)


def build_summary_stats(df: pd.DataFrame) -> pd.DataFrame:
    numeric_df = df.select_dtypes(include=["number"]).copy()
    if numeric_df.empty:
        return pd.DataFrame()

    summary = numeric_df.describe().T.reset_index().rename(columns={"index": "column"})
    return summary


def build_anomaly_hints(df: pd.DataFrame, yoy_threshold: float = 0.25) -> pd.DataFrame:
    rows = []

    yoy_cols = [c for c in df.columns if c.endswith("_yoy")]

    for _, row in df.iterrows():
        year = row["fiscal_year"]

        for col in yoy_cols:
            value = row[col]
            if pd.notna(value) and abs(value) >= yoy_threshold:
                rows.append(
                    {
                        "fiscal_year": year,
                        "feature": col,
                        "value": value,
                        "abs_value": abs(value),
                    }
                )

    if not rows:
        return pd.DataFrame(columns=["fiscal_year", "feature", "value", "abs_value"])

    out = pd.DataFrame(rows)
    out = out.sort_values(["abs_value", "fiscal_year"], ascending=[False, True]).reset_index(drop=True)
    return out