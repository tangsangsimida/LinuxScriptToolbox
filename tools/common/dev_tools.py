from tools.base import Tool
from utils.cmd_utils import run_cmd, run_verbose
from utils.distro import detect_distro
from utils.i18n import t
from utils.ui import print_success, print_error, print_info, console, prompt_selection, BACK_ACTION

TOOLCHAIN_OPTIONS = [
    {
        "id": "arm-gcc",
        "name_key": "msg.devtool_arm_gcc",
        "desc_key": "msg.devtool_arm_gcc_desc",
        "arch_pkgs": ["arm-none-eabi-gcc", "arm-none-eabi-newlib"],
        "debian_pkgs": ["gcc-arm-none-eabi", "libnewlib-arm-none-eabi", "gdb-multiarch"],
        "fedora_pkgs": ["arm-none-eabi-gcc", "arm-none-eabi-newlib"],
        "suse_pkgs": ["arm-none-eabi-gcc", "arm-none-eabi-newlib"],
    },
    {
        "id": "riscv-gcc",
        "name_key": "msg.devtool_riscv_gcc",
        "desc_key": "msg.devtool_riscv_gcc_desc",
        "arch_pkgs": ["riscv64-elf-gcc", "riscv64-elf-newlib"],
        "debian_pkgs": ["gcc-riscv64-linux-gnu", "gdb-multiarch"],
        "fedora_pkgs": ["gcc-riscv64-linux-gnu", "gdb-multiarch"],
        "suse_pkgs": ["riscv64-linux-gnu-gcc", "gdb-multiarch"],
    },
    {
        "id": "all",
        "name_key": "msg.devtool_all",
        "desc_key": "msg.devtool_all_desc",
    },
]


def _is_installed(pkg: str, distro: str) -> bool:
    if distro == "arch":
        cmd = ["pacman", "-Qi", pkg]
    elif distro in ("fedora", "suse"):
        cmd = ["rpm", "-q", pkg]
    else:
        cmd = ["dpkg", "-s", pkg]
    code, _ = run_cmd(cmd)
    return code == 0


def _install_packages(pkgs: list[str], distro: str) -> bool:
    if distro == "arch":
        code = run_verbose(["sudo", "pacman", "-S", "--noconfirm"] + pkgs)
    elif distro == "fedora":
        code = run_verbose(["sudo", "dnf", "install", "-y"] + pkgs)
    elif distro == "suse":
        code = run_verbose(["sudo", "zypper", "install", "-y"] + pkgs)
    else:
        if run_verbose(["sudo", "apt-get", "update", "-qq"]) != 0:
            print_error(t("msg.devtool_install_failed"))
            return False
        code = run_verbose(["sudo", "apt-get", "install", "-y"] + pkgs)
    return code == 0


class DevToolsSetup(Tool):
    name = "dev-tools"
    display_name = "Dev Tools Setup"
    description = "Quick install embedded toolchains (ARM GCC, RISC-V GCC)"
    distros = ["arch", "debian", "fedora", "suse"]
    requires_network = True
    requires_sudo = True

    def _install_toolchain(self, option: dict, distro: str) -> bool:
        if distro == "arch":
            pkgs = option.get("arch_pkgs", [])
        elif distro == "fedora":
            pkgs = option.get("fedora_pkgs", option.get("debian_pkgs", []))
        elif distro == "suse":
            pkgs = option.get("suse_pkgs", option.get("debian_pkgs", []))
        else:
            pkgs = option.get("debian_pkgs", [])

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

    def run(self) -> bool | None:
        distro = detect_distro()

        choice = prompt_selection(t("msg.devtool_select"), TOOLCHAIN_OPTIONS)

        if choice is None or choice == BACK_ACTION:
            return None

        if choice == "all":
            console.print()
            ok = True
            for opt in TOOLCHAIN_OPTIONS:
                if opt["id"] == "all":
                    continue
                if not self._install_toolchain(opt, distro):
                    ok = False
            return ok

        selected = next((opt for opt in TOOLCHAIN_OPTIONS if opt["id"] == choice), None)
        if selected is None:
            print_error(t("ui.invalid_selection"))
            return False

        console.print()
        return self._install_toolchain(selected, distro)
