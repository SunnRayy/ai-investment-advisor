
import json
import os
from datetime import datetime
from .parsers import load_holdings_file, parse_holdings_content, parse_us_holdings_content
from .utils import log

class HoldingsExporter:
    def export(self, output_path):
        """
        Export holdings to JSON file at output_path.
        """
        # Load content
        content = load_holdings_file()
        if not content:
            log("No content found in Holdings.md", error=True)
            return False

        # Parse
        etf, stock, hk, fund = parse_holdings_content(content)
        us_holdings = parse_us_holdings_content(content)

        holdings_list = []

        # Process A-Shares (Stock & ETF)
        for collection in [etf, stock]:
            for code, info in collection.items():
                market = self._determine_cn_market(code)
                holdings_list.append({
                    "symbol": code,
                    "market": market,
                    "quantity": float(info.get("qty", 0)),
                    "avg_cost_local": float(info.get("cost", 0)),
                    "currency": "CNY",
                    # Optional fields could be populated if we fetched market data, but spec says "current holdings snapshot"
                    # We only have configured holdings here. Market price is optional. 
                })

        # Process HK
        for code, info in hk.items():
            holdings_list.append({
                "symbol": code,
                "market": "HK",
                "quantity": float(info.get("qty", 0)),
                "avg_cost_local": float(info.get("cost", 0)),
                "currency": "HKD"
            })

        # Process US
        for item in us_holdings:
            holdings_list.append({
                "symbol": item["code"],
                "market": "US",
                "quantity": float(item.get("qty", 0)),
                "avg_cost_local": float(item.get("cost", 0)),
                "market_price": float(item.get("price", 0)),  # New field
                "market_value_usd": float(item.get("market_value", 0)), # New field
                "currency": "USD"
            })

        # Construct final JSON
        output_data = {
            "sync_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "holdings": holdings_list
        }

        # Write to file
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            log(f"Exported {len(holdings_list)} holdings to {output_path}")
            return True
        except Exception as e:
            log(f"Failed to write output: {e}", error=True)
            return False

    def _determine_cn_market(self, code):
        """
        Simple heuristic for CN market.
        6xxxxx -> SH
        0xxxxx, 3xxxxx -> SZ
        """
        code_str = str(code)
        if code_str.startswith("6") or code_str.startswith("9"): # 9 is B-share usually SH but rare
            return "CN_SH"
        elif code_str.startswith("0") or code_str.startswith("3"):
            return "CN_SZ"
        elif code_str.startswith("5"): # ETF SH
            return "CN_SH"
        elif code_str.startswith("1"): # ETF SZ
            return "CN_SZ"
        elif code_str.startswith("4") or code_str.startswith("8"): # BJ? Default to SZ/SH if not specific
             # Spec only mentions CN_SH, CN_SZ. Let's map BJ to SZ for now or leave as is?
             # Spec: Enum: `US`, `CN_SH`, `CN_SZ`, `HK`.
             # 5xxxxx is SH ETF, 1xxxxx is SZ ETF.
             pass
        
        # Default fallback
        if code_str.startswith("6"): return "CN_SH"
        return "CN_SZ"
