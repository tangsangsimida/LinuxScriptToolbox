#!/usr/bin/env python3
"""Quickly update installed npm-based AI CLI tools."""

import argparse
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = PROJECT_DIR / ".venv"
REQUIREMENTS = PROJECT_DIR / "requirements.txt"


def _setup_venv() -> None:
    """Create .venv, install dependencies, and re-exec under venv Python."""
    import subprocess

    print("Creating virtual environment...")
    if subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)]).returncode != 0:
        print("Error: Failed to create virtual environment.")
        raise SystemExit(1)

    if REQUIREMENTS.exists():
        print("Installing dependencies...")
        venv_pip = VENV_DIR / "bin" / "pip"
        if subprocess.run([str(venv_pip), "install", "-r", str(REQUIREMENTS)]).returncode != 0:
            print("Error: Failed to install dependencies.")
            raise SystemExit(1)

    venv_python = VENV_DIR / "bin" / "python"
    os.execvp(str(venv_python), [str(venv_python)] + sys.argv)


def ensure_venv() -> None:
    """Run this script under the project virtual environment."""
    if sys.prefix != sys.base_prefix:
        return

    venv_python = VENV_DIR / "bin" / "python"
    if venv_python.exists():
        os.execvp(str(venv_python), [str(venv_python)] + sys.argv)

    _setup_venv()


ensure_venv()
sys.path.insert(0, str(PROJECT_DIR))

from tools.common.ai_cli_setup import update_installed_ai_clis  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update installed npm-based AI CLI tools from LinuxScriptToolbox."
    )
    return parser.parse_args()


def main() -> int:
    parse_args()
    result = update_installed_ai_clis()
    return 0 if result is True or result is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
