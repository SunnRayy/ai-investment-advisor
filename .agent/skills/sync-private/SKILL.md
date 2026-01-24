---
name: sync-private
description: 将私有投资数据（Config, Daily, Records等）同步备份到本地 Obsidian 笔记库。
user-invocable: true
---

# /sync-private - 私有数据备份

由于 `股市信息` 目录下的个人数据（Config, Records 等）被 Git 忽略，无法同步到 Forked 仓库。此 Skill 用于将这些文件单向备份到本地 Obsidian 笔记库，利用 Obsidian 的 iCloud/Git 同步机制进行数据保护。

## 目标路径

**源目录**: `[ProjectRoot]/股市信息/`
**目标目录**: `/Users/ray/Documents/Obsidian Git/obsidian/Projects/Investment/AI-investment-advisor-notes/`

## 需要同步的子目录

仅同步以下包含私有数据的目录：

1. `Config/` (持仓、洞察、上下文)
2. `Daily/` (每日简报)
3. `Analysis/` (深度分析报告)
4. `Records/` (交易记录)
5. `Scan/` (扫描结果)

## 执行步骤

### 第一步：检查目标目录是否存在

验证目标目录是否存在，如果不存在则提示错误（不自动创建深层路径以防路径错误）。

**重要安全检查**：
在备份前，**务必**检查源数据是否有效。如果 `股市信息/Config` 下的文件因故变成了空模板或丢失，执行备份将覆盖掉好的备份及其副本，导致永久数据丢失。

```bash
# S1: 检查源文件是否存在且不为空 (size > 0)
if [ ! -s "股市信息/Config/Holdings.md" ]; then
    echo "❌ CRITICAL ERROR: 源文件 Holdings.md 丢失或为空！停止备份以保护现有备份数据。"
    exit 1
fi

# S2: 检查是否只是初始模板 (基于文件大小的启发式检查，模板通常 < 1KB)
# 注意：如果用户刚开始使用确实没持仓，请忽略此警告
FILE_SIZE=$(wc -c < "股市信息/Config/Holdings.md" | tr -d ' ')
if [ "$FILE_SIZE" -lt 1000 ]; then
    echo "⚠️ WARNING: Holdings.md 似乎非常小 ($FILE_SIZE bytes)。请确认它不是空模板。"
    echo "如果是空模板，请勿覆盖备份！"
    # 这里不强制 exit，留给 Agent 判断，但提示非常明显
fi

ls -d "/Users/ray/Documents/Obsidian Git/obsidian/Projects/Investment/AI-investment-advisor-notes/"
```

### 第二步：执行同步 (Rsync)

使用 `rsync` 进行增量同步。

- `-a`: 归档模式，保留属性
- `-v`: 显示详细信息
- `--mkpath`: 自动创建目标子目录 (macOS自带rsync可能不支持，如下方脚本改用mkdir -p)
- `--update`: 仅更新较新的文件

```bash
# 定义源和目标
SOURCE_BASE="股市信息"
TARGET_BASE="/Users/ray/Documents/Obsidian Git/obsidian/Projects/Investment/AI-investment-advisor-notes"

# 确保目标基础目录存在
mkdir -p "$TARGET_BASE/Config"
mkdir -p "$TARGET_BASE/Daily"
mkdir -p "$TARGET_BASE/Analysis"
mkdir -p "$TARGET_BASE/Records"
mkdir -p "$TARGET_BASE/Scan"

# 同步 Config
rsync -avu "$SOURCE_BASE/Config/" "$TARGET_BASE/Config/"

# 同步 Daily
rsync -avu "$SOURCE_BASE/Daily/" "$TARGET_BASE/Daily/"

# 同步 Analysis
rsync -avu "$SOURCE_BASE/Analysis/" "$TARGET_BASE/Analysis/"

# 同步 Records
rsync -avu "$SOURCE_BASE/Records/" "$TARGET_BASE/Records/"

# 同步 Scan
rsync -avu "$SOURCE_BASE/Scan/" "$TARGET_BASE/Scan/"
```

### 第三步：验证同步

列出目标目录最近更新的文件，确认同步成功。

```bash
find "/Users/ray/Documents/Obsidian Git/obsidian/Projects/Investment/AI-investment-advisor-notes" -type f -mmin -5
```

## 自动化建议

建议在每次执行完 `/trade`, `/brief`, `/analyze`, `/scan` 等会产生新数据的 Skill 后，自动询问用户或自动触发此 Skill。

## 示例对话

**用户**: "备份数据"

**助手**:
正在将私有数据同步到 Obsidian...

- 同步 Config... 完成
- 同步 Records... 完成
...
备份完成！文件已保存至 Obsidian Git 目录。
