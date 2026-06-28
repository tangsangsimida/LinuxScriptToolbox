"""System Cleanup — clean package caches, journal logs, and temporary files."""

import shutil
from pathlib import Path

from tools.base import Tool
from . import system_cleanup_translations  # noqa: F401 - side-effect import for i18n registration
from utils.cmd_utils import run_cmd, run_verbose
from utils.distro import detect_distro
from utils.i18n import t
from utils.platform import command_exists
from utils.ui import (
    print_success,
    print_error,
    print_info,
    print_warning,
    confirm,
    console,
    prompt_selection,
    BACK_ACTION,
)

CLEANUP_OPTIONS = [
    {
        "id": "pkg-cache",
        "name_key": "msg.cleanup_pkg_cache",
        "desc_key": "msg.cleanup_pkg_cache_desc",
    },
    {
        "id": "journal",
        "name_key": "msg.cleanup_journal",
        "desc_key": "msg.cleanup_journal_desc",
    },
    {
        "id": "temp-files",
        "name_key": "msg.cleanup_temp",
        "desc_key": "msg.cleanup_temp_desc",
    },
    {
        "id": "all",
        "name_key": "msg.cleanup_all",
        "desc_key": "msg.cleanup_all_desc",
    },
]


# Clean package manager cache.

def _clean_pkg_cache(distro: str) -> bool:
    print_info(t("msg.cleanup_pkg_cache_running"))

    if distro == "arch":
        # Keep only the latest version of each package
        code = run_verbose(["sudo", "pacman", "-Sc", "--noconfirm"])
    elif distro == "fedora":
        code = run_verbose(["sudo", "dnf", "clean", "all"])
    elif distro == "suse":
        code = run_verbose(["sudo", "zypper", "clean", "--all"])
    else:
        # Debian/Ubuntu
        code = run_verbose(["sudo", "apt-get", "clean"])
        if code == 0:
            run_verbose(["sudo", "apt-get", "autoremove", "-y"])

    if code != 0:
        print_error(t("msg.cleanup_pkg_cache_failed"))
        return False

    print_success(t("msg.cleanup_pkg_cache_success"))
    return True


# Clean systemd journal logs older than 7 days.

def _clean_journal() -> bool:
    print_info(t("msg.cleanup_journal_running"))

    # Check if journalctl exists
    if not command_exists("journalctl"):
        print_warning(t("msg.cleanup_journal_not_found"))
        return True

    # Show current journal size
    code, size = run_cmd(["journalctl", "--disk-usage"])
    if code == 0:
        print_info(t("msg.cleanup_journal_size", size=size))

    # Clean logs older than 7 days
    code = run_verbose(["sudo", "journalctl", "--vacuum-time=7d"])
    if code != 0:
        print_error(t("msg.cleanup_journal_failed"))
        return False

    print_success(t("msg.cleanup_journal_success"))
    return True


# Clean temporary files.

def _clean_temp_files() -> bool:
    print_info(t("msg.cleanup_temp_running"))

    # Clean /tmp files older than 7 days
    code = run_verbose(["sudo", "find", "/tmp", "-type", "f", "-atime", "+7", "-delete"])
    if code != 0:
        print_warning(t("msg.cleanup_temp_partial"))

    # Clean user cache
    cache_dir = Path.home() / ".cache"
    if cache_dir.exists():
        try:
            # Get size before cleaning
            code, size_before = run_cmd(["du", "-sh", str(cache_dir)])
            if code == 0:
                print_info(t("msg.cleanup_temp_cache_size", size=size_before))

            # Clean thumbnails and other cache files
            thumbnails = cache_dir / "thumbnails"
            if thumbnails.exists():
                shutil.rmtree(thumbnails, ignore_errors=True)

            print_success(t("msg.cleanup_temp_success"))
        except Exception as e:
            print_warning(t("msg.cleanup_temp_error", error=str(e)))
    else:
        print_info(t("msg.cleanup_temp_no_cache"))

    return True


class SystemCleanup(Tool):
    name = "system-cleanup"
    display_name = "System Cleanup"
    description = "Clean package caches, journal logs, and temporary files"
    distros = ["arch", "debian", "fedora", "suse", "unknown"]
    group = "system"
    requires_sudo = True

    def run(self) -> bool | None:
        distro = detect_distro()

        choice = prompt_selection(t("msg.cleanup_select"), CLEANUP_OPTIONS)

        if choice is None or choice == BACK_ACTION:
            return None

        selected = next((opt for opt in CLEANUP_OPTIONS if opt["id"] == choice), None)
        if selected is None:
            print_error(t("ui.invalid_selection"))
            return False

        if not confirm(t("msg.cleanup_confirm", action=t(selected["name_key"]))):
            return None

        console.print()

        if choice == "pkg-cache":
            return _clean_pkg_cache(distro)
        elif choice == "journal":
            return _clean_journal()
        elif choice == "temp-files":
            return _clean_temp_files()
        elif choice == "all":
            ok = True
            if not _clean_pkg_cache(distro):
                ok = False
            if not _clean_journal():
                ok = False
            if not _clean_temp_files():
                ok = False
            return ok

        print_error(t("ui.invalid_selection"))
        return False


    # Preview cleanup operations.

    def run_dry(self) -> str | None:
        distro = detect_distro()
        lines = ["[DRY-RUN] System Cleanup would:", ""]
        if distro == "arch":
            lines.append("  Package cache: pacman -Scc")
        elif distro in ("debian", "ubuntu"):
            lines.append("  Package cache: apt-get clean && apt-get autoremove")
        elif distro == "fedora":
            lines.append("  Package cache: dnf clean all")
        elif distro == "suse":
            lines.append("  Package cache: zypper clean")
        lines.append("  Journal logs: journalctl --vacuum-time=7d")
        lines.append("  Temp files: clean /tmp and ~/.cache/")
        return "\n".join(lines)
