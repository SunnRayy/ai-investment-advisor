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

        # Try AKShare first for richer data
        quote = fetch_us_stock_akshare_spot(ticker)
        
        # Fallback to standard fetch (Finnhub/YFinance) if AKShare fails
        if not quote:
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
                
                # Fundamentals (New)
                "pe_ttm": quote.get("pe_ttm"),
                "pb": quote.get("pb"),
                "market_cap": quote.get("market_cap"),

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


def fetch_us_stock_history(ticker: str, days: int = 365) -> Optional[Any]:
    """
    Fetch historical K-line data for US stock using yfinance.

    Args:
        ticker: US stock ticker
        days: Number of days of history

    Returns:
        pandas.DataFrame with columns: date, open, close, high, low, volume
    """
    try:
        import yfinance as yf
        import pandas as pd
        from datetime import datetime, timedelta

        start_date = (datetime.now() - timedelta(days=days + 60)).strftime("%Y-%m-%d")
        
        # Handle RSU prefix
        if ticker.startswith("RSU_"):
            ticker = ticker[4:]
            
        stock = yf.Ticker(ticker.upper())
        df = stock.history(start=start_date)
        log(f"DEBUG: yfinance returned {len(df)} rows for {ticker}")
        
        if df.empty:
            return None

        # Standardize columns
        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        df = df.rename(columns={'date': 'date', 'open': 'open', 'close': 'close', 
                              'high': 'high', 'low': 'low', 'volume': 'volume'})
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
            
        return df.tail(days)
            
    except Exception as e:
        log(f"fetch_us_stock_history error for {ticker}: {e}")
        return None


def fetch_us_stock_akshare_spot(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch real-time quote and fundamental info via AKShare (Xueqiu).
    """
    try:
        import akshare as ak
        df = ak.stock_individual_spot_xq(symbol=ticker)
        if df.empty:
            return None
            
        # Map fields
        data = {}
        for _, row in df.iterrows():
            data[row['item']] = row['value']
            
        return {
            "price": safe_float(data.get('现价')),
            "change": safe_float(data.get('涨跌')),
            "change_pct": safe_float(data.get('涨幅')),
            "open": safe_float(data.get('今开')),
            "high": safe_float(data.get('最高')),
            "low": safe_float(data.get('最低')),
            "prev_close": safe_float(data.get('昨收')),
            "volume": safe_float(data.get('成交量')),
            "amount": safe_float(data.get('成交额')),
            "pe_ttm": safe_float(data.get('市盈率(TTM)')),
            "pb": safe_float(data.get('市净率')),
            "market_cap": safe_float(data.get('资产净值/总市值')),
            "source": "akshare_xq"
        }
    except Exception as e:
        log(f"AKShare spot error for {ticker}: {e}")
        return None


def fetch_us_macro_data() -> Dict[str, Any]:
    """
    Fetch US macro economic data via AKShare.
    Returns dict with interest rate, CPI, PMI, employment data.
    """
    result = {}
    import akshare as ak
    import pandas as pd
    
    # 1. Interest Rate
    try:
        df = ak.macro_bank_usa_interest_rate()
        if not df.empty:
            latest = df.iloc[-1]
            date_col = '日期' if '日期' in df.columns else df.columns[1]
            val_col = '今值' if '今值' in df.columns else df.columns[2]
            result['interest_rate'] = {
                "current": safe_float(latest.get(val_col)),
                "date": str(latest.get(date_col))
            }
    except Exception as e:
        log(f"Macro Interest Rate error: {e}")

    # 2. CPI
    try:
        df = ak.macro_usa_cpi_monthly()
        if not df.empty:
            latest = df.iloc[-1]
            # Check trend
            prev = df.iloc[-2] if len(df) > 1 else latest
            curr_val = safe_float(latest.get('今值'))
            prev_val = safe_float(prev.get('今值'))
            
            trend = "Rising" if curr_val > prev_val else "Falling" if curr_val < prev_val else "Stable"
            
            result['cpi'] = {
                "current": curr_val,
                "prev": prev_val,
                "trend": trend,
                "date": str(latest.get('日期'))
            }
    except Exception as e:
        log(f"Macro CPI error: {e}")

    # 3. PMI (ISM Manufacturing)
    try:
        df = ak.macro_usa_ism_pmi()
        if not df.empty:
            latest = df.iloc[-1]
            val = safe_float(latest.get('今值'))
            status = "Expansion" if val > 50 else "Contraction"
            result['pmi'] = {
                "current": val,
                "status": status,
                "date": str(latest.get('日期'))
            }
    except Exception as e:
        log(f"Macro PMI error: {e}")

    # 4. Unemployment
    try:
        df = ak.macro_usa_unemployment_rate()
        if not df.empty:
            latest = df.iloc[-1]
            result['unemployment'] = {
                "current": safe_float(latest.get('今值')),
                "date": str(latest.get('日期'))
            }
    except Exception as e:
        log(f"Macro Unemployment error: {e}")
        
    # 5. Non-Farm Payrolls
    try:
        df = ak.macro_usa_non_farm()
        if not df.empty:
            latest = df.iloc[-1]
            result['non_farm'] = {
                "current": safe_float(latest.get('今值')),
                "date": str(latest.get('日期'))
            }
    except Exception as e:
        log(f"Macro Non-Farm error: {e}")

    return result


def fetch_market_calendar() -> List[Dict[str, Any]]:
    """
    Fetch today's global economic events via AKShare (Baidu source).
    """
    events = []
    try:
        import akshare as ak
        from datetime import datetime
        
        # Try fetching for today
        today_str = datetime.now().strftime("%Y%m%d")
        df = ak.news_economic_baidu(date=today_str)
        
        if df is None or df.empty:
            return events
            
        # Filter for US or High Importance
        # Columns: 日期, 时间, 地区, 事件, 公布, 预期, 前值, 重要性
        
        for _, row in df.iterrows():
            area = str(row.get('地区', ''))
            importance = row.get('重要性', 0)
            
            # Logic: US events OR very important global events (importance >= 3)
            # Note: Baidu importance is often 1-3 stars
            if "美国" in area or "美联储" in str(row.get('事件', '')) or (safe_float(importance) >= 3):
                events.append({
                    "time": str(row.get('时间')),
                    "area": area,
                    "event": str(row.get('事件')),
                    "actual": row.get('公布'),
                    "forecast": row.get('预期'),
                    "previous": row.get('前值'),
                    "importance": importance
                })
                
    except Exception as e:
        log(f"Market Calendar error: {e}")
        
    return events


def fetch_us_stock_akshare_history(ticker: str, days: int = 365) -> Optional[Any]:
    """
    Fetch historical K-line data via AKShare.
    """
    try:
        import akshare as ak
        import pandas as pd
        from datetime import datetime, timedelta
        
        start_date = (datetime.now() - timedelta(days=days + 60)).strftime("%Y%m%d")
        
        # Try both 105 (Nasdaq) and 106 (NYSE) prefixes if unknown
        prefixes = ["105.", "106.", "107."]
        df = None
        
        for prefix in prefixes:
            try:
                code = f"{prefix}{ticker}"
                temp_df = ak.stock_us_hist(symbol=code, period="daily", start_date=start_date, adjust="qfq")
                if not temp_df.empty:
                    df = temp_df
                    break
            except:
                continue
                
        if df is None or df.empty:
            # Fallback to yfinance
            log(f"AKShare returned empty history for {ticker}. Falling back to yfinance...")
            return fetch_us_stock_history(ticker, days)
            
        # Standardize columns
        # AKShare likely returns: 日期, 开盘, 收盘, 最高, 最低, 成交量...
        df = df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close', 
            '最高': 'high', '最低': 'low', '成交量': 'volume',
            '换手率': 'turnover'
        })
        
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            
        return df.tail(days)
        
    except Exception as e:
        log(f"AKShare history error for {ticker}: {e}")
        # Fallback to yfinance
        log(f"Falling back to yfinance for {ticker} history...")
        return fetch_us_stock_history(ticker, days)
        
    if df is None or df.empty:
        log(f"AKShare returned empty history for {ticker}. Falling back to yfinance...")
        return fetch_us_stock_history(ticker, days)
        
    return None # Should not reach here if logic flow is correct but for safety


def safe_float(val):
    try:
        if val is None: return 0.0
        return float(val)
    except:
        return 0.0



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
