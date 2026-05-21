#!/usr/bin/env python3
"""LinuxScriptToolbox - Quick tools for various Linux distributions."""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))


def detect_distro() -> str:
    os_release = Path("/etc/os-release")
    if os_release.exists():
        data = os_release.read_text()
        if "ID=arch" in data or "ID_LIKE=arch" in data:
            return "arch"
        if "ID=debian" in data or "ID=ubuntu" in data or "ID_LIKE=debian" in data:
            return "debian"
        if "ID=fedora" in data:
            return "fedora"
        if "ID=opensuse" in data or "ID=suse" in data:
            return "suse"
    return "unknown"


def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")


def show_header(distro: str):
    clear_screen()
    print("=" * 60)
    print(f"  LinuxScriptToolbox".center(58))
    print(f"  Detected: {distro}".center(58))
    print("=" * 60)
    print()


def show_menu(tools: list) -> int:
    print("Available tools:")
    print("-" * 60)
    for i, tool in enumerate(tools, 1):
        print(f"  [{i}] {tool.display_name}")
        print(f"      {tool.description}")
    print("-" * 60)
    print("  [a] Run all tools")
    print("  [q] Quit")
    print()
    return len(tools)


def main():
    distro = detect_distro()
    from tools import get_tools_for_distro, TOOLS

    matched = get_tools_for_distro(distro)
    if not matched:
        print(f"No tools available for distro: {distro}")
        print("Available tools for any distro:")
        show_menu(TOOLS)
        choice = input("Select: ").strip().lower()
        tools_to_run = TOOLS
    else:
        tools_to_run = matched

    while True:
        show_header(distro)
        count = show_menu(tools_to_run)

        choice = input("Select: ").strip().lower()

        if choice == "q":
            print("Goodbye!")
            break
        elif choice == "a":
            for tool in tools_to_run:
                print(f"\n--- Running: {tool.display_name} ---")
                tool.run()
            input("\nPress Enter to continue...")
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(tools_to_run):
                    print(f"\n--- Running: {tools_to_run[idx].display_name} ---")
                    tools_to_run[idx].run()
                    input("\nPress Enter to continue...")
                else:
                    print("Invalid selection")
                    input("Press Enter to continue...")
            except ValueError:
                print("Invalid input")
                input("Press Enter to continue...")


if __name__ == "__main__":
    main()
