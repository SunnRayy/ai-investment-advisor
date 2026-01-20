# [Fund Support] Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Enable analysis of open-ended funds (e.g., XXXXXX Jiashi Emerging Industry) in `fetch_full_analysis.py` to resolve conflict with stock codes.

**Architecture:** Add a `--type` argument to the analysis script. Implement a new `fetch_fund_data` function using AKShare's fund API (`fund_open_fund_info_em` with `symbol`). Adapt technical analysis to work with single-value NAV data (treating Close=NAV, with no High/Low/Volume).

**Tech Stack:** Python, Pandas, AKShare.

---

### Task 1: Add Fund Data Fetching Logic

**Files:**

- Create: `股市信息/tests/test_fund_fetch.py`
- Modify: `股市信息/scripts/fetch_full_analysis.py`

**Step 1: Write the failing test**

Create `股市信息/tests/test_fund_fetch.py`:

```python
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../scripts'))

# Import target function (will be implemented)
# We need to import the module, knowing the function might not exist yet or behave differently
import fetch_full_analysis

class TestFundFetch(unittest.TestCase):
    @patch('akshare.fund_open_fund_info_em')
    def test_fetch_fund_data(self, mock_ak):
        # Mock AKShare response
        mock_df = pd.DataFrame({
            '净值日期': ['2026-01-01', '2026-01-02'],
            '单位净值': [1.0, 1.01],
            '日增长率': [0.0, 1.0]
        })
        mock_ak.return_value = mock_df

        # Call function
        df = fetch_full_analysis.fetch_fund_data("XXXXXX")

        # Verify
        self.assertIsNotNone(df)
        self.assertIn('date', df.columns)
        self.assertIn('close', df.columns)
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[-1]['close'], 1.01)
        
        # Verify call args (should use symbol)
        mock_ak.assert_called_with(symbol="XXXXXX", indicator="单位净值走势")

if __name__ == '__main__':
    unittest.main()
```

**Step 2: Run test to verify it fails**

Run: `python3 股市信息/tests/test_fund_fetch.py`
Expected: FAIL with "AttributeError: module 'fetch_full_analysis' has no attribute 'fetch_fund_data'"

**Step 3: Implement minimal code to make test pass**

Modify `股市信息/scripts/fetch_full_analysis.py`:

```python
def fetch_fund_data(code):
    """获取公募基金已有数据"""
    log(f"【基金】获取净值数据: {code}")
    try:
        # 使用 symbol 参数
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        
        if df.empty:
            return None
            
        # 标准化列名
        rename_map = {
            '净值日期': 'date',
            '单位净值': 'close',
            '日增长率': 'change'
        }
        df = df.rename(columns=rename_map)
        
        # 格式转换
        df['date'] = pd.to_datetime(df['date'])
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['change'] = pd.to_numeric(df['change'], errors='coerce')
        
        # 补充 High/Low/Open/Volume 以兼容技术分析 (全部设为 close/0)
        df['open'] = df['close']
        df['high'] = df['close']
        df['low'] = df['close']
        df['volume'] = 0.0
        
        df = df.sort_values('date')
        return df
    except Exception as e:
        log(f"获取基金净值失败: {e}")
        return None
```

**Step 4: Run test to verify it passes**

Run: `python3 股市信息/tests/test_fund_fetch.py`
Expected: PASS

**Step 5: Commit**

```bash
git add 股市信息/scripts/fetch_full_analysis.py 股市信息/tests/test_fund_fetch.py
git commit -m "feat: add fetch_fund_data function"
```

---

### Task 2: Add CLI Argument and Main Logic

**Files:**

- Modify: `股市信息/scripts/fetch_full_analysis.py`
- Test: Manual (since it's CLI entry point)

**Step 1: Write the failing test (Manual)**

Run: `python3 股市信息/scripts/fetch_full_analysis.py XXXXXX --type fund`
Expected: Script runs but currently ignores `--type fund` or errors if not handled, analyzing stock instead.

**Step 2: Implement minimal code**

Modify `股市信息/scripts/fetch_full_analysis.py`:

1. Import `argparse` if not present (or use sys.argv).
2. Update `main()` to parse `--type`.
3. Update `full_analysis` to accept `asset_type`.
4. In `full_analysis`, if `asset_type == 'fund'`, use `fetch_fund_data` and skip unusable sections (North Flow, Sector Flow).

Snippet for `main`:

```python
    # ... inside main ...
    asset_type = "stock"
    if "--type" in sys.argv:
        idx = sys.argv.index("--type")
        if idx + 1 < len(sys.argv):
            asset_type = sys.argv[idx + 1]
    
    # ... call full_analysis with asset_type ...
```

Snippet for `full_analysis`:

```python
def full_analysis(code, market="a", asset_type="stock"):
    # ...
    # 1. 宏观 (Keep, but if fund, skip market_trend if not relevant? Actually macro is always relevant)
    result["macro"] = fetch_macro_environment(asset_type) # Maybe pass type to avoid north flow for funds? Or just ignore north flow result.
    
    # 2. 行业 (For funds, maybe skip or find way to get sector)
    if asset_type == "stock":
        result["sector"] = fetch_sector_analysis(code)
    else:
        result["sector"] = {"note": "公募基金暂不支持行业资金流向分析"}
        
    # 3. K线
    if asset_type == "fund":
        df = fetch_fund_data(code)
    else:
        df = fetch_stock_data(code, market)
        
    # ... rest ...
```

**Step 3: Run test to verify it passes**

Run: `python3 股市信息/scripts/fetch_full_analysis.py XXXXXX --type fund`
Expected: Output JSON contains fund data (NAV ~4.0) and no stock-specific errors.

**Step 4: Commit**

```bash
git add 股市信息/scripts/fetch_full_analysis.py
git commit -m "feat: support --type fund argument"
```
