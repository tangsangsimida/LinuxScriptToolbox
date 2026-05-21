import subprocess
import sys
from pathlib import Path

from tools.base import Tool
from utils.i18n import t

DESKTOP_OPTIONS = {
    "arch": {
        "kde": {
            "name_key": "msg.de_kde",
            "packages": ["plasma", "sddm", "kde-applications"],
            "service": "sddm",
        },
        "gnome": {
            "name_key": "msg.de_gnome",
            "packages": ["gnome", "gdm"],
            "service": "gdm",
        },
        "niri": {
            "name_key": "msg.de_niri",
            "packages": ["niri", "xwayland-satellite", "xdg-desktop-portal-gnome"],
            "service": None,
            "ppas": [],
        },
        "sway": {
            "name_key": "msg.de_sway",
            "packages": ["sway", "waybar", "wofi", "foot"],
            "service": None,
        },
    },
    "debian": {
        "kde": {
            "name_key": "msg.de_kde",
            "packages": ["kde-plasma-desktop", "sddm"],
            "service": "sddm",
        },
        "gnome": {
            "name_key": "msg.de_gnome",
            "packages": ["gnome", "gdm3"],
            "service": "gdm3",
        },
        "niri": {
            "name_key": "msg.de_niri",
            "packages": ["niri"],
            "service": None,
            "ppas": ["ppa:avengemedia/danklinux", "ppa:avengemedia/dms"],
        },
        "sway": {
            "name_key": "msg.de_sway",
            "packages": ["sway", "waybar", "wofi", "foot"],
            "service": None,
        },
    },
}


def _run(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def _run_verbose(cmd: list[str]) -> int:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    proc.wait()
    return proc.returncode


def _get_distro() -> str:
    os_release = Path("/etc/os-release")
    if os_release.exists():
        data = os_release.read_text()
        if "ID=arch" in data or "ID_LIKE=arch" in data:
            return "arch"
    return "debian"


def _package_installed(pkg: str, distro: str) -> bool:
    if distro == "arch":
        code, _ = _run(["pacman", "-Qi", pkg])
    else:
        code, _ = _run(["dpkg", "-s", pkg])
    return code == 0


def _install_package(pkg: str, distro: str) -> bool:
    if _package_installed(pkg, distro):
        print(t("msg.already_installed", package=pkg))
        return True
    print(t("msg.installing", package=pkg))
    if distro == "arch":
        ok = _run_verbose(["sudo", "pacman", "-S", "--noconfirm", pkg])
    else:
        ok = _run_verbose(["sudo", "apt-get", "install", "-y", pkg])
    if ok != 0:
        print(t("msg.install_failed", package=pkg))
        return False
    print(t("msg.install_success", package=pkg))
    return True


class DesktopEnvInstaller(Tool):
    name = "desktop-env"
    display_name = "Desktop Environment"
    description = "Install a desktop environment (KDE/GNOME/Niri/Sway)"
    distros = ["arch", "debian"]

    def _show_menu(self, options: dict) -> list[str]:
        print(t("msg.select_desktop"))
        print("-" * 40)
        keys = list(options.keys())
        for i, key in enumerate(keys, 1):
            opt = options[key]
            print(f"  [{i}] {t(opt['name_key'])}")
        print("-" * 40)
        return keys

    def run(self) -> bool:
        distro = _get_distro()
        options = DESKTOP_OPTIONS.get(distro, {})
        if not options:
            print(t("msg.no_desktop_options"))
            return False

        keys = self._show_menu(options)
        choice = input(t("ui.select")).strip()

        try:
            idx = int(choice) - 1
            if not (0 <= idx < len(keys)):
                print(t("ui.invalid_selection"))
                return False
        except ValueError:
            print(t("ui.invalid_input"))
            return False

        selected_key = keys[idx]
        selected = options[selected_key]
        print(t("msg.selected_desktop", de=t(selected["name_key"])))

        # Add PPAs if needed (Debian/Ubuntu)
        ppas = selected.get("ppas", [])
        if ppas and distro != "arch":
            for ppa in ppas:
                print(t("msg.adding_ppa", ppa=ppa))
                _run_verbose(["sudo", "add-apt-repository", "-y", ppa])

        if distro != "arch":
            print(t("msg.apt_update"))
            _run_verbose(["sudo", "apt-get", "update", "-qq"])

        for pkg in selected["packages"]:
            if not _install_package(pkg, distro):
                return False

        # Enable display manager service
        service = selected.get("service")
        if service:
            print(t("msg.enabling_service", service=service))
            _run(["sudo", "systemctl", "enable", service])
            print(t("msg.service_enabled_on_boot", service=service))

        print(t("msg.desktop_installed"))
        return True
