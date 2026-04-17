from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.data_fetch.sec_client import EdgarClient
from src.data_fetch.ticker_cik import lookup_company_by_ticker
from src.utils.config import PROCESSED_DATA_DIR, RAW_DATA_DIR, SEC_USER_AGENT
from src.utils.http import SECSession


ANNUAL_FORMS = {"10-K", "10-K/A"}


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def recent_filings_to_dataframe(submissions: dict) -> pd.DataFrame:
    recent = submissions.get("filings", {}).get("recent", {})
    if not recent:
        return pd.DataFrame()

    df = pd.DataFrame(recent)

    if "form" in df.columns:
        df["is_annual"] = df["form"].isin(ANNUAL_FORMS)
        #df["is_quarterly"] = df["form"].isin(QUARTERLY_FORMS)

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch SEC EDGAR raw data for one company.")
    parser.add_argument("--ticker", required=True, help="Ticker symbol, e.g. AAPL")
    args = parser.parse_args()

    ticker = args.ticker.strip().upper()

    sec_session = SECSession(user_agent=SEC_USER_AGENT)
    company = lookup_company_by_ticker(ticker=ticker, sec_session=sec_session)
    client = EdgarClient(sec_session=sec_session)

    cik = company["cik"]
    title = company["title"]

    print(f"Resolved ticker {ticker} -> CIK {cik} ({title})")

    submissions = client.get_submissions(cik=cik)
    companyfacts = client.get_companyfacts(cik=cik)

    raw_dir = RAW_DATA_DIR / ticker.lower()
    processed_dir = PROCESSED_DATA_DIR / ticker.lower()
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    save_json(raw_dir / "submissions.json", submissions)
    save_json(raw_dir / "companyfacts.json", companyfacts)

    recent_filings_df = recent_filings_to_dataframe(submissions)
    recent_filings_csv_path = processed_dir / "recent_filings.csv"
    recent_filings_df.to_csv(recent_filings_csv_path, index=False)

    print(f"Saved: {raw_dir / 'submissions.json'}")
    print(f"Saved: {raw_dir / 'companyfacts.json'}")
    print(f"Saved: {recent_filings_csv_path}")

    if not recent_filings_df.empty:
        print("\nRecent filing form counts:")
        print(recent_filings_df["form"].value_counts().head(15))

        annual_df = recent_filings_df[recent_filings_df["is_annual"]].copy()
        if not annual_df.empty:
            keep_cols = [c for c in ["filingDate", "form", "accessionNumber", "primaryDocument", "primaryDocDescription"] if c in annual_df.columns]
            print("\nRecent annual filings:")
            print(annual_df[keep_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()