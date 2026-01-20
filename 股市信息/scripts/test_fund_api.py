
import akshare as ak
import sys

code = "XXXXXX"
print(f"Testing Fund API for {code}...")

try:
    # Try open fund info
    print("Fetching fund info...")
    # fund_open_fund_info_em usually takes 'fund' (string) as first arg, maybe positional?
    # Or 'symbol'. Let's try positional first if keyword failed, or 'symbol'.
    # Actually, AKShare documentation says fund_open_fund_info_em(fund="000001", indicator="单位净值走势")
    # Wait, previous error said "unexpected keyword argument 'fund'". This is strange.
    # Maybe it's 'symbol'?
    fund_info = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
    print(f"Info columns: {fund_info.columns}")
    print(fund_info.tail())
except Exception as e:
    print(f"Error fetching fund info with symbol: {e}")
    try:
        # Try positional
        fund_info = ak.fund_open_fund_info_em(code, "单位净值走势")
        print("Success with positional args")
        print(fund_info.tail())
    except Exception as e2:
        print(f"Error with positional: {e2}")

