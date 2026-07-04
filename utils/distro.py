from pathlib import Path


def detect_distro() -> str:
    os_release = Path("/etc/os-release")
    if os_release.exists():
        data = os_release.read_text()
        if "ID=arch" in data or "ID_LIKE=arch" in data:
            return "arch"
        if "ID=debian" in data or "ID=ubuntu" in data or "ID_LIKE=debian" in data:
            return "debian"
        if "ID=fedora" in data:
            return "fedora"
        if "ID=opensuse" in data or "ID=suse" in data:
            return "suse"
        # Alibaba Cloud Linux uses ID=alinux; based on RHEL/CentOS/Anolis.
        # Report it as its own identifier so the menu shows a meaningful name;
        # tools that opt in to "unknown" will still match it today.
        # Match both unquoted (ID=alinux) and quoted (ID="alinux") forms so the
        # detection works against real /etc/os-release files, which always quote.
        # 阿里云 Linux 使用 ID=alinux，基于 RHEL/CentOS/Anolis。
        # 作为独立标识符返回，以便菜单显示有意义的名称；
        # 当前声明 distros 含 unknown 的工具仍会匹配它。
        # 同时匹配不带引号（ID=alinux）和带引号（ID="alinux"）两种形式，
        # 因为真实 /etc/os-release 文件始终对 ID 加引号。
        if 'ID="alinux"' in data or "ID=alinux" in data:
            return "alinux"
    return "unknown"
