I drafted this README around the project: the FastAPI server starts correctly, health/search/analysis routes return `200`, Apple annual financials are being extracted, and the combined risk layer is producing the expected focus years.

# SEC Red Flag Engine
A quantitative SEC 10-K analysis engine built in Python using real EDGAR data.

This project fetches real annual filing data from the SEC EDGAR APIs, extracts company-level financial facts, performs exploratory data analysis (EDA), and detects unusual years using multiple quantitative methods:

- Global Z-Score
- Beneish M-Score
- Isolation Forest

The final output is a **combined risk summary** that highlights years that deserve further investigation.

---

# 1. Project Objective

The purpose of this project is to build a quantitative analysis engine for annual SEC filings.

The engine focuses on:

- pulling real company data from SEC EDGAR
- extracting annual financial facts
- converting raw filing data into a clean year-wise table
- performing feature engineering
- detecting abnormal patterns using statistical, accounting-based, and machine-learning methods
- combining multiple signals into a final year-wise risk layer

This project is currently focused on:

- **SEC**
- **annual filings only**
- **10-K and 10-K/A forms only**

---

# 2. What This Project Does

Given a company identifier such as:

- ticker, e.g. `AAPL`
- CIK, e.g. `0000320193`
- or company text, e.g. `Apple`

the engine will:

1. resolve the company identifier
2. fetch real SEC data
3. extract annual financial concepts
4. build a clean annual financial table
5. run EDA
6. run:
   - Global Z-Score
   - Beneish M-Score
   - Isolation Forest
7. combine these methods into a final risk summary
8. expose all of this through FastAPI endpoints

---

# 3. Current Filing Scope

This project currently treats only the following annual forms as valid:

```python
ANNUAL_FORMS = {"10-K", "10-K/A"}
````

## What is 10-K/A?

* `10-K` = annual report
* `10-K/A` = amended annual report

A `10-K/A` is still part of the same annual-report family, so it is kept in scope.

Examples:

* original annual filing = `10-K`
* corrected/amended annual filing = `10-K/A`

This project does **not** use 20-F or 40-F right now.

---

# 4. Tech Stack

* Python
* pandas
* numpy
* scikit-learn
* requests
* FastAPI
* python-dotenv

---

# 5. Project Structure

```text
sec-red-flag-engine/
├── .venv/
├── .env
├── README.md
├── requirements.txt
├── data/
│   ├── raw/
│   └── processed/
├── notebooks/
├── tests/
└── src/
    ├── __init__.py
    ├── api/
    │   ├── __init__.py
    │   ├── main.py
    │   └── schemas.py
    ├── data_fetch/
    │   ├── __init__.py
    │   ├── sec_client.py
    │   └── ticker_cik.py
    ├── features/
    │   ├── __init__.py
    │   ├── annual_features.py
    │   └── beneish_features.py
    ├── models/
    │   ├── __init__.py
    │   ├── zscore_detector.py
    │   ├── zscore_analysis.py
    │   ├── rolling_zscore_analysis.py
    │   ├── isolation_forest_analysis.py
    │   └── combined_risk.py
    ├── pipeline/
    │   ├── __init__.py
    │   ├── fetch_company_data.py
    │   ├── build_annual_financials.py
    │   ├── run_annual_eda.py
    │   ├── run_zscore_analysis.py
    │   ├── run_rolling_zscore_analysis.py
    │   ├── compare_zscore_methods.py
    │   ├── run_beneish_analysis.py
    │   ├── run_isolation_forest_analysis.py
    │   └── run_combined_risk.py
    ├── preprocessing/
    │   ├── __init__.py
    │   └── companyfacts_to_annuals.py
    ├── services/
    │   ├── __init__.py
    │   └── pipeline_service.py
    └── utils/
        ├── __init__.py
        ├── config.py
        └── http.py
```

---

# 6. Setup Instructions

## 6.1 Clone / open project

```bash
cd ~/projects/sec-red-flag-engine
```

## 6.2 Activate virtual environment

```bash
source .venv/bin/activate
```

## 6.3 Install dependencies

If needed:

```bash
pip install -r requirements.txt
pip install "fastapi[standard]"
```

## 6.4 Create `.env`

Create a file named `.env` in the project root:

```env
SEC_USER_AGENT=Your Name your_email@example.com
```

This is used while calling SEC EDGAR endpoints.

---

# 7. Core Data Flow

The engine works in this order:

## Step 1 — Company resolution

The system resolves a ticker, CIK, or company text into a canonical company identity.

Example:

* input: `AAPL`
* resolved company:

  * ticker: `AAPL`
  * cik: `0000320193`
  * title: `Apple Inc.`

## Step 2 — SEC raw fetch

The engine fetches:

* submissions JSON
* companyfacts JSON

These are saved locally in `data/raw/<key>/`.

## Step 3 — Annual concept extraction

The engine extracts a selected set of annual financial concepts from `companyfacts.json`.

## Step 4 — Annual financial table

The extracted facts are converted into a clean year-wise table.

## Step 5 — EDA

The engine adds:

* YoY growth columns
* ratio columns
* missingness report
* anomaly hints

## Step 6 — Quantitative models

The project then runs:

* Global Z-Score
* Beneish M-Score
* Isolation Forest

## Step 7 — Combined risk layer

All official methods are merged into one final summary.

---

# 8. Important Files and What They Do

---

## `src/utils/config.py`

### Purpose

Loads environment configuration and prepares important paths.

### Important responsibilities

* loads `.env`
* reads `SEC_USER_AGENT`
* defines:

  * `RAW_DATA_DIR`
  * `PROCESSED_DATA_DIR`

### Why it matters

Without this file, the project does not know:

* where to store data
* which SEC user agent to send

---

## `src/utils/http.py`

### Purpose

Provides a polite SEC HTTP session wrapper.

### Important responsibilities

* sets request headers
* applies request throttling
* retries failed requests
* returns JSON responses

### Main class

`SECSession`

### Why it matters

This file is the low-level communication layer between your project and the SEC.

---

## `src/data_fetch/ticker_cik.py`

### Purpose

Resolves ticker symbols to SEC CIKs.

### Important function

`lookup_company_by_ticker(ticker, sec_session)`

### What it does

* downloads `company_tickers.json`
* finds the matching company
* returns:

  * ticker
  * zero-padded CIK
  * company title

### Example

Input:

```python
"AAPL"
```

Output:

```python
{
    "ticker": "AAPL",
    "cik": "0000320193",
    "title": "Apple Inc."
}
```

---

## `src/data_fetch/sec_client.py`

### Purpose

Provides a simple EDGAR API client.

### Main class

`EdgarClient`

### Important methods

#### `get_submissions(cik)`

Fetches:

```text
https://data.sec.gov/submissions/CIK{cik}.json
```

#### `get_companyfacts(cik)`

Fetches:

```text
https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json
```

### Why it matters

This is the direct raw-data interface to SEC EDGAR.

---

## `src/preprocessing/companyfacts_to_annuals.py`

### Purpose

Converts raw `companyfacts.json` into clean annual financial data.

### Important pieces

#### `ANNUAL_FORMS`

Defines valid annual forms for the project:

```python
{"10-K", "10-K/A"}
```

#### `METRIC_CONFIG`

Defines which SEC XBRL tags are used for each financial metric.

Examples:

* revenue
* net_income
* total_assets
* receivables
* current_liabilities
* cfo
* sga
* depreciation
* debt-related metrics

#### `_pick_usd_unit()`

Selects the USD unit series from a concept.

#### `_normalize_fact_rows()`

Cleans individual concept rows and filters them by:

* valid forms
* fiscal-year rows
* usable dates
* numeric values

#### `extract_annual_metric_rows(companyfacts)`

Builds the long-format annual facts table.

#### `build_annual_financials_wide(companyfacts, long_df)`

Builds the wide annual financial table.

### Output files

* `annual_facts_long.csv`
* `annual_financials.csv`

---

## `src/features/annual_features.py`

### Purpose

Creates derived features used for EDA and anomaly detection.

### Important functions

#### `add_growth_features(df)`

Adds YoY growth columns like:

* `revenue_yoy`
* `net_income_yoy`
* `receivables_yoy`

#### `add_ratio_features(df)`

Adds ratio columns like:

* `current_ratio`
* `liabilities_to_assets`
* `cfo_to_net_income`
* `net_margin`
* `asset_turnover`

#### `build_missingness_report(df)`

Creates a missing-value report.

#### `build_summary_stats(df)`

Creates summary statistics.

#### `build_anomaly_hints(df, yoy_threshold=0.25)`

Identifies large YoY shifts.

### Output files

* `annual_financials_enriched.csv`
* `annual_missingness_report.csv`
* `annual_summary_stats.csv`
* `annual_anomaly_hints.csv`

---

## `src/models/zscore_detector.py`

### Purpose

Provides reusable z-score helper logic.

### Important function

`zscore_series(series)`

### What it does

Computes z-scores for a single pandas Series.

### Why it matters

This file is the reusable math helper for z-score calculations.

---

## `src/models/zscore_analysis.py`

### Purpose

Runs the official **global z-score** anomaly model.

### Important functions

#### `choose_zscore_features()`

Selects stable features based on:

* missingness
* non-null count
* variation

#### `add_zscore_columns()`

Adds z-score and z-flag columns.

#### `build_zscore_anomalies_long()`

Creates a long-format anomaly table.

#### `build_zscore_yearly_summary()`

Creates a year-wise summary of z-score anomalies.

### Why it matters

This is the official baseline anomaly detector in the project.

### Output files

* `zscore_feature_selection.csv`
* `annual_financials_zscores.csv`
* `zscore_anomalies_long.csv`
* `zscore_yearly_summary.csv`

---

## `src/models/rolling_zscore_analysis.py`

### Purpose

Provides an experimental rolling 5-year z-score method.

### Status

**Experimental only**
Not part of the official combined risk layer.

### Why it exists

It compares each year to its recent history instead of the whole company history.

### Why it is not official

In this project, it was found to be too aggressive and unstable for annual data.

---

## `src/features/beneish_features.py`

### Purpose

Builds Beneish M-score inputs and computes the final score.

### Important functions

#### `build_beneish_features(df)`

Calculates:

* DSRI
* GMI
* AQI
* SGI
* DEPI
* SGAI
* LVGI
* TATA
* beneish_mscore
* beneish_flag

#### `build_beneish_summary(df)`

Builds a clean summary table for Beneish output.

### Why it matters

This is the accounting-oriented fraud-screening layer.

### Output files

* `annual_beneish_features.csv`
* `beneish_summary.csv`

---

## `src/models/isolation_forest_analysis.py`

### Purpose

Runs the multivariate anomaly detection model.

### Important functions

#### `build_iforest_feature_matrix()`

Builds the feature matrix and imputes missing values.

#### `run_isolation_forest()`

Fits scikit-learn Isolation Forest.

#### `build_iforest_yearly_output()`

Adds model outputs back to year-wise rows.

#### `build_iforest_anomalies_long()`

Builds the long anomaly table.

#### `build_iforest_summary()`

Builds the year-wise summary.

### Why it matters

This model detects multivariate outlier years, not just single-feature spikes.

### Output files

* `iforest_feature_report.csv`
* `iforest_feature_matrix.csv`
* `annual_financials_iforest.csv`
* `iforest_anomalies_long.csv`
* `iforest_summary.csv`

---

## `src/models/combined_risk.py`

### Purpose

Combines official model outputs into a final quantitative risk layer.

### Official combined methods

* global z-score
* Beneish M-score
* Isolation Forest

### Important functions

#### `build_combined_risk_summary()`

Merges year-wise summaries from all official methods.

#### `build_combined_focus_years()`

Keeps only years where at least one method triggered.

### Why it matters

This is the final decision layer used by the API.

### Output files

* `combined_risk_summary.csv`
* `combined_risk_focus_years.csv`

---

## `src/services/pipeline_service.py`

### Purpose

This is the **main service layer** used by the API.

### Why it matters

Instead of forcing the API to run CLI scripts, all important logic is wrapped in reusable service functions.

### Important functions

#### `search_companies(query, limit=10)`

Searches company metadata.

#### `resolve_company(identifier)`

Accepts:

* ticker
* CIK
* company text

and resolves it into a canonical company object.

#### `ensure_raw_company_data(identifier, force_refresh=False)`

Fetches and stores raw SEC data if not already present.

#### `build_annual_financials_service(identifier)`

Builds annual financial CSV files.

#### `run_annual_eda_service(identifier)`

Runs EDA and saves enriched outputs.

#### `run_global_zscore_service(identifier, threshold=2.0)`

Runs global z-score.

#### `run_beneish_service(identifier)`

Runs Beneish M-score.

#### `run_iforest_service(identifier, contamination=0.15, n_estimators=200, random_state=42)`

Runs Isolation Forest.

#### `run_combined_risk_service(identifier, contamination=0.15)`

Runs the final combined layer.

#### `run_full_analysis_service(identifier, contamination=0.15)`

Runs the full official pipeline and returns API-ready output.

#### `get_annual_financials_service(identifier)`

Returns annual financial rows for the API.

#### `get_combined_risk_service(identifier, contamination=0.15)`

Returns combined risk data for the API.

#### `get_beneish_service(identifier)`

Returns Beneish summary/features for the API.

---

## `src/api/schemas.py`

### Purpose

Defines request and response models for FastAPI.

### Why it matters

Makes the API:

* typed
* documented
* cleaner for frontend integration

### Important models

* `AnalyzeRequest`
* `AnalyzeResponse`
* `CompanyInfo`
* `CompanySearchResponse`
* `AnnualFinancialsResponse`
* `BeneishResponse`
* `CombinedRiskResponse`

---

## `src/api/main.py`

### Purpose

Defines the FastAPI application and public endpoints.

### Main routes

#### `GET /health`

Basic health check.

#### `GET /companies/search?q=apple`

Company search endpoint.

#### `POST /analysis/run`

Runs the complete analysis pipeline.

#### `GET /companies/{identifier}/annual-financials`

Returns annual financial table.

#### `GET /companies/{identifier}/beneish`

Returns Beneish output.

#### `GET /companies/{identifier}/combined-risk`

Returns final combined risk output.

---

# 9. Important Command-Line Pipelines

These are useful for debugging and development.

---

## 9.1 Fetch raw SEC data

```bash
python -m src.pipeline.fetch_company_data --ticker AAPL
```

### What it does

* resolves company
* fetches submissions JSON
* fetches companyfacts JSON
* saves recent filings CSV

### Output

* `data/raw/aapl/submissions.json`
* `data/raw/aapl/companyfacts.json`
* `data/processed/aapl/recent_filings.csv`

---

## 9.2 Build annual financials

```bash
python -m src.pipeline.build_annual_financials --ticker AAPL
```

### What it does

* reads companyfacts
* extracts annual facts
* builds clean annual financial table

### Output

* `annual_facts_long.csv`
* `annual_financials.csv`

---

## 9.3 Run EDA

```bash
python -m src.pipeline.run_annual_eda --ticker AAPL
```

### What it does

* adds YoY growth columns
* adds ratio columns
* saves missingness report
* saves anomaly hints

---

## 9.4 Run global z-score

```bash
python -m src.pipeline.run_zscore_analysis --ticker AAPL
```

### What it does

* selects stable features
* computes z-scores
* flags anomalies
* produces year-wise summary

---

## 9.5 Run rolling z-score (experimental)

```bash
python -m src.pipeline.run_rolling_zscore_analysis --ticker AAPL
```

### Optional comparison

```bash
python -m src.pipeline.compare_zscore_methods --ticker AAPL
```

---

## 9.6 Run Beneish

```bash
python -m src.pipeline.run_beneish_analysis --ticker AAPL
```

### What it does

* builds Beneish variables
* computes M-score
* flags years crossing the threshold

---

## 9.7 Run Isolation Forest

```bash
python -m src.pipeline.run_isolation_forest_analysis --ticker AAPL --contamination 0.15
```

### What it does

* builds multivariate feature matrix
* imputes missing values
* fits Isolation Forest
* labels outlier years

---

## 9.8 Run combined risk layer

```bash
python -m src.pipeline.run_combined_risk --ticker AAPL
```

### What it does

* merges global z-score
* merges Beneish
* merges Isolation Forest
* produces final risk summary

---

# 10. API Usage

## 10.1 Start the API server

```bash
source .venv/bin/activate
fastapi dev src/api/main.py
```

You should see:

* server URL
* docs URL

Typically:

* API base URL: `http://127.0.0.1:8000`
* docs: `http://127.0.0.1:8000/docs`

---

## 10.2 Important note about localhost

`127.0.0.1` means:

**this machine only**

So if you send `http://127.0.0.1:8000` to a teammate, it will not work on their laptop unless:

* they run the backend on their own machine, or
* the backend is deployed/shared properly

---

## 10.3 Test endpoints

### Health

```bash
curl "http://127.0.0.1:8000/health"
```

### Company search

```bash
curl "http://127.0.0.1:8000/companies/search?q=apple"
```

### Run full analysis

```bash
curl -X POST "http://127.0.0.1:8000/analysis/run" \
  -H "Content-Type: application/json" \
  -d '{"identifier":"AAPL","contamination":0.15}'
```

### Annual financials

```bash
curl "http://127.0.0.1:8000/companies/AAPL/annual-financials"
```

### Beneish

```bash
curl "http://127.0.0.1:8000/companies/AAPL/beneish"
```

### Combined risk

```bash
curl "http://127.0.0.1:8000/companies/AAPL/combined-risk"
```

---

# 11. Important API Clarification

## Why opening `/analysis/run` in a browser shows:

```json
{"detail":"Method Not Allowed"}
```

Because:

* browser address bar sends a `GET` request
* `/analysis/run` expects a `POST` request

So this is correct behavior.

### Correct way to use `/analysis/run`

Use:

* Swagger docs (`/docs`)
* curl
* Postman
* frontend code

---

# 12. Current Official Model Policy

## Official methods used in final combined risk

* Global Z-Score
* Beneish M-Score
* Isolation Forest

## Experimental only

* Rolling 5-year Z-score

Reason:
Rolling z-score was implemented successfully, but for this dataset it produced unstable/extreme behavior and is therefore not part of the official combined layer.

---

# 13. Output Files You Should Know

## Raw

* `submissions.json`
* `companyfacts.json`

## Annual extraction

* `annual_facts_long.csv`
* `annual_financials.csv`

## EDA

* `annual_financials_enriched.csv`
* `annual_missingness_report.csv`
* `annual_summary_stats.csv`
* `annual_anomaly_hints.csv`

## Z-score

* `zscore_feature_selection.csv`
* `annual_financials_zscores.csv`
* `zscore_anomalies_long.csv`
* `zscore_yearly_summary.csv`

## Rolling z-score

* `rolling_zscore_feature_selection.csv`
* `annual_financials_rolling_zscores.csv`
* `rolling_zscore_anomalies_long.csv`
* `rolling_zscore_yearly_summary.csv`
* `zscore_method_comparison.csv`

## Beneish

* `annual_beneish_features.csv`
* `beneish_summary.csv`

## Isolation Forest

* `iforest_feature_report.csv`
* `iforest_feature_matrix.csv`
* `annual_financials_iforest.csv`
* `iforest_anomalies_long.csv`
* `iforest_summary.csv`

## Combined

* `combined_risk_summary.csv`
* `combined_risk_focus_years.csv`

---

# 14. Example Interpretation of Final Output

For Apple, the current combined engine generally behaves like this:

* early years such as 2010–2012 show stronger consensus anomaly behavior
* 2021 is more of an accounting/growth watch year
* 2025 is a lighter statistical watch year
* many other years are not flagged at the combined level

This means the engine is selective and does not simply flag everything.

---

# 15. Common Confusions

## “Why does browser show Method Not Allowed?”

Because `POST` endpoint was opened like a `GET` URL.

## “Why is localhost not working for my teammate?”

Because `127.0.0.1` is only local to your own machine.

## “Do users need to run Python commands?”

No. End users should use the API or frontend.
CLI scripts are only for development/testing.

## “Why keep 10-K/A?”

Because it is an amended annual report and still belongs to the annual-report scope.

---

# 16. Recommended Development Order

If you are reading this project for the first time, understand it in this order:

1. `src/utils/config.py`
2. `src/utils/http.py`
3. `src/data_fetch/ticker_cik.py`
4. `src/data_fetch/sec_client.py`
5. `src/preprocessing/companyfacts_to_annuals.py`
6. `src/features/annual_features.py`
7. `src/models/zscore_analysis.py`
8. `src/features/beneish_features.py`
9. `src/models/isolation_forest_analysis.py`
10. `src/models/combined_risk.py`
11. `src/services/pipeline_service.py`
12. `src/api/main.py`

That gives the clearest understanding of the full flow.

---

# 17. Final Summary

This project is a quantitative SEC annual-filing analysis engine that:

* uses real EDGAR data
* focuses on 10-K / 10-K/A
* builds clean annual financial tables
* performs EDA
* detects unusual years using multiple methods
* combines those methods into a final risk summary
* exposes everything through FastAPI for frontend usage

It is designed so that:

* developers can debug with CLI pipelines
* frontend can use clean API endpoints
* future expansion can happen without rewriting the core engine

```

A couple of details in your latest API output still need cleanup if you want the README to match the code perfectly: `saved_paths` is still coming back in `POST /analysis/run`, and `triggered_methods` is still `null` for no-trigger years in part of the combined response. Your latest logs confirm those are still present right now. 

If you want, I can also turn this into a **final polished README version** with:
- badges,
- quickstart section,
- API table,
- troubleshooting section,
- and cleaner formatting for GitHub.
```
# Docker Setup

This project can be run inside Docker so teammates do not need to manually recreate the full Python environment.

## Why use Docker?

Docker helps the team run the same backend with:
- the same Python version
- the same dependencies
- the same startup command
- the same exposed API port

For this project, Docker is mainly useful for:
- local team development
- easier onboarding
- avoiding dependency mismatch issues

---

## Files used for Docker

The project uses these files in the root directory:

- `Dockerfile`
- `compose.yaml`
- `.dockerignore`
- `.env.example`

---

## Prerequisites

Before running the containerized project, make sure you have:

- Docker installed
- Docker Compose available through `docker compose`

---

## 1. Create `.env`

Create a file named `.env` in the project root.

Example:

```env id="v4jley"
SEC_USER_AGENT=Your Name your_email@example.com