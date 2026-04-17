from __future__ import annotations

import pandas as pd


def _triggered_methods(row: pd.Series) -> str:
    methods = []

    if bool(row.get("zscore_triggered", False)):
        methods.append("global_zscore")

    if bool(row.get("beneish_triggered", False)):
        methods.append("beneish")

    if bool(row.get("iforest_triggered", False)):
        methods.append("isolation_forest")

    return ", ".join(methods) if methods else ""


def _combined_risk_level(triggered_count: int) -> str:
    if triggered_count == 0:
        return "none"
    if triggered_count == 1:
        return "low"
    if triggered_count == 2:
        return "medium"
    return "high"


def build_combined_risk_summary(
    zscore_summary_df: pd.DataFrame,
    beneish_summary_df: pd.DataFrame,
    iforest_summary_df: pd.DataFrame,
) -> pd.DataFrame:
    z_df = zscore_summary_df.copy()
    z_df = z_df.rename(
        columns={
            "anomaly_count": "zscore_anomaly_count",
            "max_abs_zscore": "zscore_max_abs_zscore",
            "features_triggered": "zscore_features_triggered",
            "risk_level": "zscore_risk_level",
        }
    )

    z_df["zscore_available"] = True
    z_df["zscore_triggered"] = z_df["zscore_anomaly_count"].fillna(0).astype(int) > 0

    b_df = beneish_summary_df.copy()
    b_df = b_df.rename(
        columns={
            "beneish_complete": "beneish_available",
        }
    )

    b_df["beneish_available"] = b_df["beneish_available"].fillna(False)
    b_df["beneish_triggered"] = b_df["beneish_flag"].fillna(False)

    i_df = iforest_summary_df.copy()
    i_df["iforest_available"] = True
    i_df["iforest_triggered"] = i_df["if_flag"].fillna(False)

    keep_z = [
        "fiscal_year",
        "zscore_available",
        "zscore_triggered",
        "zscore_anomaly_count",
        "zscore_max_abs_zscore",
        "zscore_features_triggered",
        "zscore_risk_level",
    ]
    keep_b = [
        "fiscal_year",
        "beneish_available",
        "beneish_triggered",
        "beneish_input_count",
        "beneish_mscore",
        "beneish_flag",
        "beneish_label",
    ]
    keep_i = [
        "fiscal_year",
        "iforest_available",
        "iforest_triggered",
        "if_score_samples",
        "if_decision_function",
        "if_prediction",
        "if_flag",
        "if_label",
        "if_anomaly_strength_rank",
    ]

    z_df = z_df[[c for c in keep_z if c in z_df.columns]]
    b_df = b_df[[c for c in keep_b if c in b_df.columns]]
    i_df = i_df[[c for c in keep_i if c in i_df.columns]]

    out = z_df.merge(b_df, on="fiscal_year", how="outer")
    out = out.merge(i_df, on="fiscal_year", how="outer")
    out = out.sort_values("fiscal_year").reset_index(drop=True)

    bool_cols = [
        "zscore_available",
        "zscore_triggered",
        "beneish_available",
        "beneish_triggered",
        "iforest_available",
        "iforest_triggered",
    ]
    for col in bool_cols:
        if col in out.columns:
            out[col] = out[col].fillna(False)

    available_cols = ["zscore_available", "beneish_available", "iforest_available"]
    triggered_cols = ["zscore_triggered", "beneish_triggered", "iforest_triggered"]

    out["available_method_count"] = out[available_cols].sum(axis=1).astype(int)
    out["triggered_method_count"] = out[triggered_cols].sum(axis=1).astype(int)
    out["triggered_methods"] = out.apply(_triggered_methods, axis=1)
    out["triggered_methods"] = out["triggered_methods"].fillna("")
    out["triggered_methods"] = out["triggered_methods"].fillna("")

    out["coverage_note"] = "all_methods_available"
    out.loc[~out["beneish_available"], "coverage_note"] = "beneish_unavailable"

    out["combined_risk_level"] = out["triggered_method_count"].apply(_combined_risk_level)

    return out


def build_combined_focus_years(summary_df: pd.DataFrame) -> pd.DataFrame:
    out = summary_df[summary_df["triggered_method_count"] > 0].copy()
    out = out.sort_values(
        by=["triggered_method_count", "fiscal_year"],
        ascending=[False, True],
    ).reset_index(drop=True)
    return out