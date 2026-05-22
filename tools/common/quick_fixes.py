import os
import stat
import subprocess
from pathlib import Path

from tools.base import Tool
from utils.distro import detect_distro
from utils.i18n import t
from utils.ui import print_success, print_error, print_info, ask, console

FIX_OPTIONS = [
    {
        "id": "stm32cubemx-wayland",
        "name_key": "msg.qfix_stm32cubemx",
        "desc_key": "msg.qfix_stm32cubemx_desc",
    },
]

STM32_SEARCH_PATHS = [
    Path.home() / "software" / "stm32cubemx",
    Path("/opt/stm32cubemx"),
    Path("/usr/local/stm32cubemx"),
    Path.home() / "STM32CubeMX",
    Path.home() / "software" / "STM32CubeMX",
]

WRAPPER_TEMPLATE = """\
#!/bin/bash
# Auto-generated wrapper for STM32CubeMX on Wayland
# Fixes blank popup/dialog windows by forcing X11 backend

export GDK_BACKEND=x11
export SWT_GTK3=0
export _JAVA_AWT_WM_NONREPARENTING=1

exec java \\
  -Dsun.java2d.opengl=false \\
  -Dsun.java2d.xrender=false \\
  -Dawt.useSystemAAFontSettings=on \\
  -Dswing.aatext=true \\
  -Dswt.enable.autoScale=false \\
  -Dswt.autoScale=false \\
  -jar "{cubemx_path}" "$@"
"""

DESKTOP_TEMPLATE = """\
[Desktop Entry]
Name=STM32CubeMX (Wayland Fix)
Comment=STM32CubeMX with Wayland compatibility fix
Exec={wrapper_path}
Icon=stm32cubemx
Terminal=false
Type=Application
Categories=Development;Electronics;
"""


def _find_stm32cubemx() -> Path | None:
    for base in STM32_SEARCH_PATHS:
        if not base.is_dir():
            continue
        # Check for jar file
        jar = base / "STM32CubeMX"
        if jar.is_file():
            return jar
        # Check for alternative names
        for name in ["STM32CubeMX.exe", "stm32cubemx.jar"]:
            alt = base / name
            if alt.is_file():
                return alt
        # Search recursively (shallow)
        for f in base.glob("*STM32CubeMX*"):
            if f.is_file() and os.access(f, os.X_OK):
                return f
    return None


def _create_wrapper(cubemx_path: Path) -> Path | None:
    wrapper_dir = Path.home() / ".local" / "bin"
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    wrapper_path = wrapper_dir / "STM32CubeMX-fixed.sh"
    content = WRAPPER_TEMPLATE.format(cubemx_path=cubemx_path)
    try:
        wrapper_path.write_text(content)
        wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return wrapper_path
    except OSError as e:
        print_error(t("msg.qfix_wrapper_failed", error=str(e)))
        return None


def _create_desktop_file(wrapper_path: Path) -> bool:
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = desktop_dir / "stm32cubemx.desktop"
    content = DESKTOP_TEMPLATE.format(wrapper_path=wrapper_path)
    try:
        desktop_file.write_text(content)
        desktop_file.chmod(desktop_file.stat().st_mode | stat.S_IXUSR)
        return True
    except OSError as e:
        print_error(t("msg.qfix_desktop_failed", error=str(e)))
        return False


class QuickFixes(Tool):
    name = "quick-fixes"
    display_name = "Quick Fixes"
    description = "One-click fixes for common Linux software issues"
    distros = ["arch", "debian"]

    def _show_menu(self) -> str:
        console.print(f"\n  [bold]{t('msg.qfix_select')}[/bold]\n")
        for i, opt in enumerate(FIX_OPTIONS, 1):
            console.print(f"  [[bold yellow]{i}[/bold yellow]] [bold cyan]{t(opt['name_key'])}[/bold cyan]")
            console.print(f"      [dim]{t(opt['desc_key'])}[/dim]")
        console.print()
        return ask(t("ui.select"))

    def _fix_stm32cubemx_wayland(self) -> bool:
        # Step 1: Detect installation
        print_info(t("msg.qfix_detecting_path"))
        cubemx_path = _find_stm32cubemx()

        if cubemx_path is None:
            print_error(t("msg.qfix_not_found"))
            custom = ask(t("msg.qfix_enter_path")).strip()
            if not custom:
                return False
            cubemx_path = Path(custom).expanduser()
            if not cubemx_path.is_file():
                print_error(t("msg.qfix_path_invalid", path=str(cubemx_path)))
                return False

        print_success(t("msg.qfix_found", path=str(cubemx_path)))

        # Step 2: Create wrapper script
        print_info(t("msg.qfix_creating_wrapper"))
        wrapper_path = _create_wrapper(cubemx_path)
        if wrapper_path is None:
            return False
        print_success(t("msg.qfix_wrapper_created", path=str(wrapper_path)))

        # Step 3: Create .desktop file
        print_info(t("msg.qfix_creating_desktop"))
        if not _create_desktop_file(wrapper_path):
            return False
        desktop_path = Path.home() / ".local" / "share" / "applications" / "stm32cubemx.desktop"
        print_success(t("msg.qfix_desktop_created", path=str(desktop_path)))

        # Step 4: Summary
        console.print()
        print_success(t("msg.qfix_success"))
        print_info(t("msg.qfix_usage_hint", wrapper=str(wrapper_path)))
        return True

    def run(self) -> bool:
        choice = self._show_menu()

        try:
            idx = int(choice) - 1
            if not (0 <= idx < len(FIX_OPTIONS)):
                print_error(t("ui.invalid_selection"))
                return False
        except ValueError:
            print_error(t("ui.invalid_input"))
            return False

        selected = FIX_OPTIONS[idx]
        console.print()

        if selected["id"] == "stm32cubemx-wayland":
            return self._fix_stm32cubemx_wayland()

        print_error(t("msg.qfix_not_implemented"))
        return False
