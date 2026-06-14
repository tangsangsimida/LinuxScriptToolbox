#!/usr/bin/env python3
"""Quickly update installed npm-based AI CLI tools."""

import argparse
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from utils.bootstrap import ensure_venv  # noqa: E402

ensure_venv(PROJECT_DIR)

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
