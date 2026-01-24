# AIA US Market Data Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add US stock/ETF data fetching to AIA's fetch_market_data.py, enabling `us_holdings` in JSON output for UIS consumption.

**Architecture:** Create new `scripts/us_market.py` module with minimal footprint. Add `## 美股持仓` parsing to fetch_market_data.py. Keep changes isolated for upstream sync compatibility.

**Tech Stack:** Python 3.9+, finnhub-python, yfinance, akshare (existing)

---

## Prerequisites

Before starting, ensure:

- [ ] Finnhub API key available
- [ ] `finnhub-python` and `yfinance` packages installed
- [ ] AIA project at `/Users/ray/Documents/projects/ai-investment-advisor`
- [ ] Holdings.md has `## 美股持仓` section (may exist already)

---

## Task 1: Add Dependencies and Configuration

**Files:**

- Modify: `/Users/ray/Documents/projects/ai-investment-advisor/.env`
- Modify: `/Users/ray/Documents/projects/ai-investment-advisor/requirements.txt` (if exists)

**Step 1: Check if requirements.txt exists**

Run:

```bash
cd /Users/ray/Documents/projects/ai-investment-advisor
ls -la requirements.txt 2>/dev/null || echo "No requirements.txt"
```

**Step 2: Install dependencies**

Run:

```bash
pip install finnhub-python yfinance
```

Expected: Successfully installed

**Step 3: Add FINNHUB_API_KEY to .env**

Create or update `.env`:

```bash
# US Market Data
FINNHUB_API_KEY=<your_key_here>
```

**Step 4: Verify configuration**

Run:

```bash
cd /Users/ray/Documents/projects/ai-investment-advisor
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('FINNHUB_API_KEY:', 'SET' if os.getenv('FINNHUB_API_KEY') else 'MISSING')"
```

Expected: `FINNHUB_API_KEY: SET`

**Step 5: Commit**

```bash
git add .env.example 2>/dev/null || true
git commit -m "config: add FINNHUB_API_KEY for US market data" --allow-empty
```

**GATE: Do not proceed until FINNHUB_API_KEY is SET**

---

## Task 2: Create us_market.py Test File

**Files:**

- Create: `/Users/ray/Documents/projects/ai-investment-advisor/scripts/test_us_market.py`

**Step 1: Write the test file**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for us_market.py - US Market Data Module
Run: python scripts/test_us_market.py
"""

import os
import sys

# Add scripts dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_parse_rsu_ticker():
    """Test RSU ticker parsing"""
    from us_market import parse_rsu_ticker

    # RSU codes
    ticker, is_rsu = parse_rsu_ticker("RSU_AMZN")
    assert ticker == "AMZN", f"Expected AMZN, got {ticker}"
    assert is_rsu == True, f"Expected True, got {is_rsu}"

    ticker, is_rsu = parse_rsu_ticker("RSU_GOOGL")
    assert ticker == "GOOGL", f"Expected GOOGL, got {ticker}"
    assert is_rsu == True

    # Regular codes
    ticker, is_rsu = parse_rsu_ticker("AAPL")
    assert ticker == "AAPL", f"Expected AAPL, got {ticker}"
    assert is_rsu == False, f"Expected False, got {is_rsu}"

    ticker, is_rsu = parse_rsu_ticker("NVDA")
    assert ticker == "NVDA"
    assert is_rsu == False

    print("✓ test_parse_rsu_ticker passed")


def test_is_us_ticker():
    """Test US ticker detection"""
    from us_market import is_us_ticker

    # Valid US tickers
    assert is_us_ticker("AAPL") == True
    assert is_us_ticker("NVDA") == True
    assert is_us_ticker("A") == True  # Single letter
    assert is_us_ticker("BRK.B") == True  # With dot

    # Invalid (CN codes)
    assert is_us_ticker("600519") == False
    assert is_us_ticker("000001") == False

    # Edge cases
    assert is_us_ticker("") == False
    assert is_us_ticker("ABCDEF") == False  # Too long

    print("✓ test_is_us_ticker passed")


def test_fetch_us_stock_quote():
    """Test fetching a single US stock quote"""
    from us_market import fetch_us_stock_quote

    # Skip if no API key
    if not os.getenv('FINNHUB_API_KEY'):
        print("⊘ test_fetch_us_stock_quote skipped (no API key)")
        return

    quote = fetch_us_stock_quote("AAPL")
    assert quote is not None, "Quote should not be None"
    assert "price" in quote, "Quote should have price"
    assert quote["price"] > 0, "Price should be positive"

    print(f"✓ test_fetch_us_stock_quote passed (AAPL: ${quote['price']})")


def test_fetch_us_stock_data():
    """Test fetching multiple US stocks"""
    from us_market import fetch_us_stock_data

    holdings = [
        {"code": "AAPL", "name": "Apple", "cost": 150.0, "qty": 10, "buy_date": "2024-01-01"},
        {"code": "RSU_AMZN", "name": "Amazon RSU", "cost": 0, "qty": 50, "buy_date": "2023-06-01"},
    ]

    results = fetch_us_stock_data(holdings)

    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    assert results[0]["code"] == "AAPL"
    assert results[0]["market"] == "US"
    assert results[0]["currency"] == "USD"

    # RSU should keep original code but have price
    assert results[1]["code"] == "RSU_AMZN"
    assert results[1]["is_rsu"] == True

    print(f"✓ test_fetch_us_stock_data passed ({len(results)} holdings)")


def run_all_tests():
    """Run all tests"""
    from dotenv import load_dotenv
    load_dotenv()

    print("Running us_market.py tests...\n")

    try:
        test_parse_rsu_ticker()
        test_is_us_ticker()
        test_fetch_us_stock_quote()
        test_fetch_us_stock_data()
        print("\n✓ All tests passed!")
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        print("Make sure us_market.py exists in scripts/")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
```

**Step 2: Run test to verify it fails (module not found)**

Run:

```bash
cd /Users/ray/Documents/projects/ai-investment-advisor
python scripts/test_us_market.py
```

Expected: `Import error: No module named 'us_market'`

**Step 3: Commit test file**

```bash
git add scripts/test_us_market.py
git commit -m "test: add us_market.py tests (TDD)"
```

**GATE: Do not proceed until tests fail with import error**

---

## Task 3: Implement us_market.py

**Files:**

- Create: `/Users/ray/Documents/projects/ai-investment-advisor/scripts/us_market.py`

**Step 1: Write the us_market.py implementation**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US Market Data Module for AI Investment Advisor

Fetches US stock/ETF prices via Finnhub (primary) or yfinance (fallback).
Designed for minimal footprint to ease upstream sync.

Usage:
    from us_market import fetch_us_stock_data, parse_rsu_ticker

Output format matches existing holdings structure with additional fields:
    - market: "US"
    - currency: "USD"
    - is_rsu: True/False
"""

import os
import re
import sys
import logging
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime

# Setup logging to stderr (consistent with fetch_market_data.py)
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)


def log(msg: str):
    """Output log to stderr, consistent with fetch_market_data.py"""
    print(msg, file=sys.stderr)


# US ticker pattern: 1-5 uppercase letters, optional .X suffix (BRK.B)
US_TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}(\.[A-Z])?$')


def parse_rsu_ticker(code: str) -> Tuple[str, bool]:
    """
    Parse RSU code to extract underlying ticker.

    Args:
        code: Stock code, e.g., "RSU_AMZN" or "AAPL"

    Returns:
        Tuple of (ticker, is_rsu)
        Examples:
            "RSU_AMZN" -> ("AMZN", True)
            "AAPL" -> ("AAPL", False)
    """
    if code.startswith("RSU_"):
        return code[4:], True
    return code, False


def is_us_ticker(code: str) -> bool:
    """
    Check if code is a US stock ticker.

    US tickers: 1-5 uppercase letters, optional dot suffix
    CN tickers: 6 digits

    Args:
        code: Stock code to check

    Returns:
        True if US ticker, False otherwise
    """
    if not code:
        return False

    # Handle RSU prefix
    ticker, _ = parse_rsu_ticker(code)
    return bool(US_TICKER_PATTERN.match(ticker.upper()))


def _get_finnhub_client():
    """Get Finnhub client with API key from environment"""
    api_key = os.getenv('FINNHUB_API_KEY')
    if not api_key:
        return None

    try:
        import finnhub
        return finnhub.Client(api_key=api_key)
    except ImportError:
        log("Warning: finnhub-python not installed, using yfinance only")
        return None


def fetch_us_stock_quote(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch real-time quote for a single US stock.

    Args:
        ticker: US stock ticker (e.g., "AAPL")

    Returns:
        Dict with price info or None if failed
    """
    # Try Finnhub first
    client = _get_finnhub_client()
    if client:
        try:
            quote = client.quote(ticker.upper())
            if quote and quote.get('c', 0) > 0:
                return {
                    "price": quote['c'],  # current price
                    "change": quote.get('d', 0),  # change
                    "change_pct": quote.get('dp', 0),  # change percent
                    "high": quote.get('h', 0),
                    "low": quote.get('l', 0),
                    "open": quote.get('o', 0),
                    "prev_close": quote.get('pc', 0),
                    "source": "finnhub"
                }
        except Exception as e:
            log(f"Finnhub error for {ticker}: {e}")

    # Fallback to yfinance
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker.upper())
        info = stock.fast_info

        price = getattr(info, 'last_price', None)
        if price and price > 0:
            prev_close = getattr(info, 'previous_close', price)
            return {
                "price": round(price, 2),
                "change": round(price - prev_close, 2) if prev_close else 0,
                "change_pct": round((price - prev_close) / prev_close * 100, 2) if prev_close else 0,
                "high": getattr(info, 'day_high', 0) or 0,
                "low": getattr(info, 'day_low', 0) or 0,
                "open": getattr(info, 'open', 0) or 0,
                "prev_close": prev_close or 0,
                "source": "yfinance"
            }
    except Exception as e:
        log(f"yfinance error for {ticker}: {e}")

    return None


def fetch_us_stock_data(holdings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fetch US stock data for a list of holdings.

    Args:
        holdings: List of holding dicts with keys:
            - code: Stock code (e.g., "AAPL", "RSU_AMZN")
            - name: Display name
            - cost: Cost basis per share (USD)
            - qty: Quantity
            - buy_date: Purchase date (YYYY-MM-DD)

    Returns:
        List of enriched holding dicts with price data
    """
    results = []

    for holding in holdings:
        code = holding.get("code", "")
        if not code:
            continue

        ticker, is_rsu = parse_rsu_ticker(code)

        # Skip non-US tickers
        if not is_us_ticker(code):
            log(f"Skipping non-US ticker: {code}")
            continue

        quote = fetch_us_stock_quote(ticker)

        if quote:
            price = quote["price"]
            cost = holding.get("cost", 0)
            qty = holding.get("qty", 0)

            # Calculate P&L
            pnl_pct = round((price - cost) / cost * 100, 2) if cost > 0 else 0

            # Calculate holding days
            buy_date = holding.get("buy_date", "")
            try:
                days = (datetime.now() - datetime.strptime(buy_date, "%Y-%m-%d")).days
            except:
                days = 0

            result = {
                "code": code,  # Keep original code (including RSU_ prefix)
                "ticker": ticker,  # Underlying ticker for price lookup
                "name": holding.get("name", ticker),
                "market": "US",
                "currency": "USD",
                "type": "RSU" if is_rsu else "Stock",
                "is_rsu": is_rsu,

                # Price data
                "price": price,
                "change": quote.get("change", 0),
                "change_pct": quote.get("change_pct", 0),

                # Position data
                "cost": cost,
                "qty": qty,
                "market_value_usd": round(price * qty, 2),

                # Performance
                "pnl_pct": pnl_pct,
                "days_held": days,

                # Metadata
                "source": quote.get("source", "unknown"),
                "buy_date": buy_date,
            }
            results.append(result)
        else:
            log(f"Failed to fetch quote for {ticker}")
            # Include with zero price so it's visible
            results.append({
                "code": code,
                "ticker": ticker,
                "name": holding.get("name", ticker),
                "market": "US",
                "currency": "USD",
                "type": "RSU" if is_rsu else "Stock",
                "is_rsu": is_rsu,
                "price": 0,
                "error": "Failed to fetch quote",
                "cost": holding.get("cost", 0),
                "qty": holding.get("qty", 0),
            })

    return results


# ============ CLI for standalone testing ============

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Test with sample holdings
    test_holdings = [
        {"code": "AAPL", "name": "Apple Inc", "cost": 150.0, "qty": 10, "buy_date": "2024-01-15"},
        {"code": "NVDA", "name": "NVIDIA", "cost": 120.0, "qty": 5, "buy_date": "2024-06-01"},
        {"code": "RSU_AMZN", "name": "Amazon RSU", "cost": 0, "qty": 50, "buy_date": "2023-01-01"},
    ]

    print("Testing US Market Data Module\n")
    results = fetch_us_stock_data(test_holdings)

    for r in results:
        print(f"{r['code']}: ${r.get('price', 'N/A')} ({r.get('source', 'unknown')})")

    print(f"\nFetched {len(results)} US holdings")
```

**Step 2: Run tests to verify implementation**

Run:

```bash
cd /Users/ray/Documents/projects/ai-investment-advisor
python scripts/test_us_market.py
```

Expected: All tests pass (or skip if no API key for integration tests)

**Step 3: Run standalone test**

Run:

```bash
cd /Users/ray/Documents/projects/ai-investment-advisor
python scripts/us_market.py
```

Expected: AAPL, NVDA prices displayed

**Step 4: Commit**

```bash
git add scripts/us_market.py
git commit -m "feat: add us_market.py for US stock data fetching"
```

**GATE: Do not proceed until all tests pass**

---

## Task 4: Add US Holdings Parsing to fetch_market_data.py

**Files:**

- Modify: `/Users/ray/Documents/projects/ai-investment-advisor/scripts/fetch_market_data.py`

**Step 1: Add us_holdings to MODULES config**

Find the `MODULES` dict (around line 29) and add:

```python
MODULES = {
    "indices": True,
    "holdings": True,
    "watchlist": True,
    "macro": True,
    "north_flow": True,
    "sector": True,
    "fund_flow": True,
    "news": True,
    "technicals": True,
    "notices": False,
    "us_holdings": True,  # NEW: US stock holdings
}
```

**Step 2: Add parse_us_holdings_md function**

Add after the existing `parse_holdings_md()` function (around line 417):

```python
def parse_us_holdings_md():
    """从 Holdings.md 解析美股持仓 (## 美股持仓)"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    holdings_path = os.path.join(script_dir, "..", "Config", "Holdings.md")

    holdings_us = []

    if not os.path.exists(holdings_path):
        log(f"警告: Holdings.md 不存在: {holdings_path}")
        return holdings_us

    with open(holdings_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析美股持仓 (## 美股持仓)
    us_match = re.search(r"## 美股持仓[^\n]*\n\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n)*)", content)
    if us_match:
        rows = us_match.group(1).strip().split("\n")
        for row in rows:
            cols = [c.strip() for c in row.split("|")[1:-1]]
            if len(cols) >= 5:
                # Expected columns: 代码, 名称, 市场, 成本价, 持仓数量, [市值], [买入日期]
                code = cols[0]
                name = cols[1]
                # Skip market column (cols[2])
                cost_str = cols[3] if len(cols) > 3 else "-"
                qty_str = cols[4] if len(cols) > 4 else "-"
                buy_date = cols[6] if len(cols) > 6 and cols[6] != "-" else "2023-01-01"

                try:
                    cost = float(cost_str) if cost_str and cost_str != "-" else 0
                    qty = float(qty_str) if qty_str and qty_str != "-" else 0
                    holdings_us.append({
                        "code": code,
                        "name": name,
                        "cost": cost,
                        "qty": qty,
                        "buy_date": buy_date
                    })
                except (ValueError, IndexError) as e:
                    log(f"解析美股持仓失败: {row}, error: {e}")
                    continue

    log(f"解析到美股持仓: {len(holdings_us)} 只")
    return holdings_us
```

**Step 3: Add US holdings fetch to main()**

Find the `main()` function and add after the existing holdings fetch (around line 1075):

```python
    # US Holdings (Phase 1)
    if MODULES["us_holdings"]:
        try:
            from us_market import fetch_us_stock_data
            holdings_us = parse_us_holdings_md()
            if holdings_us:
                result["us_holdings"] = fetch_us_stock_data(holdings_us)
                log(f"美股数据: 获取到 {len(result['us_holdings'])} 只")
            else:
                result["us_holdings"] = []
                log("美股数据: Holdings.md 无美股持仓或解析失败")
        except ImportError as e:
            log(f"美股数据: 模块导入失败 - {e}")
            result["us_holdings"] = []
        except Exception as e:
            log(f"美股数据: 获取失败 - {e}")
            result["us_holdings"] = []
```

**Step 4: Verify JSON output includes us_holdings**

Run:

```bash
cd /Users/ray/Documents/projects/ai-investment-advisor
python scripts/fetch_market_data.py 2>/dev/null | python -c "import json,sys; d=json.load(sys.stdin); print('us_holdings:', len(d.get('us_holdings', [])))"
```

Expected: `us_holdings: N` (where N is number of US holdings in Holdings.md)

**Step 5: Commit**

```bash
git add scripts/fetch_market_data.py
git commit -m "feat: add US holdings parsing and data fetching to fetch_market_data.py"
```

**GATE: JSON output must include us_holdings array**

---

## Task 5: Verify Holdings.md Has US Section

**Files:**

- Check/Modify: `/Users/ray/Documents/projects/ai-investment-advisor/Config/Holdings.md`

**Step 1: Check if 美股持仓 section exists**

Run:

```bash
grep -n "美股持仓" /Users/ray/Documents/projects/ai-investment-advisor/Config/Holdings.md 2>/dev/null || echo "Section not found"
```

**Step 2: If section doesn't exist, verify Config-Example has it**

Run:

```bash
grep -n "美股持仓" /Users/ray/Documents/projects/ai-investment-advisor/Config-Example/Holdings.md 2>/dev/null || echo "Not in example either"
```

**Step 3: If needed, add section to Config-Example/Holdings.md**

Add to Config-Example/Holdings.md:

```markdown
## 美股持仓 (脚本支持自动更新)

| 代码 | 名称 | 市场 | 成本价 | 持仓数量 | 市值 | 买入日期 |
|------|------|------|--------|----------|------|----------|
| AAPL | Apple Inc | 美股 | 150.00 | 10 | - | 2024-01-15 |
| RSU_AMZN | Amazon RSU | 美股 | - | 50 | - | 2023-06-01 |
```

**Step 4: Commit if changed**

```bash
git add Config-Example/Holdings.md
git commit -m "docs: add 美股持仓 section example to Holdings.md"
```

**GATE: 美股持仓 section must exist in Holdings.md or example**

---

## Task 6: End-to-End Verification

**Files:**

- None (verification only)

**Step 1: Run full fetch_market_data.py**

Run:

```bash
cd /Users/ray/Documents/projects/ai-investment-advisor
python scripts/fetch_market_data.py 2>&1 | head -20
```

Expected: Logs show "美股数据: 获取到 N 只"

**Step 2: Verify JSON structure**

Run:

```bash
cd /Users/ray/Documents/projects/ai-investment-advisor
python scripts/fetch_market_data.py 2>/dev/null | python -c "
import json, sys
d = json.load(sys.stdin)
print('Holdings:', len(d.get('holdings', [])))
print('US Holdings:', len(d.get('us_holdings', [])))
if d.get('us_holdings'):
    for h in d['us_holdings'][:2]:
        print(f\"  {h['code']}: \${h.get('price', 'N/A')} ({h.get('currency', 'N/A')})\")
"
```

Expected: US holdings with USD prices

**Step 3: Verify CN holdings still work**

Run:

```bash
cd /Users/ray/Documents/projects/ai-investment-advisor
python scripts/fetch_market_data.py 2>/dev/null | python -c "
import json, sys
d = json.load(sys.stdin)
holdings = d.get('holdings', [])
print(f'Total CN holdings: {len(holdings)}')
for h in holdings[:3]:
    print(f\"  {h.get('code')}: {h.get('name')} ({h.get('type')})\")
"
```

Expected: CN holdings still present and working

**Step 4: Run all tests**

Run:

```bash
cd /Users/ray/Documents/projects/ai-investment-advisor
python scripts/test_us_market.py
```

Expected: All tests pass

**Step 5: Final commit**

```bash
git add -A
git commit -m "test: verify US market data end-to-end

Verified:
- US holdings parsed from Holdings.md
- Prices fetched via Finnhub/yfinance
- JSON output includes us_holdings array
- CN holdings unaffected
"
```

---

## Summary

| Task | Description | Verification |
|------|-------------|--------------|
| 1 | Add dependencies and config | DONE |
| 2 | Create tests (TDD) | DONE |
| 3 | Implement us_market.py | DONE |
| 4 | Integrate into fetch_market_data.py | DONE |
| 5 | Verify Holdings.md format | DONE |
| 6 | End-to-end verification | DONE |

**Status:** Completed on 2026-01-24. Integrated with AKShare for macro/fundamentals.

**Total commits:** 5-6
**Estimated time:** 2-3 hours

---

*Plan created: 2026-01-24*
*For: AIA US Market Data Support (Phase 1)*
