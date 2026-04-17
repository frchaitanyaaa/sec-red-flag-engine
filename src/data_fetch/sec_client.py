from __future__ import annotations

from typing import Any

from src.utils.http import SECSession


class EdgarClient:
    def __init__(self, sec_session: SECSession) -> None:
        self.sec_session = sec_session

    def get_submissions(self, cik: str) -> dict[str, Any]:
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        return self.sec_session.get_json(url)

    def get_companyfacts(self, cik: str) -> dict[str, Any]:
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        return self.sec_session.get_json(url)