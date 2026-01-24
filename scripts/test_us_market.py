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
