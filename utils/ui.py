import os

from utils.i18n import t, tool_display_name, tool_description


def clear_screen():
    os.system("clear" if os.name == "posix" else "cls")


def show_header(distro: str):
    clear_screen()
    print("=" * 60)
    print(f"  LinuxScriptToolbox".center(58))
    print(f"  {t('ui.detected', distro=distro)}".center(58))
    print("=" * 60)
    print()


def show_menu(tools: list) -> int:
    print(t("ui.available_tools"))
    print("-" * 60)
    if not tools:
        print(f"  {t('ui.no_tools')}")
    for i, tool in enumerate(tools, 1):
        print(f"  [{i}] {tool_display_name(tool)}")
        print(f"      {tool_description(tool)}")
    print("-" * 60)
    print(f"  [a] {t('ui.run_all')}")
    print(f"  [l] {t('ui.language')}")
    print(f"  [q] {t('ui.quit')}")
    print()
    return len(tools)
