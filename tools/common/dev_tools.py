"""Development tools setup module for embedded toolchain installation.

开发工具设置模块，用于嵌入式工具链的安装。
"""

from tools.base import Tool
from . import dev_tools_translations  # noqa: F401 - side-effect import for i18n registration
from utils.distro import detect_distro
from utils.i18n import t
from utils.platform_services import package_is_installed, packages_install
from utils.ui import print_success, print_error, print_info, console, prompt_selection, BACK_ACTION

# Available toolchain options with per-distro package mappings
# 可用的工具链选项，包含各发行版的包映射
TOOLCHAIN_OPTIONS = [
    {
        "id": "arm-gcc",  # ARM GNU Compiler Collection / ARM GNU编译器集合
        "name_key": "msg.devtool_arm_gcc",
        "desc_key": "msg.devtool_arm_gcc_desc",
        "arch_pkgs": ["arm-none-eabi-gcc", "arm-none-eabi-newlib"],
        "debian_pkgs": ["gcc-arm-none-eabi", "libnewlib-arm-none-eabi", "gdb-multiarch"],
        "fedora_pkgs": ["arm-none-eabi-gcc", "arm-none-eabi-newlib"],
        "suse_pkgs": ["arm-none-eabi-gcc", "arm-none-eabi-newlib"],
    },
    {
        "id": "riscv-gcc",  # RISC-V GNU Compiler Collection / RISC-V GNU编译器集合
        "name_key": "msg.devtool_riscv_gcc",
        "desc_key": "msg.devtool_riscv_gcc_desc",
        "arch_pkgs": ["riscv64-elf-gcc", "riscv64-elf-newlib"],
        "debian_pkgs": ["gcc-riscv64-linux-gnu", "gdb-multiarch"],
        "fedora_pkgs": ["gcc-riscv64-linux-gnu", "gdb-multiarch"],
        "suse_pkgs": ["riscv64-linux-gnu-gcc", "gdb-multiarch"],
    },
    {
        "id": "all",  # Install all toolchains / 安装所有工具链
        "name_key": "msg.devtool_all",
        "desc_key": "msg.devtool_all_desc",
    },
]


# Install a list of packages using the distro's native package manager.
#
# 使用发行版的原生包管理器安装一组软件包。
#
# Args:
#     pkgs: List of package names to install. / 要安装的软件包名称列表。
#     distro: Distribution identifier (arch, fedora, suse, debian, etc.). / 发行版标识符。
#
# Returns:
#     True if all packages installed successfully, False otherwise. / 全部安装成功返回 True，否则返回 False。
def _install_packages(pkgs: list[str], distro: str) -> bool:
    """Install packages using batch mode (one subprocess call). / 批量安装（一次子进程调用）。"""
    return packages_install(pkgs, distro) == 0


class DevToolsSetup(Tool):
    """Tool for setting up embedded development toolchains.

    嵌入式开发工具链的安装设置工具。

    Supports ARM GCC and RISC-V GCC toolchains across multiple Linux distributions.
    支持在多个 Linux 发行版上安装 ARM GCC 和 RISC-V GCC 工具链。

    Attributes:
        name: Unique tool identifier. / 工具唯一标识符。
        display_name: Human-readable tool name. / 人类可读的工具名称。
        description: Brief description of the tool. / 工具的简要描述。
        distros: Supported Linux distributions. / 支持的 Linux 发行版列表。
        requires_network: Whether the tool needs network access. / 工具是否需要网络访问。
        requires_sudo: Whether the tool needs sudo privileges. / 工具是否需要 sudo 权限。
    """

    name = "dev-tools"  # Unique tool identifier / 工具唯一标识符
    display_name = "Dev Tools Setup"  # Display name shown in menu / 菜单中显示的名称
    description = "Quick install embedded toolchains (ARM GCC, RISC-V GCC)"  # Tool description / 工具描述
    distros = ["arch", "debian", "fedora", "suse"]  # Supported distros / 支持的发行版
    group = "dev"  # Menu group / 菜单分组
    requires_network = True  # Package download requires network / 下载安装包需要网络
    requires_sudo = True  # Package installation requires root privileges / 安装包需要 root 权限

    # Install a specific toolchain for the detected distribution.
    #
    # 为检测到的发行版安装指定的工具链。
    #
    # Args:
    #     option: Toolchain option dict containing package lists per distro. / 包含各发行版软件包列表的工具链选项字典。
    #     distro: Detected distribution identifier. / 检测到的发行版标识符。
    #
    #
    # Returns:
    #     True if installation succeeded or already installed, False on failure. / 安装成功或已安装返回 True，安装失败返回 False。

    def _install_toolchain(self, option: dict, distro: str) -> bool:
        # Select distro-specific package list, falling back to debian_pkgs as default
        # 选择发行版特定的包列表，默认回退到 debian_pkgs
        if distro == "arch":
            pkgs = option.get("arch_pkgs", [])
        elif distro == "fedora":
            pkgs = option.get("fedora_pkgs", option.get("debian_pkgs", []))
        elif distro == "suse":
            pkgs = option.get("suse_pkgs", option.get("debian_pkgs", []))
        else:
            pkgs = option.get("debian_pkgs", [])

        # Filter out already-installed packages / 过滤掉已安装的包
        to_install = [p for p in pkgs if not package_is_installed(p, distro)]
        if not to_install:
            print_info(t("msg.devtool_already_installed", toolchain=t(option["name_key"])))
            return True

        print_info(t("msg.devtool_installing", packages=", ".join(to_install)))
        if not _install_packages(to_install, distro):
            print_error(t("msg.devtool_install_failed"))
            return False

        print_success(t("msg.devtool_install_success", toolchain=t(option["name_key"])))
        return True

    # Execute the dev tools setup workflow.
    #
    # 执行开发工具设置工作流程。
    #
    # Prompts the user to select a toolchain, then installs it.
    # 提示用户选择一个工具链，然后进行安装。
    #
    # Returns:
    #     True if installation succeeded, False on failure, None if user cancelled.
    #     安装成功返回 True，失败返回 False，用户取消返回 None。

    def run(self) -> bool | None:
        distro = detect_distro()

        choice = prompt_selection(t("msg.devtool_select"), TOOLCHAIN_OPTIONS)

        # User cancelled or went back / 用户取消或返回上一级
        if choice is None or choice == BACK_ACTION:
            return None

        # "all" option: install every toolchain except the "all" entry itself
        # "all" 选项：安装除 "all" 条目本身以外的所有工具链
        if choice == "all":
            console.print()
            ok = True
            for opt in TOOLCHAIN_OPTIONS:
                if opt["id"] == "all":
                    continue
                if not self._install_toolchain(opt, distro):
                    ok = False
            return ok

        # Single toolchain selection / 单个工具链选择
        selected = next((opt for opt in TOOLCHAIN_OPTIONS if opt["id"] == choice), None)
        if selected is None:
            print_error(t("ui.invalid_selection"))
            return False

        console.print()
        return self._install_toolchain(selected, distro)
