
import re
import os
from .utils import log

def parse_holdings_content(content):
    """
    Parse holdings from markdown content string.
    Returns: holdings_etf, holdings_stock, holdings_hk, holdings_fund
    """
    holdings_etf = {}
    holdings_stock = {}
    holdings_hk = {}
    holdings_fund = {}

    # Parse A-Share Holdings (Stock & ETF)
    # Match table rows under ## A股持仓
    a_stock_match = re.search(r"## A股持仓\s*\n\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n)*)", content)
    if a_stock_match:
        rows = a_stock_match.group(1).strip().split("\n")
        for row in rows:
            cols = [c.strip() for c in row.split("|")[1:-1]]
            if len(cols) >= 5:
                # Expected: Code, Name, Market, Cost, Qty...
                code, name, market, cost_str, qty_str, *rest = cols + [""] * 5
                try:
                    cost = float(cost_str)
                    qty = int(qty_str) if qty_str and qty_str != "-" else 0
                    buy_date = rest[1] if len(rest) > 1 and rest[1] and rest[1] != "-" else "2023-01-01"

                    item = {"name": name, "cost": cost, "qty": qty, "buy_date": buy_date}
                    
                    if "ETF" in name or code.startswith("5") or code.startswith("1"):
                        holdings_etf[code] = item
                    else:
                        holdings_stock[code] = item
                except (ValueError, IndexError):
                    continue

    # Parse HK Holdings
    hk_match = re.search(r"## 港股持仓\s*\n\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n)*)", content)
    if hk_match:
        rows = hk_match.group(1).strip().split("\n")
        for row in rows:
            cols = [c.strip() for c in row.split("|")[1:-1]]
            if len(cols) >= 5:
                code, name, market, cost_str, qty_str, *rest = cols + [""] * 5
                try:
                    cost = float(cost_str)
                    qty = int(qty_str) if qty_str and qty_str != "-" else 0
                    buy_date = rest[1] if len(rest) > 1 and rest[1] and rest[1] != "-" else "2023-01-01"
                    holdings_hk[code] = {"name": name, "cost": cost, "qty": qty, "buy_date": buy_date}
                except (ValueError, IndexError):
                    continue

    # Parse Fund Holdings
    fund_match = re.search(r"## 基金持仓\s*\n\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n)*)", content)
    if fund_match:
        rows = fund_match.group(1).strip().split("\n")
        for row in rows:
            cols = [c.strip() for c in row.split("|")[1:-1]]
            if len(cols) >= 6:
                # Expected: Code, Name, Type, Established, Cost, Share...
                code = cols[0]
                name = cols[1]
                cost_str = cols[4]
                qty_str = cols[5]
                buy_date = cols[7] if len(cols) > 7 and cols[7] and cols[7] != "-" else "2023-01-01"
                try:
                    cost = float(cost_str)
                    qty = float(qty_str) if qty_str and qty_str != "-" else 0
                    holdings_fund[code] = {"name": name, "cost": cost, "qty": qty, "buy_date": buy_date}
                except (ValueError, IndexError):
                    continue

    return holdings_etf, holdings_stock, holdings_hk, holdings_fund


def parse_us_holdings_content(content):
    """
    Parse US holdings from markdown content string.
    Returns: list of dicts
    """
    holdings_us = []

    # Match table rows under ## 美股持仓
    us_match = re.search(r"## 美股持仓[^\n]*\n\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n)*)", content)
    if us_match:
        rows = us_match.group(1).strip().split("\n")
        for row in rows:
            cols = [c.strip() for c in row.split("|")[1:-1]]
            if len(cols) >= 5:
                # Expected: Code, Name, Market, Cost, Qty, MarketValue...
                code = cols[0]
                name = cols[1]
                # cols[2] is Market
                cost_str = cols[3] if len(cols) > 3 else "-"
                qty_str = cols[4] if len(cols) > 4 else "-"
                mv_str = cols[5] if len(cols) > 5 else "-"
                buy_date = cols[6] if len(cols) > 6 and cols[6] != "-" else "2023-01-01"

                try:
                    cost = float(cost_str) if cost_str and cost_str != "-" else 0
                    qty = float(qty_str) if qty_str and qty_str != "-" else 0
                    
                    market_value = 0
                    price = 0
                    if mv_str and mv_str != "-":
                         # Market Value is in "Wan" (Ten Thousand) USD usually, based on header
                         # But check header? Assuming standard format.
                         # Header: 市值(万USD)
                         market_value = float(mv_str) * 10000
                         if qty > 0:
                             price = market_value / qty

                    holdings_us.append({
                        "code": code,
                        "name": name,
                        "cost": cost,
                        "qty": qty,
                        "market_value": market_value,
                        "price": price,
                        "buy_date": buy_date
                    })
                except (ValueError, IndexError) as e:
                    log(f"Parse US holdings failed: {row}, error: {e}", error=True)
                    continue

    return holdings_us

def load_holdings_file(file_path=None):
    """
    Load content from Holdings.md.
    If file_path is None, tries to locate it in standard locations.
    """
    if not file_path:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Try relative to src/aia -> project_root/股市信息/Config/Holdings.md
        # .../src/aia/../../股市信息/Config/Holdings.md
        candidate = os.path.join(script_dir, "..", "..", "股市信息", "Config", "Holdings.md")
        if os.path.exists(candidate):
            file_path = candidate
        else:
            # Fallback
            candidate = os.path.join(script_dir, "..", "..", "Config", "Holdings.md")
            if os.path.exists(candidate):
                file_path = candidate
    
    if not file_path or not os.path.exists(file_path):
        log(f"Holdings file not found: {file_path}", error=True)
        return ""
        
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
