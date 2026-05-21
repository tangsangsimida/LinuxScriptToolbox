import subprocess
import sys
from pathlib import Path

from tools.base import Tool
from utils.i18n import t

LOCALE_GEN = Path("/etc/locale.gen")
LOCALE_CONF = Path("/etc/locale.conf")
RIME_DIR = Path.home() / ".local" / "share" / "fcitx5" / "rime"
RIME_ICE_URL = "https://github.com/iDvel/rime-ice.git"

FCITX5_PACKAGES = {
    "arch": ["fcitx5", "fcitx5-rime", "fcitx5-gtk", "fcitx5-qt"],
    "debian": [
        "fcitx5", "fcitx5-rime",
        "fcitx5-frontend-gtk3", "fcitx5-frontend-gtk4",
        "fcitx5-frontend-qt5", "fcitx5-frontend-qt6",
    ],
}


def _run(cmd: list[str], **kwargs) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    return result.returncode, result.stdout.strip()


def _run_verbose(cmd: list[str], **kwargs) -> int:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kwargs)
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    proc.wait()
    return proc.returncode


def _package_installed_deb(pkg: str) -> bool:
    code, _ = _run(["dpkg", "-s", pkg])
    return code == 0


class LocaleInitializer(Tool):
    name = "locale-setup"
    display_name = "Locale & Input Method Setup"
    description = "Set timezone, Chinese locale, and install Fcitx5 + Rime with rime-ice"
    distros = ["arch", "debian"]

    # --- Timezone ---

    def _setup_timezone(self) -> None:
        _, current = _run(["timedatectl", "show", "-p", "Timezone", "--value"])
        if current == "Asia/Shanghai":
            print(t("msg.timezone_already"))
            return
        code = _run_verbose(["sudo", "timedatectl", "set-timezone", "Asia/Shanghai"])
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
        lang_ok = "LANG=zh_CN.UTF-8" in locale_out
        _, language_val = _run(["bash", "-c", "echo $LANGUAGE"])
        lang_env_ok = language_val.startswith("zh_CN")

        if lang_ok and lang_env_ok:
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
        _run_verbose(["sudo", "locale-gen"])

        locale_content = "LANG=zh_CN.UTF-8\nLANGUAGE=zh_CN:zh\n"
        if distro == "arch":
            subprocess.run(
                ["sudo", "tee", str(LOCALE_CONF)],
                input=locale_content, capture_output=True, text=True,
            )
        else:
            _run_verbose(["sudo", "update-locale", "LANG=zh_CN.UTF-8", "LANGUAGE=zh_CN:zh"])

        # Set GNOME desktop region for GUI language
        _run(["gsettings", "set", "org.gnome.system.locale", "region", "zh_CN.UTF-8"])

        print(t("msg.locale_set"))

    # --- Fcitx5 + Rime ---

    def _install_package(self, pkg: str, distro: str) -> bool:
        if distro == "arch":
            code, _ = _run(["pacman", "-Qi", pkg])
        else:
            code = 0 if _package_installed_deb(pkg) else 1
        if code == 0:
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

    def _apt_update(self) -> None:
        print(t("msg.apt_update"))
        _run_verbose(["sudo", "apt-get", "update", "-qq"])

    def _install_fcitx5_rime(self, distro: str) -> bool:
        if distro != "arch":
            self._apt_update()

        if not self._install_package("git", distro):
            return False

        for pkg in FCITX5_PACKAGES[distro]:
            if not self._install_package(pkg, distro):
                return False

        print(t("msg.fcitx5_installed"))
        return True

    # --- rime-ice ---

    def _setup_rime_ice(self) -> None:
        rime_dir = RIME_DIR
        if rime_dir.exists() and (rime_dir / ".git").exists():
            print(t("msg.rime_ice_update"))
            _run_verbose(["git", "-C", str(rime_dir), "pull"])
            return

        rime_dir.mkdir(parents=True, exist_ok=True)
        print(t("msg.cloning_rime_ice"))
        code = _run_verbose(["git", "clone", RIME_ICE_URL, str(rime_dir)])
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

        print(t("msg.step_fcitx5"))
        if not self._install_fcitx5_rime(distro):
            return False

        print(t("msg.step_rime_ice"))
        self._setup_rime_ice()

        return True
