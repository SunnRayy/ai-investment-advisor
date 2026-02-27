import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestUISPriceExports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.modules = [
            load_module(
                "root_fetch_market_data",
                cls.repo_root / "scripts" / "fetch_market_data.py",
            ),
            load_module(
                "cn_fetch_market_data",
                cls.repo_root / "股市信息" / "scripts" / "fetch_market_data.py",
            ),
        ]

    def test_build_holdings_snapshot_payload_keeps_required_and_extended_fields(self):
        market_json = {
            "metadata": {"date": "2026-02-27"},
            "holdings": [
                {
                    "code": "MSFT",
                    "type": "美股",
                    "market": "US",
                    "currency": "USD",
                    "price": 395.2,
                    "cost": 300.0,
                    "qty": 5,
                },
                {
                    "code": "MSFT",
                    "type": "美股",
                    "market": "US",
                    "currency": "USD",
                    "price": 396.0,
                    "cost": 300.0,
                    "qty": 5,
                },
                {"code": "510300", "type": "ETF", "price": 3.2},
            ],
            "us_holdings": [
                {
                    "code": "RSU_AMZN",
                    "market": "US",
                    "currency": "USD",
                    "price": 239.1,
                    "cost": 0.0,
                    "qty": 156,
                }
            ],
        }
        sync_timestamp = "2026-02-27T09:25:00Z"

        for module in self.modules:
            payload = module.build_holdings_snapshot_payload(market_json, sync_timestamp)
            self.assertEqual(payload["sync_timestamp"], sync_timestamp)
            self.assertEqual(len(payload["holdings"]), 2)

            symbols = [item["symbol"] for item in payload["holdings"]]
            self.assertEqual(symbols.count("MSFT"), 1)
            self.assertIn("RSU_AMZN", symbols)

            msft = next(item for item in payload["holdings"] if item["symbol"] == "MSFT")
            self.assertEqual(msft["market_price"], 396.0)
            self.assertEqual(msft["currency"], "USD")
            self.assertEqual(msft["market"], "US")
            self.assertEqual(msft["quantity"], 5.0)
            self.assertEqual(msft["avg_cost_local"], 300.0)
            self.assertIn("market_value_usd", msft)

    def test_build_market_data_payload_prefers_nav_date_over_technicals(self):
        market_json = {
            "metadata": {"date": "2026-02-20", "time": "10:00"},
            "holdings": [
                {
                    "code": "110022",
                    "type": "基金",
                    "price": 3.391,
                    "nav_date": "2026-02-25",
                    "technicals": {"as_of": "2026-02-24"},
                },
                {
                    "code": "100032",
                    "type": "基金",
                    "price": 1.004,
                    "technicals": {"as_of": "2026-02-26"},
                },
            ],
        }

        for module in self.modules:
            payload = module.build_market_data_payload(market_json)
            self.assertEqual(payload["metadata"]["date"], "2026-02-25")

    def test_export_uis_price_files_raises_when_write_fails(self):
        market_json = {
            "metadata": {"date": "2026-02-20", "time": "10:00"},
            "holdings": [],
            "us_holdings": [],
        }

        for module in self.modules:
            with tempfile.TemporaryDirectory() as tmp_dir:
                with patch("builtins.open", side_effect=OSError("disk full")):
                    with self.assertRaises(OSError):
                        module.export_uis_price_files(
                            market_json=market_json,
                            sync_timestamp="2026-02-27T10:00:00Z",
                            project_root=tmp_dir,
                        )


if __name__ == "__main__":
    unittest.main()
