import subprocess
import sys
from pathlib import Path

from tools.base import Tool
from utils.i18n import t


def _run(cmd: list[str]) -> tuple[int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def _run_verbose(cmd: list[str]) -> int:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    proc.wait()
    return proc.returncode


def _is_btrfs_root() -> bool:
    code, out = _run(["findmnt", "-n", "-o", "FSTYPE", "/"])
    return out.strip() == "btrfs"


def _snapper_installed() -> bool:
    code, _ = _run(["which", "snapper"])
    return code == 0


class BtrfsSnapshotTool(Tool):
    name = "btrfs-snapshot"
    display_name = "BTRFS Snapshots"
    description = "Create, list, and manage BTRFS snapshots via snapper"
    distros = ["arch", "debian"]

    def _install_snapper(self, distro: str) -> bool:
        if _snapper_installed():
            print(t("msg.already_installed", package="snapper"))
            return True
        print(t("msg.installing", package="snapper"))
        if distro == "arch":
            ok = _run_verbose(["sudo", "pacman", "-S", "--noconfirm", "snapper"])
        else:
            ok = _run_verbose(["sudo", "apt-get", "install", "-y", "snapper"])
        return ok == 0

    def _show_menu(self) -> str:
        print(t("msg.snapshot_menu"))
        print("-" * 40)
        print(f"  [1] {t('msg.snapshot_create')}")
        print(f"  [2] {t('msg.snapshot_list')}")
        print(f"  [3] {t('msg.snapshot_delete')}")
        print(f"  [4] {t('msg.snapshot_rollback')}")
        print("-" * 40)
        return input(t("ui.select")).strip()

    def _create_snapshot(self) -> None:
        desc = input(t("msg.snapshot_description")).strip()
        if not desc:
            desc = "manual snapshot"
        code = _run_verbose(["sudo", "snapper", "create", "-d", desc])
        if code == 0:
            print(t("msg.snapshot_created"))
        else:
            print(t("msg.snapshot_create_failed"))

    def _list_snapshots(self) -> None:
        _run_verbose(["sudo", "snapper", "list"])

    def _delete_snapshot(self) -> None:
        snap_id = input(t("msg.snapshot_id")).strip()
        if not snap_id:
            return
        code = _run_verbose(["sudo", "snapper", "delete", snap_id])
        if code == 0:
            print(t("msg.snapshot_deleted"))
        else:
            print(t("msg.snapshot_delete_failed"))

    def _rollback_snapshot(self) -> None:
        snap_id = input(t("msg.snapshot_id")).strip()
        if not snap_id:
            return
        print(t("msg.snapshot_rollback_warning"))
        confirm = input(t("msg.confirm")).strip().lower()
        if confirm != "y":
            return
        code = _run_verbose(["sudo", "snapper", "rollback", snap_id])
        if code == 0:
            print(t("msg.snapshot_rolled_back"))
        else:
            print(t("msg.snapshot_rollback_failed"))

    def run(self) -> bool:
        if not _is_btrfs_root():
            print(t("msg.not_btrfs"))
            return False

        # Get distro for snapper installation
        os_release = Path("/etc/os-release")
        distro = "arch"
        if os_release.exists():
            data = os_release.read_text()
            if "ID=arch" not in data and "ID_LIKE=arch" not in data:
                distro = "debian"

        if not self._install_snapper(distro):
            print(t("msg.install_failed", package="snapper"))
            return False

        while True:
            choice = self._show_menu()
            if choice == "1":
                self._create_snapshot()
            elif choice == "2":
                self._list_snapshots()
            elif choice == "3":
                self._delete_snapshot()
            elif choice == "4":
                self._rollback_snapshot()
            else:
                break
        return True
