import subprocess
import sys
from pathlib import Path

from tools.base import Tool
from utils.i18n import t

APP_CATEGORIES = {
    "arch": {
        "dev": {
            "name_key": "msg.cat_dev",
            "packages": ["git", "vim", "neovim", "curl", "wget", "base-devel"],
        },
        "system": {
            "name_key": "msg.cat_system",
            "packages": ["htop", "tmux", "unzip", "tree", "jq", "rsync"],
        },
        "network": {
            "name_key": "msg.cat_network",
            "packages": ["openssh", "net-tools", "nmap"],
        },
        "shell": {
            "name_key": "msg.cat_shell",
            "packages": ["zsh", "fish"],
        },
    },
    "debian": {
        "dev": {
            "name_key": "msg.cat_dev",
            "packages": ["git", "vim", "neovim", "curl", "wget", "build-essential"],
        },
        "system": {
            "name_key": "msg.cat_system",
            "packages": ["htop", "tmux", "unzip", "tree", "jq", "rsync"],
        },
        "network": {
            "name_key": "msg.cat_network",
            "packages": ["openssh-client", "net-tools", "nmap"],
        },
        "shell": {
            "name_key": "msg.cat_shell",
            "packages": ["zsh", "fish"],
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


class CommonAppsInstaller(Tool):
    name = "common-apps"
    display_name = "Common Apps Installer"
    description = "Install commonly used applications by category"
    distros = ["arch", "debian"]

    def _show_categories(self, categories: dict) -> list[str]:
        print(t("msg.select_categories"))
        print("-" * 40)
        keys = list(categories.keys())
        for i, key in enumerate(keys, 1):
            cat = categories[key]
            print(f"  [{i}] {t(cat['name_key'])} ({', '.join(cat['packages'])})")
        print(f"  [a] {t('msg.select_all')}")
        print("-" * 40)
        return keys

    def run(self) -> bool:
        distro = _get_distro()
        categories = APP_CATEGORIES.get(distro, {})
        if not categories:
            print(t("msg.no_categories"))
            return False

        keys = self._show_categories(categories)
        choice = input(t("ui.select")).strip().lower()

        if choice == "a":
            selected = keys
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(",")]
                selected = [keys[i] for i in indices if 0 <= i < len(keys)]
            except (ValueError, IndexError):
                print(t("ui.invalid_input"))
                return False

        if not selected:
            print(t("msg.nothing_selected"))
            return False

        if distro != "arch":
            print(t("msg.apt_update"))
            _run_verbose(["sudo", "apt-get", "update", "-qq"])

        all_pkgs = []
        for key in selected:
            all_pkgs.extend(categories[key]["packages"])

        print(t("msg.installing_packages", count=len(all_pkgs)))
        success = True
        for pkg in all_pkgs:
            if not _install_package(pkg, distro):
                success = False

        return success
