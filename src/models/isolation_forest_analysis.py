from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from src.models.zscore_analysis import choose_zscore_features


def build_iforest_feature_matrix(
    df: pd.DataFrame,
    candidate_features: list[str] | None = None,
    max_missing_pct: float = 20.0,
    min_non_null: int = 5,
) -> tuple[pd.DataFrame, list[str], pd.DataFrame]:
    """
    Select features, median-impute missing values, and return the model matrix.
    """
    selected_features, selection_report_df = choose_zscore_features(
        df=df,
        candidate_features=candidate_features,
        max_missing_pct=max_missing_pct,
        min_non_null=min_non_null,
    )

    if not selected_features:
        raise RuntimeError("No usable features selected for Isolation Forest.")

    X = df[selected_features].copy()

    prep_rows = []
    for col in selected_features:
        s = pd.to_numeric(X[col], errors="coerce")
        missing_before = int(s.isna().sum())
        median_value = float(s.median()) if s.notna().any() else np.nan

        X[col] = s.fillna(median_value)
        missing_after = int(X[col].isna().sum())

        prep_rows.append(
            {
                "feature": col,
                "missing_before": missing_before,
                "missing_after": missing_after,
                "median_used_for_imputation": median_value,
            }
        )

    prep_report_df = pd.DataFrame(prep_rows).sort_values("feature").reset_index(drop=True)
    return X, selected_features, pd.merge(
        selection_report_df,
        prep_report_df,
        on="feature",
        how="left",
    )


def run_isolation_forest(
    X: pd.DataFrame,
    contamination: float | str = 0.15,
    n_estimators: int = 200,
    random_state: int = 42,
) -> tuple[IsolationForest, pd.DataFrame]:
    """
    Fit Isolation Forest and return scores/predictions.
    """
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        max_samples="auto",
        random_state=random_state,
        n_jobs=-1,
    )

    model.fit(X)

    result_df = pd.DataFrame(index=X.index)
    result_df["if_score_samples"] = model.score_samples(X)
    result_df["if_decision_function"] = model.decision_function(X)
    result_df["if_prediction"] = model.predict(X)
    result_df["if_flag"] = result_df["if_prediction"] == -1

    return model, result_df


def build_iforest_yearly_output(
    base_df: pd.DataFrame,
    model_output_df: pd.DataFrame,
) -> pd.DataFrame:
    out = base_df.copy().reset_index(drop=True)
    out = pd.concat([out, model_output_df.reset_index(drop=True)], axis=1)

    out["if_label"] = np.where(out["if_flag"], "outlier", "inlier")

    # More negative decision_function = more anomalous.
    out["if_anomaly_strength_rank"] = (
        out["if_decision_function"]
        .rank(method="dense", ascending=True)
        .astype("Int64")
    )

    return out


def build_iforest_anomalies_long(
    scored_df: pd.DataFrame,
    feature_columns: list[str],
) -> pd.DataFrame:
    anomaly_df = scored_df[scored_df["if_flag"]].copy()

    if anomaly_df.empty:
        return pd.DataFrame(
            columns=[
                "fiscal_year",
                "if_score_samples",
                "if_decision_function",
                "if_prediction",
                "if_label",
                "if_anomaly_strength_rank",
                "feature_snapshot",
            ]
        )

    def snapshot(row: pd.Series) -> str:
        pieces = []
        for col in feature_columns:
            value = row.get(col, np.nan)
            if pd.notna(value):
                pieces.append(f"{col}={value:.6g}")
        return "; ".join(pieces)

    anomaly_df["feature_snapshot"] = anomaly_df.apply(snapshot, axis=1)

    keep_cols = [
        "fiscal_year",
        "if_score_samples",
        "if_decision_function",
        "if_prediction",
        "if_label",
        "if_anomaly_strength_rank",
        "feature_snapshot",
    ]
    keep_cols = [c for c in keep_cols if c in anomaly_df.columns]

    return anomaly_df[keep_cols].sort_values(
        by=["if_decision_function", "fiscal_year"],
        ascending=[True, True],
    ).reset_index(drop=True)


def build_iforest_summary(scored_df: pd.DataFrame) -> pd.DataFrame:
    keep_cols = [
        "fiscal_year",
        "if_score_samples",
        "if_decision_function",
        "if_prediction",
        "if_flag",
        "if_label",
        "if_anomaly_strength_rank",
    ]
    keep_cols = [c for c in keep_cols if c in scored_df.columns]

    out = scored_df[keep_cols].copy()
    out = out.sort_values("fiscal_year").reset_index(drop=True)
    return out