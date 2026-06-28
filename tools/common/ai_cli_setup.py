"""AI CLI Setup — one-click install of AI coding assistant CLI tools.

AI CLI 安装工具 — 一键安装 AI 编程助手命令行工具（Claude Code、Codex、Gemini、OpenCode、MiMo）。
"""

from tools.base import Tool
from . import ai_cli_setup_translations  # noqa: F401 - side-effect import for i18n registration
from utils.cmd_utils import run_cmd, run_verbose
from utils.distro import detect_distro
from utils.i18n import t
from utils.platform import IS_WINDOWS, command_exists
from utils.platform_services import package_install, packages_install
from utils.ui import print_success, print_error, print_info, console, prompt_selection, BACK_ACTION

MIN_NODE_MAJOR = 18  # Minimum required Node.js major version / 最低要求的 Node.js 主版本号

AI_CLI_OPTIONS = [  # Available AI CLI tool definitions / 可用的 AI CLI 工具定义列表
    {
        "id": "claude-code",
        "name_key": "msg.ai_cli_claude",        # Display name i18n key / 显示名称的国际化键
        "desc_key": "msg.ai_cli_claude_desc",    # Description i18n key / 描述的国际化键
        "package": "@anthropic-ai/claude-code",   # npm package name / npm 包名
    },
    {
        "id": "codex",
        "name_key": "msg.ai_cli_codex",
        "desc_key": "msg.ai_cli_codex_desc",
        "package": "@openai/codex",
    },
    {
        "id": "gemini",
        "name_key": "msg.ai_cli_gemini",
        "desc_key": "msg.ai_cli_gemini_desc",
        "package": "@google/gemini-cli",
    },
    {
        "id": "opencode",
        "name_key": "msg.ai_cli_opencode",
        "desc_key": "msg.ai_cli_opencode_desc",
        "package": "opencode-ai",
    },
    {
        "id": "mimo",
        "name_key": "msg.ai_cli_mimo",
        "desc_key": "msg.ai_cli_mimo_desc",
        "package": "@mimo-ai/cli",
    },
    {
        "id": "all",
        "name_key": "msg.ai_cli_all",       # Option to install all CLIs / 安装所有 CLI 的选项
        "desc_key": "msg.ai_cli_all_desc",
    },
]

DISTRO_NODEJS_PKGS = {  # Node.js package names mapped by distro family / 按发行版分类的 Node.js 包名映射
    "arch": ["nodejs", "npm"],    # Arch Linux packages / Arch Linux 包名
    "debian": ["nodejs", "npm"],  # Debian/Ubuntu packages / Debian/Ubuntu 包名
    "fedora": ["nodejs", "npm"],  # Fedora packages / Fedora 包名
    "suse": ["nodejs", "npm"],    # openSUSE packages / openSUSE 包名
}


# Check if Node.js is installed.
#
# 检查 Node.js 是否已安装。

def _has_nodejs() -> bool:
    return command_exists("node")


# Check if npm is installed.
#
# 检查 npm 是否已安装。

def _has_npm() -> bool:
    return command_exists("npm")


# Get installed Node.js version string.
#
# 获取已安装的 Node.js 版本字符串。

def _get_node_version() -> str | None:
    code, out = run_cmd(["node", "--version"])  # Run `node --version` / 执行 `node --version`
    if code == 0:
        return out  # Return version string like "v20.11.1" / 返回类似 "v20.11.1" 的版本字符串
    return None  # Node.js not found / 未找到 Node.js


# Parse a Node.js major version from strings like 'v20.11.1'.
#
# 从类似 'v20.11.1' 的字符串中解析 Node.js 主版本号。

def _parse_node_major(version: str | None) -> int | None:
    if not version:
        return None

    # Strip whitespace, remove leading 'v', then extract major part / 去除空白、去掉前缀 'v'，然后提取主版本部分
    major = version.strip().lstrip("v").split(".", 1)[0]
    if not major.isdigit():
        return None
    return int(major)


# Return True when Node.js satisfies the minimum supported version.
#
# 当 Node.js 版本满足最低支持版本要求时返回 True。

def _is_node_version_supported(version: str | None) -> bool:
    major = _parse_node_major(version)  # Parse major version number / 解析主版本号
    return major is not None and major >= MIN_NODE_MAJOR  # Check against minimum / 与最低版本要求比较


# Install Node.js and npm via the distro package manager.
#
# 通过发行版包管理器安装 Node.js 和 npm。

def _install_nodejs(distro: str) -> bool:
    print_info(t("msg.ai_cli_nodejs_installing"))

    if IS_WINDOWS:
        # Windows: winget ID differs from choco name — use :: mapping
        # Windows：winget ID 与 choco 包名不同 — 使用 :: 映射
        code = package_install("OpenJS.NodeJS.LTS::nodejs-lts", distro)
    else:
        # Linux: batch-install all required packages (one subprocess call)
        # Linux：批量安装所有必需软件包（一次子进程调用）
        pkgs = DISTRO_NODEJS_PKGS.get(distro)
        if pkgs is None:
            print_error(t("msg.ai_cli_nodejs_unknown"))
            return False
        code = packages_install(pkgs, distro)

    if code != 0:
        print_error(t("msg.ai_cli_nodejs_install_failed"))
        return False

    print_success(t("msg.ai_cli_nodejs_installed"))
    return True


# Check if an npm package is globally installed.
#
# 检查指定的 npm 包是否已全局安装。

def _is_npm_package_installed(package: str) -> bool:
    code, out = run_cmd(["npm", "list", "-g", package])  # Query global packages / 查询全局包
    return code == 0 and package in out  # Found if command succeeds and package in output / 命令成功且输出中包含该包即为已安装


# Install an npm package globally.
#
# 全局安装指定的 npm 包。

def _install_npm_package(package: str, display_name: str) -> bool:
    if _is_npm_package_installed(package):  # Skip if already installed / 如果已安装则跳过
        print_info(t("msg.ai_cli_already_installed", name=display_name))
        return True

    print_info(t("msg.ai_cli_installing", package=package))
    code = run_verbose(["npm", "install", "-g", package])  # Install globally via npm / 通过 npm 全局安装
    if code != 0:
        print_error(t("msg.ai_cli_install_failed", name=display_name))
        return False

    print_success(t("msg.ai_cli_install_success", name=display_name))
    return True


# Update a globally installed npm package to latest version.
#
# 将全局安装的 npm 包更新到最新版本。

def _update_npm_package(package: str, display_name: str) -> bool:
    if not _is_npm_package_installed(package):  # Cannot update what is not installed / 未安装则无法更新
        print_info(t("msg.ai_cli_not_installed", name=display_name))
        return False

    print_info(t("msg.ai_cli_updating", package=package))
    code = run_verbose(["npm", "install", "-g", f"{package}@latest"])  # Reinstall with @latest tag / 使用 @latest 标签重新安装
    if code != 0:
        print_error(t("msg.ai_cli_update_failed", name=display_name))
        return False

    print_success(t("msg.ai_cli_update_success", name=display_name))
    return True


# Return list of AI CLI options that are currently installed.
#
# 返回当前已安装的 AI CLI 工具列表。

def _get_installed_clis() -> list[dict]:
    installed = []
    for opt in AI_CLI_OPTIONS:
        if opt["id"] == "all":
            continue  # Skip the "install all" meta-option / 跳过"全部安装"元选项
        if _is_npm_package_installed(opt["package"]):
            installed.append(opt)  # Only include actually installed CLIs / 只包含实际已安装的 CLI
    return installed


# Update every installed AI CLI package from the shared npm package list.
#
# 更新所有已安装的 AI CLI 包到最新版本。

def update_installed_ai_clis() -> bool | None:
    if not _has_npm():
        print_error(t("msg.ai_cli_npm_not_found"))
        return False

    installed = _get_installed_clis()
    if not installed:
        print_info(t("msg.ai_cli_none_installed"))
        return None

    ok = True
    for opt in installed:  # Update each installed CLI one by one / 逐个更新已安装的 CLI
        display_name = t(opt["name_key"])
        if not _update_npm_package(opt["package"], display_name):
            ok = False  # Track any individual failure / 记录任何单个更新失败
    return ok


MAIN_MENU = [  # Main menu options for the AI CLI setup tool / AI CLI 安装工具的主菜单选项
    {
        "id": "install",
        "name_key": "msg.ai_cli_menu_install",
        "desc_key": "msg.ai_cli_menu_install_desc",
    },
    {
        "id": "update",
        "name_key": "msg.ai_cli_menu_update",
        "desc_key": "msg.ai_cli_menu_update_desc",
    },
]


class AiCliSetup(Tool):
    """AI CLI setup tool for installing and managing AI coding assistant CLIs.

    AI CLI 安装工具，用于安装和管理 AI 编程助手命令行工具。
    """

    name = "ai-cli-setup"  # Tool identifier / 工具标识符
    display_name = "AI CLI Setup"  # Human-readable display name / 人类可读的显示名称
    description = "One-click install AI coding assistant CLIs (Claude Code, Codex, Gemini, OpenCode, MiMo)"  # Tool description / 工具描述
    distros = ["arch", "debian", "fedora", "suse", "unknown", "windows"]  # Supported distros / 支持的发行版列表
    platforms = ["linux", "windows"]  # Supported platforms / 支持的平台列表
    requires_network = True  # Needs internet access / 需要网络连接
    requires_sudo = True  # Needs root privileges / 需要管理员权限

    # Ensure Node.js and npm are available. Returns False on failure.
    #
    # 确保 Node.js 和 npm 可用。失败时返回 False。

    def _ensure_nodejs(self, distro: str) -> bool:
        if not _has_nodejs():
            print_info(t("msg.ai_cli_nodejs_not_found"))
            if not _install_nodejs(distro):
                return False

        version = _get_node_version()
        if not _is_node_version_supported(version):
            print_error(
                t(
                    "msg.ai_cli_nodejs_version_too_old",
                    version=version or "unknown",
                    required=MIN_NODE_MAJOR,
                )
            )
            return False

        print_info(t("msg.ai_cli_nodejs_detected", version=version or "unknown"))

        if not _has_npm():
            print_error(t("msg.ai_cli_npm_not_found"))
            return False

        return True

    # Install flow: let user pick a CLI to install.
    #
    # 安装流程：让用户选择要安装的 CLI 工具。

    def _run_install(self) -> bool | None:
        choice = prompt_selection(t("msg.ai_cli_select"), AI_CLI_OPTIONS)

        if choice is None or choice == BACK_ACTION:
            return None

        console.print()

        if choice == "all":  # Install all AI CLIs / 安装所有 AI CLI
            ok = True
            for opt in AI_CLI_OPTIONS:
                if opt["id"] == "all":
                    continue  # Skip meta-option / 跳过元选项
                display_name = t(opt["name_key"])
                if not _install_npm_package(opt["package"], display_name):
                    ok = False  # Track any individual failure / 记录任何单个安装失败
            return ok

        selected = next((opt for opt in AI_CLI_OPTIONS if opt["id"] == choice), None)
        if selected is None:
            print_error(t("ui.invalid_selection"))
            return False

        display_name = t(selected["name_key"])
        return _install_npm_package(selected["package"], display_name)

    # Update flow: let user pick an installed CLI to update.
    #
    # 更新流程：让用户选择已安装的 CLI 工具进行更新。

    def _run_update(self) -> bool | None:
        installed = _get_installed_clis()
        if not installed:
            print_info(t("msg.ai_cli_none_installed"))
            return None

        # Build options: each installed CLI + "update all installed" / 构建选项：每个已安装的 CLI + "更新全部已安装"
        update_options = [
            {
                "id": opt["id"],
                "name_key": opt["name_key"],
                "desc_key": opt["desc_key"],
            }
            for opt in installed
        ]
        update_options.append({
            "id": "all-installed",
            "name_key": "msg.ai_cli_update_all",
            "desc_key": "msg.ai_cli_update_all_desc",
        })

        choice = prompt_selection(t("msg.ai_cli_update_select"), update_options)

        if choice is None or choice == BACK_ACTION:
            return None

        console.print()

        if choice == "all-installed":  # Update all installed CLIs at once / 一次性更新所有已安装的 CLI
            return update_installed_ai_clis()

        selected = next((opt for opt in installed if opt["id"] == choice), None)
        if selected is None:
            print_error(t("ui.invalid_selection"))
            return False

        display_name = t(selected["name_key"])
        return _update_npm_package(selected["package"], display_name)

    # Main entry point: ensure dependencies, then show install/update menu.
    #
    # 主入口：确保依赖项就绪，然后显示安装/更新菜单。

    def run(self) -> bool | None:
        distro = detect_distro()  # Detect Linux distribution / 检测 Linux 发行版

        if not self._ensure_nodejs(distro):
            return False

        # Main menu: Install / Update / 主菜单：安装 / 更新
        choice = prompt_selection(t("msg.ai_cli_menu"), MAIN_MENU)

        if choice is None or choice == BACK_ACTION:
            return None

        if choice == "install":
            return self._run_install()
        elif choice == "update":
            return self._run_update()

        return None
