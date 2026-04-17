from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.data_fetch.sec_client import EdgarClient
from src.data_fetch.ticker_cik import COMPANY_TICKERS_URL, lookup_company_by_ticker
from src.features.annual_features import (
    add_growth_features,
    add_ratio_features,
    build_anomaly_hints,
    build_missingness_report,
    build_summary_stats,
)
from src.features.beneish_features import build_beneish_features, build_beneish_summary
from src.models.combined_risk import build_combined_focus_years, build_combined_risk_summary
from src.models.isolation_forest_analysis import (
    build_iforest_anomalies_long,
    build_iforest_feature_matrix,
    build_iforest_summary,
    build_iforest_yearly_output,
    run_isolation_forest,
)
from src.models.zscore_analysis import (
    add_zscore_columns,
    build_zscore_anomalies_long,
    build_zscore_yearly_summary,
    choose_zscore_features,
)
from src.preprocessing.companyfacts_to_annuals import (
    build_annual_financials_wide,
    extract_annual_metric_rows,
)
from src.utils.config import PROCESSED_DATA_DIR, RAW_DATA_DIR, SEC_USER_AGENT
from src.utils.http import SECSession


ANNUAL_FORMS = {"10-K", "10-K/A"}   #10-K/A means an amended Form 10-K. The SEC’s investor guidance states that /A indicates an amendment, and a 10-K/A filing typically says it is being filed to amend a previously filed annual report

def _normalize_cik(value: Any) -> str | None:
    if value is None:
        return None

    if pd.isna(value):
        return None

    text = str(value).strip()
    if not text:
        return None

    if text.endswith(".0"):
        text = text[:-2]

    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return text

    return digits.zfill(10)


def _normalize_company(company: dict[str, Any]) -> dict[str, Any]:
    out = dict(company)
    if "cik" in out:
        out["cik"] = _normalize_cik(out["cik"])
    return out


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_csv_records(path: Path) -> list[dict[str, Any]]:
    df = pd.read_csv(path)

    if "cik" in df.columns:
        df["cik"] = df["cik"].apply(_normalize_cik)

    for col in ["triggered_methods", "zscore_features_triggered"]:
        if col in df.columns:
            df[col] = df[col].fillna("")

    df = df.where(pd.notna(df), None)
    return df.to_dict(orient="records")


def _storage_key(company: dict[str, Any]) -> str:
    ticker = str(company.get("ticker", "")).strip().lower()
    cik = str(company.get("cik", "")).strip()
    return ticker or cik


def _recent_filings_to_dataframe(submissions: dict[str, Any]) -> pd.DataFrame:
    recent = submissions.get("filings", {}).get("recent", {})
    if not recent:
        return pd.DataFrame()

    df = pd.DataFrame(recent)

    if "form" in df.columns:
        df["is_annual"] = df["form"].isin(ANNUAL_FORMS)
        # df["is_quarterly"] = df["form"].isin(QUARTERLY_FORMS)

    return df


def search_companies(query: str, limit: int = 10) -> list[dict[str, Any]]:
    q = query.strip().lower()
    if not q:
        return []

    sec_session = SECSession(user_agent=SEC_USER_AGENT)
    data = sec_session.get_json(COMPANY_TICKERS_URL)

    matches: list[dict[str, Any]] = []
    for _, item in data.items():
        title = str(item["title"])
        ticker = str(item["ticker"]).upper()
        cik = str(item["cik_str"]).zfill(10)

        if q in title.lower() or q in ticker.lower() or q in cik:
            matches.append(
                {
                    "name": title,
                    "ticker": ticker,
                    "cik": cik,
                }
            )

    matches.sort(
        key=lambda x: (
            x["ticker"] != query.strip().upper(),
            len(x["name"]),
            x["name"],
        )
    )
    return matches[:limit]


def resolve_company(identifier: str) -> dict[str, Any]:
    token = identifier.strip()
    if not token:
        raise ValueError("identifier is required")

    sec_session = SECSession(user_agent=SEC_USER_AGENT)
    client = EdgarClient(sec_session=sec_session)

    if token.isdigit():
        cik = token.zfill(10)
        submissions = client.get_submissions(cik=cik)
        tickers = submissions.get("tickers") or []
        ticker = str(tickers[0]).upper() if tickers else ""
        title = submissions.get("name") or submissions.get("entityName") or ""
        return {
            "ticker": ticker,
            "cik": cik,
            "title": title,
        }

    try:
        company = lookup_company_by_ticker(token, sec_session)
        return {
            "ticker": str(company["ticker"]).upper(),
            "cik": str(company["cik"]).zfill(10),
            "title": company["title"],
        }
    except ValueError:
        matches = search_companies(token, limit=1)
        if not matches:
            raise ValueError(f"Could not resolve company from identifier: {identifier}")

        best = matches[0]
        return {
            "ticker": best["ticker"],
            "cik": best["cik"],
            "title": best["name"],
        }


def ensure_raw_company_data(identifier: str, force_refresh: bool = False) -> dict[str, Any]:
    company = resolve_company(identifier)
    key = _storage_key(company)

    raw_dir = RAW_DATA_DIR / key
    processed_dir = PROCESSED_DATA_DIR / key

    submissions_path = raw_dir / "submissions.json"
    companyfacts_path = raw_dir / "companyfacts.json"
    recent_filings_path = processed_dir / "recent_filings.csv"

    if submissions_path.exists() and companyfacts_path.exists() and not force_refresh:
        return {
            "company": company,
            "storage_key": key,
            "raw_dir": str(raw_dir),
            "processed_dir": str(processed_dir),
            "saved_paths": {
                "submissions": str(submissions_path),
                "companyfacts": str(companyfacts_path),
                "recent_filings": str(recent_filings_path),
            },
        }

    sec_session = SECSession(user_agent=SEC_USER_AGENT)
    client = EdgarClient(sec_session=sec_session)

    submissions = client.get_submissions(cik=company["cik"])
    companyfacts = client.get_companyfacts(cik=company["cik"])

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    _save_json(submissions_path, submissions)
    _save_json(companyfacts_path, companyfacts)

    recent_filings_df = _recent_filings_to_dataframe(submissions)
    recent_filings_df.to_csv(recent_filings_path, index=False)

    return {
        "company": company,
        "storage_key": key,
        "raw_dir": str(raw_dir),
        "processed_dir": str(processed_dir),
        "saved_paths": {
            "submissions": str(submissions_path),
            "companyfacts": str(companyfacts_path),
            "recent_filings": str(recent_filings_path),
        },
    }


def build_annual_financials_service(identifier: str) -> dict[str, Any]:
    raw_info = ensure_raw_company_data(identifier)
    key = raw_info["storage_key"]

    companyfacts_path = RAW_DATA_DIR / key / "companyfacts.json"
    companyfacts = _load_json(companyfacts_path)

    long_df = extract_annual_metric_rows(companyfacts)
    if long_df.empty:
        raise RuntimeError("No annual financial facts were extracted from companyfacts.json")

    wide_df = build_annual_financials_wide(companyfacts, long_df)

    out_dir = PROCESSED_DATA_DIR / key
    out_dir.mkdir(parents=True, exist_ok=True)

    long_path = out_dir / "annual_facts_long.csv"
    wide_path = out_dir / "annual_financials.csv"

    long_df.to_csv(long_path, index=False)
    wide_df.to_csv(wide_path, index=False)

    return {
        "company": raw_info["company"],
        "storage_key": key,
        "saved_paths": {
            **raw_info["saved_paths"],
            "annual_facts_long": str(long_path),
            "annual_financials": str(wide_path),
        },
        "row_count": int(len(wide_df)),
    }


def run_annual_eda_service(identifier: str) -> dict[str, Any]:
    annual_info = build_annual_financials_service(identifier)
    key = annual_info["storage_key"]

    in_path = PROCESSED_DATA_DIR / key / "annual_financials.csv"
    df = pd.read_csv(in_path).sort_values("fiscal_year").reset_index(drop=True)

    enriched_df = add_growth_features(df)
    enriched_df = add_ratio_features(enriched_df)

    missingness_df = build_missingness_report(enriched_df)
    summary_df = build_summary_stats(enriched_df)
    anomaly_hints_df = build_anomaly_hints(enriched_df, yoy_threshold=0.25)

    out_dir = PROCESSED_DATA_DIR / key
    enriched_path = out_dir / "annual_financials_enriched.csv"
    missingness_path = out_dir / "annual_missingness_report.csv"
    summary_path = out_dir / "annual_summary_stats.csv"
    hints_path = out_dir / "annual_anomaly_hints.csv"

    enriched_df.to_csv(enriched_path, index=False)
    missingness_df.to_csv(missingness_path, index=False)
    summary_df.to_csv(summary_path, index=False)
    anomaly_hints_df.to_csv(hints_path, index=False)

    return {
        "company": annual_info["company"],
        "storage_key": key,
        "saved_paths": {
            **annual_info["saved_paths"],
            "annual_financials_enriched": str(enriched_path),
            "annual_missingness_report": str(missingness_path),
            "annual_summary_stats": str(summary_path),
            "annual_anomaly_hints": str(hints_path),
        },
    }


def run_global_zscore_service(identifier: str, threshold: float = 2.0) -> dict[str, Any]:
    eda_info = run_annual_eda_service(identifier)
    key = eda_info["storage_key"]

    in_path = PROCESSED_DATA_DIR / key / "annual_financials_enriched.csv"
    df = pd.read_csv(in_path).sort_values("fiscal_year").reset_index(drop=True)

    selected_features, feature_report_df = choose_zscore_features(df)
    scored_df = add_zscore_columns(df, selected_features, threshold=threshold)
    anomalies_df = build_zscore_anomalies_long(scored_df, selected_features, threshold=threshold)
    yearly_summary_df = build_zscore_yearly_summary(anomalies_df, df["fiscal_year"].tolist())

    out_dir = PROCESSED_DATA_DIR / key
    feature_report_path = out_dir / "zscore_feature_selection.csv"
    scored_path = out_dir / "annual_financials_zscores.csv"
    anomalies_path = out_dir / "zscore_anomalies_long.csv"
    summary_path = out_dir / "zscore_yearly_summary.csv"

    feature_report_df.to_csv(feature_report_path, index=False)
    scored_df.to_csv(scored_path, index=False)
    anomalies_df.to_csv(anomalies_path, index=False)
    yearly_summary_df.to_csv(summary_path, index=False)

    return {
        "company": eda_info["company"],
        "storage_key": key,
        "saved_paths": {
            **eda_info["saved_paths"],
            "zscore_feature_selection": str(feature_report_path),
            "annual_financials_zscores": str(scored_path),
            "zscore_anomalies_long": str(anomalies_path),
            "zscore_yearly_summary": str(summary_path),
        },
    }


def run_beneish_service(identifier: str) -> dict[str, Any]:
    annual_info = build_annual_financials_service(identifier)
    key = annual_info["storage_key"]

    in_path = PROCESSED_DATA_DIR / key / "annual_financials.csv"
    df = pd.read_csv(in_path).sort_values("fiscal_year").reset_index(drop=True)

    beneish_df = build_beneish_features(df)
    summary_df = build_beneish_summary(beneish_df)

    out_dir = PROCESSED_DATA_DIR / key
    features_path = out_dir / "annual_beneish_features.csv"
    summary_path = out_dir / "beneish_summary.csv"

    beneish_df.to_csv(features_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    return {
        "company": annual_info["company"],
        "storage_key": key,
        "saved_paths": {
            **annual_info["saved_paths"],
            "annual_beneish_features": str(features_path),
            "beneish_summary": str(summary_path),
        },
    }


def run_iforest_service(
    identifier: str,
    contamination: float = 0.15,
    n_estimators: int = 200,
    random_state: int = 42,
) -> dict[str, Any]:
    eda_info = run_annual_eda_service(identifier)
    key = eda_info["storage_key"]

    in_path = PROCESSED_DATA_DIR / key / "annual_financials_enriched.csv"
    df = pd.read_csv(in_path).sort_values("fiscal_year").reset_index(drop=True)

    X, selected_features, feature_report_df = build_iforest_feature_matrix(df)
    _, model_output_df = run_isolation_forest(
        X=X,
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=random_state,
    )
    scored_df = build_iforest_yearly_output(df, model_output_df)
    anomalies_df = build_iforest_anomalies_long(scored_df, selected_features)
    summary_df = build_iforest_summary(scored_df)

    out_dir = PROCESSED_DATA_DIR / key
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

    return {
        "company": eda_info["company"],
        "storage_key": key,
        "saved_paths": {
            **eda_info["saved_paths"],
            "iforest_feature_report": str(feature_report_path),
            "iforest_feature_matrix": str(matrix_path),
            "annual_financials_iforest": str(scored_path),
            "iforest_anomalies_long": str(anomalies_path),
            "iforest_summary": str(summary_path),
        },
    }


def run_combined_risk_service(identifier: str, contamination: float = 0.15) -> dict[str, Any]:
    z_info = run_global_zscore_service(identifier)
    b_info = run_beneish_service(identifier)
    i_info = run_iforest_service(identifier, contamination=contamination)

    key = z_info["storage_key"]
    out_dir = PROCESSED_DATA_DIR / key

    zscore_df = pd.read_csv(out_dir / "zscore_yearly_summary.csv")
    beneish_df = pd.read_csv(out_dir / "beneish_summary.csv")
    iforest_df = pd.read_csv(out_dir / "iforest_summary.csv")

    summary_df = build_combined_risk_summary(
        zscore_summary_df=zscore_df,
        beneish_summary_df=beneish_df,
        iforest_summary_df=iforest_df,
    )
    focus_df = build_combined_focus_years(summary_df)

    summary_path = out_dir / "combined_risk_summary.csv"
    focus_path = out_dir / "combined_risk_focus_years.csv"

    summary_df.to_csv(summary_path, index=False)
    focus_df.to_csv(focus_path, index=False)

    return {
        "company": z_info["company"],
        "storage_key": key,
        "saved_paths": {
            **z_info["saved_paths"],
            **b_info["saved_paths"],
            **i_info["saved_paths"],
            "combined_risk_summary": str(summary_path),
            "combined_risk_focus_years": str(focus_path),
        },
    }


def run_full_analysis_service(identifier: str, contamination: float = 0.15) -> dict[str, Any]:
    combined_info = run_combined_risk_service(identifier, contamination=contamination)
    key = combined_info["storage_key"]
    out_dir = PROCESSED_DATA_DIR / key

    focus_years = _read_csv_records(out_dir / "combined_risk_focus_years.csv")
    summary_rows = _read_csv_records(out_dir / "combined_risk_summary.csv")

    return {
        "company": _normalize_company(combined_info["company"]),
        "storage_key": key,
        "saved_paths": combined_info["saved_paths"],
        "combined_focus_years": focus_years,
        "combined_risk_summary": summary_rows,
    }


def get_annual_financials_service(identifier: str) -> dict[str, Any]:
    annual_info = build_annual_financials_service(identifier)
    key = annual_info["storage_key"]

    path = PROCESSED_DATA_DIR / key / "annual_financials.csv"
    return {
        "company": _normalize_company(annual_info["company"]),
        "storage_key": key,
        "rows": _read_csv_records(path),
    }


def get_combined_risk_service(identifier: str, contamination: float = 0.15) -> dict[str, Any]:
    combined_info = run_combined_risk_service(identifier, contamination=contamination)
    key = combined_info["storage_key"]

    summary_path = PROCESSED_DATA_DIR / key / "combined_risk_summary.csv"
    focus_path = PROCESSED_DATA_DIR / key / "combined_risk_focus_years.csv"

    return {
        "company": _normalize_company(combined_info["company"]),
        "storage_key": key,
        "summary": _read_csv_records(summary_path),
        "focus_years": _read_csv_records(focus_path),
    }


def get_beneish_service(identifier: str) -> dict[str, Any]:
    beneish_info = run_beneish_service(identifier)
    key = beneish_info["storage_key"]

    summary_path = PROCESSED_DATA_DIR / key / "beneish_summary.csv"
    features_path = PROCESSED_DATA_DIR / key / "annual_beneish_features.csv"

    return {
        "company": _normalize_company(beneish_info["company"]),
        "storage_key": key,
        "summary": _read_csv_records(summary_path),
        "features": _read_csv_records(features_path),
    }