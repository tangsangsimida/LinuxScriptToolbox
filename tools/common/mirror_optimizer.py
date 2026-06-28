"""Unified mirror optimizer — auto-detects package manager and applies China mirrors."""

import re
from pathlib import Path

from tools.base import Tool
from . import mirror_optimizer_translations  # noqa: F401 - side-effect import for i18n registration
from utils.platform import command_exists
from utils.sudo_utils import write_file, copy_file, need_sudo
from utils.i18n import t
from utils.ui import print_success, print_error, print_info

BACKUP_SUFFIX = ".bak"
MANAGED_BLOCK_START = "# BEGIN LinuxScriptToolbox China mirrors"
MANAGED_BLOCK_END = "# END LinuxScriptToolbox China mirrors"

# ── China mirror hosts ──────────────────────────────────────────

CHINA_MIRROR_HOSTS = [
    "mirrors.ustc.edu.cn",
    "mirrors.tuna.tsinghua.edu.cn",
    "mirrors.aliyun.com",
    "mirrors.163.com",
    "repo.huaweicloud.com",
]

CHINA_ARCH_MIRRORS = [
    f"https://{h}/archlinux/$repo/os/$arch" for h in CHINA_MIRROR_HOSTS
]

# ── Package manager detection ───────────────────────────────────

# Detect the active package manager.

def _detect_pkg_manager() -> str | None:
    for pm in ["pacman", "apt", "dnf", "zypper"]:
        if command_exists(pm):
            return pm
    return None


# ── Arch (pacman) ───────────────────────────────────────────────

PACMAN_MIRRORLIST = Path("/etc/pacman.d/mirrorlist")


def _optimize_arch() -> bool:
    if not PACMAN_MIRRORLIST.exists():
        print_error(t("msg.mirrorlist_not_found"))
        return False

    if need_sudo(PACMAN_MIRRORLIST):
        print_info(t("msg.root_required"))

    # Backup
    backup_path = PACMAN_MIRRORLIST.with_suffix(PACMAN_MIRRORLIST.suffix + BACKUP_SUFFIX)
    if not backup_path.exists():
        copy_file(PACMAN_MIRRORLIST, backup_path)
        print_info(t("msg.backup_saved", path=str(backup_path)))
    else:
        print_info(t("msg.backup_exists"))

    original = PACMAN_MIRRORLIST.read_text() if PACMAN_MIRRORLIST.exists() else ""
    content = _prepend_managed_block(original, [f"Server = {m}" for m in CHINA_ARCH_MIRRORS])

    write_file(PACMAN_MIRRORLIST, content)
    print_success(t("msg.mirrorlist_updated"))
    return True


def _strip_managed_block(content: str) -> str:
    pattern = (
        rf"{re.escape(MANAGED_BLOCK_START)}\n"
        rf".*?\n"
        rf"{re.escape(MANAGED_BLOCK_END)}\n*"
    )
    return re.sub(pattern, "", content, flags=re.DOTALL)


def _prepend_managed_block(content: str, lines: list[str]) -> str:
    remaining = _strip_managed_block(content).lstrip("\n")
    block = "\n".join([MANAGED_BLOCK_START, *lines, MANAGED_BLOCK_END])
    if remaining:
        return f"{block}\n\n{remaining}"
    return f"{block}\n"


# ── Debian/Ubuntu (apt) ─────────────────────────────────────────

SOURCES_LIST = Path("/etc/apt/sources.list")
SOURCES_LIST_DIR = Path("/etc/apt/sources.list.d")


def _get_apt_sources_path() -> Path | None:
    if SOURCES_LIST_DIR.exists():
        for sources in sorted(SOURCES_LIST_DIR.glob("*.sources")):
            if sources.is_file():
                return sources
    if SOURCES_LIST.exists():
        content = SOURCES_LIST.read_text().strip()
        if content and not content.startswith("# Ubuntu sources have moved"):
            return SOURCES_LIST
    return None


def _parse_deb822(content: str) -> list[dict[str, str]]:
    stanzas = []
    current: dict[str, str] = {}
    for line in content.splitlines():
        if not line.strip():
            if current:
                stanzas.append(current)
                current = {}
        elif line.startswith("#"):
            continue
        elif ":" in line:
            key, _, val = line.partition(":")
            current[key.strip()] = val.strip()
    if current:
        stanzas.append(current)
    return stanzas


def _build_deb822(stanzas: list[dict[str, str]]) -> str:
    blocks = []
    for s in stanzas:
        lines = [f"{k}: {v}" for k, v in s.items()]
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def _optimize_deb822(content: str) -> str:
    family = "ubuntu" if re.search(r"URIs:\s+\S*ubuntu", content) else "debian"
    mirror = f"https://{CHINA_MIRROR_HOSTS[0]}/{family}/"
    stanzas = _parse_deb822(content)
    for s in stanzas:
        if "URIs" in s:
            s["URIs"] = mirror
    return _build_deb822(stanzas)


def _detect_apt_repo(content: str) -> tuple[str, str, str]:
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        match = re.match(r"(?:deb|deb-src)\s+https?://\S+/(\S+)\s+(\S+)", line)
        if match:
            archive = match.group(1)
            codename = match.group(2)
            family = "ubuntu" if "ubuntu" in archive else "debian"
            return archive, codename, family
    return "debian", "bookworm", "debian"


def _optimize_traditional(content: str) -> str:
    archive, codename, family = _detect_apt_repo(content)
    mirror = CHINA_MIRROR_HOSTS[0]

    if family == "ubuntu":
        comp = "main restricted universe multiverse"
        lines = [
            "# China mirror (fastest for mainland China)",
            f"deb https://{mirror}/{archive} {codename} {comp}",
            f"deb-src https://{mirror}/{archive} {codename} {comp}",
            "",
            f"deb https://{mirror}/{archive} {codename}-updates {comp}",
            f"deb-src https://{mirror}/{archive} {codename}-updates {comp}",
            "",
            f"deb https://{mirror}/{archive} {codename}-backports {comp}",
            f"deb-src https://{mirror}/{archive} {codename}-backports {comp}",
            "",
            f"deb https://{mirror}/{archive} {codename}-security {comp}",
            f"deb-src https://{mirror}/{archive} {codename}-security {comp}",
        ]
    else:
        comp = "main contrib non-free non-free-firmware"
        lines = [
            "# China mirror (fastest for mainland China)",
            f"deb https://{mirror}/{archive} {codename} {comp}",
            f"deb-src https://{mirror}/{archive} {codename} {comp}",
            "",
            f"deb https://{mirror}/{archive} {codename}-updates {comp}",
            f"deb-src https://{mirror}/{archive} {codename}-updates {comp}",
            "",
            f"deb https://{mirror}/{archive}-security {codename}-security {comp}",
            f"deb-src https://{mirror}/{archive}-security {codename}-security {comp}",
        ]
    return "\n".join(lines) + "\n"


def _optimize_apt() -> bool:
    sources_path = _get_apt_sources_path()
    if sources_path is None:
        print_error(t("msg.sources_list_not_found"))
        return False

    is_deb822 = sources_path.suffix == ".sources"
    fmt = "deb822" if is_deb822 else "traditional"
    print_info(t("msg.detected_format", format=fmt, path=str(sources_path)))

    if need_sudo(sources_path):
        print_info(t("msg.root_required"))

    # Backup
    backup_path = sources_path.with_suffix(sources_path.suffix + BACKUP_SUFFIX)
    if not backup_path.exists():
        copy_file(sources_path, backup_path)
        print_info(t("msg.backup_saved", path=str(backup_path)))
    else:
        print_info(t("msg.backup_exists"))

    content = sources_path.read_text()
    if is_deb822:
        new_content = _optimize_deb822(content)
    else:
        new_content = _optimize_traditional(content)

    write_file(sources_path, new_content)
    print_success(t("msg.sources_list_updated"))
    return True


# ── Fedora (dnf) ────────────────────────────────────────────────

FEDORA_REPO_DIR = Path("/etc/yum.repos.d")
FEDORA_MIRROR = f"https://{CHINA_MIRROR_HOSTS[0]}/fedora"


def _optimize_fedora() -> bool:
    if not FEDORA_REPO_DIR.exists():
        print_error(t("msg.repo_dir_not_found", path=str(FEDORA_REPO_DIR)))
        return False

    if need_sudo(FEDORA_REPO_DIR):
        print_info(t("msg.root_required"))

    repo_files = list(FEDORA_REPO_DIR.glob("fedora*.repo"))
    if not repo_files:
        print_error(t("msg.repo_files_not_found"))
        return False

    for repo_file in repo_files:
        # Backup
        backup_path = repo_file.with_suffix(repo_file.suffix + BACKUP_SUFFIX)
        if not backup_path.exists():
            copy_file(repo_file, backup_path)
            print_info(t("msg.backup_saved", path=str(backup_path)))

        content = repo_file.read_text()
        # Comment out metalink, replace baseurl with China mirror
        new_lines = []
        for line in content.splitlines():
            if line.strip().startswith("metalink="):
                new_lines.append(f"# {line}")
            elif line.strip().startswith("baseurl="):
                # Replace the host with China mirror
                new_line = re.sub(
                    r"baseurl=https?://[^/]+",
                    f"baseurl={FEDORA_MIRROR}",
                    line,
                )
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        write_file(repo_file, "\n".join(new_lines) + "\n")

    print_success(t("msg.mirrorlist_updated"))
    return True


# ── openSUSE (zypper) ───────────────────────────────────────────

SUSE_REPO_DIR = Path("/etc/zypp/repos.d")
SUSE_MIRROR = f"https://{CHINA_MIRROR_HOSTS[0]}/opensuse"


def _optimize_suse() -> bool:
    if not SUSE_REPO_DIR.exists():
        print_error(t("msg.repo_dir_not_found", path=str(SUSE_REPO_DIR)))
        return False

    if need_sudo(SUSE_REPO_DIR):
        print_info(t("msg.root_required"))

    repo_files = list(SUSE_REPO_DIR.glob("*.repo"))
    if not repo_files:
        print_error(t("msg.repo_files_not_found"))
        return False

    for repo_file in repo_files:
        backup_path = repo_file.with_suffix(repo_file.suffix + BACKUP_SUFFIX)
        if not backup_path.exists():
            copy_file(repo_file, backup_path)
            print_info(t("msg.backup_saved", path=str(backup_path)))

        content = repo_file.read_text()
        # Replace baseurl with China mirror
        new_lines = []
        for line in content.splitlines():
            if line.startswith("baseurl="):
                new_line = re.sub(
                    r"baseurl=https?://[^/]+",
                    f"baseurl={SUSE_MIRROR}",
                    line,
                )
                new_lines.append(new_line)
            else:
                new_lines.append(line)

        write_file(repo_file, "\n".join(new_lines) + "\n")

    print_success(t("msg.mirrorlist_updated"))
    return True


# ── Tool class ──────────────────────────────────────────────────

OPTIMIZERS = {
    "pacman": ("msg.pm_pacman", _optimize_arch),
    "apt": ("msg.pm_apt", _optimize_apt),
    "dnf": ("msg.pm_dnf", _optimize_fedora),
    "zypper": ("msg.pm_zypper", _optimize_suse),
}


class MirrorOptimizer(Tool):
    name = "mirror-optimizer"
    display_name = "Optimize Mirrors"
    description = "Replace package manager mirrors with China mirrors (supports any distro)"
    distros = ["arch", "debian", "fedora", "suse", "unknown"]
    requires_sudo = True

    def run(self) -> bool | None:
        pm = _detect_pkg_manager()
        if pm is None:
            print_error(t("msg.no_pkg_manager"))
            return False

        pm_key, optimizer = OPTIMIZERS[pm]
        print_info(t("msg.detected_pm", pm=t(pm_key)))

        return optimizer()


    # Preview package manager mirror changes without modifying files.

    def run_dry(self) -> str | None:
        pm = _detect_pkg_manager()
        if pm is None:
            return "No supported package manager detected. No changes would be made."
        lines = ["[DRY-RUN] Mirror Optimizer would:", "", f"  Package manager: {pm}"]
        if pm == "pacman":
            lines.append(f"  File to modify: {PACMAN_MIRRORLIST}")
            lines.append("  Would backup before modification.")
            for m in CHINA_ARCH_MIRRORS:
                lines.append(f"  Would add: Server = {m}")
        elif pm == "apt":
            lines.append("  Would replace APT sources with USTC mirror.")
            lines.append("  Files: /etc/apt/sources.list or sources.list.d/")
            lines.append("  Would backup before modification.")
        elif pm == "dnf":
            lines.append(f"  Directory: {FEDORA_REPO_DIR}")
            lines.append("  Would replace baseurl with USTC mirror in all .repo files.")
            lines.append("  Would backup before modification.")
        elif pm == "zypper":
            lines.append(f"  Directory: {SUSE_REPO_DIR}")
            lines.append("  Would replace baseurl with USTC mirror in all .repo files.")
            lines.append("  Would backup before modification.")
        elif pm in ("winget", "choco", "scoop"):
            lines.append(f"  Would configure {pm} to use China mirrors.")
        return "\n".join(lines)
