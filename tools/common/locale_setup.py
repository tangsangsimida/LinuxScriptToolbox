import subprocess
from pathlib import Path

from tools.base import Tool
from utils.i18n import t

LOCALE_GEN = Path("/etc/locale.gen")
LOCALE_CONF = Path("/etc/locale.conf")
RIME_DIR = Path.home() / ".config" / "ibus" / "rime"
RIME_ICE_URL = "https://github.com/iDvel/rime-ice.git"


def _run(cmd: list[str], **kwargs) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    return result.returncode, result.stdout.strip()


class LocaleInitializer(Tool):
    name = "locale-setup"
    display_name = "Locale & Input Method Setup"
    description = "Set timezone, Chinese locale, and install Rime with rime-ice"
    distros = ["arch", "debian"]

    # --- Timezone ---

    def _setup_timezone(self) -> None:
        _, current = _run(["timedatectl", "show", "-p", "Timezone", "--value"])
        if current == "Asia/Shanghai":
            print(t("msg.timezone_already"))
            return
        code, _ = _run(["sudo", "timedatectl", "set-timezone", "Asia/Shanghai"])
        if code == 0:
            print(t("msg.timezone_set"))
        else:
            print(t("msg.timezone_failed"))

    # --- Locale ---

    def _get_distro(self) -> str:
        os_release = Path("/etc/os-release")
        if os_release.exists():
            data = os_release.read_text()
            if "ID=arch" in data or "ID_LIKE=arch" in data:
                return "arch"
        return "debian"

    def _setup_locale(self, distro: str) -> None:
        _, locale_out = _run(["locale"])
        if "LANG=zh_CN.UTF-8" in locale_out:
            print(t("msg.locale_already"))
            return

        if not LOCALE_GEN.exists():
            print(t("msg.locale_gen_not_found"))
            return

        content = LOCALE_GEN.read_text()
        if "# zh_CN.UTF-8 UTF-8" in content:
            content = content.replace("# zh_CN.UTF-8 UTF-8", "zh_CN.UTF-8 UTF-8")
        elif "zh_CN.UTF-8 UTF-8" not in content:
            print(t("msg.locale_not_found"))
            return

        subprocess.run(
            ["sudo", "tee", str(LOCALE_GEN)],
            input=content, capture_output=True, text=True,
        )
        _run(["sudo", "locale-gen"])

        if distro == "arch":
            subprocess.run(
                ["sudo", "tee", str(LOCALE_CONF)],
                input="LANG=zh_CN.UTF-8\n", capture_output=True, text=True,
            )
        else:
            _run(["sudo", "update-locale", "LANG=zh_CN.UTF-8"])

        print(t("msg.locale_set"))

    # --- IBus + Rime + rime-ice ---

    def _install_ibus_rime(self, distro: str) -> bool:
        if distro == "arch":
            pkgs = ["ibus-rime", "git"]
        else:
            pkgs = ["ibus-rime", "git"]

        for pkg in pkgs:
            if distro == "arch":
                code, _ = _run(["pacman", "-Qi", pkg])
            else:
                code, _ = _run(["dpkg", "-s", pkg])
            if code == 0:
                continue

            print(t("msg.installing", package=pkg))
            if distro == "arch":
                ok, _ = _run(["sudo", "pacman", "-S", "--noconfirm", pkg])
            else:
                ok, _ = _run(["sudo", "apt-get", "install", "-y", pkg])
            if ok != 0:
                print(t("msg.install_failed", package=pkg))
                return False

        print(t("msg.ibus_installed"))
        return True

    def _setup_rime_ice(self) -> None:
        rime_dir = RIME_DIR
        if rime_dir.exists() and (rime_dir / ".git").exists():
            _run(["git", "-C", str(rime_dir), "pull"])
            print(t("msg.rime_ice_update"))
            return

        rime_dir.mkdir(parents=True, exist_ok=True)
        code, _ = _run(["git", "clone", RIME_ICE_URL, str(rime_dir)])
        if code != 0:
            print(t("msg.rime_ice_failed"))
            return

        print(t("msg.rime_ice_ready"))

    # --- Main ---

    def run(self) -> bool:
        distro = self._get_distro()

        print(t("msg.step_timezone"))
        self._setup_timezone()

        print(t("msg.step_locale"))
        self._setup_locale(distro)

        print(t("msg.step_ibus"))
        if not self._install_ibus_rime(distro):
            return False

        print(t("msg.step_rime_ice"))
        self._setup_rime_ice()

        return True
