import subprocess

from tools.base import Tool
from utils.distro import detect_distro
from utils.i18n import t
from utils.ui import print_success, print_error, print_info, ask, console, prompt_selection, BACK_ACTION

TOOLCHAIN_OPTIONS = [
    {
        "id": "arm-gcc",
        "name_key": "msg.devtool_arm_gcc",
        "desc_key": "msg.devtool_arm_gcc_desc",
        "arch_pkgs": ["arm-none-eabi-gcc", "arm-none-eabi-newlib"],
        "debian_pkgs": ["gcc-arm-none-eabi", "libnewlib-arm-none-eabi", "gdb-multiarch"],
    },
    {
        "id": "riscv-gcc",
        "name_key": "msg.devtool_riscv_gcc",
        "desc_key": "msg.devtool_riscv_gcc_desc",
        "arch_pkgs": ["riscv64-elf-gcc", "riscv64-elf-newlib"],
        "debian_pkgs": ["gcc-riscv64-linux-gnu", "gdb-multiarch"],
    },
]


def _run_verbose(cmd: list[str]) -> int:
    result = subprocess.run(cmd)
    return result.returncode


def _is_installed(pkg: str, distro: str) -> bool:
    if distro == "arch":
        return subprocess.run(["pacman", "-Qi", pkg], capture_output=True).returncode == 0
    return subprocess.run(["dpkg", "-s", pkg], capture_output=True).returncode == 0


def _install_packages(pkgs: list[str], distro: str) -> bool:
    if distro == "arch":
        code = _run_verbose(["sudo", "pacman", "-S", "--noconfirm"] + pkgs)
    else:
        if _run_verbose(["sudo", "apt-get", "update", "-qq"]) != 0:
            print_error(t("msg.devtool_install_failed"))
            return False
        code = _run_verbose(["sudo", "apt-get", "install", "-y"] + pkgs)
    return code == 0


class DevToolsSetup(Tool):
    name = "dev-tools"
    display_name = "Dev Tools Setup"
    description = "Quick install embedded toolchains (ARM GCC, RISC-V GCC)"
    distros = ["arch", "debian"]

    def _install_toolchain(self, option: dict, distro: str) -> bool:
        pkgs = option["arch_pkgs"] if distro == "arch" else option["debian_pkgs"]

        # Filter out already-installed packages
        to_install = [p for p in pkgs if not _is_installed(p, distro)]
        if not to_install:
            print_info(t("msg.devtool_already_installed", toolchain=t(option["name_key"])))
            return True

        print_info(t("msg.devtool_installing", packages=", ".join(to_install)))
        if not _install_packages(to_install, distro):
            print_error(t("msg.devtool_install_failed"))
            return False

        print_success(t("msg.devtool_install_success", toolchain=t(option["name_key"])))
        return True

    def run(self) -> bool:
        distro = detect_distro()

        choice = prompt_selection(t("msg.devtool_select"), TOOLCHAIN_OPTIONS)

        if choice is None or choice == BACK_ACTION:
            return None

        selected = next((opt for opt in TOOLCHAIN_OPTIONS if opt["id"] == choice), None)
        if selected is None:
            print_error(t("ui.invalid_selection"))
            return False

        console.print()
        return self._install_toolchain(selected, distro)
