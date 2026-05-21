import os


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
