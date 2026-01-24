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
