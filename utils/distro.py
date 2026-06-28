"""Distribution detection — identifies the Linux distribution.

发行版检测 — 识别当前 Linux 发行版。

On non-Linux platforms, returns a platform-specific identifier.
Reads /etc/os-release to determine the distro family.

在非 Linux 平台上返回平台特定标识符。
通过读取 /etc/os-release 来确定发行版系列。
"""

from pathlib import Path

from utils.platform import detect_platform


def detect_distro() -> str:
    """Detect the current distribution or platform.

    检测当前发行版或平台。

    Reads /etc/os-release on Linux to map the running system to one
    of the supported distro families. On Windows/macOS, returns the
    platform name directly.

    在 Linux 上读取 /etc/os-release，将运行系统映射到支持的发行版系列。
    在 Windows/macOS 上直接返回平台名称。

    Returns:
        Linux: "arch", "debian", "fedora", "suse", "unknown"
        Windows: "windows"
        macOS: "macos"
    """
    platform = detect_platform()

    # Non-Linux platforms return their name directly / 非 Linux 平台直接返回名称
    if platform == "windows":
        return "windows"
    elif platform == "macos":
        return "macos"

    # Linux distribution detection via /etc/os-release
    # 通过 /etc/os-release 检测 Linux 发行版
    os_release = Path("/etc/os-release")
    if os_release.exists():
        data = os_release.read_text()
        # Parse key=value lines (os-release spec: KEY=VALUE with optional quoting)
        # 按行解析 key=value 格式（os-release 规范：KEY=VALUE，可选引号）
        parsed: dict[str, str] = {}
        for line in data.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                parsed[key.strip()] = value.strip("\"'")
        
        distro_id = parsed.get("ID", "")
        id_like = parsed.get("ID_LIKE", "")
        
        # Arch: exact ID=arch or ID_LIKE contains arch (e.g. Manjaro)
        # Arch：精确匹配 ID=arch 或 ID_LIKE 包含 arch（如 Manjaro）
        if distro_id == "arch" or "arch" in id_like.split():
            return "arch"
        # Debian/Ubuntu: exact ID=debian, ID=ubuntu, or ID_LIKE contains debian
        # Debian/Ubuntu：精确匹配 ID=debian、ID=ubuntu 或 ID_LIKE 包含 debian
        if distro_id in ("debian", "ubuntu") or "debian" in id_like.split():
            return "debian"
        # Fedora: exact ID=fedora / Fedora：精确匹配 ID=fedora
        if distro_id == "fedora":
            return "fedora"
        # openSUSE: ID starts with opensuse, or ID=suse, or ID_LIKE contains suse
        # openSUSE：ID 以 opensuse 开头，或 ID=suse，或 ID_LIKE 包含 suse
        if distro_id.startswith("opensuse") or distro_id == "suse" or "suse" in id_like.split():
            return "suse"
    return "unknown"
