"""Shorin Arch Setup tool for desktop environment configuration.

Shorin Arch Setup 桌面环境配置工具。

This tool clones the shorin-arch-setup repository and runs setup scripts
to configure various desktop environments (Niri, DMS, KDE, GNOME) across
multiple Linux distributions (Arch, Ubuntu/Debian, Fedora, openSUSE).

该工具克隆 shorin-arch-setup 仓库并运行安装脚本，在多种 Linux 发行版
（Arch、Ubuntu/Debian、Fedora、openSUSE）上配置各类桌面环境
（Niri、DMS、KDE、GNOME）。
"""

import shutil
from pathlib import Path

from tools.base import Tool
from . import shorin_setup_translations  # noqa: F401 - side-effect import for i18n registration
from utils.cmd_utils import run_verbose
from utils.distro import detect_distro
from utils.i18n import t
from utils.ui import (
    print_success,
    print_error,
    print_info,
    print_warning,
    confirm,
    prompt_selection,
    BACK_ACTION,
)

# Remote Git repository URL for shorin-arch-setup / shorin-arch-setup 的远程 Git 仓库地址
SHORIN_REPO = "https://github.com/SHORiN-KiWATA/shorin-arch-setup.git"

# Local directory to clone the repository into / 克隆仓库的本地目标目录
SHORIN_DIR = Path("/tmp/shorin-arch-setup")

# Available desktop environment setup options with i18n keys and scripts /
# 可用的桌面环境配置选项，包含国际化键名和对应脚本路径
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


class ShorinSetup(Tool):
    """Tool for cloning and running shorin-arch-setup desktop environment scripts.

    克隆并运行 shorin-arch-setup 桌面环境安装脚本的工具。

    Supports Arch Linux (native scripts), Ubuntu/Debian (adapted via PPAs),
    Fedora (adapted via dnf groups), and openSUSE (adapted via zypper patterns).

    支持 Arch Linux（原生脚本）、Ubuntu/Debian（通过 PPA 适配）、
    Fedora（通过 dnf 软件包组适配）和 openSUSE（通过 zypper 模式适配）。
    """

    name = "shorin-setup"  # Internal tool identifier / 工具内部标识符
    display_name = "Shorin Arch Setup"  # Display name shown to user / 向用户展示的显示名称
    description = "Clone and run shorin-arch-setup scripts for desktop environment configuration"  # Tool description / 工具描述
    distros = ["arch", "debian", "fedora", "suse", "alinux"]  # Supported distributions / 支持的发行版列表
    group = "env"  # Menu group / 菜单分组
    requires_network = True  # Requires internet access for git clone / 需要网络连接以进行 git clone
    requires_sudo = True  # Requires sudo for package installation / 需要 sudo 权限以安装软件包

    # Clone the shorin-arch-setup repository to a local temp directory.
    #
    # 克隆 shorin-arch-setup 仓库到本地临时目录。
    #
    # Returns:
    #     True if cloning succeeded, False otherwise.
    #     克隆成功返回 True，否则返回 False。

    def _clone_repo(self) -> bool:
        # Remove existing clone to ensure a fresh copy / 删除已有克隆以确保获取全新副本
        if SHORIN_DIR.exists():
            shutil.rmtree(SHORIN_DIR)

        print_info(t("msg.cloning", repo="shorin-arch-setup"))
        code = run_verbose(["git", "clone", "--depth", "1", SHORIN_REPO, str(SHORIN_DIR)])
        if code != 0:
            print_error(t("msg.clone_failed", repo="shorin-arch-setup"))
            return False
        return True

    # Run shorin setup script directly on Arch Linux.
    #
    # 在 Arch Linux 上直接运行 shorin 安装脚本。
    #
    # Args:
    #     script_path: Relative path to the setup script within the cloned repo.
    #     克隆仓库中安装脚本的相对路径。
    #
    #
    # Returns:
    #     True if the script ran successfully, False otherwise.
    #     脚本运行成功返回 True，否则返回 False。

    def _run_arch_setup(self, script_path: str) -> bool:
        full_path = SHORIN_DIR / script_path
        if not full_path.exists():
            print_error(t("msg.script_not_found", script=script_path))
            return False

        print_info(t("msg.running_script", script=script_path))
        # Make the script executable before running via bash / 通过 bash 运行前先将脚本设为可执行
        full_path.chmod(0o755)
        code = run_verbose(["bash", str(full_path)])
        return code == 0

    # Run adapted desktop environment setup for Ubuntu/Debian.
    #
    # 为 Ubuntu/Debian 运行适配后的桌面环境安装。
    #
    # Instead of using the native Arch scripts, this method installs desktop
    # environments via Ubuntu PPAs and apt packages that provide equivalent
    # functionality.
    #
    # 该方法不使用原生 Arch 脚本，而是通过 Ubuntu PPA 和 apt 软件包
    # 安装提供等效功能的桌面环境。
    #
    # Args:
    #     option_key: The desktop environment identifier (e.g. "niri", "dms", "kde", "gnome").
    #     桌面环境标识符（如 "niri"、"dms"、"kde"、"gnome"）。
    #
    #
    # Returns:
    #     True if all packages installed successfully, False otherwise.
    #     所有软件包安装成功返回 True，否则返回 False。

    def _run_ubuntu_setup(self, option_key: str) -> bool:
        print_info(t("msg.shorin_ubuntu_mode"))

        # Add third-party PPAs required for desktop environment packages /
        # 添加桌面环境软件包所需的第三方 PPA 源
        for ppa in ["ppa:avengemedia/danklinux", "ppa:avengemedia/dms"]:
            print_info(t("msg.adding_ppa", ppa=ppa))
            run_verbose(["sudo", "add-apt-repository", "-y", ppa])

        # Refresh package lists after adding new sources / 添加新源后刷新软件包列表
        print_info(t("msg.apt_update"))
        run_verbose(["sudo", "apt-get", "update", "-qq"])

        # Map option key to the corresponding Ubuntu package list /
        # 将选项键映射到对应的 Ubuntu 软件包列表
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
            ok = run_verbose(["sudo", "apt-get", "install", "-y", pkg])
            if ok != 0:
                print_error(t("msg.install_failed", package=pkg))
                return False
            print_success(t("msg.install_success", package=pkg))

        return True

    # Run adapted desktop environment setup for Fedora.
    #
    # 为 Fedora 运行适配后的桌面环境安装。
    #
    # Uses Fedora's dnf package manager and package groups to install
    # desktop environments equivalent to the Arch-based shorin scripts.
    #
    # 使用 Fedora 的 dnf 包管理器和软件包组来安装与 Arch 版 shorin
    # 脚本等效的桌面环境。
    #
    # Args:
    #     option_key: The desktop environment identifier (e.g. "niri", "dms", "kde", "gnome").
    #     桌面环境标识符（如 "niri"、"dms"、"kde"、"gnome"）。
    #
    #
    # Returns:
    #     True if all packages installed successfully, False otherwise.
    #     所有软件包安装成功返回 True，否则返回 False。

    def _run_fedora_setup(self, option_key: str) -> bool:
        print_info(t("msg.shorin_fedora_mode"))

        # Map option key to the corresponding Fedora package list /
        # 将选项键映射到对应的 Fedora 软件包列表
        if option_key == "niri":
            pkgs = ["niri"]
        elif option_key == "dms":
            print_warning(t("msg.shorin_dms_manual"))
            return False
        elif option_key == "kde":
            pkgs = ["@kde-desktop", "sddm"]
        elif option_key == "gnome":
            pkgs = ["@workstation-product", "gdm"]
        else:
            return False

        for pkg in pkgs:
            print_info(t("msg.installing", package=pkg))
            ok = run_verbose(["sudo", "dnf", "install", "-y", pkg])
            if ok != 0:
                print_error(t("msg.install_failed", package=pkg))
                return False
            print_success(t("msg.install_success", package=pkg))

        return True

    # Run adapted desktop environment setup for openSUSE.
    #
    # 为 openSUSE 运行适配后的桌面环境安装。
    #
    # Uses openSUSE's zypper package manager and software patterns to install
    # desktop environments. Note that Niri and DMS are not available on openSUSE.
    #
    # 使用 openSUSE 的 zypper 包管理器和软件模式来安装桌面环境。
    # 注意 Niri 和 DMS 在 openSUSE 上不可用。
    #
    # Args:
    #     option_key: The desktop environment identifier (e.g. "niri", "dms", "kde", "gnome").
    #     桌面环境标识符（如 "niri"、"dms"、"kde"、"gnome"）。
    #
    #
    # Returns:
    #     True if all packages installed successfully, False if unsupported or failed.
    #     所有软件包安装成功返回 True，不支持或失败返回 False。

    def _run_suse_setup(self, option_key: str) -> bool:
        print_info(t("msg.shorin_suse_mode"))

        # Map option key to the corresponding openSUSE package list;
        # Niri and DMS are not packaged for openSUSE /
        # 将选项键映射到对应的 openSUSE 软件包列表；
        # Niri 和 DMS 没有 openSUSE 软件包
        if option_key == "niri":
            print_warning(t("msg.shorin_niri_not_available"))
            return False
        elif option_key == "dms":
            print_warning(t("msg.shorin_dms_manual"))
            return False
        elif option_key == "kde":
            pkgs = ["patterns-kde-kde_plasma", "sddm"]
        elif option_key == "gnome":
            pkgs = ["patterns-gnome-gnome", "gdm"]
        else:
            return False

        for pkg in pkgs:
            print_info(t("msg.installing", package=pkg))
            ok = run_verbose(["sudo", "zypper", "install", "-y", pkg])
            if ok != 0:
                print_error(t("msg.install_failed", package=pkg))
                return False
            print_success(t("msg.install_success", package=pkg))

        return True

    # Main entry point: prompt user to select a desktop environment and install it.
    #
    # 主入口：提示用户选择桌面环境并进行安装。
    #
    # Detects the current Linux distribution, presents available desktop
    # environment options, confirms the external repository usage with the
    # user, then dispatches to the appropriate distro-specific setup method.
    #
    # 检测当前 Linux 发行版，展示可用的桌面环境选项，向用户确认
    # 使用外部仓库，然后分派到相应的发行版专属安装方法。
    #
    # Returns:
    #     True if setup completed successfully, False on error, None if user cancelled.
    #     安装成功返回 True，出错返回 False，用户取消返回 None。

    def run(self) -> bool | None:
        # Detect current distribution to choose the right setup strategy /
        # 检测当前发行版以选择正确的安装策略
        distro = detect_distro()

        # Prompt user to select which desktop environment to install /
        # 提示用户选择要安装的桌面环境
        choice = prompt_selection(t("msg.shorin_select"), SETUP_OPTIONS)

        if choice is None or choice == BACK_ACTION:
            return None

        # Find the matching option dictionary by its id /
        # 通过 id 查找匹配的选项字典
        selected = next((opt for opt in SETUP_OPTIONS if opt["id"] == choice), None)
        if selected is None:
            print_error(t("ui.invalid_selection"))
            return False

        # Confirm before cloning an external repository /
        # 克隆外部仓库前进行确认
        if not confirm(t("msg.shorin_confirm_external", repo=SHORIN_REPO, script=selected["script"])):
            return None

        # Clone the remote shorin-arch-setup repository /
        # 克隆远程 shorin-arch-setup 仓库
        if not self._clone_repo():
            return False

        print_info(t("msg.selected_desktop", de=t(selected["name_key"])))

        # Dispatch to the distro-specific setup method based on detected distro /
        # 根据检测到的发行版分派到对应的专属安装方法
        if distro == "arch":
            return self._run_arch_setup(selected["script"])
        elif distro == "fedora":
            return self._run_fedora_setup(selected["id"])
        elif distro == "suse":
            return self._run_suse_setup(selected["id"])
        else:
            # Default to Ubuntu/Debian path for all other distributions /
            # 其他所有发行版默认使用 Ubuntu/Debian 安装路径
            return self._run_ubuntu_setup(selected["id"])
