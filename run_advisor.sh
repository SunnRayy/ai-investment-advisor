#!/bin/bash
# 切换到脚本所在目录的父目录 (即 项目根目录)
cd "$(dirname "$0")"

# 激活 Python 虚拟环境 (如果有)
# source venv/bin/activate

# 运行生成脚本
echo "Running Personal Investment Advisor..."
python3 scripts/generate_brief.py
