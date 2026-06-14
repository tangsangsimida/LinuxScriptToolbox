#!/usr/bin/env python3
"""LinuxScriptToolbox - Quick tools for various Linux distributions."""

import argparse
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(PROJECT_DIR))


# ── Virtual environment bootstrap ───────────────────────────────

from utils.bootstrap import ensure_venv

ensure_venv(PROJECT_DIR)


# ── Normal imports (after deps are ensured) ─────────────────────

from utils.distro import detect_distro
from utils.ui import (
    show_header, show_tool_header, print_error,
    print_info, print_warning, console, select_tool, select_option,
    press_any_key,
)
from tools import get_tools_for_distro, TOOLS
from utils.i18n import t, set_lang, get_lang, SUPPORTED_LANGS, tool_display_name, tool_description


def parse_args():
    parser = argparse.ArgumentParser(
        description="LinuxScriptToolbox - Quick tools for various Linux distributions"
    )
    parser.add_argument(
        "--lang", choices=list(SUPPORTED_LANGS.keys()),
        help="Set language (en/zh)"
    )
    parser.add_argument(
        "--tool", metavar="NAME",
        help="Run a specific tool by name and exit (e.g. device-init, dev-tools)"
    )
    parser.add_argument(
        "--list-tools", action="store_true",
        help="List available tools and exit"
    )
    return parser.parse_args()


def find_tool(name: str, distro: str = None):
    """Find a tool by its name attribute, filtered by current distro."""
    tools = get_tools_for_distro(distro) if distro else TOOLS
    for tool in tools:
        if tool.name == name:
            return tool
    return None


def list_tools():
    """Print all available tools."""
    distro = detect_distro()
    tools = get_tools_for_distro(distro)
    if not tools:
        print(t("ui.no_tools"))
        return
    for tool in tools:
        print(f"  {tool.name:24s} {tool_display_name(tool)}")
        print(f"  {'':24s} {tool_description(tool)}")


def select_language():
    langs = list(SUPPORTED_LANGS.items())
    options = [(code, label) for code, label in langs]
    result = select_option(t("ui.select_language"), options, default=get_lang())
    if result:
        set_lang(result)


def main():
    args = parse_args()

    if args.lang:
        set_lang(args.lang)

    if args.list_tools:
        list_tools()
        return

    if args.tool:
        distro = detect_distro()
        tool = find_tool(args.tool, distro)
        if tool is None:
            print_error(f"Tool not found: {args.tool}")
            available = [t.name for t in get_tools_for_distro(distro)]
            print_info(f"Available: {', '.join(available)}")
            sys.exit(1)
        show_tool_header(tool_display_name(tool))
        result = tool.run()
        if result is not None:
            console.print()
            press_any_key()
        return

    # Interactive mode
    distro = detect_distro()
    tools_to_run = get_tools_for_distro(distro)

    while True:
        show_header(distro, lang=get_lang())

        choice = select_tool(tools_to_run)

        if choice is None:
            continue
        elif choice == -3:  # quit
            console.print(f"\n  [bold green]{t('ui.goodbye')}[/bold green]\n")
            break
        elif choice == -2:  # language
            select_language()
        elif choice == -1:  # run all
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
            show_tool_header(tool_display_name(tools_to_run[choice]))
            result = tools_to_run[choice].run()
            if result is not None:
                console.print()
                press_any_key()
        else:
            print_error(t("ui.invalid_selection"))
            press_any_key()


if __name__ == "__main__":
    main()
