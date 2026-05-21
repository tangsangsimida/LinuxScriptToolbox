import subprocess
import sys
from pathlib import Path

from tools.base import Tool
from utils.i18n import t

SHORIN_REPO = "https://github.com/SHORiN-KiWATA/shorin-arch-setup.git"
SHORIN_DIR = Path("/tmp/shorin-arch-setup")

SETUP_OPTIONS = {
    "niri": {
        "name_key": "msg.shorin_niri",
        "script": "scripts/04-niri-setup.sh",
        "desc_key": "msg.shorin_niri_desc",
    },
    "dms": {
        "name_key": "msg.shorin_dms",
        "script": "scripts/04c-dms-quickshell.sh",
        "desc_key": "msg.shorin_dms_desc",
    },
    "kde": {
        "name_key": "msg.shorin_kde",
        "script": "scripts/04b-kdeplasma-setup.sh",
        "desc_key": "msg.shorin_kde_desc",
    },
    "gnome": {
        "name_key": "msg.shorin_gnome",
        "script": "scripts/04d-gnome.sh",
        "desc_key": "msg.shorin_gnome_desc",
    },
}


def _run_verbose(cmd: list[str], **kwargs) -> int:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kwargs)
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


class ShorinSetup(Tool):
    name = "shorin-setup"
    display_name = "Shorin Arch Setup"
    description = "Clone and run shorin-arch-setup scripts for desktop environment configuration"
    distros = ["arch", "debian"]

    def _clone_repo(self) -> bool:
        if SHORIN_DIR.exists():
            import shutil
            shutil.rmtree(SHORIN_DIR)

        print(t("msg.cloning", repo="shorin-arch-setup"))
        code = _run_verbose(["git", "clone", "--depth", "1", SHORIN_REPO, str(SHORIN_DIR)])
        if code != 0:
            print(t("msg.clone_failed", repo="shorin-arch-setup"))
            return False
        return True

    def _show_menu(self) -> str:
        print(t("msg.shorin_select"))
        print("-" * 50)
        keys = list(SETUP_OPTIONS.keys())
        for i, key in enumerate(keys, 1):
            opt = SETUP_OPTIONS[key]
            print(f"  [{i}] {t(opt['name_key'])}")
            print(f"      {t(opt['desc_key'])}")
        print("-" * 50)
        return input(t("ui.select")).strip()

    def _run_arch_setup(self, script_path: str) -> bool:
        """Run shorin setup script on Arch."""
        full_path = SHORIN_DIR / script_path
        if not full_path.exists():
            print(t("msg.script_not_found", script=script_path))
            return False

        print(t("msg.running_script", script=script_path))
        # Make executable and run
        full_path.chmod(0o755)
        code = _run_verbose(["bash", str(full_path)])
        return code == 0

    def _run_ubuntu_setup(self, option_key: str) -> bool:
        """Run adapted setup for Ubuntu."""
        print(t("msg.shorin_ubuntu_mode"))

        # Add PPAs
        for ppa in ["ppa:avengemedia/danklinux", "ppa:avengemedia/dms"]:
            print(t("msg.adding_ppa", ppa=ppa))
            _run_verbose(["sudo", "add-apt-repository", "-y", ppa])

        print(t("msg.apt_update"))
        _run_verbose(["sudo", "apt-get", "update", "-qq"])

        if option_key == "niri":
            pkgs = ["niri"]
        elif option_key == "dms":
            pkgs = ["dms"]
        elif option_key == "kde":
            pkgs = ["kde-plasma-desktop", "sddm"]
        elif option_key == "gnome":
            pkgs = ["gnome", "gdm3"]
        else:
            return False

        for pkg in pkgs:
            print(t("msg.installing", package=pkg))
            ok = _run_verbose(["sudo", "apt-get", "install", "-y", pkg])
            if ok != 0:
                print(t("msg.install_failed", package=pkg))
                return False
            print(t("msg.install_success", package=pkg))

        return True

    def run(self) -> bool:
        distro = _get_distro()

        # Clone the repo
        if not self._clone_repo():
            return False

        # Show menu
        choice = self._show_menu()

        try:
            idx = int(choice) - 1
            keys = list(SETUP_OPTIONS.keys())
            if not (0 <= idx < len(keys)):
                print(t("ui.invalid_selection"))
                return False
            selected_key = keys[idx]
        except ValueError:
            print(t("ui.invalid_input"))
            return False

        selected = SETUP_OPTIONS[selected_key]
        print(t("msg.selected_desktop", de=t(selected["name_key"])))

        if distro == "arch":
            return self._run_arch_setup(selected["script"])
        else:
            return self._run_ubuntu_setup(selected_key)
