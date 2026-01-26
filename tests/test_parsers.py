
import unittest
import os
from src.aia.parsers import parse_holdings_content, parse_us_holdings_content

class TestParsers(unittest.TestCase):
    def setUp(self):
        self.sample_holdings_md = """
## A股持仓
| 代码 | 名称 | 市场 | 成本价 | 持仓数量 | 现价 | 市值 | 持仓占比 | 盈亏 |
|---|---|---|---|---|---|---|---|---|
| 600519 | 贵州茅台 | 沪A | 1650.00 | 10 | 1700.00 | 17000.00 | 50% | +3.03% |
| 000858 | 五粮液 | 深A | 150.00 | 100 | 155.00 | 15500.00 | 45% | +3.33% |

## 港股持仓
| 代码 | 名称 | 市场 | 成本价 | 持仓数量 | 现价 | 市值 | 持仓占比 | 盈亏 |
|---|---|---|---|---|---|---|---|---|
| 00700 | 腾讯控股 | 港股 | 300.00 | 100 | 320.00 | 32000.00 | 10% | +6.67% |

## 美股持仓
| 代码 | 名称 | 市场 | 成本价 | 持仓数量 | 现价 | 市值 | 买入日期 |
|---|---|---|---|---|---|---|---|
| AAPL | Apple | US | 150.00 | 10 | 170.00 | 1700.00 | 2023-01-01 |
| RSU_AMZN | Amazon | US | 0.00 | 50 | 130.00 | 6500.00 | 2023-06-01 |

## 基金持仓
| 代码 | 名称 | 类型 | 成立日 | 成本价 | 持仓份额 | 净值 | 买入日期 |
|---|---|---|---|---|---|---|---|
| 110011 | 易方达中小盘 | 混合型 | 2008-01-01 | 2.500 | 1000.00 | 3.000 | 2023-01-01 |

        """

    def test_parse_holdings_content(self):
        etf, stock, hk, fund = parse_holdings_content(self.sample_holdings_md)
        
        # Check A-Share (Stock)
        self.assertIn('600519', stock)
        self.assertEqual(stock['600519']['name'], '贵州茅台')
        self.assertEqual(stock['600519']['cost'], 1650.00)
        self.assertEqual(stock['600519']['qty'], 10)

        # Check HK Stock
        self.assertIn('00700', hk)
        self.assertEqual(hk['00700']['name'], '腾讯控股')
        self.assertEqual(hk['00700']['cost'], 300.00)

        # Check Fund
        self.assertIn('110011', fund)
        self.assertEqual(fund['110011']['qty'], 1000.00)

    def test_parse_us_holdings_content(self):
        us_holdings = parse_us_holdings_content(self.sample_holdings_md)
        
        self.assertEqual(len(us_holdings), 2)
        
        # Check AAPL
        aapl = next(x for x in us_holdings if x['code'] == 'AAPL')
        self.assertEqual(aapl['cost'], 150.0)
        self.assertEqual(aapl['qty'], 10.0)
        
        # Check RSU
        amzn = next(x for x in us_holdings if x['code'] == 'RSU_AMZN')
        self.assertEqual(amzn['cost'], 0.0)
        self.assertEqual(amzn['qty'], 50.0)

if __name__ == '__main__':
    unittest.main()
