import subprocess
from pathlib import Path

from tools.base import Tool
from utils.distro import detect_distro
from utils.i18n import t
from utils.ui import print_success, print_error, print_info, console, prompt_selection, BACK_ACTION

SHORIN_REPO = "https://github.com/SHORiN-KiWATA/shorin-arch-setup.git"
SHORIN_DIR = Path("/tmp/shorin-arch-setup")

SETUP_OPTIONS = [
    {
        "id": "niri",
        "name_key": "msg.shorin_niri",
        "script": "scripts/04-niri-setup.sh",
        "desc_key": "msg.shorin_niri_desc",
    },
    {
        "id": "dms",
        "name_key": "msg.shorin_dms",
        "script": "scripts/04c-dms-quickshell.sh",
        "desc_key": "msg.shorin_dms_desc",
    },
    {
        "id": "kde",
        "name_key": "msg.shorin_kde",
        "script": "scripts/04b-kdeplasma-setup.sh",
        "desc_key": "msg.shorin_kde_desc",
    },
    {
        "id": "gnome",
        "name_key": "msg.shorin_gnome",
        "script": "scripts/04d-gnome.sh",
        "desc_key": "msg.shorin_gnome_desc",
    },
]


def _run_verbose(cmd: list[str], **kwargs) -> int:
    result = subprocess.run(cmd, **kwargs)
    return result.returncode


class ShorinSetup(Tool):
    name = "shorin-setup"
    display_name = "Shorin Arch Setup"
    description = "Clone and run shorin-arch-setup scripts for desktop environment configuration"
    distros = ["arch", "debian"]

    def _clone_repo(self) -> bool:
        if SHORIN_DIR.exists():
            import shutil
            shutil.rmtree(SHORIN_DIR)

        print_info(t("msg.cloning", repo="shorin-arch-setup"))
        code = _run_verbose(["git", "clone", "--depth", "1", SHORIN_REPO, str(SHORIN_DIR)])
        if code != 0:
            print_error(t("msg.clone_failed", repo="shorin-arch-setup"))
            return False
        return True

    def _run_arch_setup(self, script_path: str) -> bool:
        """Run shorin setup script on Arch."""
        full_path = SHORIN_DIR / script_path
        if not full_path.exists():
            print_error(t("msg.script_not_found", script=script_path))
            return False

        print_info(t("msg.running_script", script=script_path))
        # Make executable and run
        full_path.chmod(0o755)
        code = _run_verbose(["bash", str(full_path)])
        return code == 0

    def _run_ubuntu_setup(self, option_key: str) -> bool:
        """Run adapted setup for Ubuntu."""
        print_info(t("msg.shorin_ubuntu_mode"))

        # Add PPAs
        for ppa in ["ppa:avengemedia/danklinux", "ppa:avengemedia/dms"]:
            print_info(t("msg.adding_ppa", ppa=ppa))
            _run_verbose(["sudo", "add-apt-repository", "-y", ppa])

        print_info(t("msg.apt_update"))
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
            print_info(t("msg.installing", package=pkg))
            ok = _run_verbose(["sudo", "apt-get", "install", "-y", pkg])
            if ok != 0:
                print_error(t("msg.install_failed", package=pkg))
                return False
            print_success(t("msg.install_success", package=pkg))

        return True

    def run(self) -> bool:
        distro = detect_distro()

        choice = prompt_selection(t("msg.shorin_select"), SETUP_OPTIONS)

        if choice is None or choice == BACK_ACTION:
            return None

        selected = next((opt for opt in SETUP_OPTIONS if opt["id"] == choice), None)
        if selected is None:
            print_error(t("ui.invalid_selection"))
            return False

        # Clone the repo
        if not self._clone_repo():
            return False

        print_info(t("msg.selected_desktop", de=t(selected["name_key"])))

        if distro == "arch":
            return self._run_arch_setup(selected["script"])
        else:
            return self._run_ubuntu_setup(selected["id"])
