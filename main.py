#!/usr/bin/env python3
"""LinuxScriptToolbox - Quick tools for various Linux distributions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from distro import detect_distro
from ui import show_header, show_menu
from tools import get_tools_for_distro, TOOLS


def main():
    distro = detect_distro()

    matched = get_tools_for_distro(distro)
    if not matched:
        print(f"No tools available for distro: {distro}")
        print("Available tools for any distro:")
        show_menu(TOOLS)
        input("Select: ").strip().lower()
        tools_to_run = TOOLS
    else:
        tools_to_run = matched

    while True:
        show_header(distro)
        show_menu(tools_to_run)

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
