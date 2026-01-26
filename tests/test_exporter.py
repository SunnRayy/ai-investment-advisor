
import unittest
import json
import os
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.aia.exporter import HoldingsExporter

class TestExporter(unittest.TestCase):
    def setUp(self):
        self.output_dir = "test_output"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
    def tearDown(self):
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)

    @patch('src.aia.exporter.parse_holdings_content')
    @patch('src.aia.exporter.parse_us_holdings_content')
    @patch('src.aia.exporter.load_holdings_file')
    def test_export_holdings(self, mock_load, mock_parse_us, mock_parse_content):
        # Setup mocks
        mock_load.return_value = "dummy content"
        
        # Mock parsed data
        mock_parse_content.return_value = (
            {}, # etf
            {'600519': {'name': 'Moutai', 'cost': 100, 'qty': 10, 'buy_date': '2023-01-01'}}, # stock (A-share)
            {'00700': {'name': 'Tencent', 'cost': 300, 'qty': 100, 'buy_date': '2023-01-01'}}, # hk
            {} # fund
        )
        
        mock_parse_us.return_value = [
            {'code': 'AAPL', 'name': 'Apple', 'cost': 150, 'qty': 10, 'buy_date': '2023-01-01'}
        ]
        
        output_file = os.path.join(self.output_dir, "holdings.json")
        exporter = HoldingsExporter()
        exporter.export(output_file)
        
        self.assertTrue(os.path.exists(output_file))
        
        with open(output_file, 'r') as f:
            data = json.load(f)
            
        self.assertIn("sync_timestamp", data)
        self.assertIn("holdings", data)
        self.assertEqual(len(data["holdings"]), 3)
        
        # Verify fields
        aapl = next(h for h in data["holdings"] if h["symbol"] == "AAPL")
        self.assertEqual(aapl["market"], "US")
        self.assertEqual(aapl["currency"], "USD")
        self.assertEqual(aapl["quantity"], 10)
        
        moutai = next(h for h in data["holdings"] if h["symbol"] == "600519")
        self.assertEqual(moutai["market"], "CN_SH") # Assuming simple mapping for now, or check logic
        self.assertEqual(moutai["currency"], "CNY")
        
        tencent = next(h for h in data["holdings"] if h["symbol"] == "00700")
        self.assertEqual(tencent["market"], "HK")
        self.assertEqual(tencent["currency"], "HKD")

if __name__ == '__main__':
    unittest.main()
