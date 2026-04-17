from __future__ import annotations

import numpy as np
import pandas as pd


DEFAULT_ZSCORE_FEATURES = [
    "revenue_yoy",
    "net_income_yoy",
    "current_assets_yoy",
    "current_liabilities_yoy",
    "total_assets_yoy",
    "total_liabilities_yoy",
    "receivables_yoy",
    "ppe_yoy",
    "depreciation_yoy",
    "sga_yoy",
    "cfo_yoy",
    "current_ratio",
    "liabilities_to_assets",
    "cfo_to_net_income",
    "receivables_to_revenue",
    "sga_to_revenue",
    "asset_turnover",
    "net_margin",
    "cfo_to_revenue",
]


def choose_zscore_features(
    df: pd.DataFrame,
    candidate_features: list[str] | None = None,
    max_missing_pct: float = 20.0,
    min_non_null: int = 5,
) -> tuple[list[str], pd.DataFrame]:
    if candidate_features is None:
        candidate_features = DEFAULT_ZSCORE_FEATURES

    rows = []
    selected_features: list[str] = []

    for feature in candidate_features:
        if feature not in df.columns:
            rows.append(
                {
                    "feature": feature,
                    "exists": False,
                    "non_null_count": 0,
                    "missing_pct": 100.0,
                    "std": np.nan,
                    "selected": False,
                    "exclusion_reason": "missing_column",
                }
            )
            continue

        s = pd.to_numeric(df[feature], errors="coerce")
        non_null_count = int(s.notna().sum())
        missing_pct = round(float(s.isna().mean() * 100), 2)

        std = s.std(ddof=0)
        if pd.isna(std):
            std_value = np.nan
        else:
            std_value = float(std)

        has_variation = bool(non_null_count >= 2 and pd.notna(std) and std != 0)

        exclusion_reason = ""
        selected = True

        if non_null_count < min_non_null:
            selected = False
            exclusion_reason = "too_few_values"
        elif missing_pct > max_missing_pct:
            selected = False
            exclusion_reason = "missingness_too_high"
        elif not has_variation:
            selected = False
            exclusion_reason = "no_variation"

        if selected:
            selected_features.append(feature)

        rows.append(
            {
                "feature": feature,
                "exists": True,
                "non_null_count": non_null_count,
                "missing_pct": missing_pct,
                "std": std_value,
                "selected": selected,
                "exclusion_reason": exclusion_reason,
            }
        )

    report_df = pd.DataFrame(rows).sort_values(
        by=["selected", "feature"], ascending=[False, True]
    ).reset_index(drop=True)

    return selected_features, report_df


def add_zscore_columns(
    df: pd.DataFrame,
    features: list[str],
    threshold: float = 2.0,
) -> pd.DataFrame:
    out = df.copy()

    for feature in features:
        z_col = f"{feature}_zscore"
        flag_col = f"{feature}_zflag"

        s = pd.to_numeric(out[feature], errors="coerce")
        mean = s.mean()
        std = s.std(ddof=0)

        out[z_col] = np.nan
        out[flag_col] = False

        if pd.isna(std) or std == 0:
            continue

        out[z_col] = (s - mean) / std
        out[flag_col] = out[z_col].abs() >= threshold

    return out


def build_zscore_anomalies_long(
    scored_df: pd.DataFrame,
    features: list[str],
    threshold: float = 2.0,
) -> pd.DataFrame:
    rows = []

    for _, row in scored_df.iterrows():
        fiscal_year = row["fiscal_year"]

        for feature in features:
            z_col = f"{feature}_zscore"
            z_value = row.get(z_col, np.nan)
            raw_value = row.get(feature, np.nan)

            if pd.notna(z_value) and abs(float(z_value)) >= threshold:
                rows.append(
                    {
                        "fiscal_year": fiscal_year,
                        "feature": feature,
                        "value": raw_value,
                        "zscore": float(z_value),
                        "abs_zscore": abs(float(z_value)),
                    }
                )

    if not rows:
        return pd.DataFrame(
            columns=["fiscal_year", "feature", "value", "zscore", "abs_zscore"]
        )

    out = pd.DataFrame(rows)
    out = out.sort_values(
        by=["abs_zscore", "fiscal_year", "feature"],
        ascending=[False, True, True],
    ).reset_index(drop=True)

    return out


def _risk_level(anomaly_count: int, max_abs_zscore: float | None) -> str:
    if anomaly_count == 0:
        return "none"
    if max_abs_zscore is not None and not pd.isna(max_abs_zscore) and max_abs_zscore >= 3:
        return "high"
    if anomaly_count >= 3:
        return "high"
    if anomaly_count == 2:
        return "medium"
    return "low"


def build_zscore_yearly_summary(
    anomalies_df: pd.DataFrame,
    fiscal_years: list[int],
) -> pd.DataFrame:
    base = pd.DataFrame({"fiscal_year": fiscal_years}).drop_duplicates().sort_values("fiscal_year")

    if anomalies_df.empty:
        base["anomaly_count"] = 0
        base["max_abs_zscore"] = np.nan
        base["features_triggered"] = ""
        base["risk_level"] = "none"
        return base.reset_index(drop=True)

    grouped = (
        anomalies_df.groupby("fiscal_year")
        .agg(
            anomaly_count=("feature", "count"),
            max_abs_zscore=("abs_zscore", "max"),
            features_triggered=("feature", lambda s: ", ".join(sorted(set(s)))),
        )
        .reset_index()
    )

    out = base.merge(grouped, on="fiscal_year", how="left")
    out["anomaly_count"] = out["anomaly_count"].fillna(0).astype(int)
    out["features_triggered"] = out["features_triggered"].fillna("")

    out["risk_level"] = out.apply(
        lambda row: _risk_level(
            anomaly_count=int(row["anomaly_count"]),
            max_abs_zscore=row["max_abs_zscore"],
        ),
        axis=1,
    )

    return out.reset_index(drop=True)