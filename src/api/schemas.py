from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CompanyInfo(BaseModel):
    ticker: str
    cik: str
    title: str


class CompanySearchItem(BaseModel):
    name: str
    ticker: str
    cik: str


class CompanySearchResponse(BaseModel):
    results: list[CompanySearchItem]


class AnalyzeRequest(BaseModel):
    identifier: str = Field(
        ...,
        description="Ticker, CIK, or company text like AAPL or 0000320193",
        examples=["AAPL"],
    )
    contamination: float = Field(
        default=0.15,
        gt=0,
        lt=0.5,
        description="Isolation Forest contamination",
    )


class AnalyzeResponse(BaseModel):
    company: CompanyInfo
    storage_key: str
    combined_focus_years: list[dict[str, Any]]
    combined_risk_summary: list[dict[str, Any]]


class AnnualFinancialsResponse(BaseModel):
    company: CompanyInfo
    storage_key: str
    rows: list[dict[str, Any]]


class BeneishResponse(BaseModel):
    company: CompanyInfo
    storage_key: str
    summary: list[dict[str, Any]]
    features: list[dict[str, Any]]


class CombinedRiskResponse(BaseModel):
    company: CompanyInfo
    storage_key: str
    summary: list[dict[str, Any]]
    focus_years: list[dict[str, Any]]