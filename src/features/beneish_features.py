from __future__ import annotations

import numpy as np
import pandas as pd


BENEISH_INPUT_COLUMNS = [
    "dsri",
    "gmi",
    "aqi",
    "sgi",
    "depi",
    "sgai",
    "lvgi",
    "tata",
]


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    num = pd.to_numeric(numerator, errors="coerce")
    den = pd.to_numeric(denominator, errors="coerce")
    out = num / den
    out = out.replace([np.inf, -np.inf], np.nan)
    return out


def first_existing_numeric(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    out = pd.Series(np.nan, index=df.index, dtype="float64")

    for col in columns:
        if col in df.columns:
            candidate = pd.to_numeric(df[col], errors="coerce")
            out = out.combine_first(candidate)

    return out


def build_beneish_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out.sort_values("fiscal_year").reset_index(drop=True)

    numeric_cols = [
        "revenue",
        "gross_profit",
        "cogs",
        "net_income",
        "total_assets",
        "current_assets",
        "current_liabilities",
        "total_liabilities",
        "current_debt",
        "long_term_debt",
        "receivables",
        "ppe",
        "depreciation",
        "sga",
        "cfo",
    ]

    for col in numeric_cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    gross_profit = first_existing_numeric(out, ["gross_profit"])
    cogs = first_existing_numeric(out, ["cogs"])

    gross_profit_fallback_mask = gross_profit.isna() & out["revenue"].notna() & cogs.notna()
    gross_profit.loc[gross_profit_fallback_mask] = (
        out.loc[gross_profit_fallback_mask, "revenue"] - cogs.loc[gross_profit_fallback_mask]
    )

    cogs_fallback_mask = cogs.isna() & out["revenue"].notna() & gross_profit.notna()
    cogs.loc[cogs_fallback_mask] = (
        out.loc[cogs_fallback_mask, "revenue"] - gross_profit.loc[cogs_fallback_mask]
    )

    out["gross_profit_final"] = gross_profit
    out["cogs_final"] = cogs
    out["gross_profit_used_fallback"] = gross_profit_fallback_mask.fillna(False)
    out["cogs_used_fallback"] = cogs_fallback_mask.fillna(False)

    current_debt = first_existing_numeric(out, ["current_debt"])
    long_term_debt = first_existing_numeric(out, ["long_term_debt"])

    debt_piece_available = current_debt.notna() | long_term_debt.notna()
    total_debt = (current_debt.fillna(0) + long_term_debt.fillna(0)).where(debt_piece_available, np.nan)

    liabilities_proxy_mask = total_debt.isna() & out["total_liabilities"].notna()
    total_debt.loc[liabilities_proxy_mask] = out.loc[liabilities_proxy_mask, "total_liabilities"]

    out["total_debt_final"] = total_debt
    out["total_debt_used_liabilities_proxy"] = liabilities_proxy_mask.fillna(False)

    out["receivables_to_revenue_raw"] = safe_divide(out["receivables"], out["revenue"])
    out["gross_margin_raw"] = safe_divide(out["gross_profit_final"], out["revenue"])
    out["asset_quality_raw"] = 1 - safe_divide(out["current_assets"] + out["ppe"], out["total_assets"])
    out["depreciation_rate_raw"] = safe_divide(out["depreciation"], out["depreciation"] + out["ppe"])
    out["sga_to_revenue_raw"] = safe_divide(out["sga"], out["revenue"])
    out["debt_to_assets_raw"] = safe_divide(out["total_debt_final"], out["total_assets"])
    out["tata"] = safe_divide(out["net_income"] - out["cfo"], out["total_assets"])
    out["tata_uses_net_income_proxy"] = (
        out["net_income"].notna() & out["cfo"].notna() & out["total_assets"].notna()
    )

    out["dsri"] = safe_divide(
        out["receivables_to_revenue_raw"],
        out["receivables_to_revenue_raw"].shift(1),
    )

    out["gmi"] = safe_divide(
        out["gross_margin_raw"].shift(1),
        out["gross_margin_raw"],
    )

    out["aqi"] = safe_divide(
        out["asset_quality_raw"],
        out["asset_quality_raw"].shift(1),
    )

    out["sgi"] = safe_divide(
        out["revenue"],
        out["revenue"].shift(1),
    )

    out["depi"] = safe_divide(
        out["depreciation_rate_raw"].shift(1),
        out["depreciation_rate_raw"],
    )

    out["sgai"] = safe_divide(
        out["sga_to_revenue_raw"],
        out["sga_to_revenue_raw"].shift(1),
    )

    out["lvgi"] = safe_divide(
        out["debt_to_assets_raw"],
        out["debt_to_assets_raw"].shift(1),
    )

    out["beneish_input_count"] = out[BENEISH_INPUT_COLUMNS].notna().sum(axis=1)
    out["beneish_complete"] = out[BENEISH_INPUT_COLUMNS].notna().all(axis=1)

    out["beneish_mscore"] = np.nan
    complete_mask = out["beneish_complete"]

    out.loc[complete_mask, "beneish_mscore"] = (
        -4.84
        + 0.920 * out.loc[complete_mask, "dsri"]
        + 0.528 * out.loc[complete_mask, "gmi"]
        + 0.404 * out.loc[complete_mask, "aqi"]
        + 0.892 * out.loc[complete_mask, "sgi"]
        + 0.115 * out.loc[complete_mask, "depi"]
        - 0.172 * out.loc[complete_mask, "sgai"]
        + 4.679 * out.loc[complete_mask, "tata"]
        - 0.327 * out.loc[complete_mask, "lvgi"]
    )

    out["beneish_flag"] = False
    out.loc[complete_mask, "beneish_flag"] = out.loc[complete_mask, "beneish_mscore"] > -2.22

    out["beneish_label"] = "insufficient_data"
    out.loc[complete_mask & (~out["beneish_flag"]), "beneish_label"] = "no_flag"
    out.loc[complete_mask & out["beneish_flag"], "beneish_label"] = "flagged"

    return out


def build_beneish_summary(df: pd.DataFrame) -> pd.DataFrame:
    keep_cols = [
        "fiscal_year",
        "beneish_input_count",
        "beneish_complete",
        "beneish_mscore",
        "beneish_flag",
        "beneish_label",
        "gross_profit_used_fallback",
        "cogs_used_fallback",
        "total_debt_used_liabilities_proxy",
        "tata_uses_net_income_proxy",
    ]

    keep_cols = [c for c in keep_cols if c in df.columns]
    return df[keep_cols].copy()