# US Market Data Support Design & Architecture

## 1. Executive Summary

This document outlines the design for adding US stock market data support across the investment system portfolio: **ai-investment-advisor (AIA)**, **daily_stock_analysis (DSA)**, and **Unified-Investment-System (UIS)**.

**Core Objective:** Enable tracking and analysis of US stocks (e.g., AAPL, NVDA) and ETFs (e.g., IEF, TLT) for holdings, profit, and allocation calculations.

**Phased Approach:**

| Phase | Scope | Goal |
|-------|-------|------|
| **Phase 1** | Basic Data Flow | US holdings data flows through AIA/DSA → UIS for allocation tracking |
| **Phase 2** | Full Analysis | AIA supports `/analyze` and `/committee` for US stocks |

**Key Principles:**

* **Sub-system Independence:** Each system (PIS, DSA, AIA) operates independently; don't break existing functionality
* **Currency Simplicity:** Each system outputs local currency (USD for US assets); UIS handles consolidation
* **Minimal Complexity:** Keep changes simple; more features will be added later
* **Upstream Compatibility:** Minimize diff footprint for easier upstream merges

---

## 2. System Architecture

### 2.1 Data Flow Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                                 │
├─────────────────────────────────────────────────────────────────────┤
│  CN Markets          │  US Markets           │  Currency            │
│  ├── AKShare         │  ├── Finnhub (Primary)│  ├── UIS Currency    │
│  └── Tushare         │  └── yfinance (Fallback)│ │   Converter       │
│                      │                       │  └── Fallback: 7.25  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SUB-SYSTEMS (Independent)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │      AIA        │  │      DSA        │  │      PIS        │      │
│  │                 │  │                 │  │                 │      │
│  │ Holdings.md     │  │ FinnhubFetcher  │  │ Transactions    │      │
│  │ (美股持仓)      │  │ YfinanceFetcher │  │ Holdings        │      │
│  │                 │  │                 │  │                 │      │
│  │ Output: JSON    │  │ Output: DataFrame│ │ Output: SQLite  │      │
│  │ (USD prices)    │  │ (USD prices)    │  │ (mixed currency)│      │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘      │
│           │                    │                    │                │
└───────────┼────────────────────┼────────────────────┼────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    UIS (Consolidation Layer)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │ Identity Layer  │  │ Currency Layer  │  │ Sync Layer      │      │
│  │                 │  │                 │  │                 │      │
│  │ US_STK_AAPL     │  │ USD→CNY @ sync  │  │ Canonical IDs   │      │
│  │ RSU_RSU_AMZN    │  │ Google Finance  │  │ FIFO cost basis │      │
│  │                 │  │ Fallback: 7.25  │  │                 │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
│                                                                      │
│  Output: Unified holdings, allocations, performance in CNY          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Asset ID Conventions

| Asset Type | Example Input | Canonical ID | Currency |
|------------|---------------|--------------|----------|
| US Stock | `AAPL` | `US_STK_AAPL` | USD |
| US ETF | `IEF` | `US_STK_IEF` | USD |
| RSU | `RSU_AMZN` | `RSU_RSU_AMZN` | USD |
| CN Stock | `600519` | `CN_STK_600519` | CNY |
| HK Stock | `00700` | `HK_STK_00700` | HKD |

---

## 3. Phase 1: Basic Data Flow (MVP)

**Goal:** US holdings appear in UIS allocation reports with correct market values in CNY.

### 3.1 Scope

| System | Changes | Output |
|--------|---------|--------|
| **AIA** | Parse `## 美股持仓`, fetch prices via Finnhub/yfinance | `us_holdings` in JSON (USD) |
| **DSA** | Add FinnhubFetcher, update YfinanceFetcher for US codes | OHLCV DataFrame (USD) |
| **UIS** | No code changes needed | Already supports US_STK_ prefix |

### 3.2 AIA Phase 1 Implementation

**New File:** `scripts/us_market.py`

```python
# Minimal module for US market data
def fetch_us_stock_data(holdings: list, api_key: str) -> list:
    """Fetch US stock prices via Finnhub, fallback to yfinance."""
    pass

def parse_rsu_ticker(code: str) -> str:
    """Extract ticker from RSU_AMZN -> AMZN."""
    pass
```

**Modified File:** `scripts/fetch_market_data.py`

```python
# Add to MODULES config
MODULES = {
    # ... existing ...
    "us_holdings": True,  # NEW
}

# Add to main()
if MODULES["us_holdings"]:
    from us_market import fetch_us_stock_data
    result["us_holdings"] = fetch_us_stock_data(holdings_us, api_key)
```

**Output Format:**
```json
{
  "us_holdings": [
    {
      "code": "AAPL",
      "name": "Apple Inc",
      "market": "US",
      "currency": "USD",
      "price": 185.92,
      "change_pct": 1.23,
      "cost": 150.00,
      "quantity": 100,
      "market_value_usd": 18592.00
    }
  ]
}
```

### 3.3 DSA Phase 1 Implementation

**New File:** `data_provider/finnhub_fetcher.py`

```python
class FinnhubFetcher(BaseFetcher):
    name = "FinnhubFetcher"
    priority = 1  # High priority for US stocks

    def _fetch_raw_data(self, stock_code, start_date, end_date):
        # Finnhub candles endpoint
        pass

    def _normalize_data(self, df, stock_code):
        # Map to standard columns
        pass
```

**Modified File:** `data_provider/yfinance_fetcher.py`

```python
def _convert_stock_code(self, code: str) -> str:
    # Existing: CN stock suffix logic
    # NEW: If 1-5 uppercase letters, return as-is (US stock)
    if re.match(r'^[A-Z]{1,5}$', code):
        return code  # US stock, no suffix
    # ... existing CN logic ...
```

### 3.4 UIS Phase 1 Implementation

**No code changes required.** The existing pipeline already:
- Has `US_STK_` normalization rule in `config/asset_id_rules.yaml`
- Converts USD to CNY via `CurrencyConverterService`
- Stores `original_currency` and `amount_cny` in holdings

**Verification only:** Ensure AIA JSON output is consumed by sync.

---

## 4. Phase 2: Full Analysis (AIA Enhancement)

**Goal:** `/analyze` and `/committee` skills work for US stocks with market-appropriate indicators.

### 4.1 Scope

| Component | CN Version | US Version |
|-----------|------------|------------|
| Macro benchmark | HS300 | S&P 500 (SPY) |
| Sentiment indicator | 北向资金 | VIX |
| Sector ranking | 板块/概念 | S&P 500 sectors (XLK, XLF, etc.) |
| News source | 财联社 | Finnhub news API |
| Technical indicators | MA/RSI/MACD | Same (universal) |

### 4.2 New Functions in `scripts/us_market.py`

```python
def fetch_us_macro() -> dict:
    """Fetch S&P 500, VIX, sector ETF performance."""
    pass

def fetch_us_sectors() -> list:
    """Fetch XLK, XLF, XLV, XLE, etc. vs SPY."""
    pass

def fetch_us_news(symbols: list) -> list:
    """Fetch news from Finnhub for given symbols."""
    pass
```

### 4.3 Skill Updates

**`/analyze` skill:**
- Add US market detection
- Swap macro framework: HS300 → SPY, 北向 → VIX
- Keep scoring structure (20/20/60)

**`/committee` skill:**
- Add US data field mappings in opinion template
- Same 3-model consensus workflow

**`/scan` skill:**
- Add US sector scanning (XLK, XLF, XLV rankings)
- Replace 北向资金 with VIX interpretation

### 4.4 Phase 2 Prerequisites

- Phase 1 complete and tested
- User confirms need for US analysis
- Finnhub API rate limits acceptable (60/min free)

---

## 5. Data Source Strategy

### 5.1 Priority Order

| Priority | Source | Use Case | Rate Limit |
|----------|--------|----------|------------|
| 1 | Finnhub | US real-time quotes, news | 60/min (free) |
| 2 | yfinance | US historical OHLCV, fallback | No limit |
| 3 | AKShare | CN markets, USD/CNY rate | No limit |

### 5.2 Failover Logic

```
fetch_us_quote(symbol):
    try:
        return finnhub.quote(symbol)
    except (RateLimitError, APIError):
        return yfinance.download(symbol, period="1d")
```

### 5.3 RSU Handling

```python
def parse_rsu_ticker(code: str) -> tuple[str, bool]:
    """
    Parse RSU code to extract ticker.

    Returns: (ticker, is_rsu)
    Examples:
        "RSU_AMZN" -> ("AMZN", True)
        "AAPL" -> ("AAPL", False)
    """
    if code.startswith("RSU_"):
        return code[4:], True
    return code, False
```

---

## 6. Upstream Sync Strategy

### 6.1 File Organization (Minimize Conflicts)

| System | Strategy | Risk Level |
|--------|----------|------------|
| **AIA** | New file `scripts/us_market.py`, minimal changes to main script | Low |
| **DSA** | New file `data_provider/finnhub_fetcher.py`, small manager update | Low |
| **UIS** | No changes needed | None |

### 6.2 Sync Skill Update

Add post-merge verification to `/sync-upstream`:

```markdown
## Post-Merge Checklist (US Market Features)

- [ ] `.env` contains `FINNHUB_API_KEY`
- [ ] `scripts/us_market.py` exists and imports work
- [ ] `data_provider/finnhub_fetcher.py` exists
- [ ] Run: `python scripts/fetch_market_data.py --test-us AAPL`
- [ ] Verify JSON output contains `us_holdings` array
```

---

## 7. Testing Strategy

### 7.1 Phase 1 Verification

| Test | Command | Expected |
|------|---------|----------|
| AIA US fetch | `python scripts/fetch_market_data.py` | JSON has `us_holdings` with AAPL price |
| DSA US fetch | `python -c "from data_provider import FinnhubFetcher; ..."` | DataFrame with OHLCV for AAPL |
| UIS sync | `python main.py --sync-v3` | Holdings include `US_STK_AAPL` |
| UIS allocation | Check allocation report | US Equity appears with CNY values |

### 7.2 Phase 2 Verification

| Test | Command | Expected |
|------|---------|----------|
| Analyze US stock | `/analyze NVDA` | Full report with SPY benchmark, VIX sentiment |
| Committee US | `/committee` with US holdings | 3-model consensus on US positions |
| Scan US sectors | `/scan` | Recommendations include XLK/XLF sectors |

---

## 8. Implementation Plans

Detailed task-by-task implementation plans are in:

| System | Plan Location |
|--------|---------------|
| AIA | `docs/plans/2026-01-24-aia-us-market-plan.md` |
| DSA | `docs/plans/2026-01-24-dsa-us-market-plan.md` |
| UIS | `docs/plans/2026-01-24-uis-us-market-plan.md` |

Each plan follows TDD with verification gates between tasks.

---

## 9. Rollout Sequence

```
Week 1: Phase 1
├── Day 1-2: DSA FinnhubFetcher + YfinanceFetcher update
├── Day 3-4: AIA us_market.py + fetch_market_data.py integration
├── Day 5: UIS verification + end-to-end test
└── Day 5: Update sync-upstream skill

Week 2+: Phase 2 (if approved)
├── AIA macro/sector/news functions
├── Skill prompt updates
└── Full analysis testing
```

---

*Document Version: 2.0*
*Created: 2026-01-24*
*Updated: 2026-01-24 - Added phased approach, simplified currency handling*
