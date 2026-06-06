"""Backup/Restore — backup and restore critical system configuration files."""

import shutil
from datetime import datetime
from pathlib import Path

from tools.base import Tool
from utils.cmd_utils import run_cmd
from utils.distro import detect_distro
from utils.i18n import t
from utils.sudo_utils import copy_file
from utils.ui import print_success, print_error, print_info, print_warning, confirm, console, prompt_selection, BACK_ACTION

BACKUP_DIR = Path.home() / ".config" / "LinuxScriptToolbox" / "backups"

BACKUP_OPTIONS = [
    {
        "id": "backup",
        "name_key": "msg.backup_create",
        "desc_key": "msg.backup_create_desc",
    },
    {
        "id": "restore",
        "name_key": "msg.backup_restore",
        "desc_key": "msg.backup_restore_desc",
    },
    {
        "id": "list",
        "name_key": "msg.backup_list",
        "desc_key": "msg.backup_list_desc",
    },
]

# Critical config files to backup
CONFIG_FILES = {
    "pacman-mirrorlist": "/etc/pacman.d/mirrorlist",
    "apt-sources": "/etc/apt/sources.list",
    "sshd-config": "/etc/ssh/sshd_config",
    "fstab": "/etc/fstab",
    "hosts": "/etc/hosts",
    "resolv": "/etc/resolv.conf",
}


def _get_backup_dir() -> Path:
    """Get or create backup directory."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUP_DIR


def _list_backups() -> list[dict]:
    """List available backups."""
    backup_dir = _get_backup_dir()
    backups = []

    for item in sorted(backup_dir.iterdir(), reverse=True):
        if item.is_dir():
            files = list(item.iterdir())
            backups.append({
                "id": item.name,
                "name_key": item.name,
                "desc_key": f"{len(files)} files",
            })

    return backups


def _create_backup() -> bool:
    """Create a backup of critical config files."""
    print_info(t("msg.backup_creating"))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = _get_backup_dir() / timestamp
    backup_path.mkdir(parents=True, exist_ok=True)

    backed_up = 0
    for name, path in CONFIG_FILES.items():
        src = Path(path)
        if src.exists():
            dst = backup_path / name
            try:
                # Use sudo for system files
                if str(src).startswith("/etc/"):
                    copy_file(str(src), str(dst))
                else:
                    shutil.copy2(src, dst)
                backed_up += 1
                print_info(t("msg.backup_file_backed", file=name))
            except Exception as e:
                print_warning(t("msg.backup_file_failed", file=name, error=str(e)))
        else:
            print_info(t("msg.backup_file_not_found", file=name))

    if backed_up == 0:
        print_error(t("msg.backup_no_files"))
        shutil.rmtree(backup_path, ignore_errors=True)
        return False

    print_success(t("msg.backup_created", path=str(backup_path), count=backed_up))
    return True


def _restore_backup() -> bool:
    """Restore a backup."""
    backups = _list_backups()

    if not backups:
        print_error(t("msg.backup_no_backups"))
        return False

    choice = prompt_selection(t("msg.backup_select_restore"), backups)

    if choice is None or choice == BACK_ACTION:
        return None

    backup_path = _get_backup_dir() / choice
    if not backup_path.exists():
        print_error(t("msg.backup_not_found", path=str(backup_path)))
        return False

    # List files in backup
    files = list(backup_path.iterdir())
    print_info(t("msg.backup_files_in_backup", count=len(files)))
    for f in files:
        print_info(f"  - {f.name}")

    if not confirm(t("msg.backup_confirm_restore")):
        return False

    # Restore files
    restored = 0
    for backup_file in files:
        # Find the original path
        original_path = None
        for name, path in CONFIG_FILES.items():
            if name == backup_file.name:
                original_path = path
                break

        if original_path:
            try:
                # Backup current file before restoring
                current = Path(original_path)
                if current.exists():
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    pre_restore = current.parent / f"{current.name}.pre-restore.{timestamp}"
                    copy_file(str(current), str(pre_restore))

                # Restore the file
                copy_file(str(backup_file), str(original_path))
                restored += 1
                print_info(t("msg.backup_file_restored", file=backup_file.name))
            except Exception as e:
                print_warning(t("msg.backup_restore_failed", file=backup_file.name, error=str(e)))

    print_success(t("msg.backup_restored", count=restored))
    return True


def _list_all_backups() -> bool:
    """List all available backups."""
    backups = _list_backups()

    if not backups:
        print_info(t("msg.backup_no_backups"))
        return True

    print_info(t("msg.backup_available"))
    for backup in backups:
        backup_path = _get_backup_dir() / backup["id"]
        files = list(backup_path.iterdir())
        print_info(f"  {backup['id']} ({len(files)} files)")

    return True


class BackupRestore(Tool):
    name = "backup-restore"
    display_name = "Backup/Restore"
    description = "Backup and restore critical system configuration files"
    distros = ["arch", "debian", "fedora", "suse", "unknown"]

    def run(self) -> bool | None:
        choice = prompt_selection(t("msg.backup_select"), BACKUP_OPTIONS)

        if choice is None or choice == BACK_ACTION:
            return None

        console.print()

        if choice == "backup":
            return _create_backup()
        elif choice == "restore":
            return _restore_backup()
        elif choice == "list":
            return _list_all_backups()

        print_error(t("ui.invalid_selection"))
        return False
