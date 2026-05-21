#!/usr/bin/env python3
"""LinuxScriptToolbox - Quick tools for various Linux distributions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from distro import detect_distro
from ui import show_header, show_menu
from tools import get_tools_for_distro, TOOLS
from i18n import t, set_lang, get_lang, SUPPORTED_LANGS


def select_language():
    print(t("ui.select_language"))
    langs = list(SUPPORTED_LANGS.items())
    for i, (code, label) in enumerate(langs, 1):
        print(f"  [{i}] {label}")
    choice = input(t("ui.select")).strip()
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

        choice = input(t("ui.select")).strip().lower()

        if choice == "q":
            print(t("ui.goodbye"))
            break
        elif choice == "l":
            select_language()
        elif choice == "a":
            for tool in tools_to_run:
                from i18n import tool_display_name
                print(f"\n{t('ui.running', name=tool_display_name(tool))}")
                tool.run()
            input(f"\n{t('ui.press_enter')}")
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(tools_to_run):
                    from i18n import tool_display_name
                    print(f"\n{t('ui.running', name=tool_display_name(tools_to_run[idx]))}")
                    tools_to_run[idx].run()
                    input(f"\n{t('ui.press_enter')}")
                else:
                    print(t("ui.invalid_selection"))
                    input(t("ui.press_enter"))
            except ValueError:
                print(t("ui.invalid_input"))
                input(t("ui.press_enter"))


if __name__ == "__main__":
    main()
