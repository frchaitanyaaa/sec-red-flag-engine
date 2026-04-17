from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import requests


@dataclass
class SECSession:
    user_agent: str
    min_interval_seconds: float = 0.25
    timeout_seconds: int = 30
    max_retries: int = 3
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self) -> None:
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Accept": "application/json, text/plain, */*",
            }
        )
        self._last_request_time = 0.0

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.min_interval_seconds:
            time.sleep(self.min_interval_seconds - elapsed)

    def get_json(self, url: str) -> dict[str, Any]:
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                self._throttle()
                response = self.session.get(url, timeout=self.timeout_seconds)
                self._last_request_time = time.monotonic()
                response.raise_for_status()
                return response.json()

            except requests.RequestException as exc:
                last_error = exc
                if attempt == self.max_retries:
                    break
                time.sleep(attempt)

        raise RuntimeError(f"Failed to fetch JSON from {url}") from last_error