from __future__ import annotations

from typing import Any

import pandas as pd


ANNUAL_FORMS = {"10-K", "10-K/A"}

METRIC_CONFIG = {
    "revenue": {
        "kind": "duration",
        "tags": [
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet",
            "Revenues",
        ],
    },
    "gross_profit": {
        "kind": "duration",
        "tags": [
            "GrossProfit",
        ],
    },
    "cogs": {
        "kind": "duration",
        "tags": [
            "CostOfGoodsSold",
            "CostOfSales",
            "CostOfRevenue",
            "CostOfGoodsAndServicesSold",
        ],
    },
    "net_income": {
        "kind": "duration",
        "tags": [
            "NetIncomeLoss",
        ],
    },
    "total_assets": {
        "kind": "instant",
        "tags": [
            "Assets",
        ],
    },
    "current_assets": {
        "kind": "instant",
        "tags": [
            "AssetsCurrent",
        ],
    },
    "current_liabilities": {
        "kind": "instant",
        "tags": [
            "LiabilitiesCurrent",
        ],
    },
    "total_liabilities": {
        "kind": "instant",
        "tags": [
            "Liabilities",
        ],
    },
    "current_debt": {
        "kind": "instant",
        "tags": [
            "ShortTermBorrowings",
            "ShortTermDebt",
            "LongTermDebtCurrent",
            "LongTermDebtMaturitiesCurrent",
        ],
    },
    "long_term_debt": {
        "kind": "instant",
        "tags": [
            "LongTermDebtNoncurrent",
            "LongTermDebtAndCapitalLeaseObligations",
            "LongTermDebt",
        ],
    },
    "receivables": {
        "kind": "instant",
        "tags": [
            "AccountsReceivableNetCurrent",
            "ReceivablesNetCurrent",
        ],
    },
    "ppe": {
        "kind": "instant",
        "tags": [
            "PropertyPlantAndEquipmentNet",
        ],
    },
    "depreciation": {
        "kind": "duration",
        "tags": [
            "Depreciation",
            "DepreciationDepletionAndAmortization",
            "DepreciationAmortizationAndAccretionNet",
        ],
    },
    "sga": {
        "kind": "duration",
        "tags": [
            "SellingGeneralAndAdministrativeExpense",
        ],
    },
    "cfo": {
        "kind": "duration",
        "tags": [
            "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
        ],
    },
}


def _pick_usd_unit(concept: dict[str, Any]) -> tuple[str, list[dict[str, Any]]] | None:
    units = concept.get("units", {})

    if "USD" in units:
        return "USD", units["USD"]

    for unit_name, rows in units.items():
        if "USD" in unit_name.upper():
            return unit_name, rows

    return None


def _normalize_fact_rows(
    rows: list[dict[str, Any]],
    metric: str,
    source_tag: str,
    tag_rank: int,
    kind: str,
) -> pd.DataFrame:
    df = pd.DataFrame(rows)

    if df.empty:
        return df

    expected_cols = ["val", "fy", "fp", "form", "filed", "frame", "accn", "end", "start"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = pd.NA

    df = df.copy()
    df["metric"] = metric
    df["source_tag"] = source_tag
    df["tag_rank"] = tag_rank
    df["kind"] = kind

    df["form"] = df["form"].astype("string")
    df["fp"] = df["fp"].astype("string")
    df["filed"] = pd.to_datetime(df["filed"], errors="coerce")
    df["end"] = pd.to_datetime(df["end"], errors="coerce")
    df["start"] = pd.to_datetime(df["start"], errors="coerce")
    df["val"] = pd.to_numeric(df["val"], errors="coerce")
    df["fy"] = pd.to_numeric(df["fy"], errors="coerce")

    df = df[df["val"].notna()].copy()
    df = df[df["form"].isin(ANNUAL_FORMS)].copy()
    df = df[df["fp"].isna() | (df["fp"] == "FY")].copy()

    missing_fy_mask = df["fy"].isna() & df["end"].notna()
    df.loc[missing_fy_mask, "fy"] = df.loc[missing_fy_mask, "end"].dt.year

    df = df[df["fy"].notna()].copy()
    df["fy"] = df["fy"].astype(int)

    df["duration_days"] = pd.NA
    duration_mask = df["start"].notna() & df["end"].notna()
    df.loc[duration_mask, "duration_days"] = (
        df.loc[duration_mask, "end"] - df.loc[duration_mask, "start"]
    ).dt.days

    if kind == "duration":
        df = df[
            df["duration_days"].isna()
            | df["duration_days"].between(300, 380)
        ].copy()

    keep_cols = [
        "metric",
        "source_tag",
        "tag_rank",
        "kind",
        "fy",
        "val",
        "form",
        "fp",
        "filed",
        "end",
        "start",
        "duration_days",
        "frame",
        "accn",
    ]

    return df[keep_cols].copy()


def extract_annual_metric_rows(companyfacts: dict[str, Any]) -> pd.DataFrame:
    us_gaap = companyfacts.get("facts", {}).get("us-gaap", {})
    collected: list[pd.DataFrame] = []

    for metric, cfg in METRIC_CONFIG.items():
        metric_parts: list[pd.DataFrame] = []

        for tag_rank, tag in enumerate(cfg["tags"], start=1):
            concept = us_gaap.get(tag)
            if not concept:
                continue

            picked = _pick_usd_unit(concept)
            if not picked:
                continue

            _, rows = picked
            normalized = _normalize_fact_rows(
                rows=rows,
                metric=metric,
                source_tag=tag,
                tag_rank=tag_rank,
                kind=cfg["kind"],
            )

            if not normalized.empty:
                metric_parts.append(normalized)

        if not metric_parts:
            continue

        metric_df = pd.concat(metric_parts, ignore_index=True)

        metric_df = metric_df.sort_values(
            by=["fy", "tag_rank", "filed", "end"],
            ascending=[True, True, False, False],
        )

        metric_best = metric_df.drop_duplicates(subset=["fy"], keep="first").copy()
        collected.append(metric_best)

    if not collected:
        return pd.DataFrame()

    long_df = pd.concat(collected, ignore_index=True)
    long_df = long_df.sort_values(by=["fy", "metric"]).reset_index(drop=True)

    return long_df


def build_annual_financials_wide(
    companyfacts: dict[str, Any],
    long_df: pd.DataFrame,
) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame()

    wide_df = (
        long_df.pivot(index="fy", columns="metric", values="val")
        .reset_index()
        .rename(columns={"fy": "fiscal_year"})
    )

    wide_df.columns.name = None
    wide_df = wide_df.sort_values("fiscal_year").reset_index(drop=True)

    cik = str(companyfacts.get("cik", "")).zfill(10)
    entity_name = companyfacts.get("entityName", "")

    wide_df.insert(0, "entity_name", entity_name)
    wide_df.insert(0, "cik", cik)

    return wide_df