#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Holdings Update Script
Updates 'Market Value' and 'Price' columns in Config/Holdings.md with real-time data.
Supports A-share, HK stock, Funds, and US stocks.
"""

import os
import sys
import re
import pandas as pd
from datetime import datetime

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetch_market_data import (
    fetch_indices, fetch_etf_data, fetch_a_stock_data, 
    fetch_hk_stock_data, fetch_fund_data,
    infer_asset_type, normalize_code
)
from us_market import fetch_us_stock_data

# Define file paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOLDINGS_PATH = os.path.join(BASE_DIR, "..", "股市信息", "Config", "Holdings.md")
if not os.path.exists(HOLDINGS_PATH):
    HOLDINGS_PATH = os.path.join(BASE_DIR, "..", "Config", "Holdings.md")

def log(msg):
    print(f"[UpdateHoldings] {msg}")

class HoldingsUpdater:
    def __init__(self, file_path):
        self.file_path = file_path
        self.lines = []
        self.prices = {}  # Cache prices: {code: {"price": float, "change": float}}

    def load_file(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.lines = f.readlines()
        log(f"Loaded {len(self.lines)} lines from {self.file_path}")

    def save_file(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.writelines(self.lines)
        log(f"Saved updates to {self.file_path}")

    def fetch_all_prices(self):
        """Pre-fetch all prices to batch requests where possible"""
        # 1. Parse all codes from file to categorize
        holdings_etf = {}
        holdings_stock = {}
        holdings_hk = {}
        holdings_fund = {}
        holdings_us = []

        # Simple regex to find table rows
        # We need to detect which section we are in, but for batch fetching we just need codes
        # Actually, to reuse fetch_market_data logic, we should construct the dicts it expects
        # It expects: {code: {"name":..., "cost":..., "qty":...}}
        
        current_section = None
        
        for line in self.lines:
            line = line.strip()
            if line.startswith("## "):
                if "A股" in line: current_section = "A"
                elif "港股" in line: current_section = "HK"
                elif "基金" in line: current_section = "FUND"
                elif "美股" in line: current_section = "US"
                else: current_section = None
                continue
            
            if not line.startswith("|") or "---" in line or "代码" in line:
                continue

            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) < 2: continue
            
            code = cols[0]
            name = cols[1]
            if not code: continue

            # Extract basic info for the fetcher
            # Note: Cost/Qty might be needed for PnL in fetcher, but we mostly need Price here.
            # We'll parse simplified info.
            info = {"name": name, "cost": 0, "qty": 0, "buy_date": "2000-01-01"}

            if current_section == "A":
                # Check if ETF or Stock
                asset_type = infer_asset_type(code, name, "A股")
                if asset_type == "ETF":
                    holdings_etf[code] = info
                else:
                    holdings_stock[code] = info
            elif current_section == "HK":
                holdings_hk[code] = info
            elif current_section == "FUND":
                holdings_fund[code] = info
            elif current_section == "US":
                holdings_us.append({"code": code, "name": name})

        log(f"Identified Assets: {len(holdings_etf)} ETF, {len(holdings_stock)} A-Stock, {len(holdings_hk)} HK, {len(holdings_fund)} Funds, {len(holdings_us)} US")

        # 2. Batch Fetch
        # A-Share Stocks & ETFs
        if holdings_etf:
            res, _ = fetch_etf_data(holdings_etf)
            for item in res: self.prices[item['code']] = item
            
        if holdings_stock:
            res, _ = fetch_a_stock_data(holdings_stock)
            for item in res: self.prices[item['code']] = item

        # HK
        if holdings_hk:
            res, _ = fetch_hk_stock_data(holdings_hk)
            for item in res: self.prices[item['code']] = item

        # Funds
        if holdings_fund:
            res = fetch_fund_data(holdings_fund)
            for item in res: self.prices[item['code']] = item

        # US
        if holdings_us:
            res = fetch_us_stock_data(holdings_us)
            for item in res: self.prices[item['code']] = item
            
        log(f"Fetched prices for {len(self.prices)} assets")

    def update_table_row(self, line, headers):
        """Update a specific row based on headers mapping"""
        if not line.strip().startswith("|") or "---" in line or "代码" in line:
            return line

        parts = line.strip().split("|")
        # parts[0] is empty (before first |), parts[-1] is empty (after last |)
        # Content is in parts[1:-1]
        
        cols = [c.strip() for c in parts[1:-1]]
        if len(cols) < len(headers):
            return line

        # Find Code column index
        try:
            code_idx = headers.index("代码")
            code = cols[code_idx]
        except ValueError:
            return line

        # Find Market Value column index
        # Could be "市值", "市值(万)", "市值(万HKD)", "市值(万USD)", etc.
        mv_idx = -1
        for i, h in enumerate(headers):
            if "市值" in h:
                mv_idx = i
                break
        
        # Find Qty column index
        qty_idx = -1
        for i, h in enumerate(headers):
            if "数量" in h or "份额" in h:
                qty_idx = i
                break

        if mv_idx == -1 or qty_idx == -1:
            return line

        # Try to normalize code to find in self.prices
        # A-shares/Funds in fetcher result have specific normalizations (e.g. 6 digits)
        # US codes in fetcher result (e.g. RSU_AMZN, AAPL)
        
        price_data = None
        # Try direct match
        if code in self.prices:
            price_data = self.prices[code]
        else:
            # Try normalized for A-Share/HK
            norm_code = normalize_code(code, 6) # Try 6 first
            if norm_code in self.prices:
                price_data = self.prices[norm_code]
            else:
                 norm_code_5 = normalize_code(code, 5) # HK
                 if norm_code_5 in self.prices:
                     price_data = self.prices[norm_code_5]

        if not price_data:
            return line

        try:
            qty_str = cols[qty_idx].replace(",", "")
            if qty_str == "-" or not qty_str:
                return line
            qty = float(qty_str)
            price = price_data.get('price', 0)
            
            if price <= 0:
                return line

            market_value = price * qty
            
            # Check unit in header
            header_mv = headers[mv_idx]
            if "万" in header_mv:
                market_value = market_value / 10000.0
            
            # Format update
            # Using 1 decimal for funds/stocks usually enough for 'Wan' unit, maybe 2
            if "万" in header_mv:
                new_val = f"{market_value:.0f}" # Round to integer for cleaner look? Or .2f? User used integers mostly in examples
                # Allow .2f if small
                if market_value < 100:
                    new_val = f"{market_value:.2f}"
                else:
                    new_val = f"{market_value:.0f}"
            else:
                new_val = f"{market_value:.2f}"

            # Update the column in the ORIGINAL line text preservation
            # We construct new line carefully
            
            # Update cols list first
            cols[mv_idx] = new_val

            # Optional: Update Cost Total in Remarks if requested? 
            # User sample shows "Cost_Total:xxx" in Remarks for funds.
            # Let's sticking to Updating Market Value first as requested.

            # Reconstruct line
            # We want to preserve spacing if possible, but markdown tables are flexible.
            # Simple reconstruction:
            new_line = "| " + " | ".join(cols) + " |\n"
            return new_line

        except Exception as e:
            # log(f"Error processing row {code}: {e}")
            return line

    def run(self):
        self.load_file()
        self.fetch_all_prices()

        new_lines = []
        current_headers = []
        in_table = False

        for line in self.lines:
            stripped = line.strip()
            
            # Detect Table Header
            if stripped.startswith("|") and "---" not in stripped and ("代码" in stripped):
                current_headers = [c.strip() for c in stripped.split("|")[1:-1]]
                in_table = True
                new_lines.append(line)
                continue
            
            # Detect Table Separator
            if stripped.startswith("|") and "---" in stripped:
                new_lines.append(line)
                continue

            # Data Row
            if in_table and stripped.startswith("|"):
                new_lines.append(self.update_table_row(line, current_headers))
                continue
            
            # Empty line or other text breaks table
            if not stripped.startswith("|"):
                in_table = False
                current_headers = []
            
            new_lines.append(line)

        self.lines = new_lines
        self.save_file()

if __name__ == "__main__":
    if not os.path.exists(HOLDINGS_PATH):
        print(f"Error: Holdings file not found at {HOLDINGS_PATH}")
        sys.exit(1)
        
    updater = HoldingsUpdater(HOLDINGS_PATH)
    updater.run()
