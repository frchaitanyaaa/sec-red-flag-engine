from __future__ import annotations

from typing import Any

from src.utils.http import SECSession


COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


def lookup_company_by_ticker(ticker: str, sec_session: SECSession) -> dict[str, Any]:
    ticker = ticker.strip().upper()
    data = sec_session.get_json(COMPANY_TICKERS_URL)

    for _, company in data.items():
        if str(company["ticker"]).upper() == ticker:
            cik = str(company["cik_str"]).zfill(10)
            return {
                "ticker": ticker,
                "cik": cik,
                "title": company["title"],
            }

    raise ValueError(f"Ticker not found in SEC company_tickers.json: {ticker}")