from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "").strip()

if not SEC_USER_AGENT:
    raise RuntimeError(
        "SEC_USER_AGENT is missing. Create a .env file in the project root with:\n"
        "SEC_USER_AGENT=Your Name your_email@example.com"
    )

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)