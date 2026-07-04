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

# Per-run dedup flag for apt-get update / 每次运行只执行一次 apt-get update
_apt_index_refreshed = False


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

def _parse_pkg_names(package: str) -> tuple[str, str]:
    """Parse a package name into (winget_id, choco_name).

    解析包名为 (winget_id, choco_name)。

    Supports plain strings (used as-is for both backends) and
    "winget_id::choco_name" mapping format.

    支持普通字符串（两个后端通用）和 "winget_id::choco_name" 映射格式。
    """
    if "::" in package:
        winget_id, choco_name = package.split("::", 1)
        return winget_id, choco_name
    return package, package


def _ensure_apt_index(distro: str) -> None:
    """Run apt-get update once per process for Debian-based distros.

    为 Debian 系发行版在每个进程中只执行一次 apt-get update。
    """
    global _apt_index_refreshed
    if not _apt_index_refreshed and distro in ("debian", "ubuntu"):
        run_verbose(["sudo", "apt-get", "update", "-qq"])
        _apt_index_refreshed = True


def package_install(package: str, distro: str) -> int:
    """Install a single package using the distro's package manager.

    使用发行版包管理器安装单个软件包。

    On Windows, tries winget first, falls back to chocolatey.
    Supports "winget_id::choco_name" mapping format.

    Windows 上先尝试 winget，回退到 chocolatey。支持 "winget_id::choco_name" 映射格式。

    On Debian-based distros, automatically runs apt-get update once per process.

    Debian 系发行版在首次安装前自动执行 apt-get update。

    Args:
        package: Package name (plain or winget::choco mapping) /
                 包名（普通或 winget::choco 映射格式）
        distro: Distribution identifier / 发行版标识

    Returns:
        Exit code (0 = success) / 退出码（0 = 成功）
    """
    if IS_WINDOWS:
        winget_id, choco_name = _parse_pkg_names(package)
        if command_exists("winget"):
            code = run_verbose(["winget", "install", "--id", winget_id, "-e", "--accept-source-agreements"])
            if code == 0:
                return 0
        if command_exists("choco"):
            return run_verbose(["choco", "install", choco_name, "-y"])
        return 1

    # Linux: delegate to batch function for single package
    # Linux：委托给批量函数处理单个包
    return packages_install([package], distro)


def packages_install(packages: list[str], distro: str) -> int:
    """Install multiple packages in a single operation.

    单次操作安装多个软件包。

    More efficient than calling package_install() in a loop — uses one
    subprocess call per distro instead of one per package.

    比循环调用 package_install() 更高效 — 每个发行版只用一次子进程调用。

    Args:
        packages: List of package names / 包名列表
        distro: Distribution identifier / 发行版标识

    Returns:
        Exit code (0 = all succeeded) / 退出码（0 = 全部成功）
    """
    if not packages:
        return 0

    if IS_WINDOWS:
        # Try winget first for each package, collect failures for choco batch
        # 先尝试 winget 安装每个包，收集失败的包用于 choco 批量安装
        choco_candidates = []
        for pkg in packages:
            winget_id, choco_name = _parse_pkg_names(pkg)
            if command_exists("winget"):
                code = run_verbose(["winget", "install", "--id", winget_id, "-e", "--accept-source-agreements"])
                if code == 0:
                    continue
            choco_candidates.append(choco_name)
        # Batch-install remaining packages via choco
        # 通过 choco 批量安装剩余包
        if choco_candidates:
            if command_exists("choco"):
                return run_verbose(["choco", "install"] + choco_candidates + ["-y"])
            return 1
        return 0

    _ensure_apt_index(distro)

    if distro == "arch":
        return run_verbose(["sudo", "pacman", "-S", "--noconfirm"] + packages)
    elif distro == "fedora":
        return run_verbose(["sudo", "dnf", "install", "-y"] + packages)
    elif distro == "suse":
        return run_verbose(["sudo", "zypper", "install", "-y"] + packages)
    else:
        return run_verbose(["sudo", "apt-get", "install", "-y"] + packages)


def package_is_installed(package: str, distro: str) -> bool:
    """Check if a package is installed.

    检查软件包是否已安装。

    Args:
        package: Package name (plain or winget::choco mapping) /
                 包名（普通或 winget::choco 映射格式）
        distro: Distribution identifier / 发行版标识

    Returns:
        True if installed / 已安装时返回 True
    """
    if IS_WINDOWS:
        winget_id, choco_name = _parse_pkg_names(package)

        if command_exists("winget"):
            code, out = run_cmd(["winget", "list", "--id", winget_id, "--accept-source-agreements"])
            if code == 0 and winget_id.lower() in out.lower():
                return True
        if command_exists("choco"):
            code, out = run_cmd(["choco", "list", "--local-only", choco_name, "--limit-output"])
            # choco --limit-output: "packagename|version" per line
            if code == 0:
                for line in out.splitlines():
                    if line.split("|")[0].lower() == choco_name.lower():
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
