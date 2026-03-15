# Local AI Financial Analyst System
## Technical Specification and Requirements Document
**Target platform:** macOS + local database + OpenClaw-style agent framework

**Version:** 1.0
**Date:** 2026‑03‑14
**Status:** Implementation-ready specification

---

## 1. Purpose

This document defines the architecture, design, and requirements for a **local AI financial analyst system** running on macOS. The system emulates an institutional-grade "financial analyst + quant researcher" assistant with two core capabilities:

- **Universe screening via SQL** against a local market database.
- **Quantitative analysis via Python** (technical indicators, scoring, risk flags, and reporting).

The system is designed for:

- Local-first execution on a Mac (desktop or Mac mini).
- Use within an agent framework similar to OpenClaw / LangGraph / Open Interpreter.
- Persistent local market data (historical prices, fundamentals, and metadata).
- Structured research outputs in Markdown and CSV, optionally HTML/PDF.

---

## 2. Objectives

### 2.1 Primary objectives

- Provide an **AI agent** that behaves like a human quant/analyst.
- Support **value screens** (e.g., low P/E, near 52-week lows, liquidity constraints).
- Support **momentum screens** (e.g., top 5‑day performers with ROC, RSI, trend validation).
- Maintain a robust, query-ready **local database** using SQL (DuckDB).
- Enable **Python-based** analytics on screening results.
- Produce explainable, reproducible **research reports**.

### 2.2 Secondary objectives

- Encapsulate screening logic and workflows into **reusable skills** (e.g., `value_screening`, `momentum_analysis`).
- Keep all market data local by default; external calls are optional and explicit.
- Support incremental extension to backtesting and portfolio scoring.

### 2.3 Non-goals (v1)

- Real-time intraday trading or order routing.
- High-frequency trading or sub-second latency.
- Full professional market data redistribution and entitlement compliance.
- Options/derivatives pricing beyond simple placeholders.

---

## 3. Scope

### 3.1 In scope

- End-of-day (EOD) and daily snapshot data ingestion.
- Equity universe screening with SQL.
- Technical analysis with Python (RSI, ROC, SMAs, etc.).
- Simple ranking and scoring models.
- Markdown and CSV report generation.
- Single-user macOS deployment.

### 3.2 Out of scope (v1)

- Multi-user auth system.
- Web dashboard UI (beyond optional local HTTP endpoints).
- Portfolio optimization and trade execution.
- Sophisticated event study infrastructure.

---

## 4. Intended Users

### 4.1 Profile

- Advanced technical user (e.g., IT infrastructure/DevOps/quant-minded engineer).
- Comfortable with macOS, Python, shell scripting.
- Familiar with financial markets and factor-based investing.
- Wants transparent, local, reproducible analytics.

### 4.2 Main Use Cases

- Ad‑hoc research: "Find large‑cap value names near 52‑week lows."
- Momentum scans: "Top 10 5‑day performers with trend confirmation."
- Periodic (nightly/weekly) refreshed screens and reports.
- Potential future backtests of specific screens.

---

## 5. System Overview

### 5.1 Layered architecture

- **Data Ingestion Layer**
   - Fetches symbol metadata, price history, and fundamentals from data providers.
   - Normalizes and writes data into a local analytical DB.

- **Storage Layer (DuckDB)**
   - Persists normalized tables: tickers, daily_prices, fundamentals, corporate_actions, screen_runs.
   - Provides SQL interface for screening and historical queries.

- **Computation Layer (Python)**
   - Uses Pandas + technical analysis libraries to compute indicators and scores.
   - Reads/writes CSVs and Parquet files in a shared workspace.

- **Agent Orchestration Layer**
   - LLM-based agent (local or remote model).
   - Uses tool-calling to invoke SQL and Python tools with strict rules.
   - Maintains a workflow over multiple tool calls.

- **Presentation Layer**
   - Generates Markdown research reports.
   - Exposes CSV outputs.
   - Optionally renders HTML/PDF.

### 5.2 Architectural principle

- **SQL = Universe filtering + simple statistics.**
- **Python = Technical indicators + scoring + report assembly.**

---

## 6. Platform Requirements

### 6.1 Hardware

**Minimum**

- Apple Silicon Mac (M1+).
- 16 GB RAM.
- 100 GB free disk.

**Recommended**

- 32+ GB RAM.
- 500 GB SSD free disk.
- Wired or stable Wi‑Fi for data ingestion.

### 6.2 OS and tooling

- macOS 13+ (14+ recommended).
- Python 3.11+.
- `virtualenv` or `uv` for environment management.

### 6.3 Core components

- **Database:** DuckDB (`market_data.duckdb` in `~/FinanceAgent/data/`).
- **Agent runtime:** OpenClaw-style framework, LangGraph, or Open Interpreter with:
  - Tool registration.
  - Persistent state/call graph.
  - File visibility controls.
- **Local model (optional):** LM Studio / Ollama with OpenAI-compatible API.

---

## 7. Technology Stack

### 7.1 Database: DuckDB

**Reasons:**

- In-process, no external DB server.
- Columnar OLAP engine: ideal for analytics.
- Excellent performance on Apple Silicon.
- Native integration with Pandas and Parquet.

### 7.2 Python Libraries

**Core**

- `duckdb`
- `pandas`, `numpy`, `pyarrow`
- `pydantic`
- `requests`, `tenacity`
- `ta` or `pandas-ta` (technical indicators)
- `jinja2` (templated reports)
- `markdown` (optional HTML rendering)
- `loguru` or `logging`
- `pytest` (tests)

**Optional**

- `yfinance` for prototyping data ingestion.
- Vendor SDKs for production data (Polygon, Tiingo, FMP, etc.).
- `matplotlib` / `plotly` for charts.
- `fastapi` + `uvicorn` for HTTP APIs.

### 7.3 Agent / Orchestrator

- Any framework that supports:
  - Callables / tools.
  - Simple JSON tool schemas.
  - System-level prompts.
  - Persistence across calls.

---

## 8. Data Model

### 8.1 Core Tables

#### 8.1.1 `tickers`

```sql
CREATE TABLE tickers (
    symbol VARCHAR PRIMARY KEY,
    company_name VARCHAR NOT NULL,
    exchange VARCHAR,
    country VARCHAR,
    currency VARCHAR,
    asset_type VARCHAR,  -- e.g., 'Common Stock', 'ETF'
    sector VARCHAR,
    industry VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    cik VARCHAR,
    figi VARCHAR,
    cusip VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 8.1.2 `daily_prices`

```sql
CREATE TABLE daily_prices (
    symbol VARCHAR NOT NULL,
    trade_date DATE NOT NULL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    adj_close DOUBLE,
    volume BIGINT,
    vwap DOUBLE,
    PRIMARY KEY (symbol, trade_date)
);
```

#### 8.1.3 `fundamentals_snapshot`

```sql
CREATE TABLE fundamentals_snapshot (
    symbol VARCHAR NOT NULL,
    snapshot_date DATE NOT NULL,
    market_cap BIGINT,
    shares_outstanding BIGINT,
    enterprise_value BIGINT,
    pe_ttm DOUBLE,
    pe_forward DOUBLE,
    eps_ttm DOUBLE,
    dividend_yield DOUBLE,
    price_to_book DOUBLE,
    price_to_sales_ttm DOUBLE,
    ev_to_ebitda_ttm DOUBLE,
    roe_ttm DOUBLE,
    roa_ttm DOUBLE,
    debt_to_equity DOUBLE,
    gross_margin_ttm DOUBLE,
    operating_margin_ttm DOUBLE,
    net_margin_ttm DOUBLE,
    revenue_ttm DOUBLE,
    ebitda_ttm DOUBLE,
    free_cash_flow_ttm DOUBLE,
    PRIMARY KEY (symbol, snapshot_date)
);
```

#### 8.1.4 `corporate_actions`

```sql
CREATE TABLE corporate_actions (
    symbol VARCHAR NOT NULL,
    action_date DATE NOT NULL,
    action_type VARCHAR NOT NULL,  -- 'split', 'dividend', 'spin-off', etc.
    action_value DOUBLE,
    notes VARCHAR,
    PRIMARY KEY (symbol, action_date, action_type)
);
```

#### 8.1.5 `screen_runs`

```sql
CREATE TABLE screen_runs (
    run_id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    user_prompt VARCHAR NOT NULL,
    sql_text VARCHAR,
    output_file VARCHAR,
    row_count INTEGER,
    status VARCHAR,       -- 'success', 'error'
    error_text VARCHAR
);
```

### 8.2 Derived Views

#### 8.2.1 `latest_prices`

```sql
CREATE VIEW latest_prices AS
SELECT *
FROM daily_prices
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY symbol
    ORDER BY trade_date DESC
) = 1;
```

#### 8.2.2 `avg_volume_30d`

```sql
CREATE VIEW avg_volume_30d AS
SELECT symbol, AVG(volume) AS avg_volume_30d
FROM (
    SELECT
        symbol,
        trade_date,
        volume,
        ROW_NUMBER() OVER (
            PARTITION BY symbol
            ORDER BY trade_date DESC
        ) AS rn
    FROM daily_prices
) t
WHERE rn <= 30
GROUP BY symbol;
```

#### 8.2.3 `fifty_two_week_range`

```sql
CREATE VIEW fifty_two_week_range AS
SELECT
    symbol,
    MIN(low) AS low_52w,
    MAX(high) AS high_52w
FROM (
    SELECT
        symbol,
        trade_date,
        low,
        high,
        ROW_NUMBER() OVER (
            PARTITION BY symbol
            ORDER BY trade_date DESC
        ) AS rn
    FROM daily_prices
) t
WHERE rn <= 252
GROUP BY symbol;
```

---

## 9. Data Ingestion Specification

### 9.1 Sources

**Prototype**

- `yfinance` for symbol lists and price history.
- Simple web APIs for fundamentals.

**Production-ready (later)**

- Polygon.io
- Tiingo
- Financial Modeling Prep
- Alpha Vantage
- Twelve Data

### 9.2 Ingestion cadence

- Symbol master: daily.
- EOD prices: daily after market close.
- Fundamentals snapshot: daily or as updated by provider.
- Corporate actions: daily.

### 9.3 Workflow

- Pull latest symbol master.
- Identify new/retired symbols.
- Fetch EOD prices for new days.
- Fetch/update fundamentals snapshot.
- Normalize into canonical schemas.
- Validate data quality.
- Insert or merge into DuckDB.
- Log ingestion run.

### 9.4 Validation rules

- No duplicate `(symbol, trade_date)` in `daily_prices`.
- Volume ≥ 0.
- High ≥ low.
- No obviously broken prices (e.g., zero or negative where not allowed).
- Fundamentals numeric fields non-negative when expected.

### 9.5 Failure handling

- Retries using `tenacity` for transient network errors.
- Skip failed symbols, log them for later reprocessing.
- Do not corrupt production DB; use staging tables or transactional inserts.

---

## 10. Tools (Agent "Skills")

### 10.1 Tool A: `finance_analyst_sql` (SQL Screening Tool)

**Purpose**
Generate SQL from natural-language screening requests, run it on the local DuckDB, and persist results to CSV.

**Input schema (conceptual)**

```json

  "title": "US large-cap value screen",
  "query_intent": "U.S.-listed common stocks, market cap > 10B, price > 5, avg volume 30d > 500k, within 10% of 52w low, trailing PE <= 10, exclude ETFs and preferreds.",
  "output_filename": "value_screen_20260314.csv"

```

**Output schema (conceptual)**

```json

  "status": "success",
  "row_count": 42,
  "output_filename": "value_screen_20260314.csv",
  "columns": [
    "symbol",
    "company_name",
    "sector",
    "market_cap",
    "price",
    "low_52w",
    "pct_above_52w_low",
    "pe_ttm",
    "avg_volume_30d"
  ],
  "sql_text": "SELECT ...",
  "error": null

```

**Constraints & guardrails**

- Allow only safe SQL: `SELECT`, `WITH`, views if needed.
- Disallow `DROP`, `DELETE`, `UPDATE`, `INSERT` generated by the agent.
- Log all executed SQL.
- Enforce row limits for preview when not explicitly requesting full export.

### 10.2 Tool B: `finance_calculator` (Python Analytics Tool)

**Purpose**
Run Python code, typically to:

- Load CSV created by `finance_analyst_sql`.
- Fetch additional historical data from DuckDB.
- Compute technical indicators and scoring.
- Save enriched CSVs and Markdown reports.

**Input schema (conceptual)**

```json

  "code": "import pandas as pd\\n... # Python script body"

```

**Output schema (conceptual)**

```json

  "status": "success",
  "stdout": "Printed summary for user/agent context",
  "generated_files": [
    "momentum_top10_20260314.csv",
    "momentum_report_20260314.md"
  ],
  "error": null

```

**Requirements**

- Access to the same workspace paths as SQL tool.
- Access to DuckDB connection when necessary.
- No arbitrary network calls by default unless enabled.
- Respect workspace and file path restrictions.

### 10.3 Optional Tool C: `report_writer`

n be implemented inside Python or as a separate tool:

- Accepts dataframes (or CSV paths) and Jinja2 templates.
- Produces Markdown reports with consistent layouts.
- Handles sections for methodology, results, commentary, and risks.

---

## 11. Agent Prompt & Workflow Design

### 11.1 System prompt (example)

```text
You are a local quantitative financial analyst.

You have access to:
- A SQL screening tool (`finance_analyst_sql`) connected to a local DuckDB market database.
- A Python analytics tool (`finance_calculator`) that can read CSV files and query the same database.

Rules:
- Never fabricate financial values.
- For any universe-level question, first use SQL to screen / filter the universe.
- Use Python to compute technical indicators, rankings, and reports.
- Always save intermediate results (CSV and Markdown) in the workspace.
- Clearly state data limitations when applicable.
- If an operation fails, explain why and propose a fallback.
```

### 11.2 Reusable skill prompts

Create separate Markdown skill files, e.g.:

- `prompts/value_screening.md`
- `prompts/momentum_analysis.md`
- `prompts/technical_report.md`

ch defines:

- Specific objective.
- Required inputs (e.g., constraints).
- Mandatory tool sequence.
- Output format expectations.

---

## 12. Example Workflows

### 12.1 Value screen: low P/E near 52-week lows

**User query**
"Find U.S. large-cap stocks trading within 10% of their 52-week lows with trailing P/E ≤ 10 and 30‑day avg volume > 500K."

**Steps**

- **Agent → SQL Tool**
   Generate and run SQL; save to `value_screen_YYYYMMDD.csv`.

- **SQL example**

```sql
WITH latest_fund AS (
    SELECT *
    FROM fundamentals_snapshot
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY symbol
        ORDER BY snapshot_date DESC
    ) = 1
),
latest_px AS (
    SELECT *
    FROM daily_prices
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY symbol
        ORDER BY trade_date DESC
    ) = 1
),
vol30 AS (
    SELECT symbol, AVG(volume) AS avg_volume_30d
    FROM (
        SELECT
            symbol,
            trade_date,
            volume,
            ROW_NUMBER() OVER (
                PARTITION BY symbol
                ORDER BY trade_date DESC
            ) AS rn
        FROM daily_prices
    ) t
    WHERE rn <= 30
    GROUP BY symbol
),
range52 AS (
    SELECT symbol, MIN(low) AS low_52w
    FROM (
        SELECT
            symbol,
            trade_date,
            low,
            ROW_NUMBER() OVER (
                PARTITION BY symbol
                ORDER BY trade_date DESC
            ) AS rn
        FROM daily_prices
    ) t
    WHERE rn <= 252
    GROUP BY symbol
)
SELECT
    t.symbol,
    t.company_name,
    t.sector,
    f.market_cap,
    p.close AS price,
    r.low_52w,
    ((p.close - r.low_52w) / NULLIF(r.low_52w, 0)) * 100 AS pct_above_52w_low,
    f.pe_ttm,
    v.avg_volume_30d
FROM tickers t
JOIN latest_fund f ON t.symbol = f.symbol
JOIN latest_px p ON t.symbol = p.symbol
JOIN vol30 v ON t.symbol = v.symbol
JOIN range52 r ON t.symbol = r.symbol
WHERE
    t.asset_type = 'Common Stock'
    AND f.market_cap > 10000000000
    AND p.close > 5
    AND v.avg_volume_30d > 500000
    AND f.pe_ttm <= 10
    AND ((p.close - r.low_52w) / NULLIF(r.low_52w, 0)) <= 0.10
ORDER BY pct_above_52w_low ASC;
```

- **Agent → Python Tool**
   Enrich results with additional metrics, add risk tags, and output `value_report_YYYYMMDD.md`.

### 12.2 Momentum analysis: top 10 5‑day performers

**User query**
"Show top 10 U.S. large-cap stocks over the last 5 trading days with 14‑ and 21‑day ROC, 14‑day RSI, and trend vs 20/50/200‑day MAs."

**Steps**

- **SQL Tool**
   Optionally pre-filter large-cap universe and recent history.

- **Python Tool**

```python
import pandas as pd
import duckdb

con = duckdb.connect("market_data.duckdb")

prices = con.execute("""
    SELECT symbol, trade_date, adj_close, volume
    FROM daily_prices
    WHERE trade_date >= CURRENT_DATE - INTERVAL 400 DAY
""").df()

prices = prices.sort_values(["symbol", "trade_date"])

f add_indicators(df):
    df = df.copy()
    df["return_5d"] = df["adj_close"].pct_change(5) * 100
    df["roc_14d"] = df["adj_close"].pct_change(14) * 100
    df["roc_21d"] = df["adj_close"].pct_change(21) * 100
    df["sma_20d"] = df["adj_close"].rolling(20).mean()
    df["sma_50d"] = df["adj_close"].rolling(50).mean()
    df["sma_200d"] = df["adj_close"].rolling(200).mean()

    delta = df["adj_close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss
    df["rsi_14d"] = 100 - (100 / (1 + rs))
    return df

out = prices.groupby("symbol", group_keys=False).apply(add_indicators)
latest = out.groupby("symbol").tail(1)

top10 = latest.sort_values("return_5d", ascending=False).head(10)
top10.to_csv("momentum_top10_YYYYMMDD.csv", index=False)
```

- Agent uses this data to produce a Markdown report with signal interpretation and risk commentary.

---

## 13. Indicator & Scoring Rules

### 13.1 RSI Interpretation (14‑day)

- ≥ 70: overbought.
- ≤ 30: oversold.
- 50–70: bullish-neutral.
- 30–50: bearish-neutral.

### 13.2 Trend validation using SMAs

- Strong uptrend: `price > sma_20 > sma_50 > sma_200`.
- Uptrend: `price > sma_50` and `price > sma_200`.
- Repair/bounce: `price < sma_20` but `price > sma_200`.
- Downtrend: `price < sma_50` and `price < sma_200`.

### 13.3 Short-term continuation score (example heuristic)

```text
score =
  2 if return_5d > 0
+ 1 if roc_14d > 0
+ 1 if roc_21d > 0
+ 1 if 50 <= rsi_14d <= 68
+ 1 if price > sma_20d
+ 1 if price > sma_50d
+ 1 if price > sma_200d
```

Interpretation:

- 7–8: strong continuation bias.
- 5–6: moderate continuation bias.
- 3–4: mixed, likely consolidation.
- 0–2: weak/contrarian setup; elevated downside risk.

---

## 14. Output Specification

### 14.1 Report content

Every report must include:

- Title and generation timestamp.
- Universe and filters.
- Data "as‑of" date.
- Methodology summary.
- Ranked table of results.
- Interpretation narrative.
- Risk considerations.
- File lineage (which CSVs and DB snapshot used).

### 14.2 Markdown template (skeleton)

```markdown
# [Screen Type] Report

**Generated:** 2026‑03‑14 16:00 local
**Universe:** [description]
**Data as-of:** [date/time]

## Methodology

[Short description of filters, indicators, and ranking.]

## Results

| Symbol | Name | Sector | Key Metrics... |
|--------|------|--------|----------------|

## Interpretation

[Summarize themes, show notable stocks, link value vs momentum, etc.]

## Risks and Limitations

- Data coverage notes.
- Provider-specific caveats.
- Technical indicator caveats.

## Files and Lineage

- Input: `[value_screen_YYYYMMDD.csv]`
- Input: `market_data.duckdb` snapshot timestamp
- Output: `[value_report_YYYYMMDD.md]`
```

### 14.3 File naming conventions

- Screens: `value_screen_YYYYMMDD.csv`, `momentum_screen_YYYYMMDD.csv`.
- Reports: `value_report_YYYYMMDD.md`, `momentum_report_YYYYMMDD.md`.
- Logs: `run_<uuid>.jsonl`, `ingestion_YYYYMMDD.log`.

---

## 15. Security & Privacy

### 15.1 Local-first defaults

- No external API calls unless configured.
- Data stored only under `~/FinanceAgent/`.
- No remote logging of queries unless explicitly configured.

### 15.2 Secrets management

- Use macOS Keychain or `.env` with restricted permissions for API keys.
- Keep provider credentials out of code.

### 15.3 Workspace restrictions

- Agent tools can only read/write under:
  - `~/FinanceAgent/data`
  - `~/FinanceAgent/workspace`
  - `~/FinanceAgent/logs`

### 15.4 Code & SQL safety

- Restrict SQL to read-only (SELECT/CTE).
- Restrict Python code to allowed modules and paths.
- Disallow shell execution by default.

---

## 16. Observability & Logging

### 16.1 Logging categories

- Data ingestion.
- SQL screening.
- Python analytics.
- Report generation.
- Agent decisions and errors.

### 16.2 Log schema (example JSON line)

```json

  "timestamp": "2026-03-14T16:05:12Z",
  "level": "INFO",
  "component": "sql_screen",
  "run_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_prompt": "Find U.S. large-cap value stocks...",
  "sql_text": "SELECT ...",
  "row_count": 37,
  "status": "success"

```

### 16.3 Retention

- Keep logs for at least 90 days by default.
- Use rotating file handlers and size caps.

---

## 17. Testing Requirements

### 17.1 Unit tests

- SQL query builders (where applicable).
- Indicator functions (RSI, ROC, SMA).
- Scoring functions.
- Report generation templates.
- Data validation logic.

### 17.2 Integration tests

- Full value screening workflow.
- Full momentum analysis workflow.
- Ingestion pipeline (with mock provider).
- Failure scenarios and recovery.

### 17.3 Data quality tests

- Duplicate price rows detection.
- Nulls in critical fields (price, volume).
- Consistency between adjusted and unadjusted prices.
- Fundamental fields within reasonable ranges.

### 17.4 Acceptance criteria

- Nightly ingestion succeeds for 7 consecutive days.
- Value and momentum workflows run end‑to‑end without manual intervention.
- Outputs are reproducible from logged SQL + DB + code.
- No unbounded filesystem or network accesses.

---

## 18. Deployment Specification (macOS)

### 18.1 Directory layout

```text
~/FinanceAgent/
├── app/
│   ├── agent/
│   ├── tools/
│   ├── prompts/
│   ├── templates/
│   └── config/
├── data/
│   ├── raw/
│   ├── curated/
│   └── market_data.duckdb
├── workspace/
│   ├── reports/
│   ├── exports/
│   └── temp/
├── logs/
└── tests/
```

### 18.2 Environment setup

```bash
mkdir -p ~/FinanceAgent/app,data,workspace,logs,tests
 ~/FinanceAgent

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install duckdb pandas numpy pyarrow pydantic requests tenacity ta jinja2 markdown loguru pytest
```

### 18.3 Ingestion job

- Implement `app/ingestion/run_refresh.py`.
- Configure macOS `launchd` or `cron` to run once per day after market close.

### 18.4 Optional local API

Implement `app/main.py` (FastAPI):

- `/screen` – run preset/parametric screens.
- `/analyze` – trigger Python analytics.
- `/report` – return latest report(s).
- `/refresh` – trigger ingestion.
- `/health` – health checks.

---

## 19. Configuration

### 19.1 Example config (YAML)

```yaml
app:
  name: finance-agent
  environment: local
  timezone: America/Chicago

tabase:
  engine: duckdb
  path: ~/FinanceAgent/data/market_data.duckdb

workspace:
  root: ~/FinanceAgent/workspace
  reports: ~/FinanceAgent/workspace/reports
  exports: ~/FinanceAgent/workspace/exports
  temp: ~/FinanceAgent/workspace/temp

models:
  provider: lmstudio
  base_url: http://localhost:1234/v1
  model_name: local-reasoning-model

ingestion:
  enabled: true
  schedule: "0 18 * * 1-5"
  price_provider: prototype
  fundamentals_provider: prototype

security:
  allow_shell: false
  allow_external_network: false
  approved_paths:
    - ~/FinanceAgent/data
    - ~/FinanceAgent/workspace
    - ~/FinanceAgent/logs
```

---

## 20. Implementation Roadmap

### Phase 1 – Foundation

- Repo + directory layout.
- DuckDB creation and schema.
- Minimal ingestion from prototype provider.

### Phase 2 – Screening

- Implement `finance_analyst_sql` tool.
- Unit tests for SQL generation.
- Manual CLI tests of screens.

### Phase 3 – Analytics

- Implement `finance_calculator` tool.
- Technical indicator functions and scoring.
- CSV + Markdown outputs.

### Phase 4 – Agent Integration

- Wire tools into chosen agent framework.
- Implement system + skill prompts.
- Test end‑to‑end screen → analyze → report flows.

### Phase 5 – Hardening

- Logging and monitoring.
- Error handling and retries.
- Data quality checks.
- Configuration cleanup.

### Phase 6 – Enhancements

- Basic backtesting of screens (monthly snapshots).
- Watchlist and recurring reports.
- HTML/PDF exports.
- Sector/benchmark-relative metrics.

---

## 21. Risks and Mitigations

| Risk | Description | Mitigation |
|------|-------------|-----------|
| Data quality | Inconsistent or delayed data from providers | Validation, multi-provider fallback, data freshness checks |
| LLM hallucination | Agent invents metrics or SQL | Strict prompts, tool-first policies, SQL validation, unit tests |
| Security | Arbitrary code or file access | Path sandboxing, restricted Python environment, no shell by default |
| Performance | Large universes and long histories | DuckDB, Parquet, and bounded lookbacks for indicators |
| Reproducibility | Ad‑hoc changes invisible | Logging of SQL, inputs, and outputs; pinned versions |
| Symbol lifecycle | Ticker changes, delistings | Reference tables with `is_active`, CIK/FIGI tracing |

---

## 22. Definition of Done (v1)

- Nightly ingestion stable and logged.
- Value screen and momentum analysis working end‑to‑end via agent.
- Reports generated in Markdown and CSV with clear methodology and risks.
- System runs fully local on macOS with no manual steps beyond initial configuration.
- Outputs traceable to data and SQL; calculations test‑covered.

---

## 23. Appendix A: Recommended MVP Repository Structure

```text
finance-agent/
├── README.md
├── pyproject.toml
├── .env.example
├── app/
│   ├── main.py
│   ├── config.py
│   ├── db.py
│   ├── models.py
│   ├── ingestion/
│   │   ├── prices.py
│   │   ├── fundamentals.py
│   │   └── reference.py
│   ├── tools/
│   │   ├── sql_screen.py
│   │   ├── python_analyze.py
│   │   └── report_writer.py
│   ├── prompts/
│   │   ├── system_prompt.md
│   │   ├── stock_screening.md
│   │   └── momentum_analysis.md
│   └── templates/
│       └── report.md.j2
├── data/
├── workspace/
├── logs/
└── tests/
```

---

## 24. Appendix B: Initial MVP Commands

```bash
# initialize
mkdir -p ~/FinanceAgent/app,data,workspace,logs,tests
 ~/FinanceAgent

# create env
python3 -m venv .venv
source .venv/bin/activate

# install packages
pip install duckdb pandas numpy pyarrow pydantic requests tenacity ta jinja2 fastapi uvicorn pytest

# create database bootstrap
python app/bootstrap_db.py

# run ingestion
python app/ingestion/run_refresh.py

# run local API
uvicorn app.main:app --reload

# run sample screen
python app/tools/run_sample_value_screen.py
```

---

## 25. Appendix C: DuckDB Database Bootstrap Script

```python
import duckdb

con = duckdb.connect("~/FinanceAgent/data/market_data.duckdb")

con.execute("""
CREATE TABLE IF NOT EXISTS tickers (
    symbol VARCHAR PRIMARY KEY,
    company_name VARCHAR NOT NULL,
    exchange VARCHAR,
    country VARCHAR,
    currency VARCHAR,
    asset_type VARCHAR,
    sector VARCHAR,
    industry VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    cik VARCHAR,
    figi VARCHAR,
    cusip VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

con.execute("""
CREATE TABLE IF NOT EXISTS daily_prices (
    symbol VARCHAR NOT NULL,
    trade_date DATE NOT NULL,
    open DOUBLE,
    high DOUBLE,
    low DOUBLE,
    close DOUBLE,
    adj_close DOUBLE,
    volume BIGINT,
    vwap DOUBLE,
    PRIMARY KEY (symbol, trade_date)
);
""")

con.execute("""
CREATE TABLE IF NOT EXISTS fundamentals_snapshot (
    symbol VARCHAR NOT NULL,
    snapshot_date DATE NOT NULL,
    market_cap BIGINT,
    shares_outstanding BIGINT,
    enterprise_value BIGINT,
    pe_ttm DOUBLE,
    pe_forward DOUBLE,
    eps_ttm DOUBLE,
    dividend_yield DOUBLE,
    price_to_book DOUBLE,
    price_to_sales_ttm DOUBLE,
    ev_to_ebitda_ttm DOUBLE,
    roe_ttm DOUBLE,
    roa_ttm DOUBLE,
    debt_to_equity DOUBLE,
    gross_margin_ttm DOUBLE,
    operating_margin_ttm DOUBLE,
    net_margin_ttm DOUBLE,
    revenue_ttm DOUBLE,
    ebitda_ttm DOUBLE,
    free_cash_flow_ttm DOUBLE,
    PRIMARY KEY (symbol, snapshot_date)
);
""")

con.execute("""
CREATE TABLE IF NOT EXISTS corporate_actions (
    symbol VARCHAR NOT NULL,
    action_date DATE NOT NULL,
    action_type VARCHAR NOT NULL,
    action_value DOUBLE,
    notes VARCHAR,
    PRIMARY KEY (symbol, action_date, action_type)
);
""")

con.execute("""
CREATE TABLE IF NOT EXISTS screen_runs (
    run_id VARCHAR PRIMARY KEY,
    created_at TIMESTAMP NOT NULL,
    user_prompt VARCHAR NOT NULL,
    sql_text VARCHAR,
    output_file VARCHAR,
    row_count INTEGER,
    status VARCHAR,
    error_text VARCHAR
);
""")

con.close()
print("Database schema created successfully.")
```

---

## 26. Appendix D: Sample System Prompt for Agent

```markdown
# Role
You are a local quantitative financial analyst with access to a SQL database of U.S. equity market data and a Python computation environment.

# Tools
- `finance_analyst_sql` – Query the local DuckDB database to screen stocks by fundamental and technical filters.
- `finance_calculator` – Run Python code to compute technical indicators, rank stocks, and generate reports.

# Workflow
- For any broad universe question, first use SQL to narrow the universe to relevant stocks.
- Save SQL results to a CSV file in the workspace.
- Use Python to load that CSV, compute additional metrics (RSI, ROC, SMAs, etc.), and generate reports.
- Always document your methodology in the report.
- Never fabricate data; only use actual query results.

# Output
- Generate Markdown reports with tables, interpretations, and risk assessments.
- Save all outputs to the workspace with timestamped filenames.
```

---

## 27. Approval and Sign-Off

This document represents a complete technical specification for building a local AI financial analyst system on macOS. It is ready for implementation following the phased roadmap outlined in Section 20.

**Prepared by:** AI Financial Systems Architect
**Reviewed by:** [Your Name / Team]
**Approved by:** [Your Name / Team Lead]
**Date:** 2026-03-14

---
