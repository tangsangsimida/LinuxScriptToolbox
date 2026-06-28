"""Platform-aware service management, package operations, and OS info.

平台感知的服务管理、包操作和系统信息。

Provides a unified API so tool-layer code avoids direct IS_WINDOWS branching
for common operations (service control, package install, OS version).

提供统一 API，使工具层代码无需直接使用 IS_WINDOWS 分支即可完成
常见操作（服务控制、包安装、系统版本）。
"""

import platform as platform_mod

from utils.cmd_utils import run_cmd, run_verbose
from utils.platform import IS_WINDOWS, command_exists, detect_platform


# ── PowerShell execution ────────────────────────────────────────

def run_ps(command: str) -> tuple[int, str]:
    """Execute a PowerShell command and return (returncode, output).

    执行 PowerShell 命令并返回 (返回码, 输出)。

    Args:
        command: PowerShell command string / PowerShell 命令字符串

    Returns:
        (returncode, stdout_stripped) / (返回码, 去除空白的 stdout)
    """
    return run_cmd(["powershell", "-NoProfile", "-Command", command])


# ── Service management ──────────────────────────────────────────

def service_start(service: str) -> tuple[int, str]:
    """Start a system service. / 启动系统服务。"""
    if IS_WINDOWS:
        return run_ps(f"Start-Service {service}")
    return run_cmd(["sudo", "systemctl", "start", service])


def service_stop(service: str) -> tuple[int, str]:
    """Stop a system service. / 停止系统服务。"""
    if IS_WINDOWS:
        return run_ps(f"Stop-Service {service}")
    return run_cmd(["sudo", "systemctl", "stop", service])


def service_restart(service: str) -> tuple[int, str]:
    """Restart a system service. / 重启系统服务。"""
    if IS_WINDOWS:
        return run_ps(f"Restart-Service {service}")
    return run_cmd(["sudo", "systemctl", "restart", service])


def service_enable(service: str) -> tuple[int, str]:
    """Enable a service to start on boot. / 设置服务开机自启。"""
    if IS_WINDOWS:
        return run_ps(f"Set-Service -Name {service} -StartupType Automatic")
    return run_cmd(["sudo", "systemctl", "enable", service])


def service_disable(service: str) -> tuple[int, str]:
    """Disable a service from starting on boot. / 禁止服务开机自启。"""
    if IS_WINDOWS:
        return run_ps(f"Set-Service -Name {service} -StartupType Manual")
    return run_cmd(["sudo", "systemctl", "disable", service])


def service_is_active(service: str) -> bool:
    """Check if a service is currently running. / 检查服务是否正在运行。"""
    if IS_WINDOWS:
        code, out = run_ps(
            f"Get-Service {service} | Select-Object -ExpandProperty Status"
        )
        return code == 0 and "Running" in out
    code, _ = run_cmd(["systemctl", "is-active", service])
    return code == 0


def service_is_enabled(service: str) -> bool:
    """Check if a service is enabled on boot. / 检查服务是否开机自启。"""
    if IS_WINDOWS:
        code, out = run_ps(
            f"Get-Service {service} | Select-Object -ExpandProperty StartType"
        )
        return code == 0 and "Automatic" in out
    code, _ = run_cmd(["systemctl", "is-enabled", service])
    return code == 0


def service_status(service: str) -> str:
    """Get service status as a string. / 获取服务状态字符串。"""
    if IS_WINDOWS:
        code, out = run_ps(
            f"Get-Service {service} | Select-Object -ExpandProperty Status"
        )
        return out if code == 0 else "unknown"
    code, out = run_cmd(["systemctl", "is-active", service])
    return out if code == 0 else "inactive"


# ── Package management ──────────────────────────────────────────

def package_install(package: str, distro: str, *, update_first: bool = False) -> int:
    """Install a package using the distro's package manager.

    使用发行版包管理器安装软件包。

    Args:
        package: Package name / 包名
        distro: Distribution identifier / 发行版标识
        update_first: Run apt-get update before install (Debian only) /
                      安装前先运行 apt-get update（仅 Debian）

    Returns:
        Exit code (0 = success) / 退出码（0 = 成功）
    """
    if IS_WINDOWS:
        # Windows: try winget, fall back to chocolatey
        # Windows：先尝试 winget，回退到 chocolatey
        if command_exists("winget"):
            code = run_verbose(["winget", "install", "--id", package, "-e"])
            if code == 0:
                return 0
        if command_exists("choco"):
            return run_verbose(["choco", "install", package, "-y"])
        return 1

    # Debian: optionally refresh index first
    # Debian：可选先刷新索引
    if update_first and distro in ("debian", "ubuntu"):
        run_verbose(["sudo", "apt-get", "update", "-qq"])

    if distro == "arch":
        return run_verbose(["sudo", "pacman", "-S", "--noconfirm", package])
    elif distro == "fedora":
        return run_verbose(["sudo", "dnf", "install", "-y", package])
    elif distro == "suse":
        return run_verbose(["sudo", "zypper", "install", "-y", package])
    else:
        return run_verbose(["sudo", "apt-get", "install", "-y", package])


def package_is_installed(package: str, distro: str) -> bool:
    """Check if a package is installed.

    检查软件包是否已安装。

    Args:
        package: Package name / 包名
        distro: Distribution identifier / 发行版标识

    Returns:
        True if installed / 已安装时返回 True
    """
    if IS_WINDOWS:
        # winget: search installed packages
        if command_exists("winget"):
            code, out = run_cmd(["winget", "list", "--id", package])
            if code == 0 and package.lower() in out.lower():
                return True
        # chocolatey: choco list --local-only
        if command_exists("choco"):
            code, out = run_cmd(["choco", "list", "--local-only", package])
            if code == 0 and package.lower() in out.lower():
                return True
        return False

    if distro == "arch":
        code, _ = run_cmd(["pacman", "-Qi", package])
    elif distro in ("fedora", "suse"):
        code, _ = run_cmd(["rpm", "-q", package])
    else:
        code, _ = run_cmd(["dpkg", "-s", package])
    return code == 0


# ── OS information ──────────────────────────────────────────────

def os_version_string() -> str:
    """Get a human-readable OS version string.

    获取人类可读的操作系统版本字符串。

    Returns:
        e.g. "Linux 6.1.0" or "Windows 10.0.19045"
    """
    plt = detect_platform()
    if plt == "windows":
        return f"Windows {platform_mod.version()}"
    elif plt == "macos":
        return f"macOS {platform_mod.mac_ver()[0]}"
    else:
        return f"Linux {platform_mod.release()}"


def os_display_name() -> str:
    """Get a short OS display name.

    获取简短的操作系统显示名称。

    Returns:
        e.g. "Linux", "Windows", "macOS"
    """
    return detect_platform().capitalize()
