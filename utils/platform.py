"""Platform detection — identifies the operating system.

平台检测 — 识别当前操作系统。

Returns a platform string: "linux", "windows", or "macos".
Distro detection for Linux is handled separately in utils/distro.py.

返回平台字符串："linux"、"windows" 或 "macos"。
Linux 发行版的检测在 utils/distro.py 中单独处理。
"""

import functools
import os
import platform
import shutil


@functools.lru_cache(maxsize=1)
def detect_platform() -> str:
    """Detect the current operating system.

    检测当前操作系统。

    Uses platform.system() and caches the result since the OS never
    changes during a single process lifetime.

    使用 platform.system() 检测并缓存结果，因为操作系统在进程生命周期内不会改变。

    Returns:
        "linux", "windows", or "macos"
        "linux"、"windows" 或 "macos"
    """
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    return "linux"  # fallback / 回退默认值


# Convenience constant — importable by modules that need a bool check.
# 便捷常量 — 可被其他模块导入用于布尔判断。
IS_WINDOWS = detect_platform() == "windows"


def command_exists(name: str) -> bool:
    """Check whether *name* is on PATH (cross-platform).

    检查命令 *name* 是否存在于 PATH 中（跨平台）。

    Args:
        name: Command name to look for / 要查找的命令名称

    Returns:
        True if the command is found / 命令存在时返回 True
    """
    return shutil.which(name) is not None


def is_root() -> bool:
    """Check if the current process has root/admin privileges.

    检查当前进程是否拥有 root/管理员权限。

    On Windows, uses ctypes to check admin status.
    On Linux/macOS, checks if effective UID is 0.

    在 Windows 上使用 ctypes 检查管理员状态；
    在 Linux/macOS 上检查有效 UID 是否为 0。

    Returns:
        True if running with elevated privileges / 以提升权限运行时返回 True
    """
    if IS_WINDOWS:
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except (AttributeError, OSError):
            return False
    return os.geteuid() == 0
