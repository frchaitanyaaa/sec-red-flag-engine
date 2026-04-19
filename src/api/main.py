from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.api.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnnualFinancialsResponse,
    BeneishResponse,
    CombinedRiskResponse,
    CompanySearchResponse,
)
from src.services.pipeline_service import (
    get_annual_financials_service,
    get_beneish_service,
    get_combined_risk_service,
    run_full_analysis_service,
    search_companies,
    
)

app = FastAPI(
    title="SEC Red Flag Engine API",
    version="0.1.0",
    description="Quantitative SEC 10-K anomaly engine using Z-score, Beneish M-score, and Isolation Forest.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/companies/search", response_model=CompanySearchResponse)
def company_search(
    q: str = Query(..., min_length=1, description="Ticker or company name"),
    limit: int = Query(10, ge=1, le=20),
) -> dict:
    try:
        return {"results": search_companies(q, limit=limit)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/analysis/run", response_model=AnalyzeResponse)
def run_analysis(payload: AnalyzeRequest) -> AnalyzeResponse:
    try:
        result = run_full_analysis_service(
            identifier=payload.identifier,
            contamination=payload.contamination,
        )
        return AnalyzeResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/companies/{identifier}/annual-financials", response_model=AnnualFinancialsResponse)
def annual_financials(identifier: str) -> dict:
    try:
        return get_annual_financials_service(identifier)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/companies/{identifier}/beneish", response_model=BeneishResponse)
def beneish(identifier: str) -> dict:
    try:
        return get_beneish_service(identifier)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/companies/{identifier}/combined-risk", response_model=CombinedRiskResponse)
def combined_risk(
    identifier: str,
    contamination: float = Query(0.15, gt=0, lt=0.5),
) -> dict:
    try:
        return get_combined_risk_service(identifier, contamination=contamination)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc