#!/usr/bin/env python3
"""Quickly update installed npm-based AI CLI tools.

快速更新已安装的基于 npm 的 AI CLI 工具。
"""

import argparse
import sys
from pathlib import Path

# Resolve project root directory from this script's location / 从脚本位置解析项目根目录
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from utils.bootstrap import ensure_venv  # noqa: E402

# Bootstrap virtual environment before importing project modules / 在导入项目模块之前引导虚拟环境
ensure_venv(PROJECT_DIR)

from tools.common.ai_cli_setup import update_installed_ai_clis  # noqa: E402


# Parse command-line arguments.
#
# 解析命令行参数。
#
# Returns:
#     The parsed argument namespace / 解析后的参数命名空间
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update installed npm-based AI CLI tools from LinuxScriptToolbox."
    )
    return parser.parse_args()


# Entry point for the AI CLI update script.
#
# AI CLI 更新脚本的入口函数。
#
# Returns:
#     0 on success, 1 on failure / 成功返回 0，失败返回 1
def main() -> int:
    parse_args()
    result = update_installed_ai_clis()
    # Return 0 if update succeeded (True) or no updates needed (None) / 更新成功(True)或无需更新(None)时返回 0
    return 0 if result is True or result is None else 1


# Script entry point / 脚本入口
if __name__ == "__main__":
    raise SystemExit(main())
