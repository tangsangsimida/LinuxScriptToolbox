import re
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

    def _install_language_packs(self, distro: str) -> None:
        if distro == "arch":
            return  # Arch includes translations with main packages
        for pkg in [
            "language-pack-zh-hans",
            "language-pack-zh-hans-base",
            "language-pack-gnome-zh-hans",
            "language-pack-gnome-zh-hans-base",
        ]:
            if _package_installed_deb(pkg):
                continue
            print(t("msg.installing", package=pkg))
            _run_verbose(["sudo", "apt-get", "install", "-y", pkg])

    def _setup_locale(self, distro: str) -> None:
        _, locale_out = _run(["locale"])
        lang_ok = "LANG=zh_CN.UTF-8" in locale_out
        _, language_val = _run(["bash", "-c", "echo $LANGUAGE"])
        lang_env_ok = language_val.startswith("zh_CN")

        if lang_ok and lang_env_ok:
            print(t("msg.locale_already"))
            return

        self._install_language_packs(distro)

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

        # Set AccountsService language (GNOME reads this for login language)
        import getpass
        user = getpass.getuser()
        acct_file = Path(f"/var/lib/AccountsService/users/{user}")
        if acct_file.exists():
            content = acct_file.read_text()
            if "Language=" in content:
                content = re.sub(r"Language=.*", "Language=zh_CN.UTF-8", content)
            else:
                content = content.replace("[User]", "[User]\nLanguage=zh_CN.UTF-8")
            subprocess.run(["sudo", "tee", str(acct_file)], input=content, capture_output=True, text=True)

        # Write ~/.pam_environment for user-session locale (PAM reads at login)
        pam_env = Path.home() / ".pam_environment"
        pam_content = "\n".join([
            "LANGUAGE\tDEFAULT=zh_CN:en",
            "LANG\tDEFAULT=zh_CN.UTF-8",
            "LC_NUMERIC\tDEFAULT=zh_CN.UTF-8",
            "LC_TIME\tDEFAULT=zh_CN.UTF-8",
            "LC_MONETARY\tDEFAULT=zh_CN.UTF-8",
            "LC_PAPER\tDEFAULT=zh_CN.UTF-8",
            "LC_NAME\tDEFAULT=zh_CN.UTF-8",
            "LC_ADDRESS\tDEFAULT=zh_CN.UTF-8",
            "LC_TELEPHONE\tDEFAULT=zh_CN.UTF-8",
            "LC_MEASUREMENT\tDEFAULT=zh_CN.UTF-8",
            "LC_IDENTIFICATION\tDEFAULT=zh_CN.UTF-8",
            "PAPERSIZE\tDEFAULT=a4",
            "",
        ])
        pam_env.write_text(pam_content)
        print(t("msg.pam_env_written", path=str(pam_env)))

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

    def _configure_fcitx5(self) -> None:
        # Add IM environment variables to /etc/environment
        env_file = Path("/etc/environment")
        env_content = env_file.read_text()
        im_vars = {"GTK_IM_MODULE": "fcitx", "QT_IM_MODULE": "fcitx", "XMODIFIERS": "@im=fcitx"}
        for var, val in im_vars.items():
            if var not in env_content:
                env_content = env_content.rstrip() + f"\n{var}={val}\n"
        subprocess.run(["sudo", "tee", str(env_file)], input=env_content, capture_output=True, text=True)

        # Also add to ~/.pam_environment
        pam_env = Path.home() / ".pam_environment"
        if pam_env.exists():
            pam_content = pam_env.read_text()
        else:
            pam_content = ""
        for var, val in im_vars.items():
            if var not in pam_content:
                pam_content += f"{var}\tDEFAULT={val}\n"
        pam_env.write_text(pam_content)

        # Set GNOME input sources to include Fcitx5 Rime
        _run(["gsettings", "set", "org.gnome.desktop.input-sources", "sources",
              "[('xkb', 'us'), ('fcitx', 'rime')]"])

        # Enable Fcitx5 autostart
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_src = Path("/usr/share/applications/org.fcitx.Fcitx5.desktop")
        desktop_dst = autostart_dir / "org.fcitx.Fcitx5.desktop"
        if desktop_src.exists() and not desktop_dst.exists():
            _run(["cp", str(desktop_src), str(desktop_dst)])

        print(t("msg.fcitx5_configured"))

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
        self._configure_fcitx5()

        print(t("msg.step_rime_ice"))
        self._setup_rime_ice()

        return True
