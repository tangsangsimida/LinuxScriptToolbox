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
    return "unknown"
