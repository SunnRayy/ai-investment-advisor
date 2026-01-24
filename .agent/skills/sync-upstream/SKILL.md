---
name: sync-upstream
description: 将本地代码与 Upstream 仓库 (AllenAI2014) 同步，保留定制化修改，并推送到 Origin (私有副本)。
user-invocable: true
---

# /sync-upstream - 同步上游版本

安全地将 `upstream` (官方仓库) 的更新合并到本地，并同步到 `origin` (私有仓库)。

## 使用场景

- 每次启动工作前
- 用户输入 "更新版本"、"sync"、"同步代码" 时
- 需要获取最新功能修复时

## 核心流程

1. **环境检查**：确认当前分支干净且为 `main`。
2. **拉取上游**：仅获取 `upstream/main` (稳定版)。
3. **安全合并**：将上游变更合并到本地，**保留用户配置**。
4. **推送同步**：将合并后的结果推送到 `origin/main`。

## 执行步骤

### 第一步：环境检查

确保工作区干净，避免合并冲突。**特别注意：确保 Config 文件存在且完好。**

```bash
# S1: 关键配置检查
if [ ! -s "股市信息/Config/Holdings.md" ]; then
    echo "❌ CRITICAL: Holdings.md 在同步前丢失或为空！请先恢复数据再同步。"
    exit 1
fi

git status
```

- **预期**：`nothing to commit, working tree clean`
- **如果脏**：请先提交(git commit)或暂存(git stash)更改。

验证远程仓库配置（防止推送到错误位置）：

```bash
git remote -v
```

- **必须确认**：
  - `upstream`: `https://github.com/AllenAI2014/ai-investment-advisor` (or .git)
  - `origin`: `https://github.com/SunnRayy/ai-investment-advisor` (or .git)

验证当前分支（防止推送到错误分支）：

```bash
git branch --show-current
```

- **预期**：`main`
- **如果不是**：请先切换到 main 分支 (`git checkout main`)

**自动化脚本检查（可选）**:
如果使用脚本自动运行，必须包含以下断言逻辑：

1. 检查 `git remote get-url upstream` 是否包含 `AllenAI2014`
2. 检查 `git remote get-url origin` 是否包含 `SunnRayy`
3. 检查当前分支是否为 `main`
4. **如果任何一项检查失败，立即终止执行，不进行 fetch/merge/push**

### 第二步：拉取上游 (Fetch)

```bash
git fetch upstream main
```

### 第三步：合并更新 (Merge)

将上游更新合并到本地 `main` 分支。

```bash
git merge upstream/main
```

**冲突处理策略**：

- 如果遇到 `Config/` 或 `Records/` 目录下的文件冲突：**始终保留本地版本** (User Data)。
- 如果遇到 `Config/` 或 `Records/` 目录下的文件冲突：**始终保留本地版本** (User Data)。
- 如果遇到 code 文件 (`scripts/`, `src/`) 冲突：**人工审查**。
  - **CRITICAL**: `scripts/fetch_market_data.py` 和 `scripts/fetch_full_analysis.py` 已经被深度修改以支持美股。
  - 如果上游更新了这些文件，**小心合并**。通常应保留本地的 `us_holdings` 和 `macro` 逻辑。
- 如果遇到 `scripts/us_market.py`：这是本地新增文件，不应有冲突，如果有，那是上游也加了这个（不太可能），保留本地。

```bash
# S2: 同步后完整性检查
if [ ! -s "股市信息/Config/Holdings.md" ]; then
    echo "❌ EMERGENCY: 同步操作似乎清除或重置了配置文件！"
    echo "请立即执行: git reset --hard ORIG_HEAD (尝试撤销合并)"
    exit 1
else
    echo "✅ Config check passed."
fi
```

### 第四步：推送至私有仓库 (Push)

更新合并完成后，推送到你的私有 Fork。

```bash
git push origin main
```

---

## 隐私与安全检查 (Privacy Check)

在推送之前，Skill 应快速检查：

1. **Upstream 隔离**：绝对不要执行 `git push upstream`。
2. **敏感数据**：确保没有意外修改 `.gitignore` 导致私有文件被取消忽略。

## 故障排除

**Q: 出现 "refusing to merge unrelated histories"?**
A: 首次同步可能会遇到。使用 `git merge upstream/main --allow-unrelated-histories`。

**Q: 合并后代码报错?**
A: 可能是上游更改了 API。运行测试或使用 `systematic-debugging` skill 修复。
