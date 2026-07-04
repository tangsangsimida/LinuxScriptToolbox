#!/usr/bin/env python3
"""LinuxScriptToolbox - Quick tools for various Linux distributions.

LinuxScriptToolbox — 针对各种 Linux 发行版的快捷工具集。

This is the main entry point. It bootstraps the virtual environment,
detects the current platform/distro/shell, and launches the interactive
tool selection menu or runs a single tool via --tool.

这是主入口。它引导虚拟环境、检测当前平台/发行版/Shell，
然后启动交互式工具选择菜单或通过 --tool 运行单个工具。
"""

import argparse
import os
import sys
from pathlib import Path

# Project root directory / 项目根目录
PROJECT_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(PROJECT_DIR))


# Default TERM for non-interactive sessions (e.g. ssh + --list-tools).
# Without this, Rich prints "TERM environment variable not set" and pollutes
# stdout. Set early so bootstrap's subprocess calls inherit it too.
# 非交互场景（如 ssh + --list-tools）的 TERM 默认值。
# 不设置时 Rich 会打印 "TERM environment variable not set" 污染 stdout。
# 早期设置以便 bootstrap 派生的子进程也能继承。
os.environ.setdefault("TERM", "xterm")


# ── Virtual environment bootstrap / 虚拟环境引导 ────────────────

from utils.bootstrap import ensure_venv

ensure_venv(PROJECT_DIR)


# ── Normal imports (after deps are ensured) ─────────────────────
# ── 常规导入（依赖已确保后执行）─────────────────────────────────

from utils.platform import detect_platform
from utils.distro import detect_distro
from utils.shell import detect_shell
from utils.ui import (
    show_header, show_tool_header, print_error,
    print_info, print_warning, console, select_tool, select_option,
    press_any_key,
)
from tools import get_tools, TOOLS
from utils.i18n import t, set_lang, get_lang, SUPPORTED_LANGS, tool_display_name, tool_description


# Parse command-line arguments.
#
# 解析命令行参数。
#
# Returns:
#     Parsed arguments namespace / 解析后的参数命名空间
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LinuxScriptToolbox - Quick tools for various Linux distributions"
    )
    parser.add_argument(
        "--lang", choices=list(SUPPORTED_LANGS.keys()),
        help="Set language (en/zh) / 设置语言（en/zh）"
    )
    parser.add_argument(
        "--tool", metavar="NAME",
        help="Run a specific tool by name and exit / 按名称运行指定工具后退出"
    )
    parser.add_argument(
        "--list-tools", action="store_true",
        help="List available tools and exit / 列出可用工具后退出"
    )
    return parser.parse_args()


# Find a tool by its name attribute, filtered by distro and platform.
#
# 按名称查找工具，按发行版和平台过滤。
#
# Args:
#     name: Tool name to search for / 要搜索的工具名称
#     distro: Distribution filter / 发行版过滤条件
#     platform: Platform filter / 平台过滤条件
#
# Returns:
#     Tool instance if found, None otherwise / 找到则返回 Tool 实例，否则返回 None
def find_tool(name: str, distro: str = None, platform: str = None):
    # First search the filtered list for an exact match / 先在过滤后的列表中精确查找
    tools = get_tools(distro, platform) if distro or platform else TOOLS
    for tool in tools:
        if tool.name == name:
            return tool
    return None


# Print all available tools with their display names and descriptions.
#
# 打印所有可用工具的显示名称和描述。
def list_tools() -> None:
    current_platform = detect_platform()
    distro = detect_distro()
    tools = get_tools(distro, current_platform)
    if not tools:
        print(t("ui.no_tools"))
        return
    for tool in tools:
        print(f"  {tool.name:24s} {tool_display_name(tool)}")
        print(f"  {'':24s} {tool_description(tool)}")


# Show language selection menu and apply the chosen language.
#
# 显示语言选择菜单并应用所选语言。
def select_language() -> None:
    langs = list(SUPPORTED_LANGS.items())
    options = [(code, label) for code, label in langs]
    result = select_option(t("ui.select_language"), options, default=get_lang())
    if result:
        set_lang(result)


# Main entry point — parse args, detect environment, run tools.
#
# 主入口 — 解析参数、检测环境、运行工具。
#
# Supports three modes:
# 1. --list-tools: list available tools and exit
# 2. --tool NAME: run a specific tool non-interactively
# 3. Interactive: show menu for tool selection
#
# 支持三种模式：
# 1. --list-tools：列出可用工具后退出
# 2. --tool NAME：非交互式运行指定工具
# 3. 交互式：显示工具选择菜单
def main() -> None:
    args = parse_args()

    # Apply language override if specified / 如果指定了语言则应用
    if args.lang:
        set_lang(args.lang)

    # Mode 1: list tools / 模式 1：列出工具
    if args.list_tools:
        list_tools()
        return

    # Detect platform, distro, and shell / 检测平台、发行版和 Shell
    current_platform = detect_platform()
    distro = detect_distro()
    current_shell = detect_shell()

    # Mode 2: run specific tool / 模式 2：运行指定工具
    if args.tool:
        tool = find_tool(args.tool, distro, current_platform)
        if tool is None:
            # Check if tool exists but isn't available for current env /
            # 检查工具是否存在但不适用于当前环境
            if find_tool(args.tool) is not None:
                print_error(t("msg.tool_not_available", tool=args.tool, distro=distro, platform=current_platform))
            else:
                print_error(t("msg.tool_not_found", tool=args.tool))
            available = [t.name for t in get_tools(distro, current_platform)]
            print_info(t("msg.tools_available", tools=", ".join(available)))
            sys.exit(1)
        show_tool_header(tool_display_name(tool))
        result = tool.run()
        if result is not None:
            console.print()
            press_any_key()
        return

    # Mode 3: interactive menu / 模式 3：交互式菜单
    tools_to_run = get_tools(distro, current_platform)

    while True:
        show_header(distro, lang=get_lang(), platform=current_platform, shell=current_shell)

        choice = select_tool(tools_to_run)

        if choice is None:
            continue
        elif choice == -3:  # quit / 退出
            console.print(f"\n  [bold green]{t('ui.goodbye')}[/bold green]\n")
            break
        elif choice == -2:  # language / 语言
            select_language()
        elif choice == -1:  # run all / 全部运行
            safe_tools = [tool for tool in tools_to_run if tool.safe_for_run_all]
            skipped = len(tools_to_run) - len(safe_tools)
            if skipped:
                print_warning(t("ui.run_all_safe_only", skipped=skipped))
            if not safe_tools:
                print_info(t("ui.no_run_all_tools"))
                press_any_key()
                continue
            for tool in safe_tools:
                show_tool_header(tool_display_name(tool))
                tool.run_all()
            console.print()
            press_any_key()
        elif 0 <= choice < len(tools_to_run):
            tool = tools_to_run[choice]
            show_tool_header(tool_display_name(tool))
            # Offer dry-run when the tool supports it
            # 如果工具支持 dry-run，则提供预览选项
            dry_output = tool.run_dry()
            should_run = True
            if dry_output is not None:
                options = [
                    ("r", t("ui.run_tool")),
                    ("d", t("ui.dry_run")),
                    ("q", t("ui.back")),
                ]
                sub_choice = select_option(t("ui.tool_action"), options, default="r")
                if sub_choice == "d":
                    console.print(f"\n[bold cyan]{dry_output}[/bold cyan]")
                    console.print()
                    press_any_key()
                    should_run = False
                elif sub_choice == "q":
                    should_run = False
            if should_run:
                result = tool.run()
                if result is not None:
                    console.print()
                    press_any_key()
        else:
            print_error(t("ui.invalid_selection"))
            press_any_key()


if __name__ == "__main__":
    main()
