#!/usr/bin/env python3
"""LinuxScriptToolbox - Quick tools for various Linux distributions."""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
VENV_DIR = PROJECT_DIR / ".venv"
REQUIREMENTS = PROJECT_DIR / "requirements.txt"

sys.path.insert(0, str(PROJECT_DIR))


# ── Virtual environment bootstrap ───────────────────────────────

def _setup_venv():
    """Create .venv and install dependencies, then re-exec under venv Python."""
    print("Creating virtual environment...")
    if subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)]).returncode != 0:
        print("Error: Failed to create virtual environment.")
        sys.exit(1)

    venv_pip = VENV_DIR / "bin" / "pip"
    if REQUIREMENTS.exists():
        print("Installing dependencies...")
        if subprocess.run([str(venv_pip), "install", "-r", str(REQUIREMENTS)]).returncode != 0:
            print("Error: Failed to install dependencies.")
            sys.exit(1)

    venv_python = VENV_DIR / "bin" / "python"
    os.execvp(str(venv_python), [str(venv_python)] + sys.argv)


def ensure_venv():
    """Ensure we are running inside the project virtual environment.

    If not, create it and re-launch this script under .venv/bin/python.
    """
    if sys.prefix != sys.base_prefix:
        return  # already inside a venv

    if not VENV_DIR.exists():
        _setup_venv()

    # venv exists but we are not in it — re-exec
    venv_python = VENV_DIR / "bin" / "python"
    if venv_python.exists():
        os.execvp(str(venv_python), [str(venv_python)] + sys.argv)
    else:
        _setup_venv()


ensure_venv()


# ── Normal imports (after deps are ensured) ─────────────────────

from utils.distro import detect_distro
from utils.ui import (
    show_header, show_menu, show_tool_header, print_success, print_error,
    print_info, print_running, ask, console, select_tool,
)
from tools import get_tools_for_distro, TOOLS
from utils.i18n import t, set_lang, get_lang, SUPPORTED_LANGS


def select_language():
    console.print(f"\n  [bold]{t('ui.select_language')}[/bold]\n")
    langs = list(SUPPORTED_LANGS.items())
    for i, (code, label) in enumerate(langs, 1):
        console.print(f"  [[bold yellow]{i}[/bold yellow]] {label}")
    console.print()
    choice = ask(t("ui.select"))
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(langs):
            set_lang(langs[idx][0])
    except ValueError:
        pass


def main():
    distro = detect_distro()

    tools_to_run = get_tools_for_distro(distro)

    while True:
        show_header(distro)
        show_menu(tools_to_run)

        choice = select_tool(tools_to_run)

        if choice is None:
            continue
        elif choice == -3:  # quit
            console.print(f"\n  [bold green]{t('ui.goodbye')}[/bold green]\n")
            break
        elif choice == -2:  # language
            select_language()
        elif choice == -1:  # run all
            for tool in tools_to_run:
                from utils.i18n import tool_display_name
                show_tool_header(tool_display_name(tool))
                tool.run()
            console.print()
            ask(t("ui.press_enter"))
        elif 0 <= choice < len(tools_to_run):
            from utils.i18n import tool_display_name
            show_tool_header(tool_display_name(tools_to_run[choice]))
            result = tools_to_run[choice].run()
            if result is not None:
                console.print()
                ask(t("ui.press_enter"))
        else:
            print_error(t("ui.invalid_selection"))
            ask(t("ui.press_enter"))


if __name__ == "__main__":
    main()
