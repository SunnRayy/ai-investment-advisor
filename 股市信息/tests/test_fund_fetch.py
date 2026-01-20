import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../scripts'))

# Import target function (will be implemented)
try:
    import fetch_full_analysis
except ImportError:
    # Handle case where script might not be importable yet or path issue
    pass

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
        if hasattr(fetch_full_analysis, 'fetch_fund_data'):
            df = fetch_full_analysis.fetch_fund_data("XXXXXX")
        else:
            self.fail("fetch_fund_data not implemented in fetch_full_analysis")

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
