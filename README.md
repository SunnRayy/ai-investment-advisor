# AI Investment Advisor

> 让 Claude、Codex、Gemini 三个 AI 组成你的私人投资委员会

一个基于多模型协同的个人投资分析系统，让普通投资者也能拥有专业机构级别的多维度分析和决策支持。

## 核心理念

1. **数据必须可靠客观** - 所有数据从 AKShare 实时获取，禁止估算
2. **多模型协同减少偏见** - 三个 AI 独立分析，提取共识
3. **强制数据驱动** - 每个建议必须引用 ≥2 个客观数据字段
4. **个性化 + 持续追踪** - 记住你的风格和弱点，越用越懂你

## 功能列表

| 功能 | 触发词 | 说明 |
|------|--------|------|
| 每日简报 | `/brief`、"简报" | 持仓分析 + 市场热点 + 风险预警 |
| 市场扫描 | `/scan`、"有什么机会" | 发现符合你风格的投资机会 |
| 个股分析 | `/analyze`、"分析XX" | 深度分析特定标的 |
| 交易记录 | `/trade`、"今天买了XX" | 记录交易并追踪建议执行情况 |
| 周期复盘 | `/review`、"复盘" | 验证建议准确性，总结经验 |
| 投资委员会 | `/committee`、"开会" | 三个 AI 独立分析后提取共识 |

## 快速开始

### 环境要求

- Python 3.8+
- [Obsidian](https://obsidian.md/)（可选，用于笔记管理）
- [Claude Code](https://claude.ai/) / [Cursor](https://cursor.sh/) / 其他 AI 编程工具

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/your-username/ai-investment-advisor.git
cd ai-investment-advisor
```

2. **安装 Python 依赖**
```bash
pip install akshare pandas
```

3. **配置你的持仓**
```bash
# 复制示例配置
cp -r Config-Example 股市信息/Config

# 编辑你的持仓
vim 股市信息/Config/Holdings.md
```

4. **配置 AI 工具**
- 将 `.claude/skills` 目录复制到你的项目中
- 如果使用 Codex，将 skills 复制到 `~/.codex/skills/`

5. **开始使用**
```
# 在 Claude Code 中
"给我今天的简报"
"开个投委会，讨论下加仓策略"
```

## 目录结构

```
ai-investment-advisor/
├── README.md                    # 本文件
├── AGENTS.md                    # 系统详细说明
├── 使用手册.md                   # 用户操作手册
│
├── .claude/
│   └── skills/                  # AI 技能配置
│       ├── brief/SKILL.md       # 每日简报
│       ├── scan/SKILL.md        # 市场扫描
│       ├── analyze/SKILL.md     # 个股分析
│       ├── trade/SKILL.md       # 交易记录
│       ├── review/SKILL.md      # 周期复盘
│       └── committee/SKILL.md   # 投资委员会
│
├── scripts/
│   ├── fetch_market_data.py     # 核心数据获取脚本
│   └── ...                      # 其他辅助脚本
│
├── Templates/                   # 投委会模板
│   ├── prompt_template.md       # 输入提示词模板
│   ├── opinion_template.md      # 观点输出模板
│   └── consensus_template.md    # 共识汇总模板
│
└── Config-Example/              # 配置文件示例
    ├── Holdings.md              # 持仓配置示例
    ├── Profile.md               # 投资者画像示例
    ├── Watchlist.md             # 关注池示例
    └── Principles.md            # 投资原则示例
```

## 投资委员会工作流程

```
你提出问题 → 统一输入数据
                ↓
    ┌──────────┼──────────┐
    ↓          ↓          ↓
  Claude    Codex     Gemini
    ↓          ↓          ↓
    └──────────┼──────────┘
                ↓
           共识提取
                ↓
        可执行建议
```

- **强共识 (3/3 一致)**: 值得认真考虑执行
- **弱共识 (2/3 一致)**: 参考多数意见
- **分歧区**: 需要你自己判断

## 数据来源

- **行情数据**: AKShare（A股、港股、ETF、基金）
- **宏观数据**: AKShare（PMI、CPI、M2）
- **北向资金**: AKShare
- **新闻快讯**: 财联社电报

## 自定义

### 修改投资风格

编辑 `Config/Profile.md`，写下你的投资风格和已知弱点。

### 修改关注方向

编辑 `Config/Watchlist.md`，添加你关注的行业和标的。

### 修改 AI 行为

编辑 `.claude/skills/` 下的 SKILL.md 文件，调整 AI 的分析逻辑。

## 风险提示

> ⚠️ **投资有风险，本系统仅供参考，不构成投资建议。**
> 
> AI 分析基于历史数据和模型推理，不能预测未来，请结合自身情况独立判断。
> 所有投资决策由用户自行承担责任。

## 贡献

欢迎提交 Issue 和 Pull Request！

## License

MIT License
