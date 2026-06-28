"""Quick fixes for common Linux software issues.

提供常见 Linux 软件问题的一键修复功能。
"""

import getpass
import os
import stat
from pathlib import Path

from tools.base import Tool
from . import quick_fixes_translations  # noqa: F401 - side-effect import for i18n registration
from utils.cmd_utils import run_cmd, run_verbose
from utils.i18n import t
from utils.platform import command_exists
from utils.shell import get_rc_file, get_refresh_cmd
from utils.ui import print_success, print_error, print_info, print_warning, ask, confirm, console, prompt_selection, BACK_ACTION

# List of available quick fix options with i18n keys for name and description.
# 可用的快速修复选项列表，包含名称和描述的国际化键。
FIX_OPTIONS = [
    {
        "id": "stm32cubemx-wayland",  # Fix STM32CubeMX blank popup on Wayland / 修复 STM32CubeMX 在 Wayland 下弹窗空白问题
        "name_key": "msg.qfix_stm32cubemx",
        "desc_key": "msg.qfix_stm32cubemx_desc",
    },
    {
        "id": "git-proxy",  # Configure Git proxy settings / 配置 Git 代理设置
        "name_key": "msg.qfix_git_proxy",
        "desc_key": "msg.qfix_git_proxy_desc",
    },
    {
        "id": "npm-permissions",  # Fix npm global directory permissions / 修复 npm 全局目录权限
        "name_key": "msg.qfix_npm_permissions",
        "desc_key": "msg.qfix_npm_permissions_desc",
    },
    {
        "id": "docker-group",  # Add current user to docker group / 将当前用户添加到 docker 组
        "name_key": "msg.qfix_docker_group",
        "desc_key": "msg.qfix_docker_group_desc",
    },
]

# Common installation paths for STM32CubeMX.
# STM32CubeMX 的常见安装路径。
STM32_SEARCH_PATHS = [
    Path.home() / "software" / "stm32cubemx",
    Path("/opt/stm32cubemx"),
    Path("/usr/local/stm32cubemx"),
    Path.home() / "STM32CubeMX",
    Path.home() / "software" / "STM32CubeMX",
]

# Bash wrapper script template that forces X11 backend to fix Wayland display issues.
# Bash 包装脚本模板，强制使用 X11 后端以修复 Wayland 显示问题。
WRAPPER_TEMPLATE = """\
#!/bin/bash
# Auto-generated wrapper for STM32CubeMX on Wayland
# STM32CubeMX 的 Wayland 自动生成包装脚本
# Fixes blank popup/dialog windows by forcing X11 backend
# 通过强制 X11 后端修复弹窗/对话框空白问题

export GDK_BACKEND=x11
export SWT_GTK3=0
export _JAVA_AWT_WM_NONREPARENTING=1

exec java \\
  -Dsun.java2d.opengl=false \\
  -Dsun.java2d.xrender=false \\
  -Dawt.useSystemAAFontSettings=on \\
  -Dswing.aatext=true \\
  -Dswt.enable.autoScale=false \\
  -Dswt.autoScale=false \\
  -jar "{cubemx_path}" "$@"
"""

# Desktop entry template for the Wayland-fixed STM32CubeMX launcher.
# 为修复 Wayland 问题的 STM32CubeMX 启动器提供的桌面条目模板。
DESKTOP_TEMPLATE = """\
[Desktop Entry]
Name=STM32CubeMX (Wayland Fix)
Comment=STM32CubeMX with Wayland compatibility fix
Exec={wrapper_path}
Icon=stm32cubemx
Terminal=false
Type=Application
Categories=Development;Electronics;
"""


def _find_stm32cubemx() -> Path | None:
    """Search for STM32CubeMX installation across common paths.

    在常见路径中搜索 STM32CubeMX 安装目录。

    Returns:
        Path to the STM32CubeMX executable, or None if not found.
        STM32CubeMX 可执行文件路径，未找到则返回 None。
    """
    for base in STM32_SEARCH_PATHS:
        if not base.is_dir():
            continue
        # Check for jar file
        # 检查 jar 文件
        jar = base / "STM32CubeMX"
        if jar.is_file():
            return jar
        # Check for alternative names
        # 检查其他可能的文件名
        for name in ["STM32CubeMX.exe", "stm32cubemx.jar"]:
            alt = base / name
            if alt.is_file():
                return alt
        # Search recursively (shallow) - only one level deep to avoid long scans
        # 浅层递归搜索（仅一层深度，避免长时间扫描）
        for f in base.glob("*STM32CubeMX*"):
            if f.is_file() and os.access(f, os.X_OK):
                return f
    return None


def _create_wrapper(cubemx_path: Path) -> Path | None:
    """Create a wrapper script that forces X11 backend for STM32CubeMX.

    创建一个强制使用 X11 后端的 STM32CubeMX 包装脚本。

    Args:
        cubemx_path: Path to the original STM32CubeMX executable.
                     原始 STM32CubeMX 可执行文件路径。

    Returns:
        Path to the created wrapper script, or None on failure.
        创建的包装脚本路径，失败则返回 None。
    """
    wrapper_dir = Path.home() / ".local" / "bin"
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    content = WRAPPER_TEMPLATE.format(cubemx_path=cubemx_path)

    # Create as "STM32CubeMX" so it shadows the original in PATH.
    # 命名为 "STM32CubeMX" 以在 PATH 中覆盖原始文件。
    wrapper_path = wrapper_dir / "STM32CubeMX"
    try:
        wrapper_path.write_text(content)
        wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError as e:
        print_error(t("msg.qfix_wrapper_failed", error=str(e)))
        return None

    # Also create lowercase variant (some distros install as stm32cubemx).
    # 同时创建小写变体（某些发行版以 stm32cubemx 安装）。
    lower_path = wrapper_dir / "stm32cubemx"
    try:
        if lower_path.exists() or lower_path.is_symlink():
            lower_path.unlink()
        lower_path.symlink_to(wrapper_path)
    except OSError:
        pass

    # Also create the -fixed.sh variant for explicit naming.
    # 同时创建 -fixed.sh 变体以便明确标识。
    fixed_path = wrapper_dir / "STM32CubeMX-fixed.sh"
    try:
        if fixed_path.exists() or fixed_path.is_symlink():
            fixed_path.unlink()
        fixed_path.symlink_to(wrapper_path)
    except OSError:
        pass

    return wrapper_path


def _create_desktop_file(wrapper_path: Path) -> bool:
    """Create a .desktop entry file for the Wayland-fixed STM32CubeMX.

    为修复 Wayland 问题的 STM32CubeMX 创建 .desktop 桌面条目文件。

    Args:
        wrapper_path: Path to the wrapper script to use as the Exec command.
                      用作 Exec 命令的包装脚本路径。

    Returns:
        True if the desktop file was created successfully, False otherwise.
        成功创建桌面文件返回 True，否则返回 False。
    """
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = desktop_dir / "stm32cubemx.desktop"
    content = DESKTOP_TEMPLATE.format(wrapper_path=wrapper_path)
    try:
        desktop_file.write_text(content)
        desktop_file.chmod(desktop_file.stat().st_mode | stat.S_IXUSR)
        return True
    except OSError as e:
        print_error(t("msg.qfix_desktop_failed", error=str(e)))
        return False


class QuickFixes(Tool):
    """Tool providing one-click fixes for common Linux software issues.

    提供常见 Linux 软件问题一键修复的工具。

    Attributes:
        name: Unique identifier for the tool. / 工具唯一标识符。
        display_name: Human-readable display name. / 人类可读的显示名称。
        description: Brief description of the tool. / 工具的简要描述。
        distros: Supported Linux distribution identifiers. / 支持的 Linux 发行版标识符列表。
        requires_sudo: Whether the tool needs root privileges. / 工具是否需要 root 权限。
    """

    name = "quick-fixes"  # Tool identifier / 工具标识符
    display_name = "Quick Fixes"  # Display name shown in menu / 菜单中显示的名称
    description = "One-click fixes for common Linux software issues"  # Tool description / 工具描述
    distros = ["arch", "debian", "fedora", "suse", "unknown"]  # Supported distros / 支持的发行版
    requires_sudo = True  # Requires sudo for some fixes / 部分修复需要 sudo 权限

    def _fix_stm32cubemx_wayland(self) -> bool:
        """Fix STM32CubeMX blank popup/dialog issue on Wayland by creating an X11 wrapper.

        通过创建 X11 包装脚本，修复 STM32CubeMX 在 Wayland 下弹窗/对话框空白的问题。

        Returns:
            True if the fix was applied successfully, False otherwise.
            修复成功返回 True，否则返回 False。
        """
        # Step 1: Detect installation
        # 步骤 1：检测安装路径
        print_info(t("msg.qfix_detecting_path"))
        cubemx_path = _find_stm32cubemx()

        if cubemx_path is None:
            print_error(t("msg.qfix_not_found"))
            custom = ask(t("msg.qfix_enter_path")).strip()
            if not custom:
                return False
            cubemx_path = Path(custom).expanduser()
            if not cubemx_path.is_file():
                print_error(t("msg.qfix_path_invalid", path=str(cubemx_path)))
                return False

        print_success(t("msg.qfix_found", path=str(cubemx_path)))

        # Step 2: Create wrapper script
        # 步骤 2：创建包装脚本
        print_info(t("msg.qfix_creating_wrapper"))
        wrapper_path = _create_wrapper(cubemx_path)
        if wrapper_path is None:
            return False
        print_success(t("msg.qfix_wrapper_created", path=str(wrapper_path)))

        # Step 3: Create .desktop file
        # 步骤 3：创建 .desktop 桌面文件
        print_info(t("msg.qfix_creating_desktop"))
        if not _create_desktop_file(wrapper_path):
            return False
        desktop_path = Path.home() / ".local" / "share" / "applications" / "stm32cubemx.desktop"
        print_success(t("msg.qfix_desktop_created", path=str(desktop_path)))

        # Step 4: Summary
        # 步骤 4：显示修复结果摘要
        console.print()
        print_success(t("msg.qfix_success"))
        print_info(t("msg.qfix_usage_hint", wrapper=str(wrapper_path)))
        return True

    def _fix_git_proxy(self) -> bool:
        """Configure Git global proxy settings for HTTP and HTTPS.

        配置 Git 全局 HTTP 和 HTTPS 代理设置。

        Returns:
            True if proxy was configured successfully, False otherwise.
            代理配置成功返回 True，否则返回 False。
        """
        print_info(t("msg.qfix_git_proxy_configuring"))

        # Check current proxy settings
        # 检查当前代理设置
        code, current_http = run_cmd(["git", "config", "--global", "http.proxy"])
        code2, current_https = run_cmd(["git", "config", "--global", "https.proxy"])

        if current_http or current_https:
            print_info(t("msg.qfix_git_proxy_current", http=current_http or "none", https=current_https or "none"))
            if not confirm(t("msg.qfix_git_proxy_overwrite")):
                return False

        # Ask for proxy URL
        # 请求输入代理 URL
        proxy_url = ask(t("msg.qfix_git_proxy_enter")).strip()
        if not proxy_url:
            print_warning(t("msg.qfix_git_proxy_empty"))
            return False

        # Validate proxy URL format - default to http:// if no scheme specified.
        # 验证代理 URL 格式 - 未指定协议时默认使用 http://。
        if not proxy_url.startswith(("http://", "https://", "socks5://")):
            proxy_url = "http://" + proxy_url

        # Set proxy
        # 设置代理
        run_cmd(["git", "config", "--global", "http.proxy", proxy_url])
        run_cmd(["git", "config", "--global", "https.proxy", proxy_url])

        print_success(t("msg.qfix_git_proxy_set", proxy=proxy_url))
        return True

    def _fix_npm_permissions(self) -> bool:
        """Fix npm global directory permission issues by creating a user-owned directory.

        通过创建用户拥有的目录来修复 npm 全局目录权限问题。

        Returns:
            True if the fix was applied successfully, False otherwise.
            修复成功返回 True，否则返回 False。
        """
        print_info(t("msg.qfix_npm_configuring"))

        # Check if npm is installed
        # 检查 npm 是否已安装
        if not command_exists("npm"):
            print_error(t("msg.qfix_npm_not_found"))
            return False

        # Get npm global prefix
        # 获取 npm 全局安装前缀路径
        code, npm_prefix = run_cmd(["npm", "config", "get", "prefix"])
        if code != 0:
            print_error(t("msg.qfix_npm_prefix_failed"))
            return False

        # Check if it's already user-owned (writable by current user).
        # 检查目录是否已属于当前用户（当前用户可写）。
        npm_dir = Path(npm_prefix)
        if npm_dir.exists() and os.access(npm_dir, os.W_OK):
            print_info(t("msg.qfix_npm_already_ok"))
            return True

        # Create user-owned npm directory to avoid sudo for global installs.
        # 创建用户拥有的 npm 目录，避免全局安装时需要 sudo。
        user_npm_dir = Path.home() / ".npm-global"
        print_info(t("msg.qfix_npm_creating", dir=str(user_npm_dir)))

        try:
            user_npm_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print_error(t("msg.qfix_npm_create_failed", error=str(e)))
            return False

        # Set npm prefix to the user-owned directory.
        # 将 npm 前缀设置为用户拥有的目录。
        run_cmd(["npm", "config", "set", "prefix", str(user_npm_dir)])

        # Update PATH in shell profile so npm global binaries are accessible.
        # 更新 shell 配置文件中的 PATH，使 npm 全局二进制文件可访问。
        shell_profile = get_rc_file()
        if shell_profile is None:
            shell_profile = Path.home() / ".profile"  # fallback for cmd and unknown shells

        path_export = f'export PATH="{user_npm_dir}/bin:$PATH"'
        if shell_profile.exists():
            content = shell_profile.read_text()
            if path_export not in content:
                print_info(t("msg.qfix_npm_updating_profile", profile=str(shell_profile)))
                with open(shell_profile, "a") as f:
                    f.write(f"\n# npm global directory\n{path_export}\n")

        print_success(t("msg.qfix_npm_success", dir=str(user_npm_dir)))
        hint = get_refresh_cmd() or "restart your shell"
        print_info(t("msg.qfix_npm_reload_hint", hint=hint))
        return True

    def _fix_docker_group(self) -> bool:
        """Add the current user to the docker group so docker can run without sudo.

        将当前用户添加到 docker 组，使 docker 可以无需 sudo 运行。

        Returns:
            True if the user was added successfully, False otherwise.
            用户添加成功返回 True，否则返回 False。
        """
        print_info(t("msg.qfix_docker_configuring"))

        # Check if docker is installed
        # 检查 docker 是否已安装
        if not command_exists("docker"):
            print_error(t("msg.qfix_docker_not_found"))
            return False

        # Get current user
        # 获取当前用户名
        user = getpass.getuser()

        # Check if user is already in docker group
        # 检查用户是否已在 docker 组中
        code, groups = run_cmd(["groups", user])
        if "docker" in groups:
            print_info(t("msg.qfix_docker_already_in_group", user=user))
            return True

        # Check if docker group exists; create it if not.
        # 检查 docker 组是否存在，不存在则创建。
        code, _ = run_cmd(["getent", "group", "docker"])
        if code != 0:
            print_info(t("msg.qfix_docker_creating_group"))
            run_cmd(["sudo", "groupadd", "docker"])

        # Add user to docker group using usermod -aG (append mode).
        # 使用 usermod -aG 将用户添加到 docker 组（追加模式）。
        print_info(t("msg.qfix_docker_adding_user", user=user))
        code = run_verbose(["sudo", "usermod", "-aG", "docker", user])
        if code != 0:
            print_error(t("msg.qfix_docker_add_failed"))
            return False

        print_success(t("msg.qfix_docker_success", user=user))
        print_warning(t("msg.qfix_docker_logout_hint"))
        return True

    def run(self) -> bool | None:
        """Run the quick fix tool by presenting a menu and executing the selected fix.

        运行快速修复工具，显示菜单并执行用户选择的修复。

        Returns:
            True if fix succeeded, False if it failed, None if user went back.
            修复成功返回 True，失败返回 False，用户返回上一级返回 None。
        """
        choice = prompt_selection(t("msg.qfix_select"), FIX_OPTIONS)

        if choice is None or choice == BACK_ACTION:
            return None

        selected = next((opt for opt in FIX_OPTIONS if opt["id"] == choice), None)
        if selected is None:
            print_error(t("ui.invalid_selection"))
            return False

        console.print()

        if selected["id"] == "stm32cubemx-wayland":
            return self._fix_stm32cubemx_wayland()
        elif selected["id"] == "git-proxy":
            return self._fix_git_proxy()
        elif selected["id"] == "npm-permissions":
            return self._fix_npm_permissions()
        elif selected["id"] == "docker-group":
            return self._fix_docker_group()

        print_error(t("msg.qfix_not_implemented"))
        return False
